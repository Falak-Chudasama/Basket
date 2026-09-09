from typing import Any

from src.utils.utils import get_datetime
from src.services.db.db import get_db


class Chat:
    def __init__(
        self,
        db_name: str = "quince",
        application: str = "quince"
    ):
        self.db = get_db(
            db_name
        )

        self.application = application

        self.collection = self.db[
            "chats"
        ]

    def _get_prev_session_number(self) -> int:

        recent = self.collection.find_one(
            {
                "application": self.application
            },
            sort=[
                ("session_number", -1)
            ]
        )

        if recent is None:
            return 0

        return recent[
            "session_number"
        ]

    def create(
        self,
        *,
        chats: list[dict[str, Any]],
        session_number: int | None = None,
        session_len: int = 0
    ) -> str:

        if session_number is None:
            session_number = (
                self._get_prev_session_number()
                + 1
            )

        session_id = (
            f"{self.application}:"
            f"chat:"
            f"{session_number}"
        )

        now = get_datetime()

        self.collection.insert_one({
            "session_id": session_id,
            "chats": chats,
            "application": self.application,
            "session_number": session_number,
            "session_length": session_len,
            "created_at": now,
            "updated_at": now
        })

        return session_id

    def get_current_chat(self):
        return self.collection.find_one(
            {
                "application":
                    self.application
            },
            sort=[
                ("session_number", -1)
            ]
        )

    def get_chat(
        self,
        session_id: str
    ):
        return self.collection.find_one(
            {
                "session_id": session_id,
                "application": self.application
            }
        )

    def get_all(self):
        return self.collection.find(
            {
                "application":
                    self.application
            }
        )

    def update_chat(
        self,
        *,
        session_id: str,
        role: str = "user",
        content: str
    ) -> None:

        self.collection.update_one(
            {
                "session_id": session_id,
                "application":
                    self.application
            },
            {
                "$push": {
                    "chats": {
                        "role": role,
                        "content": content
                    }
                },
                "$set": {
                    "updated_at":
                        get_datetime()
                },
                "$inc": {
                    "session_length": 1
                }
            }
        )

    def delete(
        self,
        session_id: str
    ) -> None:

        self.collection.delete_one(
            {
                "session_id": session_id,
                "application":
                    self.application
            }
        )

    def delete_all(self) -> None:

        self.collection.delete_many(
            {
                "application":
                    self.application
            }
        )