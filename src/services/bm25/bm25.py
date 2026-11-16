from __future__ import annotations
import re
from typing import Any

from rank_bm25 import BM25Okapi

from src.core.configs import DEFAULT_BM25_N


class BM25:
    """
    High-performance, lightweight BM25 lexical search engine with
    cached tokenization, bulk ingestion, and metadata filtering.
    """

    def __init__(self) -> None:
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.tokenized_documents: list[list[str]] = []
        self.index: BM25Okapi | None = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
        )

    def _rebuild(self) -> None:
        """Rebuilds the BM25Okapi index from cached tokenized documents."""
        # Filter for non-empty token lists to prevent ZeroDivisionError
        valid_tokens = [tokens for tokens in self.tokenized_documents if tokens]

        if valid_tokens and any(valid_tokens):
            try:
                # RankBM25 requires tokenized list matching document length
                # We pass tokenized_documents directly; rank_bm25 handles empty lists safely
                # if there is at least one non-empty token list and non-zero total tokens
                total_len = sum(len(t) for t in self.tokenized_documents)
                if total_len > 0:
                    self.index = BM25Okapi(self.tokenized_documents)
                else:
                    self.index = None
            except ZeroDivisionError:
                self.index = None
        else:
            self.index = None

    def build(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not (len(ids) == len(documents) == len(metadatas)):
            raise ValueError("ids, documents, and metadatas must have the same length")

        self.ids = ids.copy()
        self.documents = documents.copy()
        self.metadatas = metadatas.copy()
        self.tokenized_documents = [self._tokenize(doc) for doc in documents]

        self._rebuild()

    def upsert(
        self,
        *,
        document_id: str,
        document: str,
        metadata: dict[str, Any],
        rebuild: bool = True,
    ) -> None:
        """
        Upsert a single document. Rebuilds index immediately unless rebuild=False.
        Tokenizes only this document, preserving corpus cache.
        """
        tokens = self._tokenize(document)

        try:
            index = self.ids.index(document_id)
            self.documents[index] = document
            self.metadatas[index] = metadata
            self.tokenized_documents[index] = tokens
        except ValueError:
            self.ids.append(document_id)
            self.documents.append(document)
            self.metadatas.append(metadata)
            self.tokenized_documents.append(tokens)

        if rebuild:
            self._rebuild()

    def bulk_upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """
        Efficient bulk ingestion for large context dumps.
        Tokenizes all new documents in batch and rebuilds index exactly once.
        """
        if not (len(ids) == len(documents) == len(metadatas)):
            raise ValueError("ids, documents, and metadatas must have the same length")

        if not ids:
            return

        id_to_idx = {doc_id: i for i, doc_id in enumerate(self.ids)}

        for doc_id, doc_text, meta in zip(ids, documents, metadatas):
            tokens = self._tokenize(doc_text)
            if doc_id in id_to_idx:
                existing_idx = id_to_idx[doc_id]
                self.documents[existing_idx] = doc_text
                self.metadatas[existing_idx] = meta
                self.tokenized_documents[existing_idx] = tokens
            else:
                new_idx = len(self.ids)
                self.ids.append(doc_id)
                self.documents.append(doc_text)
                self.metadatas.append(meta)
                self.tokenized_documents.append(tokens)
                id_to_idx[doc_id] = new_idx

        self._rebuild()

    @staticmethod
    def _matches_filter(doc_meta: dict[str, Any], filter_dict: dict[str, Any]) -> bool:
        """
        Evaluates whether a document's metadata matches the filter constraints.
        Supports exact match, list membership, $in, $nin, $eq, $ne, $and, and $or.
        """
        if not filter_dict:
            return True

        for key, target_val in filter_dict.items():
            if key == "$and" and isinstance(target_val, list):
                if not all(BM25._matches_filter(doc_meta, cond) for cond in target_val):
                    return False
                continue

            if key == "$or" and isinstance(target_val, list):
                if not any(BM25._matches_filter(doc_meta, cond) for cond in target_val):
                    return False
                continue

            doc_val = doc_meta.get(key)

            if isinstance(target_val, dict):
                # Operator expression
                for op, op_val in target_val.items():
                    if op == "$eq" and doc_val != op_val:
                        return False
                    elif op == "$ne" and doc_val == op_val:
                        return False
                    elif op == "$in":
                        if isinstance(op_val, (list, tuple, set)) and doc_val not in op_val:
                            return False
                    elif op == "$nin":
                        if isinstance(op_val, (list, tuple, set)) and doc_val in op_val:
                            return False
            elif isinstance(target_val, (list, tuple, set)):
                if doc_val not in target_val:
                    return False
            else:
                if doc_val != target_val:
                    return False

        return True

    def search(
        self,
        *,
        query: str,
        n_result: int = DEFAULT_BM25_N,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Performs BM25 search optionally pre-filtered by metadata constraints.
        Returns top `n_result` matching documents sorted by BM25 score descending.
        """
        if self.index is None or not self.ids:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        try:
            scores = self.index.get_scores(query_tokens)
        except Exception:
            return []

        # Find valid candidate indices: must contain at least one query token and match metadata filter
        query_token_set = set(query_tokens)
        candidate_indices = []
        for i in range(len(self.ids)):
            if metadata_filter and not self._matches_filter(self.metadatas[i], metadata_filter):
                continue
            has_term_match = bool(query_token_set.intersection(self.tokenized_documents[i])) if i < len(self.tokenized_documents) else False
            if scores[i] > 0.0 or has_term_match:
                candidate_indices.append(i)

        if not candidate_indices:
            return []

        # Rank candidates by score descending
        ranked_indices = sorted(
            candidate_indices,
            key=lambda i: scores[i],
            reverse=True,
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
        document_id: str,
    ) -> None:
        try:
            index = self.ids.index(document_id)
        except ValueError:
            return

        self.ids.pop(index)
        self.documents.pop(index)
        self.metadatas.pop(index)
        if index < len(self.tokenized_documents):
            self.tokenized_documents.pop(index)

        self._rebuild()

    def delete_by_filter(self, *, metadata_filter: dict[str, Any]) -> int:
        """Deletes all documents matching the metadata filter."""
        indices_to_remove = [
            i for i, meta in enumerate(self.metadatas)
            if self._matches_filter(meta, metadata_filter)
        ]
        if not indices_to_remove:
            return 0

        # Remove in reverse order
        for idx in sorted(indices_to_remove, reverse=True):
            self.ids.pop(idx)
            self.documents.pop(idx)
            self.metadatas.pop(idx)
            if idx < len(self.tokenized_documents):
                self.tokenized_documents.pop(idx)

        self._rebuild()
        return len(indices_to_remove)

    def clear(self) -> None:
        """Clears the entire BM25 index."""
        self.ids.clear()
        self.documents.clear()
        self.metadatas.clear()
        self.tokenized_documents.clear()
        self.index = None
