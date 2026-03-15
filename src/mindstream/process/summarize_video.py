from __future__ import annotations

from datetime import datetime
import os
import re
from collections import Counter
from pathlib import Path

import httpx

from mindstream.process.chunking import chunk_text
from mindstream.process.embeddings import generate_embedding
from mindstream.storage.models import PerVideoSummary, RawVideoRecord, SummaryGenerationResult, VideoMetadata
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
MAX_SUMMARY_INPUT = 1500


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


def summarize_chunk(chunk_text: str) -> str:
    prompt = f"Summarize the following transcript chunk into key points:\n\n{chunk_text}"
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


def summarize_transcript(transcript_text: str) -> str:
    transcript_input = transcript_text[:MAX_SUMMARY_INPUT]
    print(f"[Summaries] Transcript length: {len(transcript_text)}")
    print(f"[Summaries] Truncated input length: {len(transcript_input)}")
    prompt = (
        "Summarize the following YouTube transcript.\n\n"
        "Provide:\n"
        "- key topics discussed\n"
        "- main points\n"
        "- important claims\n\n"
        f"Transcript:\n{transcript_input}\n\n"
        "Return concise text."
    )
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


def _store_chunks(record: RawVideoRecord, chunks: list[dict[str, object]]) -> None:
    if not chunks:
        return

    video_id = record.metadata.video_id
    video_title = record.metadata.title
    published_at = record.metadata.published_at
    ingested_at = datetime.utcnow().isoformat()
    ids: list[str] = []
    embeddings: list[list[float]] = []
    documents: list[str] = []
    metadatas: list[dict[str, object]] = []

    print(f"[Chunking] Chunks created: {len(chunks)}")

    for chunk in chunks:
        chunk_index = int(chunk["chunk_index"])
        chunk_text = str(chunk["text"])
        embedding = generate_embedding(chunk_text)
        print(f"[Chunking] Chunk {chunk_index} length: {len(chunk_text)}")
        print(f"[Chunking] Chunk {chunk_index} embedding dimension: {len(embedding)}")
        ids.append(f"{video_id}_{chunk_index}")
        embeddings.append(embedding)
        documents.append(chunk_text)
        metadatas.append(
            {
                "video_id": video_id,
                "chunk_index": chunk_index,
                "video_title": video_title,
                "published_at": published_at,
                "source_type": "youtube",
                "content_type": "transcript_chunk",
                "ingested_at": ingested_at,
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


def summarize_video(record: RawVideoRecord) -> PerVideoSummary:
    transcript_text = " ".join(segment.text for segment in record.transcript_segments if segment.text.strip())
    chunks = chunk_text(transcript_text)
    print(f"[Chunking] Generated {len(chunks)} chunks for video {record.metadata.video_id}")
    transcript_summary = summarize_transcript(transcript_text) if transcript_text else ""

    return PerVideoSummary(
        video_id=record.metadata.video_id,
        topics=_extract_topics(transcript_summary or transcript_text),
        bullets=_extract_bullets(transcript_summary or transcript_text),
        notable_claims=[],
        confidence="MEDIUM",
    )


def _save_summary(summary: PerVideoSummary, output_dir: Path = SUMMARY_OUTPUT_DIR) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{summary.video_id}.json"
    file_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved per-video summary: {file_path.as_posix()}")
    return file_path.as_posix()


def generate_summaries(records: list[RawVideoRecord]) -> SummaryGenerationResult:
    result = SummaryGenerationResult()
    for record in records:
        if record.transcript_status != "AVAILABLE":
            result.skipped_videos.append(record.metadata.video_id)
            print(f"Skipping summary for: {record.metadata.video_id}")
            continue
        try:
            transcript_text = " ".join(
                segment.text for segment in record.transcript_segments if segment.text.strip()
            )
            chunks = chunk_text(transcript_text)
            print(f"[Chunking] Generated {len(chunks)} chunks for video {record.metadata.video_id}")
            transcript_summary = summarize_transcript(transcript_text) if transcript_text else ""

            summary = PerVideoSummary(
                video_id=record.metadata.video_id,
                topics=_extract_topics(transcript_summary or transcript_text),
                bullets=_extract_bullets(transcript_summary or transcript_text),
                notable_claims=[],
                confidence="MEDIUM",
            )

            print(f"[Summaries] Saving summary for {record.metadata.video_id}")
            _save_summary(summary)
            print(f"[Summaries] Summary saved for {record.metadata.video_id}")

            if chunks:
                try:
                    print(f"[Summaries] Storing chunks in Chroma for {record.metadata.video_id}")
                    _store_chunks(record, chunks)
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
            record = RawVideoRecord(
                metadata=video,
                transcript_segments=[],
                transcript_status="AVAILABLE",
            )
            record.transcript_segments = []
            transcript_summary = summarize_transcript(transcript_text) if transcript_text else ""
            return PerVideoSummary(
                video_id=video.video_id,
                topics=_extract_topics(transcript_summary or transcript_text),
                bullets=_extract_bullets(transcript_summary or transcript_text),
                notable_claims=[],
                confidence="MEDIUM",
            )

    return _CompatibilitySummarizer()
