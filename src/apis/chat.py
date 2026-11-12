from __future__ import annotations
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.schemas.VoiceSchema import TextInputRequest
from src.services.chat.chat_pipeline import VoicePipelineConfig, chat_pipeline

logger = logging.getLogger(__name__)

chatRouter = APIRouter(prefix="/chat", tags=["chat"])


@chatRouter.post("")
@chatRouter.post("/text")
async def chat_text_endpoint(request: TextInputRequest) -> Any:
    """
    HTTP REST endpoint accepting text input for Basket chat.
    Executes context retrieval, agent loop (with Quince MCP & RTSI), and LLM response.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    pipeline_config = VoicePipelineConfig(
        application=request.application,
        system_prompt=request.llm.system_prompt if request.llm else None,
        model=request.llm.model if request.llm else None,
        temperature=request.llm.temperature if request.llm else 0.7,
        top_p=request.llm.top_p if request.llm else 1.0,
        max_tokens=request.llm.max_tokens if request.llm else None,
        stop=request.llm.stop if request.llm else None,
        seed=request.llm.seed if request.llm else None,
        abstracted=request.llm.abstracted if request.llm else True,
        voice=request.tts.voice if request.tts else "jane",
        tts_temperature=request.tts.temperature if request.tts else 0.5,
        synthesize_speech=request.synthesize_speech,
    )

    messages = list(request.llm.messages) if request.llm and request.llm.messages else []

    async def event_generator():
        try:
            async for event in chat_pipeline(
                text=request.text,
                config=pipeline_config,
                messages=messages,
            ):
                if event.type == "tts.audio":
                    # Audio bytes are streamed separately or in binary
                    continue
                yield f"data: {json.dumps({'type': event.type, 'data': event.data})}\n\n"
        except Exception as exc:
            logger.exception("Error in /chat stream")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
