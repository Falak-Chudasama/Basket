from src.services.models.manager import ModelManager
from src.clients.quince_mcp import quince_mcp

# TODO: Add logs here.

async def load_models():
    ModelManager.get_embedding_model()
    ModelManager.get_reranker_model()
    await quince_mcp.start()