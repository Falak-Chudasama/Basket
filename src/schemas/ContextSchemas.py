from pydantic import BaseModel
from typing import Literal

class Application(BaseModel):
    application: Literal["quince"] = "quince"


class AddMemory(Application):
    memory: str
    is_temporary: bool = True

class GetMemory(Application):
    memory_id: str

class DeleteMemory(Application):
    memory_id: str



class AddCommand(Application):
    command: str
    is_temporary: bool = True

class DeleteCommand(Application):
    command_id: str