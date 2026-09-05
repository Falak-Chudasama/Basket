import struct
from typing import AsyncIterator
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

# ============================================================
# REALTIME TTS - RAW PCM STREAM
# ============================================================

# Pocket TTS currently streams 16-bit mono PCM inside a WAV
# container. Basket strips the WAV container and exposes the
# underlying PCM stream to the realtime pipeline.
#
# Current Pocket TTS model output is typically 24 kHz.
# The actual sample rate is read from the WAV header so the
# adapter does not blindly depend on that assumption.
# ============================================================


class _StreamingWAVParser:
    """
    Incrementally removes the WAV container from a streamed
    Pocket TTS response and yields raw PCM bytes.

    The parser waits until it has enough data to locate the
    RIFF/WAVE data chunk. Once the data chunk begins, every
    subsequent byte is treated as PCM audio.
    """

    def __init__(self):
        self._buffer = bytearray()
        self._audio_started = False
        self.sample_rate: int | None = None
        self.channels: int | None = None
        self.sample_width: int | None = None

    def feed(
        self,
        chunk: bytes,
    ) -> bytes:

        if not chunk:
            return b""

        if self._audio_started:
            return chunk

        self._buffer.extend(chunk)

        data_offset = self._find_data_offset()

        if data_offset is None:
            return b""

        audio = bytes(
            self._buffer[data_offset:]
        )

        self._buffer.clear()
        self._audio_started = True

        return audio

    def _find_data_offset(self) -> int | None:
        """
        Parse a RIFF/WAVE stream.

        Returns the byte offset where the 'data' chunk payload
        begins.
        """

        data = self._buffer

        if len(data) < 12:
            return None

        if data[0:4] != b"RIFF":
            raise ValueError(
                "Pocket TTS did not return a RIFF/WAVE stream."
            )

        if data[8:12] != b"WAVE":
            raise ValueError(
                "Pocket TTS returned an unsupported WAV container."
            )

        offset = 12

        while len(data) >= offset + 8:

            chunk_id = bytes(
                data[offset:offset + 4]
            )

            chunk_size = struct.unpack_from(
                "<I",
                data,
                offset + 4,
            )[0]

            chunk_data_start = offset + 8
            chunk_data_end = (
                chunk_data_start + chunk_size
            )

            # We do not have the complete chunk yet.
            if len(data) < chunk_data_end:
                return None

            # ------------------------------------------------
            # FORMAT CHUNK
            # ------------------------------------------------

            if chunk_id == b"fmt ":

                if chunk_size < 16:
                    raise ValueError(
                        "Invalid WAV fmt chunk."
                    )

                audio_format = struct.unpack_from(
                    "<H",
                    data,
                    chunk_data_start,
                )[0]

                self.channels = struct.unpack_from(
                    "<H",
                    data,
                    chunk_data_start + 2,
                )[0]

                self.sample_rate = struct.unpack_from(
                    "<I",
                    data,
                    chunk_data_start + 4,
                )[0]

                self.sample_width = (
                    struct.unpack_from(
                        "<H",
                        data,
                        chunk_data_start + 14,
                    )[0]
                    // 8
                )

                if audio_format != 1:
                    raise ValueError(
                        "Pocket TTS returned non-PCM WAV audio."
                    )

                if self.channels != 1:
                    raise ValueError(
                        "Pocket TTS realtime audio must be mono."
                    )

                if self.sample_width != 2:
                    raise ValueError(
                        "Pocket TTS realtime audio must be 16-bit PCM."
                    )

            # ------------------------------------------------
            # DATA CHUNK
            # ------------------------------------------------

            elif chunk_id == b"data":

                if (
                    self.sample_rate is None
                    or self.channels is None
                    or self.sample_width is None
                ):
                    raise ValueError(
                        "WAV data chunk appeared before fmt chunk."
                    )

                return chunk_data_start

            # RIFF chunks are word aligned.
            offset = chunk_data_end

            if offset % 2:
                offset += 1

        return None


async def stream_tts_pcm(
    *,
    text: str,
    voice: str = "jane",
    temperature: float = 0.5,
) -> AsyncIterator[bytes]:
    """
    Stream Pocket TTS as raw PCM16 mono audio.

    The upstream Pocket TTS server currently sends a streaming
    WAV container. Basket removes the WAV container and yields
    only its PCM payload.

    Audio format:

        PCM
        signed 16-bit
        mono
        sample rate read from WAV header
    """

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    form_data = {
        "text": text,
        "voice_url": voice,
        "temperature": str(
            temperature
        ),
    }

    parser = _StreamingWAVParser()

    try:

        async with httpx.AsyncClient(
            timeout=_timeout()
        ) as client:

            async with client.stream(
                "POST",
                POCKET_TTS_TTS_URL,
                data=form_data,
                headers={
                    "Accept": "audio/wav",
                },
            ) as response:

                response.raise_for_status()

                async for chunk in response.aiter_bytes():

                    if not chunk:
                        continue

                    try:

                        pcm = parser.feed(
                            chunk
                        )

                    except ValueError as exc:

                        raise HTTPException(
                            status_code=502,
                            detail=(
                                "Invalid Pocket TTS "
                                f"stream: {exc}"
                            ),
                        ) from exc

                    if pcm:
                        yield pcm

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