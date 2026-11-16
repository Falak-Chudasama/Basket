from __future__ import annotations
from typing import Any

from src.utils.utils import get_datetime
from src.core.state import states
from src.services.vectordb.memory import Memory
from src.services.bm25.bm25 import BM25
from src.services.db.chats.chats import Chat

# Internal dynamic registries per application
_app_chats: dict[str, Chat] = {}
_app_vectordb: dict[str, Memory] = {}
_app_bm25: dict[str, BM25] = {}
_app_active_sessions: dict[str, str | None] = {}


def _get_db_chats(application: str) -> Chat:
    if application == "quince":
        return states["quince_chats"]
    if application not in _app_chats:
        _app_chats[application] = Chat(db_name=application, application=application)
    return _app_chats[application]


def _get_vectordb_memory(application: str) -> Memory:
    if application == "quince":
        return states["quince_memory"]
    if application not in _app_vectordb:
        _app_vectordb[application] = Memory(application=application)
    return _app_vectordb[application]


def _get_bm25_memory(application: str) -> BM25:
    if application == "quince":
        return states["quince_bm25_memory"]
    if application not in _app_bm25:
        _app_bm25[application] = BM25()
    return _app_bm25[application]


def _get_active_session_id(application: str) -> str | None:
    if application == "quince":
        return states["quince_active_session_id"]
    return _app_active_sessions.get(application)


def _set_active_session_id(application: str, id: str | None) -> None:
    if application == "quince":
        states["quince_active_session_id"] = id
    else:
        _app_active_sessions[application] = id


def create_session(application: str | None = "quince") -> str:
    app_name = application or "quince"
    assert isinstance(app_name, str)

    app_chats = _get_db_chats(app_name)
    current_chat_id = app_chats.create(chats=[])
    _set_active_session_id(application=app_name, id=current_chat_id)
    return current_chat_id


def append_chat_to_memory(
    application: str | None = "quince",
    content: str = "",
    source: str = "user",
) -> None:
    app_name = application or "quince"
    assert isinstance(app_name, str)

    chats = _get_db_chats(application=app_name)
    session_id = _get_active_session_id(application=app_name)
    if not session_id:
        create_session(application=app_name)
        session_id = _get_active_session_id(application=app_name)

    message_id = chats.update_chat(
        session_id=session_id,
        content=content,
        role=source,
    )

    vectordb_memory = _get_vectordb_memory(application=app_name)
    vectordb_memory.add_memory(
        memory_id=message_id,
        document=content,
        source=source,
        session_id=session_id,
        memory_type="short_term",
    )

    bm25_memory = _get_bm25_memory(application=app_name)
    bm25_memory.upsert(
        document_id=message_id,
        document=content,
        metadata={
            "application": app_name,
            "session_id": session_id,
            "memory_type": "short_term",
            "source": source,
            "created_at": get_datetime(),
        },
    )
