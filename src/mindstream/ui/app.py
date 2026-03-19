"""Streamlit UI for Mindstream."""

from __future__ import annotations

import io
import os
from contextlib import redirect_stdout
from typing import Callable

import httpx
import streamlit as st

from mindstream.ingest.youtube_discovery import discover_videos
from mindstream.ingest.youtube_transcript import fetch_transcripts
from mindstream.process.embeddings import generate_embedding
from mindstream.process.reranker import rerank
from mindstream.process.summarize_video import generate_summaries
from mindstream.storage.local_store import PROJECTS_DIR, ensure_data_dirs
from mindstream.storage.models import DiscoveryResult, SummaryGenerationResult, TranscriptFetchResult
from mindstream.storage.vector_store import search_chunk_collections, search_video_summaries


st.set_page_config(
    page_title="Mindstream",
    page_icon="🧠",
    layout="wide",
)


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
RAG_CHAT_MODEL = os.getenv("RAG_CHAT_MODEL", "mistral:7b-instruct")


def _parse_sources(raw_text: str) -> list[str]:
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def _append_log(message: str) -> None:
    logs = st.session_state.get("logs", "")
    st.session_state["logs"] = f"{logs}{message}\n" if logs else f"{message}\n"


def _available_projects() -> list[str]:
    project_ids = ["default"]
    if PROJECTS_DIR.exists():
        project_ids.extend(path.name for path in PROJECTS_DIR.iterdir() if path.is_dir())
    return sorted(set(project_ids))


def _build_chroma_filter(project_id: str, video_ids: list[str] | None = None) -> dict[str, object]:
    clauses: list[dict[str, object]] = [{"project_id": project_id}]
    unique_video_ids = list(dict.fromkeys(video_ids or []))
    if unique_video_ids:
        clauses.append({"video_id": {"$in": unique_video_ids}})
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def format_timestamp(seconds: float | int | None) -> str:
    total_seconds = max(0, int(seconds or 0))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def _render_sources_markdown(sources: list[dict[str, object]]) -> str:
    if not sources:
        return ""

    lines = ["", "**Sources**"]
    for source in sources:
        title = str(source.get("video_title") or source.get("video_id") or "Unknown video")
        video_id = str(source.get("video_id") or "")
        start_time = int(float(source.get("start_time") or 0.0))
        timestamp = format_timestamp(start_time)
        url = f"https://youtube.com/watch?v={video_id}&t={start_time}s" if video_id else ""
        if url:
            lines.append(f"- [{title} ({timestamp})]({url})")
        else:
            lines.append(f"- {title} ({timestamp})")
    return "\n".join(lines)


def _pipeline_progress(
    discovery_result: DiscoveryResult,
    transcript_result: TranscriptFetchResult,
    summary_result: SummaryGenerationResult,
) -> int:
    if summary_result.summaries:
        return 100
    if transcript_result.fetched_records:
        return 66
    if discovery_result.videos:
        return 33
    return 0


def _combined_error_count(
    discovery_result: DiscoveryResult,
    transcript_result: TranscriptFetchResult,
    summary_result: SummaryGenerationResult,
) -> int:
    return len(discovery_result.errors) + len(transcript_result.errors) + len(summary_result.errors)


def _render_table(title: str, rows: list[dict[str, object]], empty_text: str, height: int = 220) -> None:
    st.subheader(title)
    if rows:
        st.dataframe(rows, use_container_width=True, height=height)
    else:
        st.info(empty_text)


def _render_debug_section(
    discovery_result: DiscoveryResult,
    transcript_result: TranscriptFetchResult,
    summary_result: SummaryGenerationResult,
) -> None:
    st.subheader("🛠 Debug Info")
    with st.expander("View pipeline details", expanded=False):
        st.markdown("**Discovery errors**")
        st.write(discovery_result.errors or "None")

        st.markdown("**Transcript errors**")
        st.write(transcript_result.errors or "None")

        st.markdown("**Summary errors**")
        st.write(summary_result.errors or "None")

        st.markdown("**Skipped sources**")
        st.write(discovery_result.skipped_sources or "None")

        st.markdown("**Missing transcripts**")
        st.write(transcript_result.missing_transcripts or "None")

        st.markdown("**Logs**")
        st.text_area("Logs", value=st.session_state.get("logs", ""), height=220)


