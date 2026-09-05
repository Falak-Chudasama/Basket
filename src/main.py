from fastapi import FastAPI

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter
from src.socket.ws import router as wsRouter


app = FastAPI(title="Basket")

app.include_router(llmRouter)
app.include_router(sttRouter)
app.include_router(ttsRouter)
app.include_router(wsRouter)


@app.get("/")
def hello():
    return {"message": "Basket is Serving!"}