"""MCP tool: list_memories."""
from __future__ import annotations

from app.memory_store import get_store


def list_memories(
    project_name: str | None = None,
    tags: list[str] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Browse memories without a semantic query (paginated).

    Returns lightweight records — title only, no content.

    Args:
        project_name: Filter by project (omit = global).
        tags: AND-match filter by tags (omit = no tag filter).
        page: 1-indexed page number (default 1).
        page_size: Results per page (default 20, max 100).

    Returns:
        ``{ items: [{id, title, project_name, tags, created_at}],
            page, page_size, total, total_pages }``

    Raises:
        ValueError: If *page* < 1 or *page_size* > 100.
    """
    return get_store().list(
        project_name=project_name,
        tags=tags or [],
        page=page,
        page_size=page_size,
    )
