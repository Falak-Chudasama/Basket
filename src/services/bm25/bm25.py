import re
from typing import Any, Callable

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
            index = self.ids.index(
                document_id
            )

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
        n_result: int = DEFAULT_BM25_N,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:

        if self.index is None:
            return []

        query_tokens = self._tokenize(query)

        scores = self.index.get_scores(
            query_tokens
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )

        if session_id is not None:
            # Session retrieval includes durable memories plus the current
            # session's short-term memories. Long-term records intentionally
            # do not have a session_id.
            ranked_indices = [
                i
                for i in ranked_indices
                if (
                    self.metadatas[i].get("memory_type") == "long_term"
                    or self.metadatas[i].get("session_id") == session_id
                )
            ]

        ranked_indices = ranked_indices[:n_result]

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
            index = self.ids.index(
                document_id
            )
        except ValueError:
            return

        self.ids.pop(index)
        self.documents.pop(index)
        self.metadatas.pop(index)

        self._rebuild()

    def delete_where(
        self,
        *,
        predicate: Callable[[dict[str, Any]], bool]
    ) -> None:

        kept = [
            (document_id, document, metadata)
            for document_id, document, metadata in zip(
                self.ids,
                self.documents,
                self.metadatas,
            )
            if not predicate(metadata)
        ]

        self.ids = [item[0] for item in kept]
        self.documents = [item[1] for item in kept]
        self.metadatas = [item[2] for item in kept]

        self._rebuild()
