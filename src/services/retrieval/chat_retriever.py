from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import asyncio
import logging

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
from src.services.db.commands.commands import Command

logger = logging.getLogger(__name__)

# Application registries ensuring state isolation for all fruit apps
_vectordb_memories: dict[str, Memory] = {"quince": quince_memory}
_bm25_memories: dict[str, BM25] = {"quince": quince_bm25_memory}
_commands_registry: dict[str, Command] = {"quince": quince_commands}


@dataclass
class RAGConfig:
    """
    Dynamic configuration for hybrid RAG retrieval.
    All parameters are dynamically customizable per request or application.
    """
    top_k: int = TOP_K
    vector_k: int = DEFAULT_VECTORDB_N
    bm25_k: int = DEFAULT_BM25_N
    rrf_k: int = 60
    vector_weight: float = 0.5
    bm25_weight: float = 0.5
    use_reranker: bool = False
    rerank_top_k: int = DEFAULT_CANDIDATES_FOR_RERANKING
    score_threshold: float | None = None
    metadata_filter: dict[str, Any] | None = None


def _get_commands(application: str) -> Command:
    if application == "quince":
        return quince_commands
    if application not in _commands_registry:
        _commands_registry[application] = Command(
            db_name=application,
            application=application,
        )
    return _commands_registry[application]


def _get_vectordb_mem(application: str) -> Memory:
    if application == "quince":
        return quince_memory
    if application not in _vectordb_memories:
        _vectordb_memories[application] = Memory(application=application)
    return _vectordb_memories[application]


def _get_bm25_mem(application: str) -> BM25:
    if application == "quince":
        return quince_bm25_memory
    if application not in _bm25_memories:
        _bm25_memories[application] = BM25()
    return _bm25_memories[application]


async def semantic_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_VECTORDB_N,
    metadata_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Dense vector retrieval filtered by application and metadata."""
    vectordb_mem = _get_vectordb_mem(application=application)
    return vectordb_mem.query_memory(
        query=query,
        n_result=n_result,
        metadata_filter=metadata_filter,
    )


def bm25_retrieval(
    query: str,
    application: str,
    n_result: int = DEFAULT_BM25_N,
    metadata_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Sparse lexical BM25 retrieval filtered by application and metadata."""
    bm25_mem = _get_bm25_mem(application=application)
    combined_filter = {"application": application}
    if metadata_filter:
        combined_filter.update(metadata_filter)
    return bm25_mem.search(
        query=query,
        n_result=n_result,
        metadata_filter=combined_filter,
    )


def command_retrieval(application: str):
    commands = _get_commands(application=application)
    return commands.get_all()


