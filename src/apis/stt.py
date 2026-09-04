from fastapi import APIRouter, File, Form, UploadFile

from src.clients.llama_stt import _transcribe


sttRouter = APIRouter(
    prefix="/stt",
    tags=["STT"],
)

@sttRouter.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    prompt: str | None = Form(default=None),
):
    return await _transcribe(
        file=file,
        prompt=prompt,
    )