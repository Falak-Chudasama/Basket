from __future__ import annotations
from typing import Any
import logging

from src.utils.utils import get_datetime
from src.core.configs import DEFAULT_VECTORDB_N
from src.services.embedding.embedder import create_embedding, batch_encode
from src.services.vectordb.chroma_store import ChromaStore

logger = logging.getLogger(__name__)


class Memory:
    """
    Manages vector storage and similarity retrieval in ChromaDB
    isolated by application and rich metadata filtering.
    """

    def __init__(self, application: str = "quince", collection_name: str = "memory") -> None:
        self.application = application
        self.collection_name = collection_name
        self.collection = ChromaStore(collection_name)

    def _build_where_filter(
        self,
        metadata_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Builds a strictly valid ChromaDB `where` expression combining
        the application namespace and optional caller filters.
        """
        conditions: list[dict[str, Any]] = []
        if self.application:
            conditions.append({"application": self.application})

        if metadata_filter:
            for k, v in metadata_filter.items():
                if k == "application" and self.application:
                    continue
                if isinstance(v, (list, tuple, set)):
                    conditions.append({k: {"$in": list(v)}})
                elif isinstance(v, (str, int, float, bool, dict)):
                    conditions.append({k: v})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def add_memory(
        self,
        *,
        memory_id: str,
        document: str,
        source: str = "user",
        embedding: list[float] | None = None,
        memory_type: str = "short_term",
        session_id: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Adds or updates a single memory document in vector store."""
        if session_id is None:
            session_id = f"{self.application}:default"

        metadata: dict[str, Any] = {
            "application": self.application,
            "session_id": session_id,
            "memory_type": memory_type,
            "source": source,
            "created_at": get_datetime(),
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        if embedding is None:
            embedding = create_embedding(document)

        self.collection.upsert(
            ids=[memory_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def bulk_add_memories(
        self,
        *,
        memory_ids: list[str],
        documents: list[str],
        embeddings: list[list[float]] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        source: str = "user",
        memory_type: str = "short_term",
        session_id: str | None = None,
    ) -> None:
        """
        High-throughput bulk ingestion for dumping large contexts in one go.
        Uses batch matrix encoding and a single collection upsert.
        """
        if not memory_ids:
            return

        if len(memory_ids) != len(documents):
            raise ValueError("memory_ids and documents must have equal length")

        if session_id is None:
            session_id = f"{self.application}:default"

        now = get_datetime()

        if metadatas is None:
            final_metadatas = [
                {
                    "application": self.application,
                    "session_id": session_id,
                    "memory_type": memory_type,
                    "source": source,
                    "created_at": now,
                }
                for _ in memory_ids
            ]
        else:
            final_metadatas = []
            for meta in metadatas:
                m = {
                    "application": self.application,
                    "session_id": session_id,
                    "memory_type": memory_type,
                    "source": source,
                    "created_at": now,
                }
                m.update(meta)
                final_metadatas.append(m)

        if embeddings is None:
            embeddings = batch_encode(documents)

        self.collection.upsert(
            ids=memory_ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=final_metadatas,
        )

    def query_memory(
        self,
        *,
        query: str,
        n_result: int = DEFAULT_VECTORDB_N,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Queries semantic vector memory with dynamic metadata filtering.
        """
        try:
            count = self.collection.collection.count()
            if count == 0:
                return []
        except Exception:
            return []

        query_embedding = create_embedding(query)
        where = self._build_where_filter(metadata_filter)
        n_query = min(n_result, max(1, count))

        try:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_query,
                where=where,
            )
        except Exception as exc:
            logger.warning("Chroma query failed: %s", exc)
            return []

        ids = result["ids"][0] if result and result.get("ids") else []
        documents = result["documents"][0] if result and result.get("documents") else []
        metadatas = result["metadatas"][0] if result and result.get("metadatas") else []
        distances = result["distances"][0] if result and result.get("distances") else []

        normalized_result = []
        for i in range(len(ids)):
            dist = float(distances[i]) if i < len(distances) else 0.0
            # Convert cosine distance to positive similarity score in [0, 1]
            sim_score = 1.0 / (1.0 + max(0.0, dist))
            normalized_result.append({
                "id": ids[i],
                "document": documents[i],
                "metadata": metadatas[i],
                "distance": dist,
                "score": sim_score,
            })

        return normalized_result

    def delete_by_ids(self, ids: list[str]) -> None:
        if not ids:
            return
        self.collection.delete(ids=ids)

    def delete_by_filter(self, metadata_filter: dict[str, Any]) -> None:
        where = self._build_where_filter(metadata_filter)
        if where:
            self.collection.delete(where=where)

    def clear_short_term(self) -> None:
        self.collection.delete(
            where={
                "$and": [
                    {"application": self.application},
                    {"memory_type": "short_term"},
                ]
            }
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

    def clear_all(self) -> None:
        self.collection.delete(
            where={
                "application": self.application
            }
        )
