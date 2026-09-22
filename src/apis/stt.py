from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.clients.nemotron_stt import _transcribe


sttRouter = APIRouter(prefix="/stt", tags=["STT"])


@sttRouter.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    prompt: str | None = Form(None),
    stream: bool = Form(False),
):
    if stream:
        raise HTTPException(
            status_code=400,
            detail="Realtime STT streaming requires the WebSocket endpoint /ws.",
        )

    return await _transcribe(file=file, prompt=prompt)