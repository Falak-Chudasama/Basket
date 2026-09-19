from __future__ import annotations
from contextlib import AsyncExitStack
from typing import Any
from mcp import Client, StdioServerParameters

from src.core.configs import PATH_TO_QUINCE


class QuinceMCPClient:
    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._client: Client | None = None

        self._server = StdioServerParameters(
            command=str(
                PATH_TO_QUINCE
                / ".venv"
                / "Scripts"
                / "python.exe"
            ),
            args=[
                str(PATH_TO_QUINCE / "run_mcp.py")
            ],
        )

    async def start(self) -> None:
        if self._client is not None:
            return
        client = Client(self._server)
        self._client = await self._stack.enter_async_context(client)

    async def stop(self) -> None:
        await self._stack.aclose()
        self._client = None

    async def get_tools(self):
        if self._client is None:
            raise RuntimeError("Quince MCP client is not started.")
        result = await self._client.list_tools()
        return result.tools

    async def tool_call(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ):
        if self._client is None:
            raise RuntimeError("Quince MCP client is not started.")

        return await self._client.call_tool(name,arguments or {})


quince_mcp = QuinceMCPClient()