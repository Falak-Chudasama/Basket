from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

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

    stream: bool = True

    sample_rate: int = 16_000


    llm: VoiceLLMConfig = Field(
        default_factory=VoiceLLMConfig
    )

    tts: VoiceTTSConfig = Field(
        default_factory=VoiceTTSConfig
    )

    application: str = Field(
        min_length=1,
        description="Application identifier for namespace isolation.",
    )