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

    stream: bool = Field(
        default=False,
        description=(
            "Enable realtime streaming transcription. For live microphone "
            "streaming, use the WebSocket /stt/stream endpoint."
        ),
    )
