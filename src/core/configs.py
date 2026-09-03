import os
from dotenv import load_dotenv

load_dotenv()

BASKET_HOST = os.getenv("BASKET_HOST", "127.0.0.1")
BASKET_PORT = int(os.getenv("BASKET_PORT", "7000"))
PRODUCTION = bool(os.getenv("PRODUCTION", True))

LMS_HOST = os.getenv("LM_HOST", "127.0.0.1")
LMS_PORT = int(os.getenv("LM_PORT", "7001"))

LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY","lm-studio")

DEFAULT_LLM = "qwen/qwen3-vl-4b"

models = {
    "default": DEFAULT_LLM,
    "qwen3-vl": "qwen/qwen3-vl-4b",
    "qwen/qwen3-vl-4b": "qwen/qwen3-vl-4b",
}