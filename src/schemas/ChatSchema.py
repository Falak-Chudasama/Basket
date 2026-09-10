from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal[
        "system",
        "user",
        "assistant",
        "tool",
    ]
    content: Any = None
    tool_calls: Optional[List[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    stream: bool = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stop: Optional[Any] = None
    seed: Optional[int] = None
    system_prompt: Optional[str] = None
    command_system_prompt: Optional[str] = None
    abstracted: bool = True
    tools: Optional[List[dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
