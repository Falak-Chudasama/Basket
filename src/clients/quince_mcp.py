from __future__ import annotations
import json
from contextlib import AsyncExitStack
from typing import Any
from mcp import Client, StdioServerParameters

import logging
from src.core.configs import (
    PATH_TO_QUINCE,
    QUINCE_MCP_URL,
    QUINCE_MCP_TRANSPORT,
)
from src.schemas.QuinceMCPTool import QuinceTool

logger = logging.getLogger(__name__)


class QuinceMCPClient:
    def __init__(
        self,
        url: str = QUINCE_MCP_URL,
        transport: str = QUINCE_MCP_TRANSPORT,
    ) -> None:
        self._stack = AsyncExitStack()
        self._client: Client | None = None
        self._url = url
        self._transport = transport

        self._stdio_server = StdioServerParameters(
            command=str(
                PATH_TO_QUINCE
                / ".venv"
                / "Scripts"
                / "python.exe"
            ),
            args=[
                str(PATH_TO_QUINCE / "run_mcp.py"),
                "--transport",
                "stdio",
            ],
        )

    def _to_openai_tool(self, tool: Any):
        parameters = {
            "type": "object",
            "properties": {
                name: params
                for name, params in tool["arguments"].items()
            },
            "required": tool.get("required_arguments") or [],
        }

        return {
            "type": "function",
            "function": {
                "name": tool["tool_id"],
                "description": tool["description"],
                "parameters": parameters
            }
        }

    async def _get_tools(self):
        if self._client is None:
            await self.start()
        result = await self._client.list_tools()
        return result

    async def _tool_call(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None
    ):
        if self._client is None:
            await self.start()

        try:
            return await self._client.call_tool(
                name="navigate",
                arguments={
                    "tool_id": tool_id,
                    "arguments": arguments
                }
            )
        except Exception as exc:
            logger.warning("MCP tool call failed (%s). Reconnecting...", exc)
            await self.stop()
            await self.start()
            return await self._client.call_tool(
                name="navigate",
                arguments={
                    "tool_id": tool_id,
                    "arguments": arguments
                }
            )

    async def start(self) -> None:
        if self._client is not None:
            return

        # 1. Try Streamable HTTP if configured
        if self._transport == "streamable-http" and self._url:
            try:
                client = Client(self._url)
                self._client = await self._stack.enter_async_context(client)
                logger.info("Connected to Quince MCP server via Streamable HTTP at %s", self._url)
                return
            except Exception as exc:
                logger.warning(
                    "Could not connect to Quince MCP at %s (%s). Falling back to stdio...",
                    self._url,
                    exc,
                )
                await self._stack.aclose()
                self._stack = AsyncExitStack()

        # 2. Fallback to stdio subprocess
        client = Client(self._stdio_server)
        self._client = await self._stack.enter_async_context(client)
        logger.info("Started Quince MCP client via local stdio subprocess.")

    async def stop(self) -> None:
        try:
            await self._stack.aclose()
        except Exception:
            pass
        finally:
            self._client = None
            self._stack = AsyncExitStack()

    async def get_root(self):
        return await self.tool_call(tool_id="root")

    def get_openai_tools(self, result):
        tools = [
            self._to_openai_tool(tool)
            for tool in result["children"]
        ]

        return tools

    async def tool_call(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
    ):
        result = await self._tool_call(tool_id, arguments)

        if result.is_error == True:
            # TODO: handle error or pass it to utility function
            pass

        return json.loads(result.content[0].text)


quince_mcp = QuinceMCPClient()