from fastapi import APIRouter, HTTPException

from src.core.state import quince_db_memory, quince_commands
from src.schemas.ContextSchemas import (
    Application,
    AddCommand,
    DeleteCommand,
    AddMemory,
    GetMemory,
    DeleteMemory,
)


context_router = APIRouter(
    prefix="/context",
    tags=["Context"],
)


@context_router.post("/memory/add")
async def add_memory(request: AddMemory):
    if request.application == "quince":
        result = await quince_db_memory.add_one(
            request.memory,
            request.is_temporary
        )
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.post("/memory/get")
async def get_memory(request: GetMemory):
    if request.application == "quince":
        result = await quince_db_memory.get(request.memory_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Memory '{request.memory_id}' not found.",
            )

        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.post("/memory/get_all")
async def get_all_memory(request: Application):
    if request.application == "quince":
        result = await quince_db_memory.get_all()
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.delete("/memory/delete")
async def delete_memory(request: DeleteMemory):
    if request.application == "quince":
        result = await quince_db_memory.delete(request.memory_id)

        if result["deleted_count"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Memory '{request.memory_id}' not found.",
            )

        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )

@context_router.post("/memory/delete_all")
async def delete_all_memory(request: DeleteMemory):
    if request.application == "quince":
        result = await quince_db_memory.delete_all()

        if result["deleted_count"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Memory '{request.memory_id}' not found.",
            )

        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.post("/command/add")
async def add_command(request: AddCommand):
    if request.application == "quince":
        result = await quince_commands.add_one(
            request.command,
            request.is_temporary
        )
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.post("/command/get_all")
async def get_all_commands(application_request: Application):
    if application_request.application == "quince":
        result = await quince_commands.get_all()
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{application_request.application} does not exist.",
    )


@context_router.post("/command/delete")
async def delete_command(request: DeleteCommand):
    if request.application == "quince":
        result = await quince_commands.delete(request.command_id)
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )


@context_router.post("/command/delete_all")
async def delete_all_commands(request: Application):
    if request.application == "quince":
        result = await quince_commands.delete_all()
        return {"result": result}

    raise HTTPException(
        status_code=400,
        detail=f"{request.application} does not exist.",
    )