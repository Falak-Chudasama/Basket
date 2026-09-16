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


def _get_commands(application: str) -> Any:
    if application == "quince":
        return quince_commands

    raise ValueError(
        f"Unsupported application: {application}"
    )


def _get_mem(application: str) -> Memory:
    if application == "quince":
        return quince_memory

    raise ValueError(
        f"Unsupported application: {application}"
    )


def _get_bm25_mem(application: str) -> BM25:
    if application == "quince":
        return quince_bm25_memory

    raise ValueError(
        f"Unsupported application: {application}"
    )


async def semantic_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_VECTORDB_N,
) -> Any:
    mem = _get_mem(application)

    return mem.query_memory(
        query=query,
        n_result=n_result,
    )


def bm25_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_BM25_N,
) -> list[dict[str, Any]]:
    bm25_mem = _get_bm25_mem(application)

    return bm25_mem.search(
        query=query,
        n_result=n_result,
    )


def command_retrieval(
    application: str,
) -> list[dict[str, Any]]:
    commands = _get_commands(application)

    return [
        {
            "command": item["command"],
            "is_temporary": item.get("is_temporary", True),
            "application": item.get(
                "application",
                application
            ),
        }
        for item in commands.get_all()
    ]


def _normalize_semantic_results(
    results: dict[str, Any],
) -> list[dict[str, Any]]:
    if not results:
        return []

    ids = results.get("ids") or []
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    distances = results.get("distances") or []

    ids = ids[0] if ids else []
    documents = documents[0] if documents else []
    metadatas = metadatas[0] if metadatas else []
    distances = distances[0] if distances else []

    normalized: list[dict[str, Any]] = []

    for i, memory_id in enumerate(ids):
        normalized.append({
            "id": memory_id,
            "document": (
                documents[i]
                if i < len(documents)
                else ""
            ),
            "metadata": (
                metadatas[i]
                if i < len(metadatas)
                else {}
            ),
            "semantic_distance": (
                float(distances[i])
                if i < len(distances)
                else None
            ),
            "bm25_score": None,
            "sources": ["semantic"],
        })

    return normalized


def deduplicate_candidates(
    semantic_candidates: dict[str, Any],
    bm25_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    semantic_results = _normalize_semantic_results(
        semantic_candidates
    )

    merged: dict[str, dict[str, Any]] = {}

    for result in semantic_results:
        memory_id = result["id"]

        merged[memory_id] = {
            **result
        }

    for result in bm25_candidates:
        memory_id = result["id"]

        if memory_id in merged:
            merged[memory_id]["bm25_score"] = result["score"]
            merged[memory_id]["sources"].append("bm25")
        else:
            merged[memory_id] = {
                "id": memory_id,
                "document": result["document"],
                "metadata": result["metadata"],
                "semantic_distance": None,
                "bm25_score": result["score"],
                "sources": ["bm25"],
            }

    return list(merged.values())


async def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    reranker = ModelManager.get_reranker_model()

    candidates = candidates[
        :DEFAULT_CANDIDATES_FOR_RERANKING
    ]

    pairs = [
        (
            query,
            candidate["document"],
        )
        for candidate in candidates
    ]

    scores = await asyncio.to_thread(
        reranker.predict,
        pairs,
    )

    reranked: list[dict[str, Any]] = []

    for candidate, score in zip(
        candidates,
        scores,
    ):
        reranked.append({
            **candidate,
            "rerank_score": float(score),
        })

    reranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked[:top_k]


async def retrieve(
    query: str,
    application: str = "quince",
) -> list[dict[str, Any]]:

    semantic_task = asyncio.to_thread(
        semantic_retrieval,
        query,
        application,
        DEFAULT_VECTORDB_N,
    )

    bm25_task = asyncio.to_thread(
        bm25_retrieval,
        query,
        application,
        DEFAULT_BM25_N,
    )

    semantic_candidates, bm25_candidates = await asyncio.gather(
        semantic_task,
        bm25_task,
    )

    candidates = deduplicate_candidates(
        semantic_candidates=semantic_candidates,
        bm25_candidates=bm25_candidates,
    )

    reranked_candidates = await rerank(
        query=query,
        candidates=candidates,
        top_k=TOP_K,
    )

    commands = command_retrieval(
        application=application
    )

    return [
        *reranked_candidates,
        *commands,
    ]