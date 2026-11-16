from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException

from src.core.state import quince_db_memory, quince_commands
from src.services.db.memory.memory import DBMemory
from src.services.db.commands.commands import Command
from src.services.retrieval.chat_retriever import (
    retrieve,
    _get_vectordb_mem,
    _get_bm25_mem,
)
from src.services.chunker.chat_chunker import (
    chunk_text,
    ingest_documents,
)
from src.schemas.ContextSchemas import (
    Application,
    AddCommand,
    DeleteCommand,
    AddMemory,
    GetMemory,
    DeleteMemory,
    RAGIngestRequest,
    RAGQueryRequest,
    RAGDeleteRequest,
    RAGClearRequest,
)

context_router = APIRouter(
    prefix="/context",
    tags=["Context"],
)

_db_memories: dict[str, DBMemory] = {"quince": quince_db_memory}
_db_commands: dict[str, Command] = {"quince": quince_commands}


def _get_app_db_memory(application: str) -> DBMemory:
    if application == "quince":
        return quince_db_memory
    if application not in _db_memories:
        _db_memories[application] = DBMemory(db_name=application, application=application)
    return _db_memories[application]


def _get_app_db_command(application: str) -> Command:
    if application == "quince":
        return quince_commands
    if application not in _db_commands:
        _db_commands[application] = Command(db_name=application, application=application)
    return _db_commands[application]


# =========================================================================
# 1. Dynamic RAG Pipeline Endpoints (Bulk Ingest, Hybrid Query, Cleanup)
# =========================================================================

@context_router.post("/rag/ingest")
async def rag_ingest_endpoint(request: RAGIngestRequest) -> dict[str, Any]:
    """
    Ingest context into vector DB and BM25 index in one go.
    Supports either bulk raw text (auto-chunked and batch-embedded)
    or pre-formed document lists with rich metadata.
    """
    if not request.text and not request.documents:
        raise HTTPException(
            status_code=400,
            detail="Either 'text' or 'documents' must be provided for context ingestion.",
        )

    results: list[dict[str, Any]] = []

    if request.documents:
        docs_result = ingest_documents(
            documents=request.documents,
            application=request.application,
            session_id=request.session_id,
            memory_type=request.memory_type,
            source=request.source_type,
            extra_metadata=request.metadata,
        )
        results.extend(docs_result)

    if request.text:
        text_result = chunk_text(
            text=request.text,
            application=request.application,
            role=request.role,
            memory_type=request.memory_type,
            source_type=request.source_type,
            session_id=request.session_id,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            extra_metadata=request.metadata,
        )
        results.extend(text_result)

    return {
        "status": "success",
        "application": request.application,
        "count": len(results),
        "chunks": results,
    }


@context_router.post("/rag/query")
async def rag_query_endpoint(request: RAGQueryRequest) -> dict[str, Any]:
    """
    Execute dynamic hybrid RAG query combining vector similarity, BM25 keyword matching,
    metadata filtering, and optional neural cross-encoder reranking.
    """
    candidates = await retrieve(
        query=request.query,
        application=request.application,
        top_k=request.top_k,
        vector_k=request.vector_k,
        bm25_k=request.bm25_k,
        metadata_filter=request.metadata_filter,
        use_reranker=request.use_reranker,
        rerank_top_k=request.rerank_top_k,
        score_threshold=request.score_threshold,
        vector_weight=request.vector_weight,
        bm25_weight=request.bm25_weight,
    )

    return {
        "status": "success",
        "query": request.query,
        "application": request.application,
        "count": len(candidates),
        "results": candidates,
    }


@context_router.post("/rag/delete")
async def rag_delete_endpoint(request: RAGDeleteRequest) -> dict[str, Any]:
    """
    Delete specific chunks by ID or metadata filter from both vector and BM25 stores.
    """
    vdb = _get_vectordb_mem(request.application)
    bm25 = _get_bm25_mem(request.application)

    deleted_count = 0

    if request.ids:
        vdb.delete_by_ids(request.ids)
        for doc_id in request.ids:
            bm25.delete(document_id=doc_id)
        deleted_count += len(request.ids)

    if request.metadata_filter:
        filter_with_app = {"application": request.application, **request.metadata_filter}
        vdb.delete_by_filter(filter_with_app)
        bm_deleted = bm25.delete_by_filter(metadata_filter=filter_with_app)
        deleted_count += bm_deleted

    return {
        "status": "success",
        "application": request.application,
        "deleted_count": deleted_count,
    }


@context_router.post("/rag/clear")
async def rag_clear_endpoint(request: RAGClearRequest) -> dict[str, Any]:
    """
    Clear short-term, long-term, or all memory from vector and BM25 stores.
    """
    vdb = _get_vectordb_mem(request.application)
    bm25 = _get_bm25_mem(request.application)

    if request.memory_type == "short_term":
        vdb.clear_short_term()
        bm25.delete_by_filter(metadata_filter={"application": request.application, "memory_type": "short_term"})
    elif request.memory_type == "long_term":
        vdb.clear_long_term()
        bm25.delete_by_filter(metadata_filter={"application": request.application, "memory_type": "long_term"})
    else:
        vdb.clear_all()
        bm25.delete_by_filter(metadata_filter={"application": request.application})

    return {
        "status": "success",
        "application": request.application,
        "memory_type": request.memory_type,
    }


# =========================================================================
# 2. Key Fact Database Memory Endpoints (Backward Compatible)
# =========================================================================

