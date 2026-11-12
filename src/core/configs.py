import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:10000/")
BASKET_DB = os.getenv("BASKET_DB", "basket")
VECTOR_DB_PATH = "./chromadb"
PATH_TO_QUINCE = Path(r"C:\Users\ADMIN\OneDrive\CODES\Projects\Projects\Basket\fruits\quince")

EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v5-text-nano"  # Secondary: Qwen/Qwen3-Embedding-0.6B
RERANKER_MODEL_NAME = "cross-encoder/ettin-reranker-32m-v1"   # Secondary: jinaai/jina-reranker-v3.5

BASKET_HOST = os.getenv("BASKET_HOST", "127.0.0.1")
BASKET_PORT = int(os.getenv("BASKET_PORT", "10010"))
PRODUCTION = os.getenv("PRODUCTION", "true").lower() == "true"
WS_PATH = "/ws"

LLM_HOST = os.getenv("LLM_HOST", "127.0.0.1")
LLM_PORT = int(os.getenv("LLM_PORT", "10030"))
LLM_DEFAULT_CONTEXT_LENGTH = 12000
LLM_DEFAULT_ID = "quince-llm"
LLM_ROOT_SYSTEM_PROMPT = ""

GROQ_API_KEY=os.getenv("GROQ_API_KEY", "NONE")
GROQ_LLM_MODEL=os.getenv("GROQ_LLM_MODEL", "qwen/qwen3.8-27b")

STT_HOST = os.getenv("STT_HOST", "127.0.0.1")
STT_PORT = int(os.getenv("STT_PORT", "10040"))
# Smaller Model: "Qwen3-ASR-0.6B-Q8_0"
# Bigger Model: "Qwen3-ASR-1.7B-Q8_0"
DEFAULT_STT_MODEL = "Qwen3-ASR-0.6B-Q8_0"

TTS_HOST = os.getenv("TTS_HOST", "127.0.0.1")
TTS_PORT = int(os.getenv("TTS_PORT", "10050"))
DEFAULT_TTS_VOICE = "jane"
DEFAULT_TTS_TEMP = 0.75

DEFAULT_VECTORDB_N = 20
DEFAULT_BM25_N = 20
DEFAULT_CANDIDATES_FOR_RERANKING = 10
TOP_K = 10
CHAT_CHUNK_SIZE = 600
CHAT_CHUNK_OVERLAP = 80

MCP_TOOL_CALL_LIMIT = 20
AGENT_MAX_TOKENS = 512
AGENT_REPEAT_PENALTY = 1.2
AGENT_RETRY_MAX_TOKENS = 60
AGENT_RETRY_REPEAT_PENALTY = 1.3

QUINCE_MCP_HOST = os.getenv("QUINCE_MCP_HOST", "127.0.0.5")
QUINCE_MCP_PORT = int(os.getenv("QUINCE_MCP_PORT", "10010"))
QUINCE_MCP_URL = os.getenv("QUINCE_MCP_URL", f"http://{QUINCE_MCP_HOST}:{QUINCE_MCP_PORT}/mcp")
QUINCE_MCP_TRANSPORT = os.getenv("QUINCE_MCP_TRANSPORT", "streamable-http")