def reciprocal_rank_fusion(
    vector_candidates: list[dict[str, Any]],
    bm25_candidates: list[dict[str, Any]],
    rrf_k: int = 60,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Performs Reciprocal Rank Fusion (RRF) between dense vector and sparse BM25 lists.
    Avoids score-scaling conflicts by relying on ordinal ranks.
    """
    fused: dict[str, dict[str, Any]] = {}

    for rank, cand in enumerate(vector_candidates, start=1):
        cid = cand["id"]
        if cid not in fused:
            fused[cid] = {
                "id": cid,
                "document": cand["document"],
                "metadata": cand["metadata"],
                "rrf_score": 0.0,
                "vector_rank": rank,
                "vector_distance": cand.get("distance"),
                "vector_score": cand.get("score"),
            }
        fused[cid]["rrf_score"] += vector_weight / (rrf_k + rank)

    for rank, cand in enumerate(bm25_candidates, start=1):
        cid = cand["id"]
        if cid not in fused:
            fused[cid] = {
                "id": cid,
                "document": cand["document"],
                "metadata": cand["metadata"],
                "rrf_score": 0.0,
                "bm25_rank": rank,
                "bm25_score": cand.get("score"),
            }
        else:
            fused[cid]["bm25_rank"] = rank
            fused[cid]["bm25_score"] = cand.get("score")
        fused[cid]["rrf_score"] += bm25_weight / (rrf_k + rank)

    sorted_candidates = sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )
    return sorted_candidates


async def deduplicate_candidates(
    application: str,
    query: str,
    vector_k: int = DEFAULT_VECTORDB_N,
    bm25_k: int = DEFAULT_BM25_N,
    metadata_filter: dict[str, Any] | None = None,
    rrf_k: int = 60,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Fetches vector and BM25 candidates and fuses them via Reciprocal Rank Fusion.
    Preserves backward compatibility while upgrading from O(N*M) loop to RRF.
    """
    vector_candidates = await semantic_retrieval(
        query=query,
        application=application,
        n_result=vector_k,
        metadata_filter=metadata_filter,
    )
    bm25_candidates = bm25_retrieval(
        query=query,
        application=application,
        n_result=bm25_k,
        metadata_filter=metadata_filter,
    )

    return reciprocal_rank_fusion(
        vector_candidates=vector_candidates,
        bm25_candidates=bm25_candidates,
        rrf_k=rrf_k,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
    )


async def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Applies neural cross-encoder reranking to top candidate pool.
    Gracefully falls back to original ranking if cross-encoder is unavailable.
    """
    if not candidates:
        return []

    try:
        reranker = ModelManager.get_reranker_model()
        pairs = [(query, candidate["document"]) for candidate in candidates]

        scores = await asyncio.to_thread(reranker.predict, pairs)

        reranked_candidates = []
        for candidate, score in zip(candidates, scores):
            reranked_candidates.append({
                **candidate,
                "rerank_score": float(score),
            })

        reranked_candidates.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )
        return reranked_candidates[:top_k]
    except Exception as exc:
        logger.warning(
            "Cross-encoder reranking failed or model not available: %s. Using RRF ranking.",
            exc,
        )
        return candidates[:top_k]


async def retrieve(
    query: str,
    application: str = "quince",
    *,
    config: RAGConfig | None = None,
    top_k: int | None = None,
    vector_k: int | None = None,
    bm25_k: int | None = None,
    metadata_filter: dict[str, Any] | None = None,
    use_reranker: bool | None = None,
    score_threshold: float | None = None,
    vector_weight: float | None = None,
    bm25_weight: float | None = None,
) -> list[dict[str, Any]]:
    """
    Main entrypoint for dynamic hybrid RAG retrieval.
    Combines dense semantic vector search + sparse BM25 keyword search,
    applies metadata filtering, fuses ranks with RRF, and optionally applies
    neural cross-encoder reranking and threshold pruning.
    """
    cfg = config or RAGConfig()

    effective_top_k = top_k if top_k is not None else cfg.top_k
    effective_vector_k = vector_k if vector_k is not None else cfg.vector_k
    effective_bm25_k = bm25_k if bm25_k is not None else cfg.bm25_k
    effective_filter = metadata_filter if metadata_filter is not None else cfg.metadata_filter
    effective_use_reranker = use_reranker if use_reranker is not None else cfg.use_reranker
    effective_threshold = score_threshold if score_threshold is not None else cfg.score_threshold
    effective_vec_w = vector_weight if vector_weight is not None else cfg.vector_weight
    effective_bm25_w = bm25_weight if bm25_weight is not None else cfg.bm25_weight

    candidates = await deduplicate_candidates(
        application=application,
        query=query,
        vector_k=effective_vector_k,
        bm25_k=effective_bm25_k,
        metadata_filter=effective_filter,
        rrf_k=cfg.rrf_k,
        vector_weight=effective_vec_w,
        bm25_weight=effective_bm25_w,
    )

    if effective_use_reranker and candidates:
        pool_to_rerank = candidates[:cfg.rerank_top_k]
        final_candidates = await rerank(
            query=query,
            candidates=pool_to_rerank,
            top_k=effective_top_k,
        )
    else:
        final_candidates = candidates[:effective_top_k]

    if effective_threshold is not None:
        final_candidates = [
            c for c in final_candidates
            if c.get("rerank_score", c.get("rrf_score", 0.0)) >= effective_threshold
        ]

    return final_candidates
