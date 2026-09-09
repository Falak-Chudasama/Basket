from src.core.state import (
    quince_chats,
    states,
)


def activate_quince_session() -> dict:
    """Activate and resolve the Quince chat session."""

    active_session_id = states.get(
        "quince_active_session_id"
    )

    if active_session_id:

        current_chat = quince_chats.get_by_session_id(
            active_session_id
        )

        if current_chat is not None:
            states["quince_active_session"] = True
            return current_chat

    current_chat = quince_chats.get_current_chat()

    if current_chat is None:
        session_id = quince_chats.create(
            chats=[],
            session_len=0
        )

        current_chat = quince_chats.get_by_session_id(
            session_id
        )

    states["quince_active_session"] = True
    states["quince_active_session_id"] = (
        current_chat["session_id"]
    )

    return current_chat


def deactivate_quince_session() -> None:
    """Deactivate the current Quince chat session."""

    states["quince_active_session"] = False
    states["quince_active_session_id"] = None


def get_active_quince_session():
    """Return the explicitly active Quince chat, if any."""

    if not states.get(
        "quince_active_session",
        False
    ):
        return None

    session_id = states.get(
        "quince_active_session_id"
    )

    if not session_id:
        return activate_quince_session()

    current_chat = quince_chats.get_by_session_id(
        session_id
    )

    if current_chat is None:
        return activate_quince_session()

    return current_chat
