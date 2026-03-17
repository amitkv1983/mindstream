from __future__ import annotations

from typing import Any


RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"


class _CrossEncoderReranker:
    def __init__(self) -> None:
        # Import lazily so the rest of Mindstream remains runnable without the
        # reranker runtime dependencies being installed yet.
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(RERANKER_MODEL_NAME)

    def score(self, query: str, chunks: list[dict[str, Any]]) -> list[float]:
        pairs = [(query, str(chunk.get("chunk_text", ""))) for chunk in chunks]
        return [float(score) for score in self._model.predict(pairs)]


_RERANKER: _CrossEncoderReranker | None = None
_RERANKER_ERROR: Exception | None = None


def _get_reranker() -> _CrossEncoderReranker | None:
    global _RERANKER, _RERANKER_ERROR
    if _RERANKER is not None:
        return _RERANKER
    if _RERANKER_ERROR is not None:
        return None

    try:
        _RERANKER = _CrossEncoderReranker()
    except Exception as exc:  # pragma: no cover - depends on optional runtime deps
        _RERANKER_ERROR = exc
        print(f"[Reranker] Falling back to vector distance ordering: {exc}")
        return None

    return _RERANKER


def rerank(query: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rerank retrieved chunks and gracefully fall back if the model is unavailable."""
    if not chunks:
        return []

    model = _get_reranker()
    if model is None:
        return sorted(chunks, key=lambda chunk: float(chunk.get("distance", float("inf"))))

    scores = model.score(query, chunks)
    scored_chunks = []
    for index, chunk in enumerate(chunks):
        updated_chunk = dict(chunk)
        updated_chunk["rerank_score"] = scores[index]
        scored_chunks.append(updated_chunk)

    return sorted(scored_chunks, key=lambda chunk: float(chunk.get("rerank_score", 0.0)), reverse=True)
