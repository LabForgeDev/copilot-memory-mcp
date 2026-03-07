"""ChromaDB wrapper — all memory CRUD and search lives here."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

import chromadb

from app import embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "memories"

# Tags are stored as "|tag1|tag2|tag3|" so $contains matches exact tokens.
_TAG_SEP = "|"


def _pack_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return _TAG_SEP + _TAG_SEP.join(tags) + _TAG_SEP


def _unpack_tags(packed: str) -> list[str]:
    if not packed:
        return []
    return [t for t in packed.strip(_TAG_SEP).split(_TAG_SEP) if t]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """Thin wrapper around a ChromaDB collection."""

    def __init__(self, chroma_path: str | None = None) -> None:
        path = chroma_path or os.environ.get("CHROMA_PATH", "/data/chroma")
        logger.info("Initialising ChromaDB at %s", path)
        try:
            if path == ":memory:":
                self._client = chromadb.EphemeralClient()
            else:
                self._client = chromadb.PersistentClient(path=path)
            self._col = self._client.get_or_create_collection(
                COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:
            logger.error("ChromaDB init failed: %s", exc)
            sys.exit(1)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _build_where(
        self,
        project_name: str | None,
    ) -> dict[str, Any] | None:
        """Build a ChromaDB where clause for project_name only.
        Tag filtering is done in Python after fetching results because
        ChromaDB's $contains operator is not reliable for metadata strings.
        """
        if project_name is not None:
            return {"project_name": {"$eq": project_name}}
        return None

    @staticmethod
    def _matches_tags(meta: dict, tags: list[str]) -> bool:
        packed = meta.get("tags", "")
        return all(f"{_TAG_SEP}{tag}{_TAG_SEP}" in packed for tag in tags)

    def _row(self, doc_id: str, document: str, meta: dict) -> dict:
        return {
            "id": doc_id,
            "title": meta.get("title", ""),
            "content": document,
            "project_name": meta.get("project_name") or None,
            "tags": _unpack_tags(meta.get("tags", "")),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
        }

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        title: str,
        content: str,
        project_name: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        if not title or not title.strip():
            raise ValueError("title and content are required")
        if not content or not content.strip():
            raise ValueError("title and content are required")

        tags = tags or []
        doc_id = str(uuid.uuid4())
        now = _now()
        embedding = embeddings.encode(f"{title} {content}")

        self._col.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[
                {
                    "title": title,
                    "project_name": project_name or "",
                    "tags": _pack_tags(tags),
                    "created_at": now,
                    "updated_at": now,
                }
            ],
            embeddings=[embedding],
        )
        return {"id": doc_id, "title": title, "created_at": now}

    def get(self, doc_id: str) -> dict:
        result = self._col.get(ids=[doc_id], include=["metadatas", "documents"])
        if not result["ids"]:
            raise ValueError(f"Memory {doc_id} not found")
        meta = result["metadatas"][0]
        document = result["documents"][0]
        return self._row(doc_id, document, meta)

    def update(
        self,
        doc_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        existing = self.get(doc_id)  # raises ValueError if not found

        new_title = title if title is not None else existing["title"]
        new_content = content if content is not None else existing["content"]
        new_tags = tags if tags is not None else existing["tags"]
        now = _now()

        embedding = embeddings.encode(f"{new_title} {new_content}")

        self._col.update(
            ids=[doc_id],
            documents=[new_content],
            metadatas=[
                {
                    "title": new_title,
                    "project_name": existing["project_name"] or "",
                    "tags": _pack_tags(new_tags),
                    "created_at": existing["created_at"],
                    "updated_at": now,
                }
            ],
            embeddings=[embedding],
        )
        return {"id": doc_id, "title": new_title, "updated_at": now}

    def delete(self, doc_id: str) -> dict:
        self.get(doc_id)  # raises ValueError if not found
        self._col.delete(ids=[doc_id])
        return {"id": doc_id, "deleted": True}

    # ------------------------------------------------------------------
    # search + list
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        project_name: str | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        tags = tags or []
        where = self._build_where(project_name)
        embedding = embeddings.encode(query)

        # Overscan when tag-filtering so post-filter still returns `limit` results.
        overscan = limit * max(1, len(tags)) * 4 if tags else limit

        # ChromaDB raises if n_results > elements matching `where`.
        count_kwargs: dict[str, Any] = {"include": []}
        if where is not None:
            count_kwargs["where"] = where
        filtered_count = len(self._col.get(**count_kwargs)["ids"])
        if filtered_count == 0:
            return []

        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": min(overscan, filtered_count),
            "include": ["metadatas", "documents", "distances"],
        }
        if where is not None:
            kwargs["where"] = where

        result = self._col.query(**kwargs)

        rows = []
        for doc_id, meta, document, dist in zip(
            result["ids"][0],
            result["metadatas"][0],
            result["documents"][0],
            result["distances"][0],
        ):
            if tags and not self._matches_tags(meta, tags):
                continue
            row = self._row(doc_id, document, meta)
            row["score"] = round(1.0 - dist, 6)
            rows.append(row)
            if len(rows) == limit:
                break
        return rows

    def list(
        self,
        project_name: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")

        tags = tags or []
        where = self._build_where(project_name)

        # Fetch all project-scoped records; tag filtering done in Python.
        get_kwargs: dict[str, Any] = {"include": ["metadatas"]}
        if where is not None:
            get_kwargs["where"] = where

        all_result = self._col.get(**get_kwargs)
        all_items = [
            {
                "id": doc_id,
                "title": meta.get("title", ""),
                "project_name": meta.get("project_name") or None,
                "tags": _unpack_tags(meta.get("tags", "")),
                "created_at": meta.get("created_at", ""),
            }
            for doc_id, meta in zip(all_result["ids"], all_result["metadatas"])
            if not tags or self._matches_tags(meta, tags)
        ]

        total = len(all_items)
        total_pages = max(1, -(-total // page_size))  # ceiling division
        offset = (page - 1) * page_size
        items = all_items[offset : offset + page_size]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_store: MemoryStore | None = None


def get_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


def init_store(chroma_path: str) -> MemoryStore:
    """Replace the global singleton — used for testing."""
    global _store
    _store = MemoryStore(chroma_path=chroma_path)
    return _store
