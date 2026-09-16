from src.utils.utils import get_datetime
from src.core.state import states

def _get_db_chats(application: str):
    return states["quince_chats"]

def _get_vectordb_memory(application: str):
    return states["quince_memory"]

def _get_bm25_memory(application: str):
    return states["quince_bm25_memory"]

def _get_active_session_id(application: str):
    return states["quince_active_session_id"]

def _set_active_session_id(application: str, id):
    states["quince_active_session_id"] = id



def create_session(application: str | None = "quince"):
    assert isinstance(application, str)

    app_chats = _get_db_chats(application)
    current_chat_id = app_chats.create(chats=[])
    _set_active_session_id(application=application, id=current_chat_id)

def append_chat_to_memory(application: str | None = "quince", content: str = "", source: str = "user"):
    assert isinstance(application, str)

    chats = _get_db_chats(application=application)
    session_id = _get_active_session_id(application=application)

    message_id = chats.update_chat(
        session_id=session_id,
        content=content,
        role=source
    )

    vectordb_memory = _get_vectordb_memory(application=application)
    vectordb_memory.add_memory(
        memory_id=message_id,
        document=content,
        source=source,
        session_id=session_id,
        memory_type="short_term"
    )

    bm25_memory = _get_bm25_memory(application=application)
    bm25_memory.upsert(document_id=message_id, document=content, metadata={
        "application": application,
        "session_id": session_id,
        "memory_type": "short_term",
        "source": source,
        "created_at": get_datetime()
    })