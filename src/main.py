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
    # return {"message": "Basket is Serving Fruits!"}
    tools = await quince_mcp.get_tools()

    parsed_tools = []

    print('\n\n')
    for tool in tools:
        print(f"name: {tool.name}")
        print(f"description: {tool.description}")
        print(f"input_schema: {tool.input_schema}")
        parsed_tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        })
        print('\n')
    print('\n')


    return f"{parsed_tools}"