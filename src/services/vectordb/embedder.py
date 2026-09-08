from src.core.state import states
from src.services.models.manager import ModelManager

model = ModelManager().get_embedding_model()


def create_embedding(text: str) -> list[float]:
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def batch_encode(texts: list[str]) -> list[list[float]]:
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=64)
    return [v.tolist() for v in vectors]