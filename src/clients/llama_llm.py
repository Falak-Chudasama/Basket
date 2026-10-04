import httpx
import json
import logging
import re
import uuid
from openai import OpenAI
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from typing import Any, Optional

from src.core.configs import (
    LLM_HOST,
    LLM_PORT,
    LLM_DEFAULT_ID,
    LLM_ROOT_SYSTEM_PROMPT
)
from src.schemas.ChatSchema import ChatRequest

logger = logging.getLogger(__name__)

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

def _gbnf_literal(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'

def _enum_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

_BASE_RULES = (
    'boolean ::= "true" | "false"',
    'integer ::= "-"? [0-9]+',
    'number ::= "-"? [0-9]+ ("." [0-9]+)?',
    'string ::= [^<\\x00-\\x1F]+',
)

_PRIMITIVE_TYPES = {"string", "boolean", "integer", "number"}

_OPEN_CALL = _gbnf_literal("<tool_call>\n")
_CLOSE_CALL = _gbnf_literal("</tool_call>\n")
_CLOSE_FUNCTION = _gbnf_literal("</function>\n")
_CLOSE_PARAMETER = _gbnf_literal("\n</parameter>\n")

def _get_tool_call_grammar(tools: list[dict[str, Any]]) -> str:
    if not tools:
        raise ValueError("Cannot build a tool-call grammar without tools.")

    tool_refs: list[str] = []
    tool_rules: list[str] = []
    enum_rules: list[str] = []

    for i, tool in enumerate(tools):
        function = tool["function"]
        tool_name = function["name"]

        rule_name = f"tool-{i}"
        tool_refs.append(rule_name)

        params = function.get("parameters") or {}
        properties = params.get("properties") or {}
        required = set(params.get("required") or [])

        parts = [_gbnf_literal(f"<function={tool_name}>\n")]

        for j, (prop_name, schema) in enumerate(properties.items()):
            schema = schema or {}
            enum = schema.get("enum")

            if enum:
                value_ref = f"tool-{i}-arg-{j}"
                choices = " | ".join(
                    _gbnf_literal(_enum_text(v)) for v in dict.fromkeys(enum)
                )
                enum_rules.append(f"{value_ref} ::= {choices}")
            else:
                schema_type = schema.get("type")
                if isinstance(schema_type, list):
                    schema_type = next((t for t in schema_type if t != "null"), None)
                if schema_type not in _PRIMITIVE_TYPES:
                    raise ValueError(
                        f"Unsupported type {schema_type!r} for parameter "
                        f"'{prop_name}' of tool '{tool_name}'."
                    )
                value_ref = schema_type

            parameter = " ".join(
                [
                    _gbnf_literal(f"<parameter={prop_name}>\n"),
                    value_ref,
                    _CLOSE_PARAMETER,
                ]
            )
            parts.append(parameter if prop_name in required else f"({parameter})?")

        parts.append(_CLOSE_FUNCTION)
        tool_rules.append(f"{rule_name} ::= " + " ".join(parts))

    grammar = [
        f"root ::= {_OPEN_CALL} tool {_CLOSE_CALL}",
        f"tool ::= {' | '.join(tool_refs)}",
        *tool_rules,
        *enum_rules,
        *_BASE_RULES,
    ]

    return "\n".join(grammar) + "\n"

_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*<function=([^>\n]+)>\n(.*?)</function>\s*</tool_call>",
    re.DOTALL,
)
_PARAM_RE = re.compile(r"<parameter=([^>\n]+)>\n(.*?)\n</parameter>", re.DOTALL)

def _parse_grammar_tool_call(
    text: Optional[str],
    tools: list[dict[str, Any]]
) -> Optional[dict]:
    match = _TOOL_CALL_RE.search(text or "")

    if not match:
        return None

    name, body = match.group(1), match.group(2)

    schema = next(
        (
            (tool["function"].get("parameters") or {})
            for tool in tools
            if tool["function"]["name"] == name
        ),
        {},
    )
    properties = schema.get("properties") or {}

    arguments: dict[str, Any] = {}

    for prop_name, raw in _PARAM_RE.findall(body):
        prop_type = (properties.get(prop_name) or {}).get("type")

        if prop_type == "integer":
            arguments[prop_name] = int(raw)
        elif prop_type == "number":
            arguments[prop_name] = float(raw)
        elif prop_type == "boolean":
            arguments[prop_name] = raw == "true"
        else:
            arguments[prop_name] = raw

    return {
        "id": f"call_{uuid.uuid4().hex[:12]}",
        "name": name,
        "arguments": json.dumps(arguments),
    }

