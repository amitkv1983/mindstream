from __future__ import annotations

from datetime import datetime
import os
import re
from collections import Counter
from pathlib import Path

import httpx

from mindstream.process.chunking import chunk_text
from mindstream.process.embeddings import generate_embedding
from mindstream.storage.local_store import per_video_dir
from mindstream.storage.models import (
    PerVideoSummary,
    RawVideoRecord,
    SummaryGenerationResult,
    TranscriptSegment,
    VideoMetadata,
)
from mindstream.storage.vector_store import ChromaVectorStore


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "this",
    "they",
    "their",
    "or",
    "we",
    "you",
    "i",
    "our",
    "about",
    "but",
    "not",
    "if",
    "then",
    "than",
    "so",
    "can",
    "could",
    "should",
    "would",
    "into",
}
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "mistral:7b-instruct"
SUMMARY_OUTPUT_DIR = Path("data/per_video")
DIRECT_SUMMARY_THRESHOLD = 2000
MAX_SUMMARY_CHUNKS = 30


def _extract_topics(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    freq = Counter(word for word in words if word not in STOPWORDS)
    return [word for word, _count in freq.most_common(limit)]


def _extract_bullets(summary_text: str, limit: int = 5) -> list[str]:
    lines = []
    for raw_line in summary_text.splitlines():
        line = raw_line.strip().lstrip("-* ").strip()
        if len(line) < 12:
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    if lines:
        return lines
    sentences = re.split(r"(?<=[.!?])\s+", summary_text.strip())
    return [sentence.strip()[:300] for sentence in sentences if sentence.strip()][:limit]


def _ollama_generate(prompt: str) -> str:
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
    return str(data.get("response", "")).strip()


def summarize_chunk(chunk_text: str) -> str:
    prompt = (
        "You are summarizing one section of a YouTube transcript.\n\n"
        "Return 3-4 concise bullet points that capture the main ideas, claims, and takeaways.\n\n"
        f"Transcript chunk:\n{chunk_text}"
    )
    return _ollama_generate(prompt)


def summarize_full_transcript(transcript_text: str) -> str:
    transcript_text = transcript_text.strip()
    if not transcript_text:
        return ""

    if len(transcript_text) < DIRECT_SUMMARY_THRESHOLD:
        prompt = (
            "Summarize the following YouTube transcript.\n\n"
            "Provide concise bullet points covering key topics, main points, and important claims.\n\n"
            f"Transcript:\n{transcript_text}"
        )
        return _ollama_generate(prompt)

    transcript_chunks = chunk_text(transcript_text)[:MAX_SUMMARY_CHUNKS]
    print(f"[Summaries] Map-reduce chunk count: {len(transcript_chunks)}")
    chunk_summaries = []
    for chunk in transcript_chunks:
        summary = summarize_chunk(str(chunk["text"]))
        if summary:
            chunk_summaries.append(summary)

    combined_summary = "\n\n".join(
        f"Chunk {index + 1} summary:\n{summary}" for index, summary in enumerate(chunk_summaries)
    )
    reduce_prompt = (
        "You are combining partial transcript summaries into one final video summary.\n\n"
        "Return a concise final summary with 5-7 bullet points that remove repetition and preserve the most important ideas.\n\n"
        f"Partial summaries:\n{combined_summary}"
    )
    return _ollama_generate(reduce_prompt)


def _transcript_text(segments: list[TranscriptSegment]) -> str:
    return " ".join(segment.text for segment in segments if segment.text.strip())


def _format_segment_text(segment: TranscriptSegment) -> str:
    speaker = (segment.speaker or "Unknown").strip() or "Unknown"
    statement = segment.text.strip()
    return f"Speaker: {speaker}\nStatement: {statement}"


def _build_speaker_aware_chunks(
    segments: list[TranscriptSegment],
    chunk_size: int = 6000,
    overlap_segments: int = 1,
) -> list[dict[str, object]]:
    if not segments:
        return []

    chunks: list[dict[str, object]] = []
    buffer: list[TranscriptSegment] = []
    current_length = 0

    for segment in segments:
        if not segment.text.strip():
            continue

        formatted_segment = _format_segment_text(segment)
        if buffer and current_length + len(formatted_segment) > chunk_size:
            start_segment = buffer[0]
            combined_text = "\n\n".join(_format_segment_text(item) for item in buffer)
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "text": combined_text,
                    "speaker": start_segment.speaker or "Unknown",
                    "start_time": float(start_segment.start),
                }
            )
            buffer = buffer[-overlap_segments:] if overlap_segments > 0 else []
            current_length = sum(len(_format_segment_text(item)) for item in buffer)

        buffer.append(segment)
        current_length += len(formatted_segment)

    if buffer:
        start_segment = buffer[0]
        combined_text = "\n\n".join(_format_segment_text(item) for item in buffer)
        chunks.append(
            {
                "chunk_index": len(chunks),
                "text": combined_text,
                "speaker": start_segment.speaker or "Unknown",
                "start_time": float(start_segment.start),
            }
        )

    return chunks


