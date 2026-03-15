from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 6000, overlap: int = 300) -> list[dict[str, object]]:
    text = text.strip()
    if not text:
        return []
    if chunk_size <= 0:
        return [{"chunk_index": 0, "text": text}]
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 10)

    chunks: list[dict[str, object]] = []
    start = 0
    step = max(1, chunk_size - overlap)
    chunk_index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            split_at = text.rfind(" ", start, end)
            if split_at > start + (chunk_size // 2):
                end = split_at

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"chunk_index": chunk_index, "text": chunk})
            chunk_index += 1
        if end == len(text):
            break

        next_start = max(0, end - overlap)
        if next_start > 0:
            next_split = text.find(" ", next_start, min(len(text), next_start + overlap))
            if next_split != -1:
                next_start = next_split + 1
        if next_start <= start:
            next_start = start + step
        start = next_start

    return chunks
