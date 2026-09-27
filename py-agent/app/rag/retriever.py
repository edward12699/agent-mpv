"""Retriever 封装。"""

from __future__ import annotations

from functools import lru_cache

from app.rag.vector_store import get_or_create_vector_store


@lru_cache
def get_retriever():
    vector_store = get_or_create_vector_store()
    return vector_store.as_retriever(search_kwargs={"k": 3})
