from __future__ import annotations

from datetime import datetime
import os
from typing import Any
from urllib.parse import urlparse


class ChromaVectorStore:
    COLLECTION_PREFIX = "mindstream_"
    SUMMARY_COLLECTION_NAME = "mindstream_video_summaries"

    def __init__(self, host: str | None = None):
        import chromadb

        host = host or os.getenv("CHROMA_HOST", "http://localhost:8000")
        parsed = urlparse(host)
        client_host = parsed.hostname or "chroma"
        client_port = parsed.port or 8000
        ssl = parsed.scheme == "https"

        self.client = chromadb.HttpClient(host=client_host, port=client_port, ssl=ssl)
        collection_name = datetime.utcnow().strftime(f"{self.COLLECTION_PREFIX}%Y_%m")
        print(f"[VectorStore] Host: {host}")
        print(f"[VectorStore] Using chunk collection: {collection_name}")
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.summary_collection = self.client.get_or_create_collection(name=self.SUMMARY_COLLECTION_NAME)
        print(f"[VectorStore] Existing vectors in chunk collection: {self.collection.count()}")
        print(f"[VectorStore] Existing vectors in summary collection: {self.summary_collection.count()}")

    def _mindstream_collection_names(self) -> list[str]:
        """Return all Mindstream collections so retrieval can span monthly partitions."""
        names: list[str] = []
        for item in self.client.list_collections():
            name = item if isinstance(item, str) else getattr(item, "name", "")
            if (
                isinstance(name, str)
                and name.startswith(self.COLLECTION_PREFIX)
                and name != self.SUMMARY_COLLECTION_NAME
            ):
                names.append(name)
        return sorted(set(names))

    def add_chunks(self, ids, embeddings, documents, metadatas):
        timestamp = datetime.utcnow().isoformat() + "Z"
        enriched_metadatas = []
        for metadata in metadatas:
            enriched_metadata = dict(metadata)
            enriched_metadata.setdefault("video_id", None)
            enriched_metadata.setdefault("chunk_index", None)
            enriched_metadata.setdefault("video_title", None)
            enriched_metadata.setdefault("published_at", None)
            enriched_metadata.setdefault("ingested_at", timestamp)
            enriched_metadata.setdefault("source_type", "youtube")
            enriched_metadata.setdefault("content_type", "transcript_chunk")
            enriched_metadata.setdefault("project_id", "default")
            enriched_metadata.setdefault("speaker", "Unknown")
            enriched_metadata.setdefault("start_time", 0.0)
            enriched_metadatas.append(enriched_metadata)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=enriched_metadatas,
        )
        print(f"[VectorStore] Upserted vectors: {len(ids)}")
        print(f"[VectorStore] Total vectors stored: {self.collection.count()}")

    def add_video_summaries(self, ids, embeddings, documents, metadatas):
        timestamp = datetime.utcnow().isoformat() + "Z"
        enriched_metadatas = []
        for metadata in metadatas:
            enriched_metadata = dict(metadata)
            enriched_metadata.setdefault("video_id", None)
            enriched_metadata.setdefault("video_title", None)
            enriched_metadata.setdefault("channel", None)
            enriched_metadata.setdefault("project_id", "default")
            enriched_metadata.setdefault("ingested_at", timestamp)
            enriched_metadata.setdefault("content_type", "video_summary")
            enriched_metadatas.append(enriched_metadata)

        self.summary_collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=enriched_metadatas,
        )
        print(f"[VectorStore] Upserted summary vectors: {len(ids)}")
        print(f"[VectorStore] Total summaries stored: {self.summary_collection.count()}")

    def query(self, query_embedding, n_results: int = 5, where: dict[str, Any] | None = None):
        print(f"[VectorStore] Query embedding dimension: {len(query_embedding)}")
        print(f"[VectorStore] Querying top {n_results} results")
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    def query_summaries(
        self,
        query_embedding,
        n_results: int = 3,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        print(f"[VectorStore] Querying summary collection for top {n_results} results")
        return self.summary_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    def search_all_collections(
        self,
        query_embedding,
        top_k: int = 5,
        per_collection_k: int = 3,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Query all monthly Mindstream collections and globally rerank the matches.

        This preserves the existing ingestion strategy while fixing retrieval for
        data indexed in prior months.
        """
        print(f"[VectorStore] Cross-collection query embedding dimension: {len(query_embedding)}")
        collection_names = self._mindstream_collection_names()
        print(f"[VectorStore] Searching collections: {collection_names}")

        merged_results: list[dict[str, Any]] = []
        for collection_name in collection_names:
            collection = self.client.get_collection(name=collection_name)
            query_result = collection.query(
                query_embeddings=[query_embedding],
                n_results=per_collection_k,
                where=where,
            )

            ids = (query_result.get("ids") or [[]])[0]
            documents = (query_result.get("documents") or [[]])[0]
            metadatas = (query_result.get("metadatas") or [[]])[0]
            distances = (query_result.get("distances") or [[]])[0]

            for index, chunk_text in enumerate(documents):
                metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
                distance = distances[index] if index < len(distances) else None
                merged_results.append(
                    {
                        "id": ids[index] if index < len(ids) else None,
                        "collection_name": collection_name,
                        "distance": float(distance) if distance is not None else float("inf"),
                        "video_id": metadata.get("video_id"),
                        "video_title": metadata.get("video_title"),
                        "chunk_text": str(chunk_text),
                        "metadata": metadata,
                    }
                )

        merged_results.sort(key=lambda item: item["distance"])
        top_results = merged_results[:top_k]
        print(f"[VectorStore] Cross-collection results merged: {len(merged_results)}")
        print(f"[VectorStore] Cross-collection results returned: {len(top_results)}")

        return {
            "ids": [[result["id"] for result in top_results]],
            "documents": [[result["chunk_text"] for result in top_results]],
            "metadatas": [[result["metadata"] for result in top_results]],
            "distances": [[result["distance"] for result in top_results]],
            "results": top_results,
        }


def search_all_collections(query_embedding, top_k: int = 5, per_collection_k: int = 3) -> dict[str, Any]:
    """Convenience helper for RAG retrieval across all monthly Mindstream collections."""
    store = ChromaVectorStore()
    return store.search_all_collections(
        query_embedding=query_embedding,
        top_k=top_k,
        per_collection_k=per_collection_k,
    )


def search_chunk_collections(
    query_embedding,
    top_k: int = 5,
    per_collection_k: int = 3,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience helper for chunk retrieval across monthly collections."""
    store = ChromaVectorStore()
    return store.search_all_collections(
        query_embedding=query_embedding,
        top_k=top_k,
        per_collection_k=per_collection_k,
        where=where,
    )


def search_video_summaries(
    query_embedding,
    top_k: int = 3,
    where: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience helper for top-level video summary retrieval."""
    store = ChromaVectorStore()
    return store.query_summaries(
        query_embedding=query_embedding,
        n_results=top_k,
        where=where,
    )
