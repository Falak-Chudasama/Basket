from src.utils.utils import get_datetime
from src.core.configs import DEFAULT_VECTORDB_N
from src.services.embedding.embedder import create_embedding
from src.services.vectordb.chroma_store import ChromaStore
import logging
import time
from typing import Any

logger = logging.getLogger("basket.memory")


class Memory:
    def __init__(
        self,
        application: str = "quince",
        bm25_memory=None,
    ):
        self.application = application
        self.collection = ChromaStore("memory")
        self.bm25_memory = bm25_memory

    def add_memory(
        self,
        *,
        memory_id: str,
        document: str,
        source: str = "user",
        embedding: list[float] | None = None,
        memory_type: str = "short_term",
        session_id: str | None = None,
    ) -> None:
        started = time.perf_counter()

        if not document or not document.strip():
            raise ValueError("document is required")

        metadata: dict[str, Any] = {
            "application": self.application,
            "memory_type": memory_type,
            "source": source,
            "created_at": get_datetime(),
        }

        if session_id is not None:
            metadata["session_id"] = session_id

        if embedding is None:
            embedding = create_embedding(document)

        self.collection.upsert(
            ids=[memory_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        # Keep the in-process hybrid BM25 index synchronized immediately.
        # Previously only Chroma was updated, so new long-term memories were
        # invisible to BM25 until the next Basket restart.
        if self.bm25_memory is not None:
            self.bm25_memory.upsert(
                document_id=memory_id,
                document=document,
                metadata=metadata,
            )

        logger.info(
            "MEMORY UPSERT complete id=%s type=%s elapsed=%.3fs",
            memory_id,
            memory_type,
            time.perf_counter() - started,
        )

    def query_memory(
        self,
        *,
        query: str,
        n_result: int = DEFAULT_VECTORDB_N,
        session_id: str | None = None,
    ):
        query = query.strip()
        if not query:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        started = time.perf_counter()
        query_embedding = create_embedding(query)

        if session_id is None:
            where = {"application": self.application}
        else:
            # A session-scoped retrieval must include both the current session's
            # short-term memories and all durable long-term memories.
            where = {
                "$and": [
                    {"application": self.application},
                    {
                        "$or": [
                            {"memory_type": "long_term"},
                            {"session_id": session_id},
                        ]
                    },
                ]
            }

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result,
            where=where,
        )

        logger.info(
            "MEMORY QUERY complete query=%r results=%d elapsed=%.3fs",
            query,
            len(result.get("documents", [[]])[0] if isinstance(result, dict) else []),
            time.perf_counter() - started,
        )
        return result

    def get_all(self):
        return self.collection.get(where={"application": self.application})

    def _clear_bm25(self, predicate) -> None:
        if self.bm25_memory is not None:
            self.bm25_memory.delete_where(predicate=predicate)

    def clear_short_term(self) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"application": self.application},
                    {"memory_type": "short_term"},
                ]
            }
        )
        self._clear_bm25(
            lambda metadata: (
                metadata.get("application") == self.application
                and metadata.get("memory_type") == "short_term"
            )
        )

    def clear_long_term(self) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"application": self.application},
                    {"memory_type": "long_term"},
                ]
            }
        )
        self._clear_bm25(
            lambda metadata: (
                metadata.get("application") == self.application
                and metadata.get("memory_type") == "long_term"
            )
        )

    def clear_all(self) -> None:
        self.collection.delete(where={"application": self.application})
        self._clear_bm25(
            lambda metadata: metadata.get("application") == self.application
        )
