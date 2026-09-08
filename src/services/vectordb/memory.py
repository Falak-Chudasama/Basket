import time
from typing import Any

from src.core.state import memory_collection
from src.core.configs import DEFAULT_VECTORDB_N
from src.services.embedding.embedder import create_embedding
from src.services.vectordb.chroma_store import ChromaStore


class Memory:
    def __init__(self, application: str = "quince"):
        self.application = application
        self.collection = ChromaStore("memory")

    def add_memory(
            self,
            *,
            memory_id: str,
            document: str,
            embedding: list[float] | None = None,
            memory_type: str = "short_term",
            source: str = "user"
    ) -> None :
        metadata = {
            "application": self.application,
            "memory_type": memory_type,
            "source": source,
            "created_at": int(time.time())
        }
        if embedding is None:
            embedding = create_embedding(document)

        self.collection.upsert(
            ids=[memory_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    def query_memory(
            self,
            *,
            query: str,
            n_result: int = DEFAULT_VECTORDB_N
    ):
        query_embedding = create_embedding(query)

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result,
            where={
                "application": self.application
            }
        )

    def clear_short_term(self) -> None:
        self.collection.delete(
            where={
                "$and": [
                    { "application": self.application },
                    { "memory_type": "short_term" }
                ]
            }
        )

    def clear_long_term(self) -> None:
        self.collection.delete(
            where={
                "$and": [
                    { "application": self.application },
                    { "memory_type": "long_term" }
                ]
            }
        )

    def clear_all(self) -> None:
        self.collection.delete(
            where={
                "application": self.application
            }
        )