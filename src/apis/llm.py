from fastapi import APIRouter, HTTPException

from src.schemas.ChatSchema import ChatRequest
from src.clients.lm_studio import (
    _chat,
    _get_models,
    _unload_all_models,
    _unload_model,
    _load_model,
)

llmRouter = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


# ============================================================
# CHAT
# ============================================================

@llmRouter.post("/chat")
async def chat(req: ChatRequest):
    return await _chat(req)


# ============================================================
# GET AVAILABLE MODELS
# ============================================================

@llmRouter.get("/models")
async def get_models():
    return await _get_models()


# ============================================================
# LOAD MODEL
# ============================================================

@llmRouter.post("/load")
async def load_model(
    model_id: str,
    context_length: int | None = None,
    eval_batch_size: int | None = None,
    flash_attention: bool | None = None,
    num_experts: int | None = None,
):
    if not model_id:
        raise HTTPException(
            status_code=400,
            detail="model_id is required.",
        )

    return await _load_model(
        model_id=model_id,
        context_length=context_length,
        eval_batch_size=eval_batch_size,
        flash_attention=flash_attention,
        num_experts=num_experts,
    )


# ============================================================
# UNLOAD MODEL
# ============================================================

@llmRouter.post("/unload")
async def unload_model(
    instance_id: str,
):
    if not instance_id:
        raise HTTPException(
            status_code=400,
            detail="instance_id is required.",
        )

    return await _unload_model(
        instance_id
    )


# ============================================================
# UNLOAD ALL MODELS
# ============================================================

@llmRouter.post("/unload-all")
async def unload_all_models():
    return await _unload_all_models()