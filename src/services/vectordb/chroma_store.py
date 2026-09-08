from typing import Any
from chromadb import Embeddings, Metadata

from src.core.state import client
from src.core.configs import VECTOR_DB_PATH, DEFAULT_VECTORDB_N


class ChromaStore:
    def __init__(self, collection_name: str):
        self.path = VECTOR_DB_PATH,
        self.collection = client.get_or_create_collection(collection_name)

    def create(
            self,
            *,
            ids: list[str],
            documents: list[str],
            embeddings: list[Embeddings] | None,
            metadatas: list[Metadata] | None
    ):

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
    
    def get(
            self,
            *,
            ids: list[str] | None = None,
            where: dict[str, Any] | None = None
    ):

        return self.collection.get(
            ids=ids,
            where=where
        )

    def query(
            self,
            *,
            query_embeddings: list[Embeddings],
            n_results: int = DEFAULT_VECTORDB_N,
            where: dict[str, Any] | None = None
    ):
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

    def update(
            self,
            *,
            ids: list[str],
            documents: list[str] | None = None,
            embeddings: list[Embeddings] | None = None,
            metadatas: list[Metadata] | None = None
    ):
        self.update(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def upsert(
            self,
            *,
            ids: list[str],
            documents: list[str] | None = None,
            embeddings: list[Embeddings] | None = None,
            metadatas: list[Metadata] | None = None
    ):
        self.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )


    def delete(
            self,
            *,
            ids: list[str] | None = None,
            where: dict[str, Any] | None = None    
    ) -> None:
        self.collection.delete(
            ids=ids,
            where=where
        )