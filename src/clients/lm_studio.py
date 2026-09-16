import json
import time

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from src.core.configs import DEFAULT_LMS_LLM, LMS_HOST, LMS_PORT, LM_STUDIO_API_KEY
from src.schemas.ChatSchema import ChatRequest

# ============================================================
# LM STUDIO CONFIGURATION
# ============================================================

LM_STUDIO_BASE_URL = f"http://{LMS_HOST}:{LMS_PORT}"
LM_STUDIO_URL = f"{LM_STUDIO_BASE_URL}/v1/chat/completions"

# OpenAI-compatible model listing.
LM_STUDIO_MODELS_URL = f"{LM_STUDIO_BASE_URL}/v1/models"

# Native LM Studio model-management API.
LM_STUDIO_API_MODELS_URL = f"{LM_STUDIO_BASE_URL}/api/v1/models"
LM_STUDIO_LOAD_URL = f"{LM_STUDIO_BASE_URL}/api/v1/models/load"
LM_STUDIO_UNLOAD_URL = f"{LM_STUDIO_BASE_URL}/api/v1/models/unload"


# ============================================================
# OPENAI CLIENT
# ============================================================

client = OpenAI(base_url=f"{LM_STUDIO_BASE_URL}/v1", api_key=LM_STUDIO_API_KEY)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = ""


# ============================================================
# HTTP HELPERS
# ============================================================


def _headers(accept: str = "application/json"):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LM_STUDIO_API_KEY}",
        "Accept": accept,
    }


def _timeout():
    return httpx.Timeout(connect=10.0, read=None, write=30.0, pool=30.0)


def _error_body(response: httpx.Response) -> dict:
    """Best-effort parse of an error response body as JSON."""
    try:
        return response.json()
    except Exception:
        return {"error": response.text}


def _raise_for_status(response: httpx.Response) -> None:
    """Raise HTTPException mirroring an LM Studio error response, if any."""
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=_error_body(response))


async def _lms_request(method: str, url: str, *, action: str, **kwargs) -> httpx.Response:
    """
    Send one request to LM Studio, translating transport failures into
    HTTPException. `action` describes the request for error messages
    (e.g. "connect to LM Studio", "model request").
    """
    async with httpx.AsyncClient(timeout=_timeout()) as http_client:
        try:
            return await http_client.request(method, url, **kwargs)
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Unable to connect to LM Studio.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"LM Studio {action} timed out.")
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"LM Studio HTTP error: {exc}")


def _is_model_not_loaded_error(error_data: object) -> bool:
    error_text = json.dumps(error_data).lower()
    return any(
        phrase in error_text
        for phrase in ("model not loaded", "no model is loaded", "model is not loaded", "no loaded model")
    )


# ============================================================
# MESSAGE BUILDING
# ============================================================


def _build_messages(request: ChatRequest):
    system_prompt = request.system_prompt if request.system_prompt is not None else SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_prompt}]

    for message in request.messages:
        messages.append({"role": message.role, "content": message.content})

    return messages


# ============================================================
# LM STUDIO PAYLOAD
# ============================================================


def _build_lm_payload(request: ChatRequest):
    payload = {
        "model": request.model or DEFAULT_LMS_LLM,
        "messages": _build_messages(request),
        "stream": request.stream,
    }

    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    if request.max_tokens is not None and request.max_tokens > 0:
        payload["max_tokens"] = request.max_tokens
    if request.stop is not None:
        payload["stop"] = request.stop
    if request.seed is not None:
        payload["seed"] = request.seed

    return payload


# ============================================================
# RESPONSE ABSTRACTION
# ============================================================


