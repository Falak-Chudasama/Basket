from src.services.db.db import get_db


class DBMemory:
    def __init__(self, db_name: str = "quince", application: str = "quince"):
        self.db = get_db(db_name)
        self.application = application
        self.collection = self.db["memory"]

    def _get_recent_mem(self):
        return self.collection.find_one(
            {"application": self.application},
            sort=[("memory_number", -1)]
        )

    def _get_memory_number(self) -> int:
        recent_mem = self._get_recent_mem()

        if recent_mem is None:
            return 1

        return int(recent_mem["memory_number"]) + 1

    def _get_mem_id(self, memory_number: int) -> str:
        return f"{self.application.lower()}:memory:{memory_number}"

    async def add_one(self, memory: str, is_temporary: bool = True):
        memory_number = self._get_memory_number()
        memory_id = self._get_mem_id(memory_number)

        self.collection.insert_one({
            "memory_id": memory_id,
            "memory": memory,
            "is_temporary": is_temporary,
            "application": self.application,
            "memory_number": memory_number
        })

        return {
            "memory_id": memory_id,
            "memory_number": memory_number
        }

    async def add_many(self, memories: list[str], is_temporary: bool = True):
        memory_number = self._get_memory_number()

        documents = []

        for offset, memory in enumerate(memories):
            current_number = memory_number + offset

            documents.append({
                "memory_id": self._get_mem_id(current_number),
                "memory": memory,
                "is_temporary": is_temporary,
                "application": self.application,
                "memory_number": current_number
            })

        if not documents:
            return []

        self.collection.insert_many(documents)

        return [
            {
                "memory_id": document["memory_id"],
                "memory_number": document["memory_number"]
            }
            for document in documents
        ]

    async def get(self, memory_id: str):
        document = self.collection.find_one({
            "memory_id": memory_id,
            "application": self.application
        })

        if document is None:
            return None

        document["_id"] = str(document["_id"])
        return document

    async def get_all(self):
        documents = list(
            self.collection.find({
                "application": self.application
            })
        )

        for document in documents:
            document["_id"] = str(document["_id"])

        return documents

    async def delete(self, memory_id: str):
        result = self.collection.delete_one({
            "memory_id": memory_id,
            "application": self.application,
        })

        return {
            "deleted_count": result.deleted_count
        }

    async def delete_all_temp(self):
        result = self.collection.delete_many({
            "application": self.application,
            "is_temporary": True
        })

        return {
            "deleted_count": result.deleted_count
        }

    async def delete_all(self):
        result = self.collection.delete_many({
            "application": self.application
        })

        return {
            "deleted_count": result.deleted_count
        }