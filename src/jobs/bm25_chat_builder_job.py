from src.core.state import quince_bm25_memory, quince_memory


def build_bm25_index() -> None:
    persisted = quince_memory.get_all()

    ids = list(
        persisted.get("ids", []) or []
    )

    documents = list(
        persisted.get("documents", []) or []
    )

    metadatas = list(
        persisted.get("metadatas", []) or []
    )

    quince_bm25_memory.build(
        ids=ids,
        documents=documents,
        metadatas=[metadata or {} for metadata in metadatas]
    )
