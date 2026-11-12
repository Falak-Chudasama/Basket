import asyncio
import logging
from src.services.models.manager import ModelManager
from src.clients.quince_mcp import quince_mcp

logger = logging.getLogger(__name__)

async def load_models():
    ModelManager.get_embedding_model()
    ModelManager.get_reranker_model()
    try:
        await asyncio.wait_for(quince_mcp.start(), timeout=4.0)
    except Exception as exc:
        logger.info("Quince MCP connect deferred (will connect on-demand): %s", exc)