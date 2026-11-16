import uuid
import json
from typing import Optional, Union, List, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Header, Response

from src.schemas.ChatSchema import ChatRequest, Message
from src.services.embedding.embedder import create_embedding, batch_encode
from src.services.context.tiered_context import tiered_context
from src.clients.llama_llm import (
    _chat,
    _get_models,
    _unload_all_models,
    _unload_model,
    _load_model,
    _chat_completion_non_streaming,
    _chat_completion_streaming,
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


class ContextItem(BaseModel):
    content: str = Field(description="Context reading, document snippet, or fact.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata describing the context item.")


class CompletionRequest(BaseModel):
    prompt: Optional[str] = Field(default=None, description="User prompt text.")
    text: Optional[str] = Field(default=None, description="Alias for prompt.")
    application: str = Field(default="basket", description="Calling fruit application namespace.")
    system_prompt: Optional[str] = Field(default=None, description="Optional system instructions.")
    grammar: Optional[str] = Field(default=None, description="Optional GBNF grammar or JSON schema constraint.")
    context: Optional[List[ContextItem]] = Field(default=None, description="Optional list of inline context items [{content, metadata}].")
    chat_id: Optional[str] = Field(default=None, description="Optional chat ID if querying conversation context.")
    retrieve_chat: bool = Field(default=False, description="Toggle whether to retrieve volatile chat context.")
    retrieve_notes: bool = Field(default=False, description="Toggle whether to retrieve persistent notes context.")
    top_k_chat: int = Field(default=4, description="Maximum chat chunks to retrieve if retrieve_chat is true.")
    top_k_notes: int = Field(default=3, description="Maximum note chunks to retrieve if retrieve_notes is true.")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature.")
    top_p: Optional[float] = Field(default=1.0, description="Top-p nucleus sampling.")
    max_tokens: Optional[int] = Field(default=None, description="Maximum output tokens.")
    stop: Optional[Any] = Field(default=None, description="Stop sequence(s).")
    seed: Optional[int] = Field(default=None, description="Random seed.")
    model: Optional[str] = Field(default=None, description="Target model identifier.")
    stream: bool = Field(default=False, description="Whether to stream response via Server-Sent Events.")


@llmRouter.post("/completion")
async def completion_endpoint(
    req: CompletionRequest,
    response: Response,
    x_basket_application: Optional[str] = Header(None, alias="X-Basket-Application"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
):
    """
    Fast LLM completion endpoint for quick extraction, classification, or generation.
    Optionally stateful (via retrieve_chat / retrieve_notes) or completely stateless.
    Accepts inline context: [{content, metadata}], system_prompt, and GBNF grammar.
    """
    app_name = x_basket_application or req.application or "basket"
    headers = _prepare_headers(response, app_name, x_request_id)
    prompt_text = req.prompt or req.text or ""
    if not prompt_text.strip():
        raise HTTPException(status_code=400, detail="Either 'prompt' or 'text' must be provided.", headers=headers)

    system_sections: list[str] = []

    # 1. Base system prompt
    if req.system_prompt and req.system_prompt.strip():
        system_sections.append(req.system_prompt.strip())

    # 2. Tier 3: Stitched Commands for this fruit
    commands_block = tiered_context.get_formatted_commands(app_name)
    if commands_block:
        system_sections.append(commands_block)

    # 3. Dynamic Inline Context ([{content, metadata}])
    if req.context:
        context_data = [{"content": item.content, "metadata": item.metadata} for item in req.context]
        context_json = json.dumps(context_data, indent=2)
        system_sections.append(f"<INLINE_CONTEXT>\n{context_json}\n</INLINE_CONTEXT>")

    # 4. Optional Retrieval (Chat / Notes)
    if req.retrieve_chat or req.retrieve_notes:
        tiered_res = await tiered_context.retrieve_tiered_context(
            query=prompt_text,
            application=app_name,
            chat_id=req.chat_id,
            retrieve_chat=req.retrieve_chat,
            retrieve_notes=req.retrieve_notes,
            top_k_chat=req.top_k_chat,
            top_k_notes=req.top_k_notes,
        )
        chat_chunks = tiered_res.get("chat_chunks", [])
        notes_chunks = tiered_res.get("notes_chunks", [])

        if chat_chunks:
            c_text = "\n".join(f"- ({c['metadata'].get('role', 'user')}): {c['document']}" for c in chat_chunks)
            system_sections.append(f"<CONVERSATION_CONTEXT>\n{c_text}\n</CONVERSATION_CONTEXT>")

        if notes_chunks:
            n_text = "\n".join(f"- {n['document']}" for n in notes_chunks)
            system_sections.append(f"<RELEVANT_NOTES>\n{n_text}\n</RELEVANT_NOTES>")

    # Assemble messages
    messages: list[Message] = []
    if system_sections:
        messages.append(Message(role="system", content="\n\n".join(system_sections)))
    messages.append(Message(role="user", content=prompt_text))

    chat_req = ChatRequest(
        messages=messages,
        stream=req.stream,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
        stop=req.stop,
        seed=req.seed,
        model=req.model,
        grammar=req.grammar,
    )

    if req.stream:
        return await _chat_completion_streaming(
            chat_req,
            application=app_name,
            request_id=headers["X-Request-ID"],
        )

    raw_res = await _chat_completion_non_streaming(chat_req)
    content = ""
    model_name = req.model
    usage = {}
    if isinstance(raw_res, dict):
        if "choices" in raw_res and raw_res["choices"]:
            content = raw_res["choices"][0].get("message", {}).get("content", "")
        model_name = raw_res.get("model", req.model)
        usage = raw_res.get("usage", {})
    elif isinstance(raw_res, str):
        content = raw_res

    return {
        "status": "success",
        "content": content,
        "application": app_name,
        "model": model_name,
        "usage": usage,
        "raw": raw_res,
    }


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