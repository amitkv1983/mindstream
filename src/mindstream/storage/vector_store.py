from __future__ import annotations

from datetime import datetime
import os
from urllib.parse import urlparse


class ChromaVectorStore:
    def __init__(self, host: str | None = None):
        import chromadb

        host = host or os.getenv("CHROMA_HOST", "http://localhost:8000")
        parsed = urlparse(host)
        client_host = parsed.hostname or "chroma"
        client_port = parsed.port or 8000
        ssl = parsed.scheme == "https"

        self.client = chromadb.HttpClient(host=client_host, port=client_port, ssl=ssl)
        collection_name = datetime.utcnow().strftime("mindstream_%Y_%m")
        print(f"[VectorStore] Host: {host}")
        print(f"[VectorStore] Using collection: {collection_name}")
        self.collection = self.client.get_or_create_collection(name=collection_name)
        print(f"[VectorStore] Existing vectors in collection: {self.collection.count()}")

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
            enriched_metadatas.append(enriched_metadata)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=enriched_metadatas,
        )
        print(f"[VectorStore] Upserted vectors: {len(ids)}")
        print(f"[VectorStore] Total vectors stored: {self.collection.count()}")

    def query(self, query_embedding, n_results: int = 5):
        print(f"[VectorStore] Query embedding dimension: {len(query_embedding)}")
        print(f"[VectorStore] Querying top {n_results} results")
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
