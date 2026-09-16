from src.core.state import quince_memory, quince_commands, quince_bm25_memory
from src.services.vectordb.vectordb import client


def clear_session():
    # client.delete_collection("memory") # USE IT: When you want to clear vectorb.
    quince_memory.clear_short_term()
    quince_commands.delete_all_temp()
    # TODO: load long term memory in bm25 as well.