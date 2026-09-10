from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import websockets

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MCPState:
    visible_tools: list[dict[str, Any]] = field(default_factory=list)
    path: list[str] = field(default_factory=lambda: ["root"])
    tool_call_history: list[dict[str, Any]] = field(default_factory=list)
    execution_results: list[Any] = field(default_factory=list)

    def reset(self, tools: list[dict[str, Any]]) -> None:
        self.visible_tools = tools
        self.path = ["root"]
        self.tool_call_history.clear()
        self.execution_results.clear()


class MCPClient:
    """Persistent Basket -> Quince MCP connection for one voice connection."""

    def __init__(self, url: str, *, connect_timeout: float = 5.0) -> None:
        self.url = url
        self.connect_timeout = connect_timeout
        self.websocket = None
        self.state = MCPState()
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self.websocket is not None

    async def connect(self) -> None:
        if self.websocket is not None:
            return
        try:
            logger.info("MCP CONNECT start url=%s", self.url)
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.url),
                timeout=self.connect_timeout,
            )
            logger.info("MCP CONNECT complete url=%s", self.url)
        except Exception:
            self.websocket = None
            logger.warning("MCP unavailable at %s", self.url, exc_info=True)
            raise

    async def close(self) -> None:
        websocket = self.websocket
        self.websocket = None
        if websocket is not None:
            await websocket.close()

    async def reset(self) -> list[dict[str, Any]]:
        async with self._lock:
            logger.info("MCP RESET request")
            reply = await self._request({"type": "reset"})
            if reply.get("type") != "reset":
                raise RuntimeError(reply.get("error", "Invalid MCP reset response"))
            tools = reply.get("tools", [])
            self.state.reset(tools)
            logger.info("MCP RESET response tools=%s path=%s", [t.get("function", {}).get("name") for t in tools], self.state.path)
            return tools

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            request_id = uuid.uuid4().hex
            logger.info("MCP CALL request name=%s arguments=%r path=%s", name, arguments, self.state.path)
            reply = await self._request({
                "id": request_id,
                "type": "call",
                "name": name,
                "arguments": arguments,
            })

            if reply.get("type") == "explore":
                self.state.visible_tools = reply.get("tools", [])
                self.state.path = reply.get("path", self.state.path)
            elif reply.get("type") == "execute":
                self.state.execution_results.append(reply.get("result"))
            elif reply.get("type") == "error":
                raise RuntimeError(reply.get("error", "MCP tool call failed"))
            else:
                raise RuntimeError(f"Unknown MCP response type: {reply.get('type')!r}")

            logger.info("MCP CALL response name=%s type=%s path=%s", name, reply.get("type"), self.state.path)
            self.state.tool_call_history.append({
                "name": name,
                "arguments": arguments,
                "response": reply,
            })
            return reply

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.websocket is None:
            await self.connect()

        assert self.websocket is not None
        request_id = payload.setdefault("id", uuid.uuid4().hex)

        try:
            logger.debug("MCP WS SEND payload=%r", payload)
            await self.websocket.send(json.dumps(payload))
            raw = await self.websocket.recv()
            logger.debug("MCP WS RECV raw=%r", raw)
        except Exception:
            await self.close()
            raise

        reply = json.loads(raw)
        if reply.get("id") != request_id:
            raise RuntimeError("MCP response id mismatch")
        return reply


async def call_with_optional_mcp(
    mcp: MCPClient | None,
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    if mcp is None:
        raise RuntimeError("MCP is not configured for this turn")
    return await mcp.call(name, arguments)
