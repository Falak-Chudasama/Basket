from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from src.clients.lmstudio import non_streaming_completion
from src.schemas.ChatSchema import ChatRequest, Message
from src.services.mcp.client import MCPClient
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.chat.chat_pipeline import VoicePipelineConfig

logger = logging.getLogger(__name__)

MAX_AGENT_STEPS = 8


@dataclass(slots=True)
class AgentTurn:
    messages: list[Message]
    tool_steps: int = 0


def _assistant_tool_message(message: dict[str, Any]) -> Message:
    return Message(
        role="assistant",
        content=message.get("content"),
        tool_calls=message.get("tool_calls"),
    )


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        return [call for call in calls if isinstance(call, dict)]

    legacy = message.get("function_call")
    if isinstance(legacy, dict):
        return [{
            "id": legacy.get("id", "legacy-tool-call"),
            "type": "function",
            "function": legacy,
        }]
    return []


def _call_name(call: dict[str, Any]) -> str:
    function = call.get("function") or {}
    return str(function.get("name") or "")


def _call_arguments(call: dict[str, Any]) -> dict[str, Any]:
    function = call.get("function") or {}
    raw = function.get("arguments") or {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Tool arguments are not valid JSON: {exc.msg}") from exc
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("Tool arguments must be a JSON object")


def _tool_message(call_id: str, result: Any) -> Message:
    return Message(
        role="tool",
        content=json.dumps(result, ensure_ascii=False, default=str),
        tool_call_id=call_id,
    )


async def resolve_agent_turn(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
    mcp: MCPClient | None,
) -> AgentTurn:
    """Run EXPLORE/EXECUTE until the model emits a normal answer."""

    if mcp is None:
        return AgentTurn(messages=list(messages))

    try:
        logger.info("AGENT START messages=%d", len(messages))
        await mcp.reset()
    except Exception:
        logger.warning("MCP reset failed; falling back to normal LLM response.", exc_info=True)
        return AgentTurn(messages=list(messages))

    conversation = list(messages)

    for step in range(MAX_AGENT_STEPS):
        request = ChatRequest(
            model=config.model,
            messages=conversation,
            stream=False,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_tokens,
            stop=config.stop,
            seed=config.seed,
            system_prompt=config.system_prompt,
            command_system_prompt=config.command_system_prompt,
            abstracted=False,
            tools=mcp.state.visible_tools,
        )

        logger.info("AGENT LLM REQUEST step=%d visible_tools=%s", step + 1, [t.get("function", {}).get("name") for t in mcp.state.visible_tools])
        raw = await non_streaming_completion(request)
        logger.debug("AGENT LLM RAW RESPONSE step=%d response=%r", step + 1, raw)
        if not isinstance(raw, dict):
            return AgentTurn(messages=conversation, tool_steps=step)

        choices = raw.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return AgentTurn(messages=conversation, tool_steps=step)

        assistant = choices[0].get("message") or {}
        if not isinstance(assistant, dict):
            return AgentTurn(messages=conversation, tool_steps=step)

        calls = _tool_calls(assistant)
        logger.info("AGENT LLM DECISION step=%d content=%r tool_calls=%d", step + 1, assistant.get("content"), len(calls))
        if not calls:
            return AgentTurn(messages=conversation, tool_steps=step)

        # One tool decision per agent iteration keeps traversal deterministic
        # and ensures the visible tool set always matches the current path.
        call = calls[0]
        name = _call_name(call)
        if not name:
            raise ValueError("LLM returned a tool call without a name")

        conversation.append(_assistant_tool_message(assistant))

        try:
            arguments = _call_arguments(call)
            logger.info(
                "AGENT TOOL INTENT step=%d tool=%s arguments=%r path=%s",
                step + 1,
                name,
                arguments,
                "/".join(mcp.state.path),
            )

            logger.info(
                "MCP TOOL CALL step=%d tool=%s path=%s",
                step + 1,
                name,
                "/".join(mcp.state.path),
            )
            reply = await mcp.call(name, arguments)
        except Exception as exc:
            # Tool failures are fed back to the model as normal tool results so
            # it can recover, choose another tool, or answer without crashing
            # the entire voice turn.
            logger.exception(
                "AGENT TOOL FAILED step=%d tool=%s",
                step + 1,
                name,
            )
            reply = {
                "type": "error",
                "error": str(exc),
                "recoverable": True,
            }

        logger.info(
            "AGENT MCP RESULT step=%d type=%s path=%s result=%r",
            step + 1,
            reply.get("type"),
            reply.get("path"),
            reply,
        )
        conversation.append(
            _tool_message(
                str(call.get("id", "tool-call")),
                reply,
            )
        )
        logger.info(
            "AGENT CONVERSATION APPENDED step=%d total_messages=%d",
            step + 1,
            len(conversation),
        )

    raise RuntimeError(f"MCP agent exceeded {MAX_AGENT_STEPS} steps")
