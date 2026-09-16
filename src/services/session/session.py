from src.core.state import states

def _get_chats():
    return {}


def create_session(application: str | None = "quince"):
    app_chats = None

    if (application == "quince"):
        app_chats = states["quince_chats"]

    current_chat_id = app_chats.create(chats=[])

    if application == "quince":
        states["quince_active_session_id"] = current_chat_id

def append_chat_to_memory(application: str | None = "quince"):
    # TODO: Append all the new responses or prompts into db, bm25 and vectordb (short term)
    return {}