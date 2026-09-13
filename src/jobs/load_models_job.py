from src.clients.lm_studio import _load_model
from src.services.models.manager import ModelManager

# TODO: Add logs here.

async def load_models():
    await _load_model()
    ModelManager.get_embedding_model()
    ModelManager.get_reranker_model()