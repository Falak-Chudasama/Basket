import uuid
from typing import Optional, Union, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Response

from src.schemas.ChatSchema import ChatRequest
from src.services.embedding.embedder import create_embedding, batch_encode
from src.clients.llama_llm import (
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


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None


@llmRouter.post("/embeddings")
async def create_embeddings_endpoint(
    req: EmbeddingRequest,
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    try:
        if isinstance(req.input, str):
            vec = create_embedding(req.input)
            data = [{"object": "embedding", "index": 0, "embedding": vec}]
        elif isinstance(req.input, list):
            vecs = batch_encode(req.input)
            data = [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vecs)]
        else:
            raise HTTPException(status_code=400, detail="input must be string or list of strings", headers=headers)
        return {"object": "list", "data": data, "model": "jina-embeddings-v5-text-nano"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc), headers=headers)



def _prepare_headers(
    response: Response,
    application: Optional[str],
    request_id: Optional[str],
) -> dict[str, str]:
    headers = {}
    req_id = request_id or str(uuid.uuid4())
    headers["X-Request-ID"] = req_id
    if application:
        headers["X-Basket-Application"] = application
    for k, v in headers.items():
        response.headers[k] = v
    return headers


@llmRouter.post("/chat")
async def chat(
    req: ChatRequest,
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    try:
        return await _chat(
            req,
            application=x_basket_application,
            request_id=headers["X-Request-ID"],
            response=response,
        )
    except HTTPException as exc:
        exc.headers = exc.headers or {}
        for k, v in headers.items():
            exc.headers[k] = v
        raise exc

@llmRouter.get("/models")
async def get_models(
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    try:
        return await _get_models()
    except HTTPException as exc:
        exc.headers = exc.headers or {}
        for k, v in headers.items():
            exc.headers[k] = v
        raise exc

@llmRouter.post("/load")
async def load_model(
    model_id: str,
    response: Response,
    context_length: int | None = None,
    eval_batch_size: int | None = None,
    flash_attention: bool | None = None,
    num_experts: int | None = None,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    if not model_id:
        raise HTTPException(
            status_code=400,
            detail="model_id is required.",
            headers=headers,
        )
    try:
        return await _load_model(model_id=model_id)
    except HTTPException as exc:
        exc.headers = exc.headers or {}
        for k, v in headers.items():
            exc.headers[k] = v
        raise exc

@llmRouter.post("/unload")
async def unload_model(
    instance_id: str,
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    if not instance_id:
        raise HTTPException(
            status_code=400,
            detail="instance_id is required.",
            headers=headers,
        )
    try:
        return await _unload_model(instance_id)
    except HTTPException as exc:
        exc.headers = exc.headers or {}
        for k, v in headers.items():
            exc.headers[k] = v
        raise exc

@llmRouter.post("/unload-all")
async def unload_all_models(
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    headers = _prepare_headers(response, x_basket_application, x_request_id)
    try:
        return await _unload_all_models()
    except HTTPException as exc:
        exc.headers = exc.headers or {}
        for k, v in headers.items():
            exc.headers[k] = v
        raise exc