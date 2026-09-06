from src.core.db import get_db

quince_db = get_db("quince")
plum_db = get_db("plum")
kiwi_db = get_db("kiwi")
lychee_db = get_db("lychee")

states = {
    "embedding_model_loaded": False,
    "embedding_model": None,
    "reranker_model_loaded": False,
    "reranker_model": None,
    "quince_db": quince_db,
    "plum_db": plum_db,
    "kiwi_db": kiwi_db,
    "lychee_db": lychee_db,
}