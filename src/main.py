from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter
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
app.include_router(wsRouter)


@app.get("/")
def hello():
    return {"message": "Basket is Serving!"}