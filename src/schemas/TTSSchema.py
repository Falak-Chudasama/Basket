from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Text to synthesize into speech.",
    )

    voice: str = Field(
        default="jane",
        description="Pocket TTS voice to use.",
    )

    temperature: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Sampling temperature controlling expressiveness.",
    )

    stream: bool = Field(
        default=False,
        description="Stream audio chunks as they are generated.",
    )