from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

from src.core.configs import CHAT_CHUNK_SIZE, CHAT_CHUNK_OVERLAP, TOP_K, DEFAULT_VECTORDB_N, DEFAULT_BM25_N


class Application(BaseModel):
    application: str = Field(
        default="quince",
        min_length=1,
        description="Application identifier for namespace isolation across Fruit ecosystem.",
    )


class AddMemory(Application):
    memory: str
    is_temporary: bool = True


class GetMemory(Application):
    memory_id: str


class DeleteMemory(Application):
    memory_id: str


class AddCommand(Application):
    command: str
    is_temporary: bool = True


class DeleteCommand(Application):
    command_id: str


class RAGIngestRequest(Application):
    """Payload for dumping context into Basket's RAG pipeline in one go."""
    text: str | None = Field(
        default=None,
        description="Raw full context text to be dynamically chunked and indexed.",
    )
    documents: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional list of pre-formed document dicts, each with 'text' or 'document' and optional 'id'/'metadata'.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Global metadata dict applied to all ingested chunks.",
    )
    chunk_size: int = Field(
        default=CHAT_CHUNK_SIZE,
        gt=0,
        description="Chunk character size for splitting raw text.",
    )
    chunk_overlap: int = Field(
        default=CHAT_CHUNK_OVERLAP,
        ge=0,
        description="Chunk character overlap for splitting raw text.",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session or document collection identifier.",
    )
    memory_type: str = Field(
        default="short_term",
        description="Memory type: 'short_term', 'long_term', or 'knowledge'.",
    )
    source_type: str = Field(
        default="context_dump",
        description="Source identifier (e.g., 'conversation', 'context_dump', 'documentation').",
    )
    role: str = Field(
        default="user",
        description="Author role associated with the context.",
    )


class RAGQueryRequest(Application):
    """Dynamic query configuration for hybrid RAG retrieval."""
    query: str = Field(
        min_length=1,
        description="User query string for hybrid semantic and keyword retrieval.",
    )
    top_k: int = Field(
        default=TOP_K,
        gt=0,
        description="Dynamic number of final fused chunks returned.",
    )
    vector_k: int = Field(
        default=DEFAULT_VECTORDB_N,
        gt=0,
        description="Dynamic candidate pool size for dense vector retrieval.",
    )
    bm25_k: int = Field(
        default=DEFAULT_BM25_N,
        gt=0,
        description="Dynamic candidate pool size for sparse BM25 retrieval.",
    )
    metadata_filter: dict[str, Any] | None = Field(
        default=None,
        description="Dynamic key-value metadata filter applied to both vector and BM25 indices.",
    )
    use_reranker: bool = Field(
        default=False,
        description="Whether to execute neural cross-encoder reranking on candidate pool.",
    )
    rerank_top_k: int = Field(
        default=10,
        gt=0,
        description="Dynamic number of top RRF candidates sent to neural reranker.",
    )
    score_threshold: float | None = Field(
        default=None,
        description="Optional minimum relevance score threshold.",
    )
    vector_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relative weight for dense vector ranking in RRF fusion.",
    )
    bm25_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relative weight for sparse BM25 ranking in RRF fusion.",
    )


class RAGDeleteRequest(Application):
    """Request to remove indexed chunks from vector and BM25 stores."""
    ids: list[str] | None = Field(
        default=None,
        description="Specific document chunk IDs to delete.",
    )
    metadata_filter: dict[str, Any] | None = Field(
        default=None,
        description="Metadata filter specifying which chunks to purge.",
    )


class RAGClearRequest(Application):
    """Request to clear all or partitioned memory for an application."""
    memory_type: Literal["short_term", "long_term", "all"] = "all"
