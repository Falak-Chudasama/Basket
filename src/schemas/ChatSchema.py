from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: Literal[
        "system",
        "user",
        "assistant",
        "tool"
    ]

    content: Any

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message] = Field(
        default_factory=list
    )
    stream: bool = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stop: Optional[Any] = None
    seed: Optional[int] = None
    system_prompt: Optional[str] = None