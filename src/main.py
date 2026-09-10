from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter
from src.apis.mcp import router as mcpRouter
from src.socket.ws import router as wsRouter
from src.jobs.jobs import run_jobs
from src.core.logging_setup import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = __import__("logging").getLogger("basket.lifecycle")
    logger.info("BASKET STARTUP: initializing jobs")
    await run_jobs()
    logger.info("BASKET STARTUP: jobs complete")
    yield

app = FastAPI(
    title="Basket",
    lifespan=lifespan
)

app.include_router(llmRouter)
app.include_router(sttRouter)
app.include_router(ttsRouter)
app.include_router(mcpRouter)
app.include_router(wsRouter)


@app.get("/")
def hello():
    return {"message": "Basket is Serving!"}