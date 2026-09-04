from pydantic import BaseModel, Field


class STTRequest(BaseModel):
    prompt: str | None = Field(
        default=None,
        description=(
            "Optional transcription context or instruction "
            "to improve recognition of terminology, names, "
            "and formatting."
        ),
    )