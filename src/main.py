from fastapi import FastAPI

from src.apis.llm import llmRouter
from src.apis.stt import sttRouter
from src.apis.tts import ttsRouter


app = FastAPI(title="Basket")

app.include_router(llmRouter)
app.include_router(sttRouter)
app.include_router(ttsRouter)

@app.get("/")
def hello():
    return {"message": "Basket is Serving!"}