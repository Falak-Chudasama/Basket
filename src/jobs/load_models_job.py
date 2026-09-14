from src.services.models.manager import ModelManager

# TODO: Add logs here.

async def load_models():
    ModelManager.get_embedding_model()
    ModelManager.get_reranker_model()