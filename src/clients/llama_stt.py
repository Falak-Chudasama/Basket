import httpx

from fastapi import HTTPException, UploadFile

from src.core.configs import (
    DEFAULT_STT_MODEL,
    STT_HOST,
    STT_PORT,
)


# ============================================================
# LLAMA.CPP STT CONFIGURATION
# ============================================================

STT_BASE_URL = (
    f"http://{STT_HOST}:{STT_PORT}"
)

STT_TRANSCRIBE_URL = (
    f"{STT_BASE_URL}/v1/audio/transcriptions"
)

STT_HEALTH_URL = (
    f"{STT_BASE_URL}/health"
)


# ============================================================
# HTTP CONFIGURATION
# ============================================================

def _timeout():
    return httpx.Timeout(
        connect=10.0,
        read=120.0,
        write=120.0,
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
                STT_HEALTH_URL
            )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "STT health check failed: "
                f"{exc.response.status_code}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to STT service: "
                f"{exc}"
            ),
        )


# ============================================================
# MODEL
# ============================================================

async def _load_model():
    """
    llama.cpp loads the STT model when its server starts.

    Basket does not load the model itself. This function
    verifies that the llama.cpp STT service is available.
    """

    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.get(
                STT_HEALTH_URL
            )

        response.raise_for_status()

        return {
            "status": "ready",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
            "host": STT_HOST,
            "port": STT_PORT,
        }

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "STT service is not healthy: "
                f"{exc.response.status_code}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "STT service is not running: "
                f"{exc}"
            ),
        )


async def _model_status():
    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.get(
                STT_HEALTH_URL
            )

        response.raise_for_status()

        return {
            "available": True,
            "status": "ready",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
        }

    except httpx.HTTPStatusError as exc:

        return {
            "available": False,
            "status": "unhealthy",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
            "error": (
                f"HTTP {exc.response.status_code}"
            ),
        }

    except httpx.RequestError as exc:

        return {
            "available": False,
            "status": "offline",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
            "error": str(exc),
        }


# ============================================================
# TRANSCRIPTION
# ============================================================

async def _transcribe(
    file: UploadFile,
    prompt: str | None = None,
):
    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty.",
        )

    files = {
        "file": (
            file.filename or "audio.wav",
            audio_bytes,
            file.content_type or "application/octet-stream",
        )
    }

    data = {
        "model": DEFAULT_STT_MODEL,
        "language": "en",
        "response_format": "json",
    }

    if prompt:
        data["prompt"] = prompt

    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            response = await client.post(
                STT_TRANSCRIBE_URL,
                files=files,
                data=data,
            )

        response.raise_for_status()

        return response.json()

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "STT backend returned "
                f"{exc.response.status_code}: "
                f"{exc.response.text}"
            ),
        )

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to STT backend: "
                f"{exc}"
            ),
        )