def _get_tool_list_message(tools: list[dict[str, Any]]) -> str:
    lines = [
        "AVAILABLE TOOLS:",
        "",
        "Choose exactly one tool when a tool is required.",
        "Only use tools listed below. Never invent tool names or arguments.",
        "",
        "OUTPUT FORMAT (exactly):",
        "<tool_call>",
        "<function=TOOL_NAME>",
        "<parameter=ARG_NAME>",
        "VALUE",
        "</parameter>",
        "</function>",
        "</tool_call>",
        ""
    ]

    for tool in tools:
        function = tool["function"]
        name = function["name"]
        description = function.get("description", "").strip()

        lines.append(f"TOOL: {name}")

        if description:
            lines.append(f"DESCRIPTION: {description}")

        params = function.get("parameters") or {}
        properties = params.get("properties", {})
        required = set(params.get("required", []))

        if properties:
            lines.append("ARGUMENTS:")
            for prop_name, schema in properties.items():
                prop_type = schema.get("type", "any")
                prop_desc = schema.get("description", "").strip()
                enum = schema.get("enum")

                required_text = "required" if prop_name in required else "optional"

                lines.append(f"- {prop_name} ({prop_type}, {required_text})")

                if enum:
                    lines.append(f"  allowed values: {', '.join(map(str, enum))}")
                if prop_desc:
                    lines.append(f"  description: {prop_desc}")

        else:
            lines.append("ARGUMENTS: none")

        lines.append("")

    return "\n".join(lines)

def _build_message(request: ChatRequest):
    system_parts: list[str] = []
    conversation_messages: list[dict] = []

    if LLM_ROOT_SYSTEM_PROMPT:
        system_parts.append(LLM_ROOT_SYSTEM_PROMPT)

    if request.system_prompt:
        system_parts.append(request.system_prompt)

    if request.tools:
        tool_message = _get_tool_list_message(request.tools)
        system_parts.append(
            f"Available Tools:\n{tool_message}"
        )

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
        "model": request.model or LLM_DEFAULT_ID,
        "messages": _build_message(request),
        "stream": stream,
        "chat_template_kwargs": {
            "enable_thinking": False
        },
    }

    force_tool_call = bool(request.tools) and (
        request.is_tool_call_request or request.tool_choice == "required"
    )

    if force_tool_call:
        try:
            payload["grammar"] = _get_tool_call_grammar(request.tools)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        logger.debug("Tool-call grammar:\n%s", payload["grammar"])

        payload["temperature"] = 0
        payload["repeat_penalty"] = 1.0
    else:
        if request.tools is not None:
            payload["parallel_tool_calls"] = False
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.repeat_penalty is not None:
            payload["repeat_penalty"] = request.repeat_penalty

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

    timeout = httpx.Timeout(
        connect=10.0,
        read=None,
        write=30.0,
        pool=30.0
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            response = await http_client.post(
                CHAT_COMPLETION_URL,
                json=_build_request(request, stream=False),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to llama.cpp."
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="llama.cpp request timed out."
        )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"llama.cpp HTTP error: {exc}"
        )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    data = response.json()

    if request.abstracted:
        choices = data.get("choices", [])

        if not choices:
            return ""

        message = choices[0].get("message", {})
        return _abstract_response(message.get("content"))

    if request.abstract_tool_use:
        choices = data.get("choices", [])

        if not choices:
            return None

        message = choices[0].get("message", {})
        content = message.get("content")
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            parsed = _parse_grammar_tool_call(content, request.tools or [])

            if parsed:
                return parsed

            finish_reason = choices[0].get("finish_reason")

            if finish_reason == "length":
                logger.error(
                    "LLM hit max_tokens with no tool call (likely decoding "
                    "collapse/repetition loop). content=%r",
                    content,
                )
            else:
                logger.warning(
                    "LLM returned no tool call. finish_reason=%r content=%r",
                    finish_reason,
                    content,
                )
            return None

        first_tool_call = tool_calls[0] or {}
        tool_call = first_tool_call.get("function") or {}

        return {
            "id": first_tool_call.get("id"),
            "name": tool_call.get("name"),
            "arguments": tool_call.get("arguments", "{}"),
        }

    return data

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