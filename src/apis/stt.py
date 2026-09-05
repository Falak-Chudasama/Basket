from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.clients.llama_stt import _transcribe


sttRouter = APIRouter(
    prefix="/stt",
    tags=["STT"],
)


@sttRouter.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    prompt: str | None = Form(default=None),
    stream: bool = Form(default=False),
):
    """
    Batch STT endpoint.

    Live microphone streaming is exposed separately through the WebSocket
    endpoint /stt/stream. The `stream` field exists here for API/schema
    consistency, but a multipart upload cannot become a true realtime
    microphone stream after the file has already been received.
    """

    if stream:
        raise HTTPException(
            status_code=400,
            detail=(
                "Realtime STT streaming requires the WebSocket "
                "endpoint /stt/stream."
            ),
        )

    return await _transcribe(
        file=file,
        prompt=prompt,
    )
