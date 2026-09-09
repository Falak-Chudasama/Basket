from typing import Any

from src.core.configs import (
    DEFAULT_CANDIDATES_FOR_RERANKING,
    TOP_K
)
from src.core.state import (
    quince_bm25_memory,
    quince_memory
)
from src.services.retrieval.reranker import rerank


def _semantic_results(
    results: dict[str, Any],
) -> list[dict[str, Any]]:

    ids = (
        results.get("ids", [[]])[0]
        if results
        else []
    )

    documents = (
        results.get("documents", [[]])[0]
        if results
        else []
    )

    metadatas = (
        results.get("metadatas", [[]])[0]
        if results
        else []
    )

    distances = (
        results.get("distances", [[]])[0]
        if results
        else []
    )

    output = []

    for index, document_id in enumerate(ids):

        document = (
            documents[index]
            if index < len(documents)
            else ""
        )

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        score = (
            1.0 - float(distance)
            if distance is not None
            else 0.0
        )

        output.append({
            "id": document_id,
            "document": document,
            "metadata": metadata or {},
            "semantic_score": score,
        })

    return output


def _merge_candidates(
    bm25_results: list[dict[str, Any]],
    semantic_results: list[dict[str, Any]],
    candidates_for_reranking: int = DEFAULT_CANDIDATES_FOR_RERANKING,
) -> list[dict[str, Any]]:

    candidates: dict[str, dict[str, Any]] = {}

    for rank, result in enumerate(
        bm25_results,
        start=1
    ):

        document_id = result["id"]

        candidate = candidates.setdefault(
            document_id,
            {
                "id": document_id,
                "document": result["document"],
                "metadata": result.get(
                    "metadata",
                    {}
                ),
                "bm25_score": 0.0,
                "semantic_score": 0.0,
                "rrf_score": 0.0,
            }
        )

        candidate["bm25_score"] = float(
            result.get(
                "score",
                0.0
            )
        )

        candidate["rrf_score"] += (
            1.0 / (60 + rank)
        )

    for rank, result in enumerate(
        semantic_results,
        start=1
    ):

        document_id = result["id"]

        candidate = candidates.setdefault(
            document_id,
            {
                "id": document_id,
                "document": result["document"],
                "metadata": result.get(
                    "metadata",
                    {}
                ),
                "bm25_score": 0.0,
                "semantic_score": 0.0,
                "rrf_score": 0.0,
            }
        )

        candidate["semantic_score"] = float(
            result.get(
                "semantic_score",
                0.0
            )
        )

        if (
            not candidate.get("metadata")
            and result.get("metadata")
        ):
            candidate["metadata"] = result[
                "metadata"
            ]

        candidate["rrf_score"] += (
            1.0 / (60 + rank)
        )

    return sorted(
        candidates.values(),
        key=lambda item: item["rrf_score"],
        reverse=True
    )[:candidates_for_reranking]


def retrieve(
    *,
    query: str,
    top_k: int = TOP_K,
    candidates_for_reranking: int = (
        DEFAULT_CANDIDATES_FOR_RERANKING
    ),
    semantic_memory=quince_memory,
    bm25_memory=quince_bm25_memory,
    session_id: str | None = None,
) -> list[dict[str, Any]]:

    query = query.strip()

    if not query:
        return []

    bm25_results = bm25_memory.search(
        query=query,
        n_result=candidates_for_reranking,
        session_id=session_id,
    )

    semantic_results = _semantic_results(
        semantic_memory.query_memory(
            query=query,
            n_result=candidates_for_reranking,
            session_id=session_id,
        )
    )

    candidates = _merge_candidates(
        bm25_results,
        semantic_results,
        candidates_for_reranking=candidates_for_reranking,
    )

    if not candidates:
        return []

    return rerank(
        query=query,
        candidates=candidates,
        top_k=min(
            top_k,
            TOP_K
        )
    )
