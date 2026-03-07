"""Integration tests — call tool functions directly against an in-memory store."""
from __future__ import annotations

import pytest

import app.embeddings as emb_module
import app.memory_store as ms_module
from app.tools.create_memory import create_memory
from app.tools.delete_memory import delete_memory
from app.tools.list_memories import list_memories
from app.tools.search_memories import search_memories
from app.tools.update_memory import update_memory


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    monkeypatch.setattr(emb_module, "encode", lambda text: [0.0] * 384)


@pytest.fixture(autouse=True)
def in_memory_store():
    """Replace the global store singleton with an ephemeral in-memory instance."""
    ms_module.init_store(":memory:")
    yield
    ms_module._store = None


# ---------------------------------------------------------------------------
# create_memory
# ---------------------------------------------------------------------------


def test_create_memory_happy(mock_embeddings, in_memory_store):
    result = create_memory(title="Deploy tip", content="Use blue-green deployments.")
    assert result["title"] == "Deploy tip"
    assert "id" in result
    assert "created_at" in result


def test_create_memory_missing_title_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError, match="required"):
        create_memory(title="", content="Some content")


def test_create_memory_missing_content_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError, match="required"):
        create_memory(title="Title", content="")


def test_create_memory_with_tags_and_project(mock_embeddings, in_memory_store):
    result = create_memory(
        title="T",
        content="C",
        project_name="myproject",
        tags=["infra", "docker"],
    )
    assert "id" in result


# ---------------------------------------------------------------------------
# search_memories
# ---------------------------------------------------------------------------


def test_search_memories_happy(mock_embeddings, in_memory_store):
    create_memory(title="Caching", content="Redis is great for caching.")
    results = search_memories(query="caching")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert "score" in results[0]


def test_search_memories_global(mock_embeddings, in_memory_store):
    create_memory(title="A", content="alpha", project_name="p1")
    create_memory(title="B", content="beta", project_name="p2")
    results = search_memories(query="content", limit=10)
    project_names = {r["project_name"] for r in results}
    assert "p1" in project_names
    assert "p2" in project_names


def test_search_memories_project_filter(mock_embeddings, in_memory_store):
    create_memory(title="A", content="alpha", project_name="p1")
    create_memory(title="B", content="beta", project_name="p2")
    results = search_memories(query="content", project_name="p1", limit=10)
    assert all(r["project_name"] == "p1" for r in results)


def test_search_memories_tag_filter(mock_embeddings, in_memory_store):
    create_memory(title="Tagged", content="c", tags=["python"])
    create_memory(title="Untagged", content="c")
    results = search_memories(query="c", tags=["python"], limit=10)
    assert all("python" in r["tags"] for r in results)


# ---------------------------------------------------------------------------
# update_memory
# ---------------------------------------------------------------------------


def test_update_memory_happy(mock_embeddings, in_memory_store):
    created = create_memory(title="Old", content="Old content")
    result = update_memory(id=created["id"], title="New")
    assert result["title"] == "New"
    assert "updated_at" in result


def test_update_memory_not_found_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError, match="not found"):
        update_memory(id="00000000-0000-0000-0000-000000000000", title="X")


def test_update_memory_partial(mock_embeddings, in_memory_store):
    created = create_memory(title="T", content="Original content", tags=["a"])
    update_memory(id=created["id"], tags=["b"])
    # Verify via search that the update took effect (title/content unchanged)
    results = search_memories(query="Original content", limit=1)
    assert results[0]["tags"] == ["b"]


# ---------------------------------------------------------------------------
# delete_memory
# ---------------------------------------------------------------------------


def test_delete_memory_happy(mock_embeddings, in_memory_store):
    created = create_memory(title="T", content="C")
    result = delete_memory(id=created["id"])
    assert result == {"id": created["id"], "deleted": True}


def test_delete_memory_not_found_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError, match="not found"):
        delete_memory(id="00000000-0000-0000-0000-000000000000")


def test_delete_memory_then_search_excludes(mock_embeddings, in_memory_store):
    created = create_memory(title="Gone", content="soon deleted")
    delete_memory(id=created["id"])
    results = search_memories(query="soon deleted", limit=10)
    assert all(r["id"] != created["id"] for r in results)


# ---------------------------------------------------------------------------
# list_memories
# ---------------------------------------------------------------------------


def test_list_memories_happy(mock_embeddings, in_memory_store):
    create_memory(title="A", content="c")
    create_memory(title="B", content="c")
    result = list_memories()
    assert result["total"] >= 2
    assert "items" in result
    assert "total_pages" in result


def test_list_memories_project_filter(mock_embeddings, in_memory_store):
    create_memory(title="In P1", content="c", project_name="p1")
    create_memory(title="In P2", content="c", project_name="p2")
    result = list_memories(project_name="p1")
    assert result["total"] == 1
    assert result["items"][0]["title"] == "In P1"


def test_list_memories_tag_filter_and_semantics(mock_embeddings, in_memory_store):
    create_memory(title="Both", content="c", tags=["x", "y"])
    create_memory(title="X only", content="c", tags=["x"])
    result = list_memories(tags=["x", "y"])
    assert result["total"] == 1


def test_list_memories_pagination_boundary(mock_embeddings, in_memory_store):
    for i in range(5):
        create_memory(title=f"M{i}", content="c")
    result = list_memories(page=1, page_size=3)
    assert len(result["items"]) == 3
    assert result["total_pages"] == 2


def test_list_memories_last_page(mock_embeddings, in_memory_store):
    for i in range(5):
        create_memory(title=f"M{i}", content="c")
    result = list_memories(page=2, page_size=3)
    assert len(result["items"]) == 2


def test_list_memories_beyond_last_page(mock_embeddings, in_memory_store):
    create_memory(title="Only", content="c")
    result = list_memories(page=99, page_size=20)
    assert result["items"] == []


def test_list_memories_invalid_page_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError):
        list_memories(page=0)


def test_list_memories_invalid_page_size_raises(mock_embeddings, in_memory_store):
    with pytest.raises(ValueError):
        list_memories(page_size=101)
