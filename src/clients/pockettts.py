import httpx
from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from src.core.configs import (
    TTS_HOST,
    TTS_PORT,
)
from src.schemas.TTSSchema import TTSRequest


# ============================================================
# POCKET TTS CONFIGURATION
# ============================================================

POCKET_TTS_BASE_URL = (
    f"http://{TTS_HOST}:{TTS_PORT}"
)

POCKET_TTS_TTS_URL = (
    f"{POCKET_TTS_BASE_URL}/tts"
)

POCKET_TTS_HEALTH_URL = (
    f"{POCKET_TTS_BASE_URL}/health"
)


# ============================================================
# HTTP CONFIGURATION
# ============================================================

def _timeout():
    return httpx.Timeout(
        connect=10.0,
        read=120.0,
        write=30.0,
        pool=30.0,
    )


# ============================================================
# UTIL
# ============================================================

async def _health():
    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.get(
                POCKET_TTS_HEALTH_URL
            )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Pocket TTS health check failed: "
                f"{exc.response.status_code}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to Pocket TTS: "
                f"{exc}"
            ),
        )


# ============================================================
# MODEL
# ============================================================

async def _load_model():
    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.get(
                POCKET_TTS_HEALTH_URL
            )

        response.raise_for_status()

        return {
            "status": "ready",
            "backend": "pocket-tts",
            "host": TTS_HOST,
            "port": TTS_PORT,
        }

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Pocket TTS service is not healthy: "
                f"{exc.response.status_code}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Pocket TTS service is not running: "
                f"{exc}"
            ),
        )


async def _model_status():
    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.get(
                POCKET_TTS_HEALTH_URL
            )

        response.raise_for_status()

        return {
            "available": True,
            "status": "ready",
            "backend": "pocket-tts",
        }

    except httpx.HTTPStatusError as exc:

        return {
            "available": False,
            "status": "unhealthy",
            "backend": "pocket-tts",
            "error": (
                f"HTTP {exc.response.status_code}"
            ),
        }

    except httpx.RequestError as exc:

        return {
            "available": False,
            "status": "offline",
            "backend": "pocket-tts",
            "error": str(exc),
        }

# ============================================================
# TEXT TO SPEECH
# ============================================================

async def _synthesize(request: TTSRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    form_data = {
        "text": text,
        "voice_url": request.voice,
        "temperature": str(request.temperature),
    }

    if request.stream:

        async def audio_stream():
            try:
                async with httpx.AsyncClient(
                    timeout=_timeout()
                ) as client:

                    async with client.stream(
                        "POST",
                        POCKET_TTS_TTS_URL,
                        data=form_data,
                    ) as response:

                        response.raise_for_status()

                        async for chunk in response.aiter_bytes():
                            if chunk:
                                yield chunk

            except httpx.HTTPStatusError as exc:

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Pocket TTS returned "
                        f"{exc.response.status_code}: "
                        f"{exc.response.text}"
                    ),
                )

            except httpx.RequestError as exc:

                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Could not connect to Pocket TTS: "
                        f"{exc}"
                    ),
                )

        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": (
                    'inline; filename="speech.wav"'
                )
            },
        )

    # --------------------------------------------------------
    # NON-STREAMING
    # --------------------------------------------------------

    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.post(
                POCKET_TTS_TTS_URL,
                data=form_data,
            )

        response.raise_for_status()

        return Response(
            content=response.content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": (
                    'inline; filename="speech.wav"'
                )
            },
        )

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Pocket TTS returned "
                f"{exc.response.status_code}: "
                f"{exc.response.text}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to Pocket TTS: "
                f"{exc}"
            ),
        )