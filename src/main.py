from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter
from src.apis.context import context_router
from src.apis.chat import chatRouter
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:10020",
        "http://localhost:10020",
        "http://127.0.0.1:10010",
        "http://localhost:10010",
        "http://basket.jam",
        "https://basket.jam",
        "http://api.basket.jam",
        "https://api.basket.jam",
        "http://plum.jam",
        "https://plum.jam",
        "http://api.plum.jam",
        "https://api.plum.jam",
        "http://kiwi.jam",
        "https://kiwi.jam",
        "http://api.kiwi.jam",
        "https://api.kiwi.jam",
        "http://banana.jam",
        "https://banana.jam",
        "http://api.banana.jam",
        "https://api.banana.jam",
        "http://quince.jam",
        "https://quince.jam",
        "http://api.quince.jam",
        "https://api.quince.jam",
        "http://lemon.jam",
        "https://lemon.jam",
        "http://api.lemon.jam",
        "https://api.lemon.jam",
        "http://cherry.jam",
        "https://cherry.jam",
        "http://api.cherry.jam",
        "https://api.cherry.jam",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llmRouter)
app.include_router(sttRouter)
app.include_router(ttsRouter)
app.include_router(context_router)
app.include_router(chatRouter)
app.include_router(wsRouter)

# TODO: Remove this and keep "Serving Fruits!"
from src.clients.quince_mcp import quince_mcp

@app.get("/")
async def hello():
    tools = await quince_mcp.tool_call("root")
    return {"tools": tools}