@context_router.post("/memory/add")
async def add_memory(request: AddMemory):
    db_mem = _get_app_db_memory(request.application)
    result = await db_mem.add_one(
        request.memory,
        request.is_temporary,
    )
    return {"result": result}


@context_router.post("/memory/get")
async def get_memory(request: GetMemory):
    db_mem = _get_app_db_memory(request.application)
    result = await db_mem.get(request.memory_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{request.memory_id}' not found.",
        )

    return {"result": result}


@context_router.post("/memory/get_all")
async def get_all_memory(request: Application):
    db_mem = _get_app_db_memory(request.application)
    result = await db_mem.get_all()
    return {"result": result}


@context_router.delete("/memory/delete")
async def delete_memory(request: DeleteMemory):
    db_mem = _get_app_db_memory(request.application)
    result = await db_mem.delete(request.memory_id)

    if result["deleted_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{request.memory_id}' not found.",
        )

    return {"result": result}


@context_router.post("/memory/delete_all")
async def delete_all_memory(request: DeleteMemory):
    db_mem = _get_app_db_memory(request.application)
    result = await db_mem.delete_all()

    if result["deleted_count"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Memory '{request.memory_id}' not found.",
        )

    return {"result": result}


# =========================================================================
# 3. Macro Command Endpoints (Backward Compatible)
# =========================================================================

@context_router.post("/command/add")
async def add_command(request: AddCommand):
    cmd_mem = _get_app_db_command(request.application)
    result = await cmd_mem.add_one(
        request.command,
        request.is_temporary,
    )
    return {"result": result}


@context_router.post("/command/get_all")
async def get_all_commands(application_request: Application):
    cmd_mem = _get_app_db_command(application_request.application)
    result = await cmd_mem.get_all()
    return {"result": result}


@context_router.post("/command/delete")
async def delete_command(request: DeleteCommand):
    cmd_mem = _get_app_db_command(request.application)
    result = await cmd_mem.delete(request.command_id)
    return {"result": result}


@context_router.post("/command/delete_all")
async def delete_all_commands(request: Application):
    cmd_mem = _get_app_db_command(request.application)
    result = await cmd_mem.delete_all()
    return {"result": result}


# =========================================================================
# 4. Tiered 3-Way Context Sync Endpoints (Chats, Notes, Commands)
# =========================================================================

from pydantic import BaseModel, Field
from src.services.context.tiered_context import tiered_context


class NoteSyncRequest(BaseModel):
    application: str = Field(description="Target fruit application namespace.")
    action: str = Field(default="upsert", description="'upsert' or 'delete'.")
    note_id: str = Field(description="Unique note ID.")
    title: str = Field(default="", description="Title of the note.")
    content: str = Field(default="", description="Body content of the note.")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional custom metadata.")


class CommandSyncRequest(BaseModel):
    application: str = Field(description="Target fruit application namespace.")
    action: str = Field(default="upsert", description="'upsert' or 'delete'.")
    command_id: str = Field(description="Unique command ID.")
    command: str = Field(default="", description="Command text or instruction.")


class TieredQueryRequest(BaseModel):
    application: str
    query: str
    chat_id: str | None = None
    retrieve_chat: bool = True
    retrieve_notes: bool = True
    top_k_chat: int = 4
    top_k_notes: int = 3
    metadata_filter: dict[str, Any] | None = None


@context_router.post("/notes/sync")
async def sync_note_endpoint(request: NoteSyncRequest) -> dict[str, Any]:
    """
    Real-time webhook/API endpoint for fruit applications to notify Basket of note changes.
    Incrementally updates the persistent VectorDB and BM25 index.
    """
    if request.action == "delete":
        tiered_context.delete_note(application=request.application, note_id=request.note_id)
        return {"status": "success", "action": "delete", "note_id": request.note_id}

    chunks_indexed = tiered_context.upsert_note(
        application=request.application,
        note_id=request.note_id,
        title=request.title,
        content=request.content,
        metadata=request.metadata,
    )
    return {
        "status": "success",
        "action": "upsert",
        "note_id": request.note_id,
        "chunks_indexed": chunks_indexed,
    }


@context_router.post("/commands/sync")
async def sync_command_endpoint(request: CommandSyncRequest) -> dict[str, Any]:
    """
    Real-time webhook/API endpoint for fruit applications to notify Basket of command changes.
    Updates the in-memory command cache and MongoDB.
    """
    if request.action == "delete":
        tiered_context.delete_command(application=request.application, command_id=request.command_id)
        return {"status": "success", "action": "delete", "command_id": request.command_id}

    tiered_context.upsert_command(
        application=request.application,
        command_id=request.command_id,
        command=request.command,
    )
    return {
        "status": "success",
        "action": "upsert",
        "command_id": request.command_id,
        "command": request.command,
    }


@context_router.post("/rag/tiered-query")
async def tiered_query_endpoint(request: TieredQueryRequest) -> dict[str, Any]:
    """
    Direct endpoint to query both volatile chat and persistent notes with tiered ranking.
    """
    results = await tiered_context.retrieve_tiered_context(
        query=request.query,
        application=request.application,
        chat_id=request.chat_id,
        retrieve_chat=request.retrieve_chat,
        retrieve_notes=request.retrieve_notes,
        top_k_chat=request.top_k_chat,
        top_k_notes=request.top_k_notes,
        metadata_filter=request.metadata_filter,
    )
    return {"status": "success", "application": request.application, "results": results}

