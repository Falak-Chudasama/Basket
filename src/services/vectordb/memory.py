from src.utils.utils import get_datetime
from src.core.configs import DEFAULT_VECTORDB_N
from src.services.embedding.embedder import create_embedding
from src.services.vectordb.chroma_store import ChromaStore


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

        metadata = {
            "application": self.application,
            "memory_type": memory_type,
            "source": source,
            "created_at": get_datetime()
        }

        if session_id is not None:
            metadata["session_id"] = session_id

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
        n_result: int = DEFAULT_VECTORDB_N,
        session_id: str | None = None,
    ):

        query_embedding = create_embedding(query)

        if session_id is None:
            where = {
                "application": self.application
            }
        else:
            where = {
                "$and": [
                    {
                        "application": self.application
                    },
                    {
                        "session_id": session_id
                    }
                ]
            }

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result,
            where=where
        )

    def get_all(self):
        return self.collection.get(
            where={
                "application": self.application
            }
        )

    def _clear_bm25(
        self,
        predicate,
    ) -> None:

        if self.bm25_memory is not None:
            self.bm25_memory.delete_where(
                predicate=predicate
            )

    def clear_short_term(self) -> None:

        self.collection.delete(
            where={
                "$and": [
                    {
                        "application": self.application
                    },
                    {
                        "memory_type": "short_term"
                    }
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
                    {
                        "application": self.application
                    },
                    {
                        "memory_type": "long_term"
                    }
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

        self.collection.delete(
            where={
                "application": self.application
            }
        )

        self._clear_bm25(
            lambda metadata: (
                metadata.get("application") == self.application
            )
        )
