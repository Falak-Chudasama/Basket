from fastapi import FastAPI

from src.apis.llm import llmRouter


app = FastAPI(title="Basket")

app.include_router(llmRouter)

@app.get("/")
def hello():
    return {"message": "Basket is Serving!"}