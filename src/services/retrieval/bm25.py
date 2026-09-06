import re
import chromadb
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


class BM25Retriever:
    def __init__(self, chroma_path: str = "./chroma_db", collection_name: str = "university_docs"):
        self._client = chromadb.PersistentClient(path=chroma_path)
        self._collection = self._client.get_or_create_collection(name=collection_name)
        self._documents: list[str] | None = None
        self._metadatas: list[dict] | None = None
        self._ids: list[str] | None = None
        self._bm25: BM25Okapi | None = None

    def load(self) -> None:
        results = self._collection.get()
        self._documents = results["documents"]
        self._metadatas = results["metadatas"]
        self._ids = results["ids"]

        if not self._documents:
            self._bm25 = None
            return

        tokenized = [tokenize(doc) for doc in self._documents]
        self._bm25 = BM25Okapi(tokenized)

    def _ensure_loaded(self) -> None:
        if self._documents is None:
            raise RuntimeError("BM25Retriever has not been loaded. Call .load() at startup.")

    def _matches_departments(self, idx: int, departments: list[str] | None) -> bool:
        if not departments:
            return True

        meta = (self._metadatas or [])[idx] or {}
        department = str(meta.get("department", "") or "").strip().lower()
        allowed = {str(dep).strip().lower() for dep in departments if str(dep).strip()}
        return department in allowed

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.01) -> list[dict]:
        self._ensure_loaded()

        if not self._bm25:
            return []

        tokens = tokenize(query)
        scores = self._bm25.get_scores(tokens)

        ranked = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )

        results = []
        for idx in ranked:
            if scores[idx] < score_threshold:
                break
            if len(results) >= top_k:
                break
            results.append({
                "content": self._documents[idx],
                "metadata": self._metadatas[idx],
                "id": self._ids[idx],
                "bm25_score": float(scores[idx])
            })

        return results

    def retrieve_by_departments(
        self,
        query: str,
        departments: list[str],
        top_k: int = 5,
        score_threshold: float = 0.01,
    ) -> list[dict]:
        self._ensure_loaded()

        if not self._bm25:
            return []

        if not departments:
            return self.retrieve(query, top_k=top_k, score_threshold=score_threshold)

        tokens = tokenize(query)
        scores = self._bm25.get_scores(tokens)

        filtered_indices = [
            idx
            for idx in range(len(scores))
            if self._matches_departments(idx, departments)
        ]

        if not filtered_indices:
            return []

        ranked = sorted(
            filtered_indices,
            key=lambda i: scores[i],
            reverse=True
        )

        results = []
        for idx in ranked:
            if scores[idx] < score_threshold:
                continue
            if len(results) >= top_k:
                break
            results.append({
                "content": self._documents[idx],
                "metadata": self._metadatas[idx],
                "id": self._ids[idx],
                "bm25_score": float(scores[idx])
            })

        return results

    def reload(self) -> None:
        self._bm25 = None
        self.load()


bm25_retriever = BM25Retriever()
