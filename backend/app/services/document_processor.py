"""Document processor — splits documents into chunks for RAG.

Large documents must be broken into smaller overlapping chunks before
embedding. Why?
- LLMs have context-window limits.
- Smaller chunks produce more precise retrieval results.
- Overlap ensures we don't lose meaning at chunk boundaries.
"""


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks by character count.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Characters shared between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap

    return chunks