def _store_chunks(record: RawVideoRecord, chunks: list[dict[str, object]], project_id: str = "default") -> None:
    if not chunks:
        return

    video_id = record.metadata.video_id
    video_title = record.metadata.title
    published_at = record.metadata.published_at
    channel = record.metadata.channel
    ingested_at = datetime.utcnow().isoformat()
    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict[str, object]] = []

    print(f"[Chunking] Chunks created: {len(chunks)}")

    for chunk in chunks:
        chunk_index = int(chunk["chunk_index"])
        chunk_body = str(chunk["text"])
        embedding = generate_embedding(chunk_body)
        print(f"[Chunking] Chunk {chunk_index} length: {len(chunk_body)}")
        print(f"[Chunking] Chunk {chunk_index} embedding dimension: {len(embedding)}")
        ids.append(f"{project_id}_{video_id}_{chunk_index}")
        embeddings.append(embedding)
        documents.append(chunk_body)
        metadatas.append(
            {
                "video_id": video_id,
                "chunk_index": chunk_index,
                "video_title": video_title,
                "channel": channel,
                "published_at": published_at,
                "source_type": "youtube",
                "content_type": "transcript_chunk",
                "ingested_at": ingested_at,
                "project_id": project_id,
                "speaker": str(chunk.get("speaker", "Unknown")),
                "start_time": float(chunk.get("start_time", 0.0)),
            }
        )

    store = ChromaVectorStore()
    store.add_chunks(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    print(f"[VectorStore] Stored {len(ids)} chunk embeddings for: {video_id}")


def _store_summary_embedding(
    record: RawVideoRecord,
    summary: PerVideoSummary,
    summary_text: str,
    project_id: str = "default",
) -> None:
    if not summary_text.strip():
        return

    embedding = generate_embedding(summary_text)
    store = ChromaVectorStore()
    store.add_video_summaries(
        ids=[f"{project_id}_{record.metadata.video_id}_summary"],
        embeddings=[embedding],
        documents=[summary_text],
        metadatas=[
            {
                "video_id": record.metadata.video_id,
                "video_title": record.metadata.title,
                "channel": record.metadata.channel,
                "project_id": project_id,
                "summary_topics": ", ".join(summary.topics),
            }
        ],
    )


def summarize_video(record: RawVideoRecord) -> PerVideoSummary:
    transcript_text = _transcript_text(record.transcript_segments)
    transcript_summary = summarize_full_transcript(transcript_text) if transcript_text else ""

    return PerVideoSummary(
        video_id=record.metadata.video_id,
        topics=_extract_topics(transcript_summary or transcript_text),
        bullets=_extract_bullets(transcript_summary or transcript_text),
        notable_claims=[],
        confidence="MEDIUM",
    )


def _save_summary(
    summary: PerVideoSummary,
    output_dir: Path | None = None,
    project_id: str = "default",
) -> str:
    output_dir = output_dir or per_video_dir(project_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{summary.video_id}.json"
    file_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved per-video summary: {file_path.as_posix()}")
    return file_path.as_posix()


def generate_summaries(records: list[RawVideoRecord], project_id: str = "default") -> SummaryGenerationResult:
    result = SummaryGenerationResult()
    for record in records:
        if record.transcript_status != "AVAILABLE":
            result.skipped_videos.append(record.metadata.video_id)
            print(f"Skipping summary for: {record.metadata.video_id}")
            continue
        try:
            transcript_text = _transcript_text(record.transcript_segments)
            chunks = _build_speaker_aware_chunks(record.transcript_segments)
            print(f"[Chunking] Generated {len(chunks)} chunks for video {record.metadata.video_id}")
            transcript_summary = summarize_full_transcript(transcript_text) if transcript_text else ""

            summary = PerVideoSummary(
                video_id=record.metadata.video_id,
                topics=_extract_topics(transcript_summary or transcript_text),
                bullets=_extract_bullets(transcript_summary or transcript_text),
                notable_claims=[],
                confidence="MEDIUM",
            )

            print(f"[Summaries] Saving summary for {record.metadata.video_id}")
            _save_summary(summary, output_dir=SUMMARY_OUTPUT_DIR if project_id == "default" else None, project_id=project_id)
            print(f"[Summaries] Summary saved for {record.metadata.video_id}")

            if transcript_summary:
                try:
                    print(f"[Summaries] Storing summary embedding in Chroma for {record.metadata.video_id}")
                    _store_summary_embedding(record, summary, transcript_summary, project_id=project_id)
                except Exception as exc:
                    warning = f"[Summaries] Summary embedding storage failed for {record.metadata.video_id}: {exc}"
                    print(warning)
                    result.errors.append(warning)

            if chunks:
                try:
                    print(f"[Summaries] Storing chunks in Chroma for {record.metadata.video_id}")
                    _store_chunks(record, chunks, project_id=project_id)
                except Exception as exc:
                    warning = f"[Summaries] Chunk storage failed for {record.metadata.video_id}: {exc}"
                    print(warning)
                    result.errors.append(warning)

            result.summaries.append(summary)
        except Exception as exc:
            message = f"Summary error for {record.metadata.video_id}: {exc}"
            print(message)
            result.errors.append(message)
    return result


def get_summarizer():
    class _CompatibilitySummarizer:
        def summarize(self, video: VideoMetadata, transcript_text: str) -> PerVideoSummary:
            transcript_summary = summarize_full_transcript(transcript_text) if transcript_text else ""
            return PerVideoSummary(
                video_id=video.video_id,
                topics=_extract_topics(transcript_summary or transcript_text),
                bullets=_extract_bullets(transcript_summary or transcript_text),
                notable_claims=[],
                confidence="MEDIUM",
            )

    return _CompatibilitySummarizer()
