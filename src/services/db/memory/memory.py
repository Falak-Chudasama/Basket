from src.services.db.db import get_db

class DBMemory:
    def __init__(self, db_name: str = "quince", application: str = "quince"):
        self.db = get_db(db_name)
        self.application = application
        self.collection = self.db["memory"]

    def _get_recent_mem(self):
        recent = self.collection.find_one(
            {
                "application": self.application
            },
            sort=[
                ("memory_number", -1)
            ]
        )

        return recent

    def _get_memory_number(self) -> int:
        recent_mem = self._get_recent_mem()
        if recent_mem is None:
            return 1

        return int(recent_mem['session_number']) + 1

    def _get_mem_id(self) -> str:
        mem_number = self._get_memory_number()
        return f"{(self.application).lower()}:memory:{mem_number}"

    def add_one(self, memory: str, is_temporary: bool = True):
        self.collection.insert_one({
            "memory_id": self._get_mem_id(),
            "memory": memory,
            "is_temporary": is_temporary,
            "application": self.application,
            "memory_number": self._get_memory_number()
        })

    def add_many(self, memories: list[str]):
        self.collection.insert_many([
            {
                "memory": memory,
                "application": self.application,
            }
            for memory in memories
        ])

    def get_all(self):
        return self.collection.find({ "application": self.application })

    def delete(self, memory_id: str):
        self.collection.delete_one({
            "memory_id": memory_id,
            "application": self.application,
        })

    def delete_all_temp(self):
        self.collection.delete_many({
            "application": self.application,
            "is_temporary": True
        })

    def delete_all(self):
        self.collection.delete_many({ "application": self.application })