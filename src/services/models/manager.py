from sentence_transformers import SentenceTransformer, CrossEncoder

from src.core.configs import EMBEDDING_MODEL_NAME, RERANKER_MODEL_NAME
from src.core.state import states


class ModelManager:
    @staticmethod
    def get_embedding_model():
        if states["embedding_model"] is None:
            states["embedding_model"] = SentenceTransformer(
                EMBEDDING_MODEL_NAME,
                device="cpu"
            )

        return states["embedding_model"]

    @staticmethod
    def get_reranker_model():
        if states["reranker_model"] is None:
            states["reranker_model"] = CrossEncoder(
                RERANKER_MODEL_NAME,
                device="cpu"
            )

        return states["reranker_model"]

    @staticmethod
    def embedding_model_is_loaded():
        return states["embedding_model"] is not None

    @staticmethod
    def reranker_model_is_loaded():
        return states["reranker_model"] is not None