"""MCP tool: create_memory."""
from __future__ import annotations

from app.memory_store import get_store


def create_memory(
    title: str,
    content: str,
    project_name: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Store a new memory.

    Args:
        title: Short human-readable label.
        content: Full memory body — this text is embedded for semantic search.
        project_name: Optional project scope (omit for global memories).
        tags: Optional free-form categorical tags.

    Returns:
        ``{ id, title, created_at }``
    """
    return get_store().create(
        title=title,
        content=content,
        project_name=project_name,
        tags=tags or [],
    )
