from __future__ import annotations

from uuid import uuid4
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.state import quince_commands, quince_memory

router = APIRouter(prefix="/mcp-api", tags=["MCP"])
logger = logging.getLogger("basket.mcp_api")


class MemoryStoreRequest(BaseModel):
    document: str
    source: str = "user"


class MemorySearchRequest(BaseModel):
    query: str
    n_result: int = Field(default=5, ge=1, le=10)


class CommandAddRequest(BaseModel):
    command: str
    is_temporary: bool = False


class CommandDeleteRequest(BaseModel):
    command: str


@router.post("/memory/store")
async def memory_store(req: MemoryStoreRequest):
    started = time.perf_counter()
    document = req.document.strip()
    if not document:
        raise HTTPException(status_code=400, detail="document is required")

    memory_id = uuid4().hex
    try:
        quince_memory.add_memory(
            memory_id=memory_id,
            document=document,
            source=req.source,
            memory_type="long_term",
        )
        verification = quince_memory.collection.get(ids=[memory_id])
        verified = bool(verification.get("ids")) and memory_id in verification.get("ids", [])
    except Exception as exc:
        logger.exception("MEMORY STORE FAILED id=%s", memory_id)
        raise HTTPException(status_code=500, detail=f"memory store failed: {exc}") from exc

    logger.info(
        "MEMORY STORE COMPLETE id=%s verified=%s elapsed=%.3fs",
        memory_id,
        verified,
        time.perf_counter() - started,
    )
    return {"stored": True, "verified": verified, "memory_id": memory_id}


@router.post("/memory/search")
async def memory_search(req: MemorySearchRequest):
    started = time.perf_counter()
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        result = quince_memory.query_memory(query=query, n_result=req.n_result)
    except Exception as exc:
        logger.exception("MEMORY SEARCH FAILED query=%r", query)
        raise HTTPException(status_code=500, detail=f"memory search failed: {exc}") from exc

    documents = result.get("documents", [[]])[0] if isinstance(result, dict) else []
    ids = result.get("ids", [[]])[0] if isinstance(result, dict) else []
    distances = result.get("distances", [[]])[0] if isinstance(result, dict) else []
    metadatas = result.get("metadatas", [[]])[0] if isinstance(result, dict) else []
    payload = {
        "results": [
            {
                "id": ids[i] if i < len(ids) else None,
                "document": documents[i] if i < len(documents) else "",
                "distance": distances[i] if i < len(distances) else None,
                "memory_type": (
                    metadatas[i].get("memory_type")
                    if i < len(metadatas) and isinstance(metadatas[i], dict)
                    else None
                ),
            }
            for i in range(len(documents))
        ]
    }
    logger.info(
        "MEMORY SEARCH COMPLETE results=%d elapsed=%.3fs",
        len(payload["results"]),
        time.perf_counter() - started,
    )
    return payload


@router.post("/commands/add")
async def command_add(req: CommandAddRequest):
    started = time.perf_counter()
    command = req.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="command is required")

    try:
        quince_commands.add_one(command, is_temporary=req.is_temporary)
    except Exception as exc:
        logger.exception("COMMAND ADD FAILED command=%r", command)
        raise HTTPException(status_code=500, detail=f"command add failed: {exc}") from exc

    logger.info(
        "COMMAND ADD COMPLETE command=%r temporary=%s elapsed=%.3fs",
        command,
        req.is_temporary,
        time.perf_counter() - started,
    )
    return {"added": True, "command": command, "is_temporary": req.is_temporary}


@router.get("/commands")
async def command_list():
    try:
        items = list(quince_commands.get_all())
    except Exception as exc:
        logger.exception("COMMAND LIST FAILED")
        raise HTTPException(status_code=500, detail=f"command list failed: {exc}") from exc

    return {
        "commands": [
            {
                "command": item.get("command"),
                "is_temporary": bool(item.get("is_temporary", False)),
            }
            for item in items
            if item.get("command")
        ]
    }


@router.post("/commands/delete")
async def command_delete(req: CommandDeleteRequest):
    command = req.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="command is required")

    try:
        quince_commands.delete(command)
    except Exception as exc:
        logger.exception("COMMAND DELETE FAILED command=%r", command)
        raise HTTPException(status_code=500, detail=f"command delete failed: {exc}") from exc

    return {"deleted": True, "command": command}
