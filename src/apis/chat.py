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

    active_chat_id = request.chat_id
    if not active_chat_id:
        from bson import ObjectId
        active_chat_id = str(ObjectId())

    pipeline_config = VoicePipelineConfig(
        application=request.application,
        chat_id=active_chat_id,
        retrieve_chat=request.retrieve_chat,
        retrieve_notes=request.retrieve_notes,
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
        rag_top_k=request.rag_top_k,
        rag_metadata_filter=request.rag_metadata_filter,
        rag_use_reranker=request.rag_use_reranker,
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
                if event.type == "llm.token":
                    yield f"event: delta\ndata: {json.dumps({'content': event.data, 'chat_id': active_chat_id})}\n\n"
                elif event.type == "pipeline.completed":
                    yield f"event: done\ndata: {json.dumps({'finish_reason': 'stop', 'chat_id': active_chat_id})}\n\n"
                yield f"data: {json.dumps({'type': event.type, 'data': event.data, 'chat_id': active_chat_id})}\n\n"
        except Exception as exc:
            logger.exception("Error in /chat stream")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
