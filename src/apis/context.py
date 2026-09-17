from fastapi import APIRouter, HTTPException

from src.core.state import quince_db_memory, quince_commands


context_router = APIRouter(
    prefix="/context",
    tags=["Context"],
)

@context_router.post("/memory/add")
def add_memory():
    pass
@context_router.post("/memory/get")
def get_memory():
    pass
@context_router.post("/memory/get_all")
def get_all_memory():
    pass
@context_router.post("/memory/delete")
def delete_memory():
    pass

@context_router.post("/command/add")
def add_command():
    pass
@context_router.post("/command/get")
def get_command():
    pass
@context_router.post("/command/get_all")
def get_all_command():
    pass
@context_router.post("/command/delete")
def delete_command():
    pass
