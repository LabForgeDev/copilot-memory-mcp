"""MCP tool: search_memories."""
from __future__ import annotations

from app.memory_store import get_store


def search_memories(
    query: str,
    project_name: str | None = None,
    tags: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """Semantic vector search over stored memories.

    Args:
        query: Natural language search query.
        project_name: Filter to a specific project (omit = global search).
        tags: AND-match filter by tags (omit = no tag filter).
        limit: Maximum number of results to return (default 5).

    Returns:
        List of ``{ id, title, content, project_name, tags, score, created_at }``.
    """
    return get_store().search(
        query=query,
        project_name=project_name,
        tags=tags or [],
        limit=limit,
    )
