from src.services.db.db import get_db
from src.services.vectordb.vectordb import client

quince_db = get_db("quince")
plum_db = get_db("plum")
kiwi_db = get_db("kiwi")
lychee_db = get_db("lychee")

memory_collection = client.get_or_create_collection("memory_collection")

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
    "memory_collection": memory_collection
}