from __future__ import annotations

import numpy as np
import hdbscan
from sklearn.cluster import KMeans


def _chunk_text(chunk: object) -> str:
    if isinstance(chunk, dict):
        if "text" in chunk:
            return str(chunk["text"])
        if "document" in chunk:
            return str(chunk["document"])
    return str(chunk)


def _chunk_video_id(chunk: object) -> str | None:
    if not isinstance(chunk, dict):
        return None

    metadata = chunk.get("metadata")
    if isinstance(metadata, dict) and metadata.get("video_id") is not None:
        return str(metadata["video_id"])

    if chunk.get("video_id") is not None:
        return str(chunk["video_id"])

    return None


def _build_clusters(chunks, labels):
    clusters: dict[int, dict[str, object]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue

        cluster_id = int(label)
        if cluster_id not in clusters:
            clusters[cluster_id] = {
                "cluster_id": cluster_id,
                "chunks": [],
                "video_ids": set(),
            }

        chunk = chunks[idx]
        clusters[cluster_id]["chunks"].append(_chunk_text(chunk))
        video_id = _chunk_video_id(chunk)
        if video_id:
            clusters[cluster_id]["video_ids"].add(video_id)

    results = []
    for cluster_id in sorted(clusters):
        cluster = clusters[cluster_id]
        results.append(
            {
                "cluster_id": cluster["cluster_id"],
                "chunk_count": len(cluster["chunks"]),
                "video_ids": list(cluster["video_ids"]),
                "chunks": cluster["chunks"],
            }
        )

    return results


def cluster_chunks(chunks, embeddings):
    print(f"[Clustering] Received {len(chunks)} chunks")

    if len(chunks) == 0 or len(embeddings) == 0:
        return []

    sample_count = min(len(chunks), len(embeddings))
    chunks = list(chunks[:sample_count])
    embeddings = np.array(embeddings[:sample_count])

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        metric="euclidean",
    )
    labels = clusterer.fit_predict(embeddings)
    results = _build_clusters(chunks, labels)
    print(f"[Clustering] Found {len(results)} clusters")

    if results:
        return results

    print("[Clustering] No clusters detected with HDBSCAN, falling back to KMeans")
    n_clusters = max(2, int(len(chunks) ** 0.5))
    n_clusters = min(n_clusters, len(chunks))
    print(f"[Clustering] Using fallback KMeans with {n_clusters} clusters")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    results = _build_clusters(chunks, labels)

    return results
