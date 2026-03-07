"""Unit tests for MemoryStore (ChromaDB wrapper)."""
from __future__ import annotations

import pytest

import app.embeddings as emb_module
from app.memory_store import MemoryStore


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    """Replace real sentence-transformer encoding with a zero vector."""
    monkeypatch.setattr(emb_module, "encode", lambda text: [0.0] * 384)


@pytest.fixture()
def store():
    return MemoryStore(chroma_path=":memory:")


# ---------------------------------------------------------------------------
# create / retrieve
# ---------------------------------------------------------------------------


def test_create_returns_id_title_created_at(store):
    result = store.create(title="Test", content="Some content")
    assert "id" in result
    assert result["title"] == "Test"
    assert "created_at" in result


def test_get_roundtrip(store):
    created = store.create(
        title="Redis tips",
        content="Use pipelining for bulk writes.",
        project_name="backend",
        tags=["redis", "performance"],
    )
    fetched = store.get(created["id"])
    assert fetched["title"] == "Redis tips"
    assert fetched["content"] == "Use pipelining for bulk writes."
    assert fetched["project_name"] == "backend"
    assert set(fetched["tags"]) == {"redis", "performance"}


def test_get_unknown_id_raises(store):
    with pytest.raises(ValueError, match="not found"):
        store.get("00000000-0000-0000-0000-000000000000")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


def test_update_title(store):
    created = store.create(title="Old title", content="Content")
    result = store.update(created["id"], title="New title")
    assert result["title"] == "New title"
    fetched = store.get(created["id"])
    assert fetched["title"] == "New title"
    assert fetched["content"] == "Content"  # unchanged


def test_update_content_re_embed(store, monkeypatch):
    calls: list[str] = []

    def tracking_encode(text: str) -> list[float]:
        calls.append(text)
        return [0.0] * 384

    monkeypatch.setattr(emb_module, "encode", tracking_encode)

    created = store.create(title="T", content="Old content")
    calls.clear()
    store.update(created["id"], content="New content")
    assert any("New content" in c for c in calls)


def test_update_tags(store):
    created = store.create(title="T", content="C", tags=["a"])
    store.update(created["id"], tags=["b", "c"])
    fetched = store.get(created["id"])
    assert set(fetched["tags"]) == {"b", "c"}


def test_update_unknown_id_raises(store):
    with pytest.raises(ValueError, match="not found"):
        store.update("00000000-0000-0000-0000-000000000000", title="X")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete(store):
    created = store.create(title="T", content="C")
    result = store.delete(created["id"])
    assert result == {"id": created["id"], "deleted": True}
    with pytest.raises(ValueError, match="not found"):
        store.get(created["id"])


def test_delete_unknown_id_raises(store):
    with pytest.raises(ValueError, match="not found"):
        store.delete("00000000-0000-0000-0000-000000000000")


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


def test_search_returns_results(store):
    store.create(title="Caching", content="Redis is fast.")
    store.create(title="Databases", content="Use indexes.")
    results = store.search("Redis caching", limit=5)
    assert len(results) >= 1
    assert all("score" in r for r in results)
    assert all("content" in r for r in results)


def test_search_results_ordered_by_score(store):
    for i in range(3):
        store.create(title=f"Mem {i}", content=f"Content {i}")
    results = store.search("content", limit=3)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_project_name_filter_scopes_results(store):
    store.create(title="Alpha", content="In project A", project_name="projectA")
    store.create(title="Beta", content="In project B", project_name="projectB")
    results = store.search("project", project_name="projectA", limit=5)
    assert all(r["project_name"] == "projectA" for r in results)


def test_search_global_returns_across_projects(store):
    store.create(title="X", content="global content", project_name="p1")
    store.create(title="Y", content="global content", project_name="p2")
    results = store.search("global content", limit=10)
    projects = {r["project_name"] for r in results}
    assert "p1" in projects
    assert "p2" in projects


def test_search_empty_collection_returns_empty(store):
    results = store.search("anything")
    assert results == []


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_all(store):
    for i in range(5):
        store.create(title=f"M{i}", content="c")
    result = store.list(page=1, page_size=20)
    assert result["total"] == 5
    assert len(result["items"]) == 5


def test_list_pagination(store):
    for i in range(7):
        store.create(title=f"M{i}", content="c")
    page1 = store.list(page=1, page_size=3)
    page2 = store.list(page=2, page_size=3)
    page3 = store.list(page=3, page_size=3)
    assert len(page1["items"]) == 3
    assert len(page2["items"]) == 3
    assert len(page3["items"]) == 1
    assert page1["total_pages"] == 3
    ids_page1 = {r["id"] for r in page1["items"]}
    ids_page2 = {r["id"] for r in page2["items"]}
    assert ids_page1.isdisjoint(ids_page2)


def test_list_project_filter(store):
    store.create(title="A", content="c", project_name="p1")
    store.create(title="B", content="c", project_name="p2")
    result = store.list(project_name="p1")
    assert result["total"] == 1
    assert result["items"][0]["title"] == "A"


def test_list_tag_filter_and_semantics(store):
    store.create(title="Both", content="c", tags=["x", "y"])
    store.create(title="OnlyX", content="c", tags=["x"])
    store.create(title="OnlyY", content="c", tags=["y"])
    result = store.list(tags=["x", "y"])
    assert result["total"] == 1
    assert result["items"][0]["title"] == "Both"


def test_list_invalid_page_raises(store):
    with pytest.raises(ValueError):
        store.list(page=0)


def test_list_invalid_page_size_raises(store):
    with pytest.raises(ValueError):
        store.list(page_size=101)
