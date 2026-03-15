"""Streamlit UI for Mindstream."""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout

import httpx
import streamlit as st

from mindstream.ingest.youtube_discovery import discover_videos
from mindstream.ingest.youtube_transcript import fetch_transcripts
from mindstream.process.embeddings import generate_embedding
from mindstream.process.summarize_video import generate_summaries
from mindstream.storage.vector_store import ChromaVectorStore
from mindstream.storage.models import DiscoveryResult, SummaryGenerationResult, TranscriptFetchResult


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
RAG_CHAT_MODEL = os.getenv("RAG_CHAT_MODEL", "mistral:7b-instruct")


def _parse_sources(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def _append_log(message: str) -> None:
    logs = st.session_state.get("logs", "")
    st.session_state["logs"] = f"{logs}{message}\n" if logs else f"{message}\n"


def _rag_answer(prompt: str) -> str:
    print(f"[RAG] Ollama base URL: {OLLAMA_BASE_URL}")
    print(f"[RAG] Chat model: {RAG_CHAT_MODEL}")
    query_embedding = generate_embedding(prompt)
    print(f"[RAG] Query embedding generated: {bool(query_embedding)}")
    store = ChromaVectorStore()
    results = store.query(query_embedding, n_results=3)

    documents = []
    result_documents = results.get("documents", [])
    if result_documents:
        documents = result_documents[0] or []

    retrieved_chunks = [str(document) for document in documents if str(document).strip()]
    print(f"[RAG] Retrieved {len(retrieved_chunks)} chunks")
    print("[RAG] Retrieved docs:")
    for chunk in retrieved_chunks:
        print(chunk[:200])
    context = "\n\n".join([chunk[:1000] for chunk in retrieved_chunks])
    print(f"[RAG] Context size: {len(context)} characters")
    if not context:
        return "I don't have enough indexed transcript context yet. Run the pipeline to generate summaries and vector chunks first."

    rag_prompt = (
        "You are Mindstream, a helpful analyst assistant answering questions about processed video transcripts.\n\n"
        "Use only the retrieved context below. If the context is insufficient, say so clearly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{prompt}\n\n"
        "Answer in a concise, helpful style."
    )
    print("[RAG] PROMPT SENT TO LLM:")
    print(rag_prompt)

    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": RAG_CHAT_MODEL,
                "prompt": rag_prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

    return str(data.get("response", "")).strip() or "I couldn't generate an answer from the retrieved context."


def _discover(sources: list[str], max_per_channel: int) -> None:
    if not sources:
        _append_log("No sources provided.")
        st.session_state["discovery_result"] = DiscoveryResult(skipped_sources=[], errors=[])
        return

    _append_log(f"Running discovery for {len(sources)} source(s)...")
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            result = discover_videos(sources, max_per_channel=max_per_channel)
    except Exception as exc:
        _append_log(f"Discovery failed: {exc}")
        st.session_state["discovery_result"] = DiscoveryResult(errors=[str(exc)])
        return

    output = captured.getvalue().strip()
    if output:
        _append_log(output)
    st.session_state["discovery_result"] = result
    st.session_state["transcript_result"] = TranscriptFetchResult()
    st.session_state["summary_result"] = SummaryGenerationResult()
    _append_log(f"Discovered {len(result.videos)} video(s).")


def _fetch_transcripts() -> None:
    discovery_result = st.session_state.get("discovery_result", DiscoveryResult())
    if not discovery_result.videos:
        st.warning("No discovered videos available. Run Discover Videos first.")
        return

    _append_log(f"Fetching transcripts for {len(discovery_result.videos)} video(s)...")
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            result = fetch_transcripts(discovery_result.videos)
    except Exception as exc:
        _append_log(f"Transcript fetch failed: {exc}")
        st.session_state["transcript_result"] = TranscriptFetchResult(errors=[str(exc)])
        return

    output = captured.getvalue().strip()
    if output:
        _append_log(output)
    st.session_state["transcript_result"] = result
    st.session_state["summary_result"] = SummaryGenerationResult()
    _append_log(f"Fetched transcripts for {len(result.fetched_records)} video(s).")


def _generate_summaries() -> None:
    transcript_result = st.session_state.get("transcript_result", TranscriptFetchResult())
    if not transcript_result.fetched_records:
        st.warning("No transcript records available. Run Fetch Transcripts first.")
        return

    _append_log(f"Generating summaries for {len(transcript_result.fetched_records)} video(s)...")
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            result = generate_summaries(transcript_result.fetched_records)
    except Exception as exc:
        _append_log(f"Summary generation failed: {exc}")
        st.session_state["summary_result"] = SummaryGenerationResult(errors=[str(exc)])
        return

    output = captured.getvalue().strip()
    if output:
        _append_log(output)
    st.session_state["summary_result"] = result
    _append_log(f"Generated summaries for {len(result.summaries)} video(s).")


def main() -> None:
    st.set_page_config(page_title="Mindstream", layout="wide")
    st.title("Mindstream")

    if "discovery_result" not in st.session_state:
        st.session_state["discovery_result"] = DiscoveryResult()
    if "transcript_result" not in st.session_state:
        st.session_state["transcript_result"] = TranscriptFetchResult()
    if "summary_result" not in st.session_state:
        st.session_state["summary_result"] = SummaryGenerationResult()
    if "logs" not in st.session_state:
        st.session_state["logs"] = ""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Ask Mindstream about the processed videos after you run discovery, transcripts, and summaries.",
            }
        ]

    content_col, right_panel = st.columns([3, 2], gap="large")

    with content_col:
        st.header("1) Source Input")
        sources_input = st.text_area(
            "Enter YouTube Sources",
            value="https://www.youtube.com/channel/UCsBjURrPoezykLs9EqgamOA",
            height=140,
        )
        sources = _parse_sources(sources_input)
        max_per_channel = st.number_input(
            "Max videos per channel",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )

        st.header("2) Pipeline Stage Controls")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Discover Videos", use_container_width=True):
                _discover(sources, int(max_per_channel))
        with col2:
            if st.button("Fetch Transcripts", use_container_width=True):
                _fetch_transcripts()
        with col3:
            if st.button("Generate Summaries", use_container_width=True):
                _generate_summaries()
        with col4:
            if st.button("Build Report", use_container_width=True):
                _append_log("Not implemented yet")
                st.info("Not implemented yet")

        st.header("3) Pipeline Output Display")
        discovery_result = st.session_state.get("discovery_result", DiscoveryResult())
        st.write(f"Discovered videos: {len(discovery_result.videos)}")
        st.write(f"Skipped sources: {len(discovery_result.skipped_sources)}")
        st.write(f"Errors: {len(discovery_result.errors)}")

        if discovery_result.videos:
            st.dataframe(
                [
                    {
                        "video_id": video.video_id,
                        "video_url": video.video_url,
                        "title": video.title,
                        "published_at": video.published_at,
                    }
                    for video in discovery_result.videos
                ],
                use_container_width=True,
            )
        else:
            st.dataframe([], use_container_width=True)

        with st.expander("Skipped Sources"):
            if discovery_result.skipped_sources:
                st.write(discovery_result.skipped_sources)
            else:
                st.write("None")

        with st.expander("Errors"):
            if discovery_result.errors:
                st.write(discovery_result.errors)
            else:
                st.write("None")

        transcript_result = st.session_state.get("transcript_result", TranscriptFetchResult())
        available_count = sum(
            1 for record in transcript_result.fetched_records if record.transcript_status == "AVAILABLE"
        )
        st.write(f"Transcript videos attempted: {len(transcript_result.fetched_records)}")
        st.write(f"Transcript available: {available_count}")
        st.write(f"Transcript missing: {len(transcript_result.missing_transcripts)}")
        st.write(f"Transcript errors: {len(transcript_result.errors)}")

        if transcript_result.fetched_records:
            st.dataframe(
                [
                    {
                        "video_id": record.metadata.video_id,
                        "transcript_status": record.transcript_status,
                        "detail": record.transcript_detail,
                        "segment_count": len(record.transcript_segments),
                    }
                    for record in transcript_result.fetched_records
                ],
                use_container_width=True,
            )
        else:
            st.dataframe([], use_container_width=True)

        with st.expander("Missing Transcripts"):
            if transcript_result.missing_transcripts:
                st.write(transcript_result.missing_transcripts)
            else:
                st.write("None")

        with st.expander("Transcript Errors"):
            if transcript_result.errors:
                st.write(transcript_result.errors)
            else:
                st.write("None")

        summary_result = st.session_state.get("summary_result", SummaryGenerationResult())
        st.write(f"Summaries generated: {len(summary_result.summaries)}")
        st.write(f"Summary skipped videos: {len(summary_result.skipped_videos)}")
        st.write(f"Summary errors: {len(summary_result.errors)}")

        if summary_result.summaries:
            st.dataframe(
                [
                    {
                        "video_id": summary.video_id,
                        "topic_count": len(summary.topics),
                        "bullet_count": len(summary.bullets),
                        "confidence": summary.confidence,
                    }
                    for summary in summary_result.summaries
                ],
                use_container_width=True,
            )
        else:
            st.dataframe([], use_container_width=True)

        with st.expander("Summary Errors"):
            if summary_result.errors:
                st.write(summary_result.errors)
            else:
                st.write("None")

        with st.expander("Logs", expanded=False):
            st.text_area("Logs", value=st.session_state.get("logs", ""), height=240)

    with right_panel:
        st.subheader("Mindstream RAG Chat")

        prompt = st.chat_input("Ask Mindstream about the processed videos")

        chat_container = st.container(height=860, border=True)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt:
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )
            _append_log(f"RAG chat question: {prompt}")
            try:
                answer = _rag_answer(prompt)
            except Exception as exc:
                answer = f"I couldn't complete the RAG query: {exc}"
                _append_log(f"RAG chat failed: {exc}")

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )
            st.rerun()


if __name__ == "__main__":
    main()
