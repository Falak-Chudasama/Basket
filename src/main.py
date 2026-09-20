from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter
from src.apis.context import context_router
from src.socket.ws import router as wsRouter
from src.jobs.jobs import run_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_jobs()
    yield

app = FastAPI(
    title="Basket",
    lifespan=lifespan
)

app.include_router(llmRouter)
app.include_router(sttRouter)
app.include_router(ttsRouter)
app.include_router(context_router)
app.include_router(wsRouter)


from src.clients.quince_mcp import quince_mcp

@app.get("/")
async def hello():
    tools = await quince_mcp.tool_call("root")
    return {"tools": tools}