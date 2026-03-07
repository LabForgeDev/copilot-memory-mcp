"""MCP tool: update_memory."""
from __future__ import annotations

from app.memory_store import get_store


def update_memory(
    id: str,
    title: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Update an existing memory by ID.

    Only supplied fields are changed; the embedding is recomputed when
    title or content changes.

    Args:
        id: UUID of the memory to update.
        title: New title (omit to keep existing).
        content: New content (omit to keep existing).
        tags: Replacement tag list (omit to keep existing).

    Returns:
        ``{ id, title, updated_at }``

    Raises:
        ValueError: If no memory with *id* exists.
    """
    return get_store().update(
        doc_id=id,
        title=title,
        content=content,
        tags=tags,
    )
