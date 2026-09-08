from src.services.db.db import get_db

class Command:
    def __init__(self, db_name: str = "quince", application: str = "quince"):
        self.db = get_db(db_name)
        self.application = application,
        self.collection = self.db.create_collection("commands")

    def add_one(self, command: str, is_temporary: bool = True):
        self.collection.insert_one({
            "command": command,
            "is_temporary": is_temporary
        })

    def add_many(self, commands: list[str]):
        self.collection.insert_many([
            {
                "command": command
            }
            for command in commands
        ])

    def get_all(self):
        return self.collection.find()

    def delete(self, command: str):
        self.collection.delete_one({
            "command": command
        })

    def delete_all_temp(self):
        self.collection.delete_many({
            "is_temporary": True
        })

    def delete_all(self):
        self.collection.delete_many({})