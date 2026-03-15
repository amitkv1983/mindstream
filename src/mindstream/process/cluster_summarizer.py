from __future__ import annotations

import json
import os

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "mistral"


def _select_chunks(chunks: list[str]) -> list[str]:
    if len(chunks) <= 5:
        return chunks

    middle_start = max(0, (len(chunks) // 2) - 1)
    selected = chunks[:2] + chunks[middle_start : middle_start + 2] + chunks[-2:]

    deduped: list[str] = []
    for chunk in selected:
        if chunk not in deduped:
            deduped.append(chunk)
    return deduped


def _fallback_summary(cluster: dict, context: str) -> dict[str, object]:
    return {
        "cluster_id": cluster["cluster_id"],
        "summary": context[:200],
        "key_points": [],
        "chunk_count": cluster["chunk_count"],
        "video_count": len(cluster["video_ids"]),
    }


def summarize_cluster(cluster):
    cluster_id = cluster["cluster_id"]
    print(f"[ClusterSummarizer] Summarizing cluster {cluster_id}")

    selected_chunks = _select_chunks(list(cluster.get("chunks", [])))
    context = "\n\n".join(selected_chunks)
    prompt = (
        "You are summarizing a set of related transcript excerpts.\n\n"
        "Extract a concise cluster summary describing the main topic discussed.\n\n"
        f"Text:\n\n{context}\n\n"
        "Return JSON only:\n\n"
        '{\n  "cluster_summary": "...",\n  "key_points": ["...", "..."]\n}'
    )

    try:
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

        raw_text = str(data.get("response", "")).strip()
        parsed = json.loads(raw_text)
        return {
            "cluster_id": cluster_id,
            "summary": str(parsed.get("cluster_summary", "")).strip(),
            "key_points": [str(item) for item in parsed.get("key_points", [])],
            "chunk_count": cluster["chunk_count"],
            "video_count": len(cluster["video_ids"]),
        }
    except Exception:
        return _fallback_summary(cluster, context)


def summarize_clusters(clusters):
    return [summarize_cluster(cluster) for cluster in clusters]