def _run_action_with_feedback(
    label: str,
    action: Callable[[], None],
    success_message: str,
    running_message: str,
) -> None:
    """Show visible UI feedback while a long-running pipeline action executes."""
    st.session_state["ui_busy"] = True
    st.session_state["active_action"] = label
    try:
        with st.status(f"{label} in progress", expanded=True) as status:
            status.write(running_message)
            status.write("Mindstream is still working even if the page feels quiet for a moment.")
            with st.spinner(f"{label}..."):
                action()
            status.update(label=f"{label} complete", state="complete", expanded=False)
        st.success(success_message)
    finally:
        st.session_state["ui_busy"] = False
        st.session_state["active_action"] = ""


def _rag_answer(prompt: str, project_id: str) -> tuple[str, list[dict[str, object]]]:
    print(f"[RAG] Ollama base URL: {OLLAMA_BASE_URL}")
    print(f"[RAG] Chat model: {RAG_CHAT_MODEL}")
    query_embedding = generate_embedding(prompt)
    print(f"[RAG] Query embedding generated: {bool(query_embedding)}")
    summary_results = search_video_summaries(query_embedding, top_k=3, where=_build_chroma_filter(project_id))
    summary_metadatas = (summary_results.get("metadatas") or [[]])[0]
    video_ids = []
    for metadata in summary_metadatas:
        if isinstance(metadata, dict) and metadata.get("video_id"):
            video_ids.append(str(metadata["video_id"]))
    video_ids = list(dict.fromkeys(video_ids))
    print(f"[RAG] Summary-stage videos: {video_ids}")

    chunk_where = _build_chroma_filter(project_id, video_ids)

    chunk_results = search_chunk_collections(
        query_embedding,
        top_k=20,
        per_collection_k=10,
        where=chunk_where,
    )
    retrieved_results = chunk_results.get("results", [])
    if not retrieved_results and video_ids:
        # Preserve usability if filtered chunk search misses while summary hits exist.
        retrieved_results = search_chunk_collections(
            query_embedding,
            top_k=20,
            per_collection_k=10,
            where=_build_chroma_filter(project_id),
        ).get("results", [])

    reranked_results = rerank(prompt, retrieved_results)[:5]
    retrieved_chunks = [
        str(result.get("chunk_text", "")).strip()
        for result in reranked_results
        if str(result.get("chunk_text", "")).strip()
    ]
    print(f"[RAG] Retrieved {len(retrieved_chunks)} chunks after reranking")
    print("[RAG] Retrieved docs:")
    for chunk in retrieved_chunks:
        print(chunk[:200])
    context = "\n\n".join([chunk[:1000] for chunk in retrieved_chunks])
    print(f"[RAG] Context size: {len(context)} characters")
    if not context:
        return (
            "I don't have enough indexed transcript context yet. Run the pipeline to generate summaries and vector chunks first.",
            [],
        )

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

    answer = str(data.get("response", "")).strip() or "I couldn't generate an answer from the retrieved context."
    sources = []
    seen_sources: set[tuple[str, int]] = set()
    for result in reranked_results:
        video_id = str(result.get("video_id") or "")
        metadata = result.get("metadata", {}) if isinstance(result.get("metadata"), dict) else {}
        start_time = int(float(metadata.get("start_time", 0.0)))
        source_key = (video_id, start_time)
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        sources.append(
            {
                "video_id": video_id,
                "video_title": metadata.get("video_title") or result.get("video_title"),
                "start_time": start_time,
            }
        )

    return answer, sources


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


def _fetch_transcripts(project_id: str) -> None:
    discovery_result = st.session_state.get("discovery_result", DiscoveryResult())
    if not discovery_result.videos:
        st.warning("No discovered videos available. Run Discover Videos first.")
        return

    _append_log(f"Fetching transcripts for {len(discovery_result.videos)} video(s)...")
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            result = fetch_transcripts(discovery_result.videos, project_id=project_id)
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


