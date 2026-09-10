from src.services.db.db import get_db


class Command:
    def __init__(self, db_name: str = "quince", application: str = "quince"):
        self.db = get_db(db_name)
        self.application = application
        self.collection = self.db["commands"]

    def add_one(self, command: str, is_temporary: bool = False):
        command = command.strip()
        if not command:
            raise ValueError("command is required")

        # Exact command text is the stable identity. Upsert avoids duplicate
        # command records and lets the user change temporary/durable state.
        self.collection.replace_one(
            {
                "application": self.application,
                "command": command,
            },
            {
                "command": command,
                "is_temporary": bool(is_temporary),
                "application": self.application,
            },
            upsert=True,
        )

    def add_many(self, commands: list[str]):
        for command in commands:
            self.add_one(command, is_temporary=False)

    def get_all(self):
        return self.collection.find(
            {"application": self.application}
        )

    def delete(self, command: str):
        self.collection.delete_one({
            "application": self.application,
            "command": command.strip(),
        })

    def delete_all_temp(self):
        self.collection.delete_many({
            "application": self.application,
            "is_temporary": True,
        })

    def delete_all(self):
        self.collection.delete_many({"application": self.application})
