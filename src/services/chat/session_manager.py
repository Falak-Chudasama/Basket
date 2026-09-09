from src.core.state import states, quince_chats


APPLICATION = "quince"


def activate_quince_session() -> str:
    """Activate the current Quince chat and return its session ID."""

    active_session_id = states.get(
        "quince_active_session_id"
    )

    if (
        states.get("quince_active_session")
        and active_session_id
    ):
        chat = quince_chats.get_chat(
            active_session_id
        )

        if chat is not None:
            return active_session_id

    current_chat = quince_chats.get_current_chat()

    if current_chat is None:
        active_session_id = quince_chats.create(
            chats=[],
            session_len=0
        )
    else:
        active_session_id = current_chat[
            "session_id"
        ]

    states["quince_active_session"] = True
    states["quince_active_session_id"] = active_session_id

    return active_session_id


def deactivate_quince_session() -> None:
    """Deactivate Quince without deleting its MongoDB history."""

    states["quince_active_session"] = False
    states["quince_active_session_id"] = None


def get_active_quince_chat():
    """Return the active Quince chat, or None when inactive."""

    if not states.get("quince_active_session"):
        return None

    session_id = states.get(
        "quince_active_session_id"
    )

    if not session_id:
        return None

    return quince_chats.get_chat(
        session_id
    )


def get_active_quince_messages() -> list[dict[str, str]]:
    chat = get_active_quince_chat()

    if chat is None:
        return []

    messages = chat.get("chats", [])

    return [
        {
            "role": str(message.get("role", "")),
            "content": str(message.get("content", "")),
        }
        for message in messages
        if message.get("role")
        and message.get("content")
    ]


def append_active_quince_message(
    *,
    role: str,
    content: str,
) -> None:
    session_id = states.get(
        "quince_active_session_id"
    )

    if not (
        states.get("quince_active_session")
        and session_id
    ):
        return

    quince_chats.update_chat(
        session_id=session_id,
        role=role,
        content=content,
    )
