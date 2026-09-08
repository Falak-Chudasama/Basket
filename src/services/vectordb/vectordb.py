import chromadb

from src.core.configs import VECTOR_DB_PATH


client = chromadb.PersistentClient(
    path=VECTOR_DB_PATH
)