from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from src.schemas.ChatSchema import Message


class VoiceLLMConfig(BaseModel):
    model: str | None = None

    messages: list[Message] = Field(
        default_factory=list
    )

    temperature: float | None = 0.7
    top_p: float | None = 1.0
    max_tokens: int | None = None
    stop: Any | None = None
    seed: int | None = None

    system_prompt: str | None = None

    abstracted: bool = True


class VoiceTTSConfig(BaseModel):

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


class VoiceStartRequest(BaseModel):
    """Start configuration for one Basket voice turn."""

    type: Literal["start"] = "start"

    prompt: str | None = None

    text: str | None = None

    stream: bool = True

    sample_rate: int = 16_000

    llm: VoiceLLMConfig = Field(
        default_factory=VoiceLLMConfig
    )

    tts: VoiceTTSConfig = Field(
        default_factory=VoiceTTSConfig
    )

    application: str = Field(
        default="quince",
        min_length=1,
        description="Application identifier for namespace isolation.",
    )

class TextInputRequest(BaseModel):
    """Configuration and text input for a Basket chat turn."""

    type: Literal["text", "text_input"] = "text_input"

    text: str = Field(
        min_length=1,
        description="User text input for the turn.",
    )

    synthesize_speech: bool = Field(
        default=True,
        description="Whether to synthesize TTS audio speech for the response.",
    )

    application: str = Field(
        default="quince",
        min_length=1,
        description="Application identifier for namespace isolation.",
    )

    llm: VoiceLLMConfig | None = Field(
        default_factory=VoiceLLMConfig
    )

    tts: VoiceTTSConfig | None = Field(
        default_factory=VoiceTTSConfig
    )

    @field_validator("text")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("text cannot be empty or whitespace only")
        return stripped