def _generate_summaries(project_id: str) -> None:
    transcript_result = st.session_state.get("transcript_result", TranscriptFetchResult())
    if not transcript_result.fetched_records:
        st.warning("No transcript records available. Run Fetch Transcripts first.")
        return

    _append_log(f"Generating summaries for {len(transcript_result.fetched_records)} video(s)...")
    captured = io.StringIO()
    try:
        with redirect_stdout(captured):
            result = generate_summaries(transcript_result.fetched_records, project_id=project_id)
    except Exception as exc:
        _append_log(f"Summary generation failed: {exc}")
        st.session_state["summary_result"] = SummaryGenerationResult(errors=[str(exc)])
        return

    output = captured.getvalue().strip()
    if output:
        _append_log(output)
    st.session_state["summary_result"] = result
    _append_log(f"Generated summaries for {len(result.summaries)} video(s).")


def _run_full_pipeline(sources: list[str], max_per_channel: int, project_id: str) -> None:
    """Run all pipeline stages in order using the existing stage handlers."""
    _discover(sources, max_per_channel)

    discovery_result = st.session_state.get("discovery_result", DiscoveryResult())
    if not discovery_result.videos:
        return

    _fetch_transcripts(project_id)

    transcript_result = st.session_state.get("transcript_result", TranscriptFetchResult())
    if not transcript_result.fetched_records:
        return

    _generate_summaries(project_id)


