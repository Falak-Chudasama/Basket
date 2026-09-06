from src.clients.lmstudio import _load_model
from src.services.models.manager import ModelManager

async def load_models():
    print("models being loaded")
    await _load_model()
    ModelManager.get_embedding_model()
    ModelManager.get_reranker_model()
    print("models loaded!")
    

async def run_jobs():
    await load_models()