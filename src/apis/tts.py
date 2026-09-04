from fastapi import APIRouter, HTTPException

from src.schemas.TTSSchema import TTSRequest
from src.clients.pockettts import (
    _synthesize
)

ttsRouter = APIRouter(
    prefix="/tts",
    tags=["TTS"],
)

@ttsRouter.post("/synthesize")
async def synthesize(req: TTSRequest):
    return await _synthesize(req)