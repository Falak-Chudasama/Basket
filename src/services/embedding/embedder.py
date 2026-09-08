from src.services.models.manager import ModelManager


def create_embedding(text: str) -> list[float]:
    model = ModelManager.get_embedding_model()

    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()


def batch_encode(
    texts: list[str]
) -> list[list[float]]:
    model = ModelManager.get_embedding_model()

    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=64
    )

    return [vector.tolist() for vector in vectors]