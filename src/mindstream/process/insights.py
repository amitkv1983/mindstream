from __future__ import annotations

import os

import httpx

from mindstream.process.clustering import cluster_summary_documents
from mindstream.process.embeddings import generate_embedding
from mindstream.storage.models import PerVideoSummary, VideoMetadata


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("INSIGHTS_MODEL", "mistral:7b-instruct")


def _summary_document(summary: PerVideoSummary, metadata: VideoMetadata | None) -> dict[str, object]:
    return {
        "video_id": summary.video_id,
        "text": "\n".join(summary.bullets),
        "metadata": {
            "video_id": summary.video_id,
            "video_title": metadata.title if metadata else summary.video_id,
        },
    }


def _generate_cluster_summary(topic: str, cluster_chunks: list[str]) -> str:
    prompt = (
        "You are generating a concise topic insight from related video summaries.\n\n"
        f"Topic label: {topic}\n\n"
        "Source summary bullets:\n"
        f"{chr(10).join(f'- {chunk}' for chunk in cluster_chunks[:12])}\n\n"
        "Return 2-3 sentences that describe the shared theme and why it matters."
    )
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        data = response.json()
    return str(data.get("response", "")).strip()


def generate_topic_insights(
    summaries: list[PerVideoSummary],
    metadata_by_video_id: dict[str, VideoMetadata] | None = None,
) -> list[dict[str, object]]:
    metadata_by_video_id = metadata_by_video_id or {}
    summary_documents = [_summary_document(summary, metadata_by_video_id.get(summary.video_id)) for summary in summaries]
    embeddings = [generate_embedding(str(document["text"])) for document in summary_documents if str(document["text"]).strip()]
    usable_documents = [document for document in summary_documents if str(document["text"]).strip()]
    if not usable_documents or not embeddings:
        return []

    clusters = cluster_summary_documents(usable_documents, embeddings)
    insights = []
    for cluster in clusters:
        video_ids = [str(video_id) for video_id in cluster.get("video_ids", [])]
        cluster_texts = [str(chunk) for chunk in cluster.get("chunks", [])]
        topic = video_ids[0] if video_ids else f"cluster_{cluster.get('cluster_id', 'unknown')}"
        insights.append(
            {
                "topic": topic,
                "videos": video_ids,
                "summary": _generate_cluster_summary(topic, cluster_texts) if cluster_texts else "",
            }
        )
    return insights
