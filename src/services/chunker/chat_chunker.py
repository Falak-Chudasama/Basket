from __future__ import annotations
from typing import Any
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.configs import (
    CHAT_CHUNK_SIZE,
    CHAT_CHUNK_OVERLAP,
)
from src.utils.utils import get_datetime
from src.services.retrieval.chat_retriever import (
    _get_vectordb_mem,
    _get_bm25_mem,
)
from src.services.session.session import _get_db_chats


def _get_splitter(chunk_size: int = CHAT_CHUNK_SIZE, chunk_overlap: int = CHAT_CHUNK_OVERLAP) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            ", ",
            " ",
            "",
        ],
    )


def chunk_text(
    text: str,
    application: str = "quince",
    role: str = "user",
    memory_type: str = "short_term",
    source_type: str = "conversation",
    application_semantic_memory=None,
    application_bm25_memory=None,
    application_chats=None,
    session_id: str | None = None,
    chunk_size: int = CHAT_CHUNK_SIZE,
    chunk_overlap: int = CHAT_CHUNK_OVERLAP,
    extra_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Chunks text and ingests it into both dense vector and BM25 stores in batch.
    Optimized for high-volume context dumps with zero rebuild lag.
    """
    if not text or not text.strip():
        return []

    if application_chats is None:
        application_chats = _get_db_chats(application)

    if application_semantic_memory is None:
        application_semantic_memory = _get_vectordb_mem(application)

    if application_bm25_memory is None:
        application_bm25_memory = _get_bm25_mem(application)

    # Resolve session_id
    if session_id is None:
        try:
            current_chat = application_chats.get_current_chat()
            if current_chat and "session_id" in current_chat:
                session_id = current_chat["session_id"]
        except Exception:
            pass

    if session_id is None:
        session_id = f"{application}:session:{uuid4().hex[:8]}"

    splitter = _get_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)
    if not chunks:
        return []

    chunk_ids: list[str] = []
    chunk_docs: list[str] = []
    chunk_metadatas: list[dict[str, Any]] = []
    now = get_datetime()

    for chunk_index, chunk_text_val in enumerate(chunks):
        cid = f"{session_id}:{role}:{chunk_index}"
        meta: dict[str, Any] = {
            "application": application,
            "memory_type": memory_type,
            "source_type": source_type,
            "role": role,
            "source": role,
            "session_id": session_id,
            "chunk_index": chunk_index,
            "created_at": now,
        }
        if extra_metadata:
            meta.update(extra_metadata)

        chunk_ids.append(cid)
        chunk_docs.append(chunk_text_val)
        chunk_metadatas.append(meta)

    # 1. Bulk vector ingestion (uses batch_encode for single forward-pass)
    application_semantic_memory.bulk_add_memories(
        memory_ids=chunk_ids,
        documents=chunk_docs,
        metadatas=chunk_metadatas,
        source=role,
        memory_type=memory_type,
        session_id=session_id,
    )

    # 2. Bulk BM25 ingestion (tokenizes batch and rebuilds index once)
    application_bm25_memory.bulk_upsert(
        ids=chunk_ids,
        documents=chunk_docs,
        metadatas=chunk_metadatas,
    )

    return [
        {
            "chunk_id": cid,
            "document": doc,
            "metadata": meta,
        }
        for cid, doc, meta in zip(chunk_ids, chunk_docs, chunk_metadatas)
    ]


def ingest_documents(
    documents: list[dict[str, Any]],
    application: str = "quince",
    session_id: str | None = None,
    memory_type: str = "short_term",
    source: str = "context_dump",
    extra_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Directly ingests a list of pre-formed document dicts into vector and BM25 stores.
    Each dict must have 'text' or 'document', with optional 'id' and 'metadata'.
    """
    if not documents:
        return []

    application_semantic_memory = _get_vectordb_mem(application)
    application_bm25_memory = _get_bm25_mem(application)

    if session_id is None:
        session_id = f"{application}:dump:{uuid4().hex[:8]}"

    now = get_datetime()
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for i, doc_obj in enumerate(documents):
        doc_text = doc_obj.get("text") or doc_obj.get("document", "")
        if not doc_text:
            continue

        cid = doc_obj.get("id") or f"{session_id}:doc:{i}"
        meta = {
            "application": application,
            "session_id": session_id,
            "memory_type": memory_type,
            "source": source,
            "created_at": now,
        }
        if extra_metadata:
            meta.update(extra_metadata)
        if "metadata" in doc_obj and isinstance(doc_obj["metadata"], dict):
            meta.update(doc_obj["metadata"])

        ids.append(cid)
        texts.append(doc_text)
        metadatas.append(meta)

    if not ids:
        return []

    application_semantic_memory.bulk_add_memories(
        memory_ids=ids,
        documents=texts,
        metadatas=metadatas,
        source=source,
        memory_type=memory_type,
        session_id=session_id,
    )

    application_bm25_memory.bulk_upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )

    return [
        {
            "id": cid,
            "document": txt,
            "metadata": m,
        }
        for cid, txt, m in zip(ids, texts, metadatas)
    ]


def chunk(
    text: str,
    application: str = "quince",
    role: str = "user",
    memory_type: str = "short_term",
    source_type: str = "conversation",
    session_id: str | None = None,
    chunk_size: int = CHAT_CHUNK_SIZE,
    chunk_overlap: int = CHAT_CHUNK_OVERLAP,
    extra_metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Unified entrypoint for chunking text for any Fruit application.
    """
    return chunk_text(
        text=text,
        application=application,
        role=role,
        memory_type=memory_type,
        source_type=source_type,
        session_id=session_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        extra_metadata=extra_metadata,
    )
