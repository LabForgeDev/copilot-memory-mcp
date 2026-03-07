"""MCP tool: delete_memory."""
from __future__ import annotations

from app.memory_store import get_store


def delete_memory(id: str) -> dict:
    """Permanently delete a memory by ID.

    Args:
        id: UUID of the memory to delete.

    Returns:
        ``{ id, deleted: true }``

    Raises:
        ValueError: If no memory with *id* exists.
    """
    return get_store().delete(doc_id=id)
