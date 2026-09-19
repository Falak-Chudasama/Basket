from src.services.db.db import get_db
from src.services.vectordb.vectordb import client
from src.services.vectordb.memory import Memory
from src.services.db.commands.commands import Command
from src.services.db.chats.chats import Chat
from src.services.db.memory.memory import DBMemory
from src.services.bm25.bm25 import BM25
from src.clients.quince_mcp import QuinceMCPClient


# ============================================================
# DATABASES
# ============================================================

quince_db = get_db("quince")
plum_db = get_db("plum")
kiwi_db = get_db("kiwi")
lychee_db = get_db("lychee")


# ============================================================
# QUINCE SERVICES
# ============================================================

quince_memory = Memory(
    application="quince"
)

quince_db_memory = DBMemory(
    db_name="quince",
    application="quince",
)

quince_commands = Command(
    db_name="quince",
    application="quince"
)

quince_chats = Chat(
    db_name="quince",
    application="quince"
)

quince_bm25_memory = BM25()

# ============================================================
# SHARED APPLICATION STATE
# ============================================================

states = {
    "quince_db": quince_db,
    "plum_db": plum_db,
    "kiwi_db": kiwi_db,
    "lychee_db": lychee_db,

    "chroma_client": client,

    "quince_memory": quince_memory,
    "quince_db_memory": quince_db_memory,
    "quince_chats": quince_chats,
    "quince_commands": quince_commands,
    "quince_bm25_memory": quince_bm25_memory,
    "quince_active_session_id": None,
}