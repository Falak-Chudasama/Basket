from src.services.db.db import get_db

class Command:
    def __init__(self, db_name: str = "quince", application: str = "quince"):
        self.db = get_db(db_name)
        self.application = application
        self.collection = self.db["commands"]

    async def add_one(self, command: str, is_temporary: bool = True):
        result = self.collection.insert_one({
            "command": command,
            "is_temporary": is_temporary,
            "application": self.application
        })

        return {
            "success": result.acknowledged,
            "inserted_id": str(result.inserted_id)
        }

    async def add_many(self, commands: list[str]):
        return self.collection.insert_many([
            {
                "command": command,
                "application": self.application,
            }
            for command in commands
        ])

    async def get_all(self):
        documents = list(self.collection.find({}))
        for document in documents:
            document["_id"] = str(document["_id"])
        return documents

    async def delete(self, command_id: str):
        result = self.collection.delete_one({
            "application": self.application,
            "_id": command_id
        })
        return result.deleted_count

    async def delete_all_temp(self):
        result = self.collection.delete_many({
            "application": self.application,
            "is_temporary": True
        })
        return result.deleted_count

    async def delete_all(self):
        result = self.collection.delete_many({
            "application": self.application
        })
        return result.deleted_count