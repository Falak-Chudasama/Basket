import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:7005/")
BASKET_DB: str = os.getenv("BASKET_DB", "basket")

EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-0.6B")
RERANKER_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "jinaai/jina-reranker-v3.5")

BASKET_HOST = os.getenv("BASKET_HOST", "127.0.0.1")
BASKET_PORT = int(os.getenv("BASKET_PORT", "7000"))
PRODUCTION = bool(os.getenv("PRODUCTION", True))

LMS_HOST = os.getenv("LM_HOST", "127.0.0.1")
LMS_PORT = int(os.getenv("LM_PORT", "7001"))
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY","lm-studio")
DEFAULT_LLM = "qwen/qwen3-vl-4b"

TTS_HOST = os.getenv("TTS_HOST", "127.0.0.1")
TTS_PORT = int(os.getenv("TTS_PORT", "7003"))
DEFAULT_TTS_VOICE = "jane"
DEFAULT_TTS_TEMP = 0.75

STT_HOST = os.getenv("STT_HOST", "127.0.0.1")
STT_PORT = int(os.getenv("STT_PORT", "7002"))
DEFAULT_STT_MODEL = "Qwen3-ASR-0.6B-Q8_0"

models = {
    "default": DEFAULT_LLM,
    "qwen3-vl": "qwen/qwen3-vl-4b",
    "qwen/qwen3-vl-4b": "qwen/qwen3-vl-4b",
}