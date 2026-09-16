from __future__ import annotations

import asyncio
from typing import Any

from src.core.configs import (
    DEFAULT_VECTORDB_N,
    TOP_K,
    DEFAULT_BM25_N,
    DEFAULT_CANDIDATES_FOR_RERANKING,
)
from src.core.state import (
    quince_bm25_memory,
    quince_commands,
    quince_memory,
)
from src.services.vectordb.memory import Memory
from src.services.bm25.bm25 import BM25
from src.services.embedding.embedder import ModelManager


def _get_commands(application: str):
    return quince_commands


def _get_vectordb_mem(application: str):
    return quince_memory


def _get_bm25_mem(application: str):
    return quince_bm25_memory


async def semantic_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_VECTORDB_N,
):
    vectordb_mem = _get_vectordb_mem(application=application)
    return vectordb_mem.query_memory(query=query, n_result=n_result)


def bm25_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_BM25_N,
):
    b25_mem = _get_bm25_mem(application=application)
    return b25_mem.search(query=query, n_result=n_result)


def command_retrieval(application: str):
    commands = _get_commands(application=application)
    return commands.get_all()


def deduplicate_candidates(application: str, query: str):
    unique_candidates = []

    semantic_candidates = semantic_retrieval(query=query, application=application)
    bm25_candidates = bm25_retrieval(query=query, application=application)

    # bm25_indices = bm25_candidates
    # TODO: Finish this.

    return unique_candidates


async def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
):

    pass


async def retrieve(
    query: str,
    application: str = "quince",
):
    pass