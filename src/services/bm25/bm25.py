import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.core.configs import DEFAULT_BM25_N


class BM25:
    def __init__(self):
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.index: BM25Okapi | None = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower()
        )

    def _rebuild(self) -> None:
        tokenized_documents = [
            self._tokenize(document)
            for document in self.documents
        ]

        if tokenized_documents:
            self.index = BM25Okapi(
                tokenized_documents
            )
        else:
            self.index = None

    def build(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]]
    ) -> None:

        if not (
            len(ids)
            == len(documents)
            == len(metadatas)
        ):
            raise ValueError(
                "ids, documents, and metadatas "
                "must have the same length"
            )

        self.ids = ids.copy()
        self.documents = documents.copy()
        self.metadatas = metadatas.copy()

        self._rebuild()

    def upsert(
        self,
        *,
        document_id: str,
        document: str,
        metadata: dict[str, Any]
    ) -> None:

        try:
            index = self.ids.index(document_id)

            self.documents[index] = document
            self.metadatas[index] = metadata

        except ValueError:
            self.ids.append(document_id)
            self.documents.append(document)
            self.metadatas.append(metadata)

        self._rebuild()

    def search(
        self,
        *,
        query: str,
        n_result: int = DEFAULT_BM25_N
    ) -> list[dict[str, Any]]:

        if self.index is None:
            return []

        query_tokens = self._tokenize(query)

        scores = self.index.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:n_result]

        return [
            {
                "id": self.ids[i],
                "document": self.documents[i],
                "metadata": self.metadatas[i],
                "score": float(scores[i]),
            }
            for i in ranked_indices
        ]

    def delete(
        self,
        *,
        document_id: str
    ) -> None:

        try:
            index = self.ids.index(document_id)
        except ValueError:
            return

        self.ids.pop(index)
        self.documents.pop(index)
        self.metadatas.pop(index)

        self._rebuild()