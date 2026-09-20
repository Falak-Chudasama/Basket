from __future__ import annotations
from collections.abc import Awaitable, Callable
from typing import Any, Literal


class QuinceTool:
    def __init__(
        self,
        tool_id: str,
        description: str,
        kind: Literal["category","leaf"] = "leaf",
        feedback: str = "",
        handler: Callable[..., Any] | Callable[..., Awaitable[Any]] | None = None,
        arguments: dict[str, dict[str, Any]] = {},
        required_arguments: list[str] = [],
        choice: Literal["none", "auto", "required"] = "required",
        children: list[QuinceTool] | None = None,
    ) -> None:
        self.name = tool_id.split('.')[-1]
        self.tool_id = tool_id
        self.description = description
        self.feedback = feedback
        self.arguments = arguments
        self.required_arguments = required_arguments
        self.handler = handler
        self.choice = choice
        self.children = children or []
        self.kind = kind
        

# Exmaple

# file_search = Tool(
#     tool_id="root.filesystem.search",
#     description="If user wants you to search a file in the filesystem, choose this",
#     handler=search_file,
#     arguments_types={
#         "folder_path": {
#               "type": "string",
#               "description": "folder's path",
#               "enums": [""],
#         },
#         "query": "string",
#         "file_name": "string",
#         "extension": "string"
#     },
#     required_arguments=["folder_path", "query"],
#     children=[terminate, reset],
# )

# folder_system = Tool(
#     tool_id="root.filesystem",
#     description="If user wants file or folder related operations to be done, choose this",
#     type="category",
#     children=[terminate, reset, file_search]
# )