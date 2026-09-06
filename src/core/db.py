from pymongo import MongoClient
from pymongo.database import Database

from src.core.configs import MONGODB_URI


client = MongoClient(MONGODB_URI)

def get_db(db_name: str) -> Database:
    db = client[db_name]
    return db