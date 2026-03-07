"""Sentence-transformers encoder — loaded once as a module-level singleton."""
from __future__ import annotations

import logging
import os
import sys

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def _load_model() -> SentenceTransformer:
    cache = os.environ.get("SENTENCE_TRANSFORMERS_HOME", "/app/models")
    logger.info("Loading embedding model %s from %s", MODEL_NAME, cache)
    try:
        return SentenceTransformer(MODEL_NAME, cache_folder=cache)
    except Exception as exc:
        logger.error("Failed to load embedding model: %s", exc)
        sys.exit(1)


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def encode(text: str) -> list[float]:
    """Return a 384-dim embedding for *text*."""
    return get_model().encode(text).tolist()
