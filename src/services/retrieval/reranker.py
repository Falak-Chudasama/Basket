from typing import Any

from src.core.configs import TOP_K
from src.services.models.manager import ModelManager


def rerank(
    *,
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:

    if not query.strip() or not candidates:
        return []

    model = ModelManager.get_reranker_model()

    pairs = [
        [
            query,
            candidate["document"]
        ]
        for candidate in candidates
    ]

    scores = model.predict(
        pairs,
        show_progress_bar=False
    )

    ranked = []

    for candidate, score in zip(
        candidates,
        scores
    ):

        item = dict(candidate)

        item["rerank_score"] = float(
            score
        )

        ranked.append(item)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return ranked[:top_k]