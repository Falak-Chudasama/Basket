from groq import AsyncGroq
import logging
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from src.core.configs import (
    LLM_ROOT_SYSTEM_PROMPT,
    GROQ_API_KEY,
    GROQ_LLM_MODEL,
)
from src.schemas.ChatSchema import ChatRequest

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=GROQ_API_KEY)


async def _ensure_model_loaded(model_id: str = GROQ_LLM_MODEL) -> bool:
    return True


def _build_message(request: ChatRequest):
    system_parts: list[str] = []
    conversation_messages: list[dict] = []

    if LLM_ROOT_SYSTEM_PROMPT:
        system_parts.append(LLM_ROOT_SYSTEM_PROMPT)

    if request.system_prompt:
        system_parts.append(request.system_prompt)

    for message in request.messages:
        if message.role == "system":
            system_parts.append(str(message.content))
            continue

        item = {
            "role": message.role,
            "content": message.content,
        }

        if message.tool_calls is not None:
            item["tool_calls"] = message.tool_calls

        if message.tool_call_id is not None:
            item["tool_call_id"] = message.tool_call_id

        conversation_messages.append(item)

    final_messages: list[dict] = []

    if system_parts:
        final_messages.append({
            "role": "system",
            "content": "\n\n".join(system_parts),
        })

    final_messages.extend(conversation_messages)

    return final_messages


def _build_request(request: ChatRequest, stream: bool):
    payload = {
        "model": GROQ_LLM_MODEL,
        "messages": _build_message(request),
        "stream": stream,
    }

    if request.thinking:
        payload["reasoning_effort"] = "default"
    else:
        payload["reasoning_effort"] = "none"

    if request.tools is not None:
        payload["tools"] = request.tools
        payload["parallel_tool_calls"] = False

    if request.tool_choice is not None:
        payload["tool_choice"] = request.tool_choice

    if request.temperature is not None:
        payload["temperature"] = request.temperature

    if request.top_p is not None:
        payload["top_p"] = request.top_p

    if request.max_tokens is not None:
        payload["max_completion_tokens"] = request.max_tokens

    if request.stop is not None:
        payload["stop"] = request.stop

    if request.seed is not None:
        payload["seed"] = request.seed

    return payload


def _content_to_text(content) -> str:
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    return str(content)


def _abstract_response(content) -> str:
    text = _content_to_text(content)
    return text.split("</thinking>", 1)[-1].strip()


async def _chat_completion_non_streaming(request: ChatRequest):
    await _ensure_model_loaded()

    try:
        response = await client.chat.completions.create(
            **_build_request(request, stream=False)
        )

    except Exception as exc:
        logger.exception("Groq request failed")

        status_code = getattr(getattr(exc, "response", None), "status_code", None)

        if status_code is not None:
            raise HTTPException(
                status_code=status_code,
                detail=str(exc),
            )

        raise HTTPException(
            status_code=502,
            detail=f"Groq request failed: {exc}",
        )

    if not response.choices:
        return "" if request.abstracted else None

    message = response.choices[0].message

    if request.abstracted:
        return _abstract_response(message.content)

    if request.abstract_tool_use:
        tool_calls = message.tool_calls or []

        if not tool_calls:
            finish_reason = response.choices[0].finish_reason
            content = message.content

            if finish_reason == "length":
                logger.error(
                    "Groq hit max_completion_tokens with no tool call. content=%r",
                    content,
                )
            else:
                logger.warning(
                    "Groq returned no tool call. finish_reason=%r content=%r",
                    finish_reason,
                    content,
                )

            return None

        first_tool_call = tool_calls[0]

        return {
            "id": first_tool_call.id,
            "name": first_tool_call.function.name,
            "arguments": first_tool_call.function.arguments or "{}",
        }

    return response.model_dump()


async def _chat_completion_streaming(request: ChatRequest):
    await _ensure_model_loaded()

    try:
        stream = await client.chat.completions.create(
            **_build_request(request, stream=True)
        )

    except Exception as exc:
        logger.exception("Groq streaming request failed")

        status_code = getattr(getattr(exc, "response", None), "status_code", None)

        if status_code is not None:
            raise HTTPException(
                status_code=status_code,
                detail=str(exc),
            )

        raise HTTPException(
            status_code=502,
            detail=f"Groq streaming request failed: {exc}",
        )

    async def event_generator():
        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                text = _content_to_text(delta.content)

                if text:
                    yield text

        except Exception:
            logger.exception("Groq streaming failed")
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="At least one message is required.",
        )

    if request.stream:
        return await _chat_completion_streaming(request)

    return await _chat_completion_non_streaming(request)


async def _get_models():
    raise HTTPException(
        status_code=501,
        detail="Model listing is not supported through the Groq SDK.",
    )


async def _load_model(model_id: str = GROQ_LLM_MODEL):
    raise HTTPException(
        status_code=501,
        detail="Model loading is not supported through the Groq API.",
    )


async def _unload_model(instance_id: str):
    raise HTTPException(
        status_code=501,
        detail="Model unloading is not supported through the Groq API.",
    )


async def _unload_all_models():
    raise HTTPException(
        status_code=501,
        detail="Model unloading is not supported through the Groq API.",
    )