import io
import re
import wave
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
# STREAMING CONFIGURATION
# ============================================================

STREAM_SAMPLE_RATE = 16_000
STREAM_SAMPLE_WIDTH = 2
STREAM_WINDOW_SECONDS = 8.0
STREAM_MIN_AUDIO_SECONDS = 1.5
STREAM_PARTIAL_INTERVAL_SECONDS = 0.75


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

def _pcm16_to_wav(
    pcm_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> bytes:
    """Wrap raw mono PCM16 audio in an in-memory WAV container."""

    if not pcm_bytes:
        raise ValueError("PCM audio cannot be empty.")

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(STREAM_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    return buffer.getvalue()


def _clean_transcription(text: str) -> str:
    """
    Normalize llama.cpp/Qwen3-ASR output before exposing it through Basket.

    Some llama.cpp builds have returned Qwen control markers such as:
    "language English<asr_text>...". Basket should expose only the
    actual transcription to its clients.
    """

    text = (text or "").strip()

    if not text:
        return ""

    # Remove everything through the ASR marker when present.
    marker_match = re.search(r"<asr_text>", text, flags=re.IGNORECASE)
    if marker_match:
        text = text[marker_match.end():].strip()

    # Fallback for language-prefix output if the marker is absent.
    text = re.sub(
        r"^language\s+[A-Za-z][A-Za-z ._-]*\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    return text


def _extract_text(payload) -> str:
    """Extract transcript text from llama.cpp's JSON response."""

    if isinstance(payload, dict):
        value = payload.get("text")
        if isinstance(value, str):
            return _clean_transcription(value)

        # Be tolerant of compatible OpenAI-style payloads.
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                text = first.get("text")
                if isinstance(text, str):
                    return _clean_transcription(text)

    if isinstance(payload, str):
        return _clean_transcription(payload)

    return ""


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
# TRANSCRIPTION HELPERS
# ============================================================


async def _transcribe_bytes(
    client: httpx.AsyncClient,
    audio_bytes: bytes,
    *,
    filename: str = "audio.wav",
    content_type: str = "audio/wav",
    prompt: str | None = None,
) -> dict:
    """Transcribe an in-memory audio payload through llama.cpp."""

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Audio data is empty.",
        )

    files = {
        "file": (
            filename,
            audio_bytes,
            content_type,
        )
    }

    data = {
    "model": DEFAULT_STT_MODEL,
    "language": "en",
    "response_format": "json",

        "prompt": (
            "Transcribe the speech in English only. "
            "Do not output Chinese, Japanese, Korean, Arabic, "
            "Hindi, Cyrillic, or any other non-English language."
        ),
    }

    if prompt:
        data["prompt"] = (
            "Transcribe the speech in English only. "
            "Do not output any non-English language. "
            + prompt
        )

    try:
        response = await client.post(
            STT_TRANSCRIBE_URL,
            files=files,
            data=data,
        )

        response.raise_for_status()

        payload = response.json()
        text = _extract_text(payload)

        # Preserve the backend response shape while ensuring the returned
        # transcript is clean for Basket consumers.
        if isinstance(payload, dict):
            result = dict(payload)
            result["text"] = text
            return result

        return {"text": text}

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

    try:
        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:
            return await _transcribe_bytes(
                client,
                audio_bytes,
                filename=file.filename or "audio.wav",
                content_type=file.content_type or "application/octet-stream",
                prompt=prompt,
            )

    except HTTPException:
        raise


# ============================================================
# STREAMING AUDIO HELPERS
# ============================================================


def stream_audio_duration_seconds(
    audio_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> float:
    """Return the duration of mono PCM16 bytes."""

    bytes_per_second = sample_rate * STREAM_SAMPLE_WIDTH
    if bytes_per_second <= 0:
        return 0.0

    return len(audio_bytes) / bytes_per_second


def make_stream_wav(
    pcm_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> bytes:
    """Public helper used by Basket's WebSocket STT transport."""

    return _pcm16_to_wav(
        pcm_bytes,
        sample_rate=sample_rate,
    )


async def _stream_transcribe_window(
    client: httpx.AsyncClient,
    pcm_bytes: bytes,
    *,
    prompt: str | None = None,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> dict:
    """
    Transcribe one rolling PCM16 window.

    This is intentionally stateless: llama.cpp receives a fresh WAV for
    each partial update. The WebSocket layer owns the rolling context.
    """

    wav_bytes = _pcm16_to_wav(
        pcm_bytes,
        sample_rate=sample_rate,
    )

    return await _transcribe_bytes(
        client,
        wav_bytes,
        filename="stream.wav",
        content_type="audio/wav",
        prompt=prompt,
    )
