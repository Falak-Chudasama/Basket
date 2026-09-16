from __future__ import annotations
from typing import Any
import asyncio

from src.core.configs import (
    DEFAULT_VECTORDB_N,
    TOP_K,
    DEFAULT_BM25_N,
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


async def deduplicate_candidates(application: str, query: str) -> list[dict[str, Any]]:
    unique_candidates: list[dict[str, Any]] = []

    semantic_candidates = await semantic_retrieval(query=query, application=application)
    bm25_candidates = bm25_retrieval(query=query, application=application)

    for bm25_candidate in bm25_candidates:
        flag = True
        for semantic_candidate in semantic_candidates:
            if semantic_candidate['id'] == bm25_candidate['id']:
                flag = False
                break
        if flag:
            unique_candidates.append(bm25_candidate)

    for semantic_candidate in semantic_candidates:
        unique_candidates.append(semantic_candidate)      

    return unique_candidates


async def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
):
    if not candidates:
        return []

    reranker = ModelManager.get_reranker_model()

    pairs = [
        (
            query,
            candidate["document"]
        ) for candidate in candidates
    ]

    scores = await asyncio.to_thread(
        reranker.predict,
        pairs
    )

    reranked_candidates = []

    for candidate, score in zip(candidates,scores):
        reranked_candidates.append({
            **candidate,
            "rerank_score": float(score),
        })

    reranked_candidates.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked_candidates[:top_k]


async def retrieve(
    query: str,
    application: str = "quince",
):
    unique_candidates = await deduplicate_candidates(application=application, query=query)
    reranked_candidates = await rerank(query=query, candidates=unique_candidates)
    return reranked_candidates