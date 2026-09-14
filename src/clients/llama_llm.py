import httpx
import json
from openai import OpenAI
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from src.core.configs import (
    LLM_HOST,
    LLM_PORT,
    LLM_DEFAULT_ID,
    LLM_ROOT_SYSTEM_PROMPT
)
from src.schemas.ChatSchema import ChatRequest

BASE_LLAMA_URL = f"http://{LLM_HOST}:{LLM_PORT}/v1"
CHAT_COMPLETION_URL = f"{BASE_LLAMA_URL}/chat/completions"
MODELS_URL = f"{BASE_LLAMA_URL}/models"

client = OpenAI(
    base_url=BASE_LLAMA_URL,
    api_key="sk-no-key-required"
)

async def _ensure_model_loaded(model_id: str = LLM_DEFAULT_ID) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(MODELS_URL)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to llama.cpp.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="llama.cpp model request timed out.")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"llama.cpp HTTP error: {exc}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    data = response.json()
    models = data.get("data", [])

    if not any(isinstance(model, dict) and model.get("id") == model_id for model in models):
        raise HTTPException(
            status_code=503,
            detail=f"Model '{model_id}' is not available in llama.cpp."
        )

    return True

def _build_message(request: ChatRequest):
    messages = []

    if LLM_ROOT_SYSTEM_PROMPT:
        messages.append({
            "role": "system",
            "content": LLM_ROOT_SYSTEM_PROMPT
        })

    if request.system_prompt:
        messages.append({
            "role": "system",
            "content": request.system_prompt
        })

    for message in request.messages:
        messages.append({
            "role": message.role,
            "content": message.content
        })

    return messages

def _build_request(request: ChatRequest, stream: bool):
    payload = {
        "model": request.model or LLM_DEFAULT_ID,
        "messages": _build_message(request),
        "stream": stream,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False
            } # TODO: Enable thinking too
        }
    }

    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens
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
    response = text.split("</thinking>", 1)[-1].strip()
    return response

def _extract_stream_text(data: dict) -> str:
    choices = data.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        return ""

    delta = choices[0].get("delta", {})
    if not isinstance(delta, dict):
        return ""

    return _content_to_text(delta.get("content"))

async def _chat_completion_non_streaming(request: ChatRequest):
    model = request.model or LLM_DEFAULT_ID
    await _ensure_model_loaded(model)

    response = client.chat.completions.create(
        **_build_request(request, stream=False)
    )

    if request.abstracted:
        return _abstract_response(response.choices[0].message.content)

    return response

async def _chat_completion_streaming(request: ChatRequest):
    model = request.model or LLM_DEFAULT_ID
    await _ensure_model_loaded(model)

    timeout = httpx.Timeout(
        connect=10.0,
        read=None,
        write=30.0,
        pool=30.0
    )

    http_client = httpx.AsyncClient(timeout=timeout)

    try:
        request_obj = http_client.build_request(
            "POST",
            CHAT_COMPLETION_URL,
            json=_build_request(request, stream=True),
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )

        response = await http_client.send(request_obj, stream=True)

    except httpx.ConnectError:
        await http_client.aclose()
        raise HTTPException(status_code=503, detail="Unable to connect to llama.cpp.")
    except httpx.TimeoutException:
        await http_client.aclose()
        raise HTTPException(status_code=504, detail="llama.cpp request timed out.")
    except httpx.HTTPError as exc:
        await http_client.aclose()
        raise HTTPException(status_code=502, detail=f"llama.cpp HTTP error: {exc}")

    if response.status_code >= 400:
        body = await response.aread()
        await response.aclose()
        await http_client.aclose()
        raise HTTPException(
            status_code=response.status_code,
            detail=body.decode("utf-8", errors="replace")
        )

    async def event_generator():
        try:
            async for line in response.aiter_lines():
                if not line or line.startswith(":") or not line.startswith("data:"):
                    continue

                data = line[len("data:"):].strip()

                if not data:
                    continue
                if data == "[DONE]":
                    break

                try:
                    chunk_data = json.loads(data)
                except json.JSONDecodeError:
                    continue

                text = _extract_stream_text(chunk_data)

                if text:
                    yield text
        finally:
            await response.aclose()
            await http_client.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def _chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="At least one message is required."
        )

    if request.stream:
        return await _chat_completion_streaming(request)

    return await _chat_completion_non_streaming(request)

async def _get_models():
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(MODELS_URL)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to llama.cpp.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="llama.cpp model request timed out.")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"llama.cpp HTTP error: {exc}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    return response.json()

async def _load_model(model_id: str = LLM_DEFAULT_ID):
    await _ensure_model_loaded(model_id)
    return {
        "status": "already_loaded",
        "model": model_id
    }

async def _unload_model(instance_id: str):
    raise HTTPException(
        status_code=501,
        detail="Model unloading is not supported through the llama.cpp REST API."
    )

async def _unload_all_models():
    raise HTTPException(
        status_code=501,
        detail="Model unloading is not supported through the llama.cpp REST API."
    )