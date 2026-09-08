from src.services.db.db import get_db
from src.services.vectordb.vectordb import client
from src.services.vectordb.memory import Memory
from src.services.db.commands.commands import Command

quince_db = get_db("quince")
plum_db = get_db("plum")
kiwi_db = get_db("kiwi")
lychee_db = get_db("lychee")

quince_memory = Memory("quince")
quince_commands = Command(db_name="quince", application="quince")

states = {
    "embedding_model_loaded": False,
    "embedding_model": None,
    "reranker_model_loaded": False,
    "reranker_model": None,
    "quince_db": quince_db,
    "plum_db": plum_db,
    "kiwi_db": kiwi_db,
    "lychee_db": lychee_db,
    "chroma_client": client,
    "quince_memory": quince_memory,
    "quince_commands": quince_commands
}