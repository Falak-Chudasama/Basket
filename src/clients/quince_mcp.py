from __future__ import annotations
import json
from contextlib import AsyncExitStack
from typing import Any
from mcp import Client, StdioServerParameters

from src.core.configs import PATH_TO_QUINCE
from src.schemas.QuinceMCPTool import QuinceTool


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
            raise RuntimeError("Quince MCP client is not started.")
        result = await self._client.list_tools()
        return result

    async def _tool_call(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None
    ):
        if self._client is None:
            raise RuntimeError("Quince MCP client is not started.")

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
        client = Client(self._server)
        self._client = await self._stack.enter_async_context(client)

    async def stop(self) -> None:
        await self._stack.aclose()
        self._client = None

    async def get_root(self):
        return await self.tool_call(tool_id="root")

    async def tool_call(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
    ):
        result = await self._tool_call(tool_id, arguments)

        if result.is_error == True:
            # TODO: handle error or pass it to utility function
            pass

        data = json.loads(result.content[0].text)

        tools = [
            self._to_openai_tool(tool)
            for tool in data["children"]
        ]

        return tools


quince_mcp = QuinceMCPClient()