def main() -> None:
    """Render the product-style Mindstream dashboard while preserving pipeline behavior."""
    project_options = _available_projects()
    sidebar_project = st.sidebar.selectbox("Project", options=project_options, index=0)
    new_project_id = st.sidebar.text_input("New project ID", value="").strip()
    selected_project = new_project_id or sidebar_project
    ensure_data_dirs(selected_project)

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
    if "ui_busy" not in st.session_state:
        st.session_state["ui_busy"] = False
    if "active_action" not in st.session_state:
        st.session_state["active_action"] = ""
    if "active_project" not in st.session_state:
        st.session_state["active_project"] = selected_project

    if st.session_state.get("active_project") != selected_project:
        st.session_state["active_project"] = selected_project
        st.session_state["discovery_result"] = DiscoveryResult()
        st.session_state["transcript_result"] = TranscriptFetchResult()
        st.session_state["summary_result"] = SummaryGenerationResult()
        st.session_state["logs"] = ""
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": f"Project `{selected_project}` is active. Ask Mindstream about the processed videos after you run discovery, transcripts, and summaries.",
            }
        ]

    discovery_result = st.session_state.get("discovery_result", DiscoveryResult())
    transcript_result = st.session_state.get("transcript_result", TranscriptFetchResult())
    summary_result = st.session_state.get("summary_result", SummaryGenerationResult())
    ui_busy = bool(st.session_state.get("ui_busy", False))
    active_action = st.session_state.get("active_action", "")
    available_count = sum(
        1 for record in transcript_result.fetched_records if record.transcript_status == "AVAILABLE"
    )
    progress_value = _pipeline_progress(discovery_result, transcript_result, summary_result)
    total_errors = _combined_error_count(discovery_result, transcript_result, summary_result)

    # Header
    st.title("🧠 Mindstream")
    st.caption("AI-powered YouTube intelligence pipeline")
    st.divider()

    main_col, chat_col = st.columns([3, 2], gap="large")

    with main_col:
        # Input
        st.subheader("📺 Sources")
        sources_input = st.text_area(
            "YouTube channels",
            value="https://www.youtube.com/channel/UCsBjURrPoezykLs9EqgamOA",
            height=140,
            placeholder="Paste YouTube channel URLs (one per line)",
        )
        sources = _parse_sources(sources_input)
        st.caption(f"Active project: `{selected_project}`")
        max_per_channel = st.number_input(
            "Max videos per channel",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )

        st.divider()

        # Pipeline
        st.subheader("⚙️ Pipeline")
        if ui_busy:
            st.info(f"{active_action or 'A pipeline task'} is running. Please wait for it to finish.")

        action_col, _ = st.columns([1, 2], gap="large")
        with action_col:
            if st.button("Run Full Pipeline", use_container_width=True, type="primary", disabled=ui_busy):
                _run_action_with_feedback(
                    label="Full pipeline",
                    action=lambda: _run_full_pipeline(sources, int(max_per_channel), selected_project),
                    success_message="Pipeline run finished.",
                    running_message="Running discovery, transcript fetch, and summary generation in sequence.",
                )

        step1, step2, step3 = st.columns(3, gap="large")

        with step1:
            st.markdown("#### 1️⃣ Discover Videos")
            st.caption("Find the latest videos from the provided channels.")
            if st.button("Discover Videos", use_container_width=True, disabled=ui_busy):
                _run_action_with_feedback(
                    label="Video discovery",
                    action=lambda: _discover(sources, int(max_per_channel)),
                    success_message="Video discovery finished.",
                    running_message="Discovering videos from the provided YouTube sources.",
                )

        with step2:
            st.markdown("#### 2️⃣ Fetch Transcripts")
            st.caption("Collect transcript text for the discovered videos.")
            if st.button("Fetch Transcripts", use_container_width=True, disabled=ui_busy):
                _run_action_with_feedback(
                    label="Transcript fetch",
                    action=lambda: _fetch_transcripts(selected_project),
                    success_message="Transcript fetch finished.",
                    running_message="Fetching transcript text for the discovered videos.",
                )

        with step3:
            st.markdown("#### 3️⃣ Generate Summaries")
            st.caption("Create structured summaries from transcript content.")
            if st.button("Generate Summaries", use_container_width=True, disabled=ui_busy):
                _run_action_with_feedback(
                    label="Summary generation",
                    action=lambda: _generate_summaries(selected_project),
                    success_message="Summary generation finished.",
                    running_message="Generating summaries with the model. This can take a while for multiple videos.",
                )

        st.progress(progress_value, text=f"Pipeline progress: {progress_value}%")

        st.divider()

        # Metrics
        st.subheader("📊 Metrics")
        metric1, metric2, metric3, metric4 = st.columns(4, gap="large")
        metric1.metric("Videos discovered", len(discovery_result.videos))
        metric2.metric("Transcripts", available_count)
        metric3.metric("Summaries", len(summary_result.summaries))
        metric4.metric("Errors", total_errors)

        st.divider()

        st.subheader("📁 Results")
        _render_table(
            "Discovered Videos",
            [
                {
                    "video_id": video.video_id,
                    "video_url": video.video_url,
                    "title": video.title,
                    "published_at": video.published_at,
                    "channel": video.channel,
                }
                for video in discovery_result.videos
            ],
            "No videos discovered yet.",
        )
        _render_table(
            "Transcripts",
            [
                {
                    "video_id": record.metadata.video_id,
                    "transcript_status": record.transcript_status,
                    "detail": record.transcript_detail,
                    "segment_count": len(record.transcript_segments),
                }
                for record in transcript_result.fetched_records
            ],
            "No transcripts fetched yet.",
        )
        _render_table(
            "Summaries",
            [
                {
                    "video_id": summary.video_id,
                    "topic_count": len(summary.topics),
                    "bullet_count": len(summary.bullets),
                    "confidence": summary.confidence,
                }
                for summary in summary_result.summaries
            ],
            "No summaries generated yet.",
        )

        st.divider()
        _render_debug_section(discovery_result, transcript_result, summary_result)

    with chat_col:
        st.subheader("💬 Ask Mindstream")
        st.caption("Ask questions about the processed videos")
        prompt = st.chat_input("Ask Mindstream about the processed videos", disabled=ui_busy)
        st.markdown(
            "\n".join(
                [
                    "**Example questions**",
                    "",
                    "• What are the main topics across these videos?",
                    "• Which videos discuss AI safety?",
                    "• Summarize the key insights.",
                ]
            )
        )

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
                answer, sources = _rag_answer(prompt, selected_project)
            except Exception as exc:
                answer = f"I couldn't complete the RAG query: {exc}"
                sources = []
                _append_log(f"RAG chat failed: {exc}")

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"{answer}{_render_sources_markdown(sources)}",
                }
            )
            st.rerun()


if __name__ == "__main__":
    main()
