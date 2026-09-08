from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.configs import (
    CHAT_CHUNK_SIZE,
    CHAT_CHUNK_OVERLAP
)
from src.utils.utils import get_datetime
from src.core.state import (
    quince_chats,
    quince_memory,
    quince_bm25_memory
)


splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHAT_CHUNK_SIZE,
    chunk_overlap=CHAT_CHUNK_OVERLAP,
    separators=[
        "\n\n",
        "\n",
        ". ",
        "? ",
        "! ",
        ", ",
        " ",
        ""
    ],
)


def chunk_text(
    text: str,
    application: str,
    role: str,
    memory_type: str,
    source_type: str,
    application_semantic_memory,
    application_bm25_memory,
    application_chats
):
    current_chat = (
        application_chats.get_current_chat()
    )

    if current_chat is None:
        raise ValueError(
            "No current chat session exists."
        )

    session_id = current_chat[
        "session_id"
    ]

    chunks = splitter.split_text(
        text
    )

    full_chunks = []

    for chunk_index, chunk_text_value in enumerate(
        chunks
    ):

        chunk_id = (
            f"{session_id}:"
            f"{role}:"
            f"{chunk_index}"
        )

        metadata = {
            "application": application,
            "memory_type": memory_type,
            "source_type": source_type,
            "role": role,
            "session_id": session_id,
            "chunk_index": chunk_index,
            "created_at": get_datetime(),
        }

        application_semantic_memory.add_memory(
            memory_id=chunk_id,
            document=chunk_text_value,
            source=role,
            memory_type=memory_type
        )

        application_bm25_memory.upsert(
            document_id=chunk_id,
            document=chunk_text_value,
            metadata=metadata
        )

        full_chunks.append({
            "chunk_id": chunk_id,
            "document": chunk_text_value,
            "metadata": metadata
        })

    return full_chunks


def chunk(
    text: str,
    application: str = "quince",
    role: str = "user",
    memory_type: str = "short_term",
    source_type: str = "conversation"
):
    if application == "quince":

        return chunk_text(
            text=text,
            application=application,
            role=role,
            memory_type=memory_type,
            source_type=source_type,
            application_semantic_memory=quince_memory,
            application_bm25_memory=quince_bm25_memory,
            application_chats=quince_chats
        )

    raise ValueError(
        f"Unsupported application: {application}"
    )