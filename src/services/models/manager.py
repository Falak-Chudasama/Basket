from sentence_transformers import SentenceTransformer, CrossEncoder

from src.core.configs import EMBEDDING_MODEL_NAME, RERANKER_MODEL_NAME


class ModelManager:
    _embedding_model = None
    _reranker_model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            cls._embedding_model = SentenceTransformer(
                EMBEDDING_MODEL_NAME,
                device="cpu"
            )

        return cls._embedding_model

    @classmethod
    def get_reranker_model(cls):
        if cls._reranker_model is None:
            cls._reranker_model = CrossEncoder(
                RERANKER_MODEL_NAME,
                device="cpu"
            )

        return cls._reranker_model

    @classmethod
    def embedding_model_is_loaded(cls) -> bool:
        return cls._embedding_model is not None

    @classmethod
    def reranker_model_is_loaded(cls) -> bool:
        return cls._reranker_model is not None