import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:7005/")
BASKET_DB: str = os.getenv("BASKET_DB", "basket")

VECTOR_DB_PATH: str = "./chromadb"
PATH_TO_QUINCE = Path(r"C:\Users\ADMIN\OneDrive\CODES\Projects\Projects\Basket\fruits\quince")

# Primary -> jinaai/jina-embeddings-v5-text-nano
# Secondary -> Qwen/Qwen3-Embedding-0.6B
EMBEDDING_MODEL_NAME: str = "jinaai/jina-embeddings-v5-text-nano"

# Primary -> cross-encoder/ettin-reranker-32m-v1
# Secondary -> jinaai/jina-reranker-v3.5
RERANKER_MODEL_NAME: str = "cross-encoder/ettin-reranker-32m-v1"

BASKET_HOST = os.getenv("BASKET_HOST", "127.0.0.1")
BASKET_PORT = int(os.getenv("BASKET_PORT", "7000"))
PRODUCTION = bool(os.getenv("PRODUCTION", True))

WS_PATH="/ws"

LLM_HOST = os.getenv("LLM_HOST", "127.0.0.1")
LLM_PORT = int(os.getenv("LLM_PORT", "7001"))
LLM_DEFAULT_CONTEXT_LENGTH = 12000
LLM_DEFAULT_ID = "quince-llm"
LLM_ROOT_SYSTEM_PROMPT = ""

STT_HOST = os.getenv("STT_HOST", "127.0.0.1")
STT_PORT = int(os.getenv("STT_PORT", "7002"))
# Smaller Model: "Qwen3-ASR-0.6B-Q8_0"
# Bigger Model: "Qwen3-ASR-1.7B-Q8_0"
DEFAULT_STT_MODEL = "Qwen3-ASR-0.6B-Q8_0"

TTS_HOST = os.getenv("TTS_HOST", "127.0.0.1")
TTS_PORT = int(os.getenv("TTS_PORT", "7003"))
DEFAULT_TTS_VOICE = "jane"
DEFAULT_TTS_TEMP = 0.75

LMS_HOST = os.getenv("LMS_HOST", "127.0.0.1")
LMS_PORT = int(os.getenv("LMS_PORT", "7006"))
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY","lm-studio")
DEFAULT_LMS_LLM = "qwen/qwen3-vl-4b"

DEFAULT_VECTORDB_N = 20
DEFAULT_BM25_N = 20
DEFAULT_CANDIDATES_FOR_RERANKING = 10
TOP_K = 6
CHAT_CHUNK_SIZE = 600
CHAT_CHUNK_OVERLAP = 80

MCP_TOOL_CALL_LIMIT = 20