def _content_to_text(content) -> str:
    """Shared logic: flatten an OpenAI-style `content` field to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [item.get("text") for item in content if isinstance(item, dict)]
        return "".join(text for text in parts if isinstance(text, str))
    return str(content)


def _extract_text(response_data):
    """Extract only the generated assistant text from an OpenAI-compatible
    non-streaming response."""
    if not isinstance(response_data, dict):
        return str(response_data)

    choices = response_data.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        return ""

    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        return ""

    return _content_to_text(message.get("content", ""))


def _extract_stream_text(data):
    """Extract only the generated text from one OpenAI-compatible streaming
    SSE JSON payload."""
    if not isinstance(data, dict):
        return ""

    choices = data.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        return ""

    delta = choices[0].get("delta", {})
    if not isinstance(delta, dict):
        return ""

    return _content_to_text(delta.get("content", ""))


# ============================================================
# MODEL STATE HELPERS
# ============================================================


async def _get_model_state():
    """Get all models known to LM Studio, including their currently loaded
    instances."""
    response = await _lms_request("GET", LM_STUDIO_API_MODELS_URL, action="model-state request", headers=_headers())
    _raise_for_status(response)
    return response.json()


async def _get_loaded_instances():
    """Return all loaded LM Studio model instances."""
    model_state = await _get_model_state()
    models = model_state.get("models", [])

    loaded_instances = []
    for model in models:
        if not isinstance(model, dict):
            continue

        instances = model.get("loaded_instances", [])
        if not isinstance(instances, list):
            continue

        for instance in instances:
            if isinstance(instance, dict):
                loaded_instances.append({"model": model, "instance": instance})

    return loaded_instances


# ============================================================
# MODEL-LOADED CACHE
#
# Basket's architecture keeps the LLM resident on the GPU for the entire
# runtime (no load/unload swapping). Hitting LM Studio's /api/v1/models
# endpoint on every single chat turn just to re-confirm this is a fixed
# latency tax with no payoff. Cache a positive result in-process and only
# pay the HTTP round-trip again if a request actually fails.
# ============================================================

_model_loaded_cache: bool = False
_model_loaded_cache_at: float = 0.0

# Re-verify at most this often even on the "assume loaded" path, in case the
# model was unloaded out-of-band (e.g. manually in LM Studio's UI). Set to 0
# to disable periodic re-checks.
_MODEL_LOADED_REVALIDATE_SECONDS = 300.0


def _invalidate_model_loaded_cache() -> None:
    """Call this after any request fails so the next call re-checks."""
    global _model_loaded_cache
    _model_loaded_cache = False


async def _ensure_model_loaded(force: bool = False):
    """
    Ensure that at least one model is loaded.

    If nothing is loaded, DEFAULT_LMS_LLM is loaded automatically.

    This result is cached in-process: once we've confirmed a model is
    loaded, subsequent calls skip the LM Studio round trip entirely unless
    `force=True`, the cache has expired, or a previous call explicitly
    invalidated it after a failure.
    """
    global _model_loaded_cache, _model_loaded_cache_at

    now = time.monotonic()
    cache_is_fresh = (
        _MODEL_LOADED_REVALIDATE_SECONDS <= 0
        or (now - _model_loaded_cache_at) < _MODEL_LOADED_REVALIDATE_SECONDS
    )

    if not force and _model_loaded_cache and cache_is_fresh:
        return {"loaded": True, "loaded_instances": None, "loaded_default": False, "cached": True}

    loaded_instances = await _get_loaded_instances()
    if loaded_instances:
        _model_loaded_cache = True
        _model_loaded_cache_at = now
        return {"loaded": True, "loaded_instances": loaded_instances, "loaded_default": False}

    await _load_model(DEFAULT_LMS_LLM)
    loaded_instances = await _get_loaded_instances()

    if not loaded_instances:
        _model_loaded_cache = False
        raise HTTPException(
            status_code=503,
            detail=f"LM Studio has no loaded models and DEFAULT_LMS_LLM '{DEFAULT_LMS_LLM}' could not be loaded.",
        )

    _model_loaded_cache = True
    _model_loaded_cache_at = now
    return {"loaded": True, "loaded_instances": loaded_instances, "loaded_default": True}


# ============================================================
# NON-STREAMING
# ============================================================


async def non_streaming_completion(request: ChatRequest):
    await _ensure_model_loaded()

    payload = _build_lm_payload(request)
    payload["stream"] = False

    response = await _lms_request("POST", LM_STUDIO_URL, action="request", json=payload, headers=_headers())

    # ----------------------------------------------------------------
    # MODEL-NOT-LOADED RETRY
    # ----------------------------------------------------------------
    if response.status_code >= 400 and _is_model_not_loaded_error(_error_body(response)):
        await _load_model(DEFAULT_LMS_LLM)
        response = await _lms_request("POST", LM_STUDIO_URL, action="retry", json=payload, headers=_headers())

    _raise_for_status(response)
    response_data = response.json()

    if request.abstracted:
        return _extract_text(response_data)
    return response_data


# ============================================================
# STREAMING
# ============================================================


async def streaming_completion(request: ChatRequest):
    await _ensure_model_loaded()

    payload = _build_lm_payload(request)
    payload["stream"] = True

    http_client = httpx.AsyncClient(timeout=_timeout())
    try:
        request_obj = http_client.build_request(
            "POST", LM_STUDIO_URL, json=payload, headers=_headers(accept="text/event-stream")
        )
        response = await http_client.send(request_obj, stream=True)

    except httpx.ConnectError:
        await http_client.aclose()
        _invalidate_model_loaded_cache()
        raise HTTPException(status_code=503, detail="Unable to connect to LM Studio.")

    except httpx.TimeoutException:
        await http_client.aclose()
        raise HTTPException(status_code=504, detail="LM Studio request timed out.")

    except httpx.HTTPError as exc:
        await http_client.aclose()
        raise HTTPException(status_code=502, detail=f"LM Studio HTTP error: {exc}")

    # ----------------------------------------------------------------
    # ERROR RESPONSE
    # ----------------------------------------------------------------
    if response.status_code >= 400:
        body = await response.aread()
        await response.aclose()
        await http_client.aclose()

        if response.status_code in (404, 503):
            _invalidate_model_loaded_cache()

        try:
            error_data = json.loads(body.decode("utf-8", errors="replace"))
        except Exception:
            error_data = {"error": body.decode("utf-8", errors="replace")}

        if _is_model_not_loaded_error(error_data):
            await _load_model(DEFAULT_LMS_LLM)
            return await streaming_completion(request.model_copy(deep=True))

        raise HTTPException(status_code=response.status_code, detail=error_data)

    # ----------------------------------------------------------------
    # STREAM GENERATOR
    # ----------------------------------------------------------------
    async def event_generator():
        try:
            # RAW MODE
            if not request.abstracted:
                async for chunk in response.aiter_raw():
                    if chunk:
                        yield chunk
                return

            # ABSTRACTED MODE
            #
            # LM Studio -> SSE:  data: {"choices":[{"delta":{"content":"Hello"}}]}
            # Basket -> "Hello"
            #
            # No SSE envelope reaches Quince.
            async for line in response.aiter_lines():
                if not line or line.startswith(":") or not line.startswith("data:"):
                    continue  # blank, SSE comment, or non-data line

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

        except httpx.HTTPError as exc:
            print(f"[Basket][LLM][STREAM ERROR] {exc}")

        finally:
            await response.aclose()
            await http_client.aclose()

    media_type = "text/plain" if request.abstracted else "text/event-stream"
    return StreamingResponse(
        event_generator(),
        media_type=media_type,
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ============================================================
# OPENAI-COMPATIBLE MODEL LIST
# ============================================================


async def _get_models():
    response = await _lms_request("GET", LM_STUDIO_MODELS_URL, action="model request", headers=_headers())
    _raise_for_status(response)
    return response.json()


# ============================================================
# UNLOAD MODEL
# ============================================================


async def _unload_model(model_id: str):
    payload = {"instance_id": model_id}
    response = await _lms_request(
        "POST", LM_STUDIO_UNLOAD_URL, action="unload request", json=payload, headers=_headers()
    )
    _raise_for_status(response)
    return response.json()


# ============================================================
# UNLOAD ALL MODELS
# ============================================================


async def _unload_all_models():
    loaded_instances = await _get_loaded_instances()

    unloaded = []
    for entry in loaded_instances:
        instance = entry.get("instance", {})
        if not isinstance(instance, dict):
            continue

        instance_id = instance.get("model_instance_id") or instance.get("instance_id") or instance.get("id")
        if not instance_id:
            continue

        try:
            result = await _unload_model(instance_id)
            unloaded.append({"instance_id": instance_id, "result": result})
        except HTTPException:
            continue

    return {"unloaded": unloaded, "count": len(unloaded)}


# ============================================================
# LOAD MODEL
# ============================================================


async def _load_model(
    model_id: str = DEFAULT_LMS_LLM,
    context_length: int | None = None,
    eval_batch_size: int | None = None,
    flash_attention: bool | None = None,
    num_experts: int | None = None,
):
    # ----------------------------------------------------------------
    # DO NOT LOAD DUPLICATE
    # ----------------------------------------------------------------
    loaded_instances = await _get_loaded_instances()

    for entry in loaded_instances:
        model = entry.get("model", {})
        instance = entry.get("instance", {})
        if not isinstance(model, dict) or not isinstance(instance, dict):
            continue

        loaded_model_key = model.get("key")
        loaded_instance_model = instance.get("model") or instance.get("model_key")

        if loaded_model_key == model_id or loaded_instance_model == model_id:
            return {
                "status": "already_loaded",
                "model": model_id,
                "instance_id": instance.get("model_instance_id") or instance.get("instance_id") or instance.get("id"),
            }

    # ----------------------------------------------------------------
    # LOAD
    # ----------------------------------------------------------------
    payload = {"model": model_id}
    if context_length is not None:
        payload["context_length"] = context_length
    if eval_batch_size is not None:
        payload["eval_batch_size"] = eval_batch_size
    if flash_attention is not None:
        payload["flash_attention"] = flash_attention
    if num_experts is not None:
        payload["num_experts"] = num_experts

    response = await _lms_request("POST", LM_STUDIO_LOAD_URL, action="load request", json=payload, headers=_headers())
    _raise_for_status(response)
    return response.json()


# ============================================================
# CHAT DISPATCHER
# ============================================================


async def _chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required.")

    await _ensure_model_loaded()

    if request.stream:
        return await streaming_completion(request)
    return await non_streaming_completion(request)