from src.core.state import states, quince_chats


APPLICATION = "quince"


def start_new_quince_session() -> str:
    """
    Unconditionally create a brand-new Quince chat and make it active.

    This must be called exactly once per WebSocket CONNECTION (i.e. when
    Quince's client first connects), never per-message and never per-turn.
    Calling this repeatedly within one connection would fragment a single
    conversation across multiple chat documents.
    """

    active_session_id = quince_chats.create(
        chats=[],
        session_len=0,
    )

    states["quince_active_session"] = True
    states["quince_active_session_id"] = active_session_id

    return active_session_id


def activate_quince_session() -> str:
    """
    Return the session ID for the currently active Quince turn.

    This is safe to call on every turn ("start" message) within an
    already-connected WebSocket session: it only ever resumes the
    session established by start_new_quince_session() at connect time
    and never falls back to the most recent chat in the database. If
    no session has been activated yet (e.g. this function is reached
    outside the normal connect -> start_new_quince_session() flow),
    it creates one, so callers never crash — but the normal path
    should always have already called start_new_quince_session().
    """

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

    # Fallback safety net only — the normal flow always creates the
    # session up front via start_new_quince_session() on WS connect.
    return start_new_quince_session()


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
