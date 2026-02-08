"""
Smart Document Chunking with Map-Reduce for Large Documents (Test Case 1)
Handles 200+ page PDFs without losing critical content.

Instead of truncating at MAX_CONTEXT_CHARS (losing 75% of a 200-page PDF),
this module:
  1. Splits documents into overlapping chunks
  2. Extracts key content from each chunk in parallel
  3. Merges into a condensed version that fits context limits
"""

import asyncio
from typing import List, Optional

from app.core.config import model_text, settings
from app.core.logging import get_logger

logger = get_logger("chunker")

# Chunk configuration
MAX_CHUNK_CHARS = 25000   # Safe limit per LLM call
OVERLAP_CHARS = 500       # Overlap between chunks for continuity


def chunk_document(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap: int = OVERLAP_CHARS
) -> List[str]:
    """
    Split a large document into overlapping chunks.
    Tries to split at paragraph boundaries to preserve context.

    Args:
        text: Full document text
        max_chars: Maximum characters per chunk
        overlap: Character overlap between adjacent chunks

    Returns:
        List of text chunks
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + max_chars

        # Try to break at a paragraph boundary (double newline)
        if end < len(text):
            search_start = max(end - 2000, start)
            last_para = text.rfind("\n\n", search_start, end)
            if last_para > start + 1000:  # Only use if we get a reasonable chunk
                end = last_para + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward, accounting for overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks


async def condense_large_document(
    text: str,
    max_output_chars: Optional[int] = None,
    purpose: str = "multi-agent council analysis"
) -> str:
    """
    For very large documents (200+ pages), create a condensed version
    using map-reduce so the council can analyze everything without truncation.

    Flow:
      1. Chunk the document into manageable pieces
      2. Extract key content from each chunk (preserving exact quotes)
      3. Merge into a single condensed document

    Args:
        text: Full document text (could be 400k+ chars for 200-page PDFs)
        max_output_chars: Target size for condensed output
        purpose: Description of what the condensed text will be used for

    Returns:
        Condensed text that fits within context limits, or original if small enough
    """
    max_output = max_output_chars or settings.MAX_CONTEXT_CHARS

    if len(text) <= max_output:
        return text

    # Safety check: if model is unavailable, fall back to smart truncation
    if model_text is None:
        logger.warning("Model unavailable for condensation, using smart truncation")
        return _smart_truncate(text, max_output)

    chunks = chunk_document(text)

    if len(chunks) <= 1:
        return text[:max_output]

    logger.info(
        f"Condensing large document: {len(text):,} chars → {len(chunks)} chunks "
        f"(target: {max_output:,} chars)"
    )

    # === MAP PHASE: extract key content from each chunk in parallel ===
    async def summarize_chunk(chunk: str, idx: int) -> str:
        prompt = (
            f"You are a document analyst preparing content for {purpose}.\n"
            f"This is section {idx + 1} of {len(chunks)} from a large document.\n\n"
            "TASK: Extract and preserve ALL of the following from this section:\n"
            "- Specific requirements, obligations, and commitments\n"
            "- Financial terms, dates, deadlines, and SLAs\n"
            "- Legal clauses, liability terms, and penalties\n"
            "- Technical specifications and architecture decisions\n"
            "- Any ambiguous or concerning language\n\n"
            "Preserve EXACT QUOTES for important clauses. Be thorough — do not summarize.\n"
            "Output a structured extraction, NOT a summary.\n\n"
            f"--- SECTION {idx + 1}/{len(chunks)} ---\n{chunk}"
        )
        try:
            await asyncio.sleep(settings.AI_REQUEST_DELAY * 0.5)
            response = await model_text.generate_content_async(prompt)
            return response.text.strip() if response and response.text else ""
        except Exception as e:
            logger.warning(f"Chunk {idx + 1} extraction failed: {e}")
            # Fallback: return head + tail of the chunk to preserve some content
            return chunk[:3000] + "\n...[extraction failed]...\n" + chunk[-1000:]

    # Run chunk extractions in parallel batches (respect rate limits)
    chunk_summaries: List[str] = []
    batch_size = 3
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        tasks = [summarize_chunk(c, i + j) for j, c in enumerate(batch)]
        results = await asyncio.gather(*tasks)
        chunk_summaries.extend(results)

    # === REDUCE PHASE: merge all extractions ===
    condensed = "\n\n".join([
        f"=== Section {i + 1}/{len(chunk_summaries)} ===\n{s}"
        for i, s in enumerate(chunk_summaries) if s
    ])

    # If still too long after extraction, truncate with a note
    if len(condensed) > max_output:
        condensed = condensed[:max_output] + (
            "\n\n[Document condensed from original via map-reduce extraction]"
        )

    logger.info(f"Document condensed: {len(text):,} → {len(condensed):,} chars")
    return condensed


def _smart_truncate(text: str, max_chars: int) -> str:
    """
    Smart truncation fallback: keeps the beginning (context/definitions),
    a sample from the middle, and the end (signatures/conclusions).
    """
    if len(text) <= max_chars:
        return text

    # Allocate: 50% beginning, 20% middle, 30% end
    head_size = int(max_chars * 0.50)
    mid_size = int(max_chars * 0.20)
    tail_size = int(max_chars * 0.30)

    mid_start = (len(text) - mid_size) // 2

    head = text[:head_size]
    middle = text[mid_start:mid_start + mid_size]
    tail = text[-tail_size:]

    return (
        head
        + f"\n\n[...{len(text) - max_chars:,} characters omitted (beginning section)...]\n\n"
        + middle
        + f"\n\n[...omitted (middle section)...]\n\n"
        + tail
    )
