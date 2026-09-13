from __future__ import annotations
import struct
from typing import AsyncIterator
import httpx
from fastapi import HTTPException
from fastapi.responses import Response, StreamingResponse

from src.core.configs import TTS_HOST, TTS_PORT
from src.schemas.TTSSchema import TTSRequest

# ============================================================
# POCKET TTS CONFIGURATION
# ============================================================

POCKET_TTS_BASE_URL = f"http://{TTS_HOST}:{TTS_PORT}"
POCKET_TTS_TTS_URL = f"{POCKET_TTS_BASE_URL}/tts"
POCKET_TTS_HEALTH_URL = f"{POCKET_TTS_BASE_URL}/health"


# ============================================================
# HTTP CONFIGURATION
# ============================================================

def _timeout():
    return httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=30.0)


def _translate_http_error(exc: Exception) -> HTTPException:
    """Map an httpx transport/status error to the HTTPException Basket
    raises for it. Callers still `raise ... from exc` for a clean traceback."""
    if isinstance(exc, httpx.HTTPStatusError):
        return HTTPException(
            status_code=502,
            detail=f"Pocket TTS returned {exc.response.status_code}: {exc.response.text}",
        )
    return HTTPException(status_code=502, detail=f"Could not connect to Pocket TTS: {exc}")


# ============================================================
# HEALTH
# ============================================================

async def _health():
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.get(POCKET_TTS_HEALTH_URL)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Pocket TTS health check failed: {exc.response.status_code}") from exc

    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not connect to Pocket TTS: {exc}") from exc


# ============================================================
# MODEL
# ============================================================

async def _load_model():
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.get(POCKET_TTS_HEALTH_URL)
        response.raise_for_status()

        return {"status": "ready", "backend": "pocket-tts", "host": TTS_HOST, "port": TTS_PORT}

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"Pocket TTS service is not healthy: {exc.response.status_code}"
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Pocket TTS service is not running: {exc}") from exc


# ============================================================
# MODEL STATUS
# ============================================================


async def _model_status():
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.get(POCKET_TTS_HEALTH_URL)
        response.raise_for_status()

        return {"available": True, "status": "ready", "backend": "pocket-tts"}

    except httpx.HTTPStatusError as exc:
        return {
            "available": False,
            "status": "unhealthy",
            "backend": "pocket-tts",
            "error": f"HTTP {exc.response.status_code}",
        }

    except httpx.RequestError as exc:
        return {"available": False, "status": "offline", "backend": "pocket-tts", "error": str(exc)}


# ============================================================
# TEXT TO SPEECH
# ============================================================


async def _synthesize(request: TTSRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    form_data = {"text": text, "voice_url": request.voice, "temperature": str(request.temperature)}

    # ----------------------------------------------------------------
    # STREAMING
    # ----------------------------------------------------------------
    if request.stream:
        async def audio_stream():
            try:
                async with httpx.AsyncClient(timeout=_timeout()) as client:
                    async with client.stream(
                        "POST", POCKET_TTS_TTS_URL, data=form_data, headers={"Accept": "audio/wav"}
                    ) as response:
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            if chunk:
                                yield chunk

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                raise _translate_http_error(exc) from exc

        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )

    # ----------------------------------------------------------------
    # NON-STREAMING
    # ----------------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.post(POCKET_TTS_TTS_URL, data=form_data, headers={"Accept": "audio/wav"})
        response.raise_for_status()

        return Response(
            content=response.content,
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )

    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise _translate_http_error(exc) from exc


# ============================================================
# REALTIME TTS - STREAMING WAV -> RAW PCM
# ============================================================


class _StreamingWAVParser:
    def __init__(self):
        self._buffer = bytearray()
        self._header_parsed = False
        self._audio_started = False

        self.sample_rate: int | None = None
        self.channels: int | None = None
        self.sample_width: int | None = None

        self._offset = 12

    def feed(self, chunk: bytes) -> bytes:
        if not chunk:
            return b""

        if self._audio_started:
            return bytes(chunk)

        self._buffer.extend(chunk)
        audio = self._try_parse_header()
        return audio if audio is not None else b""

    def _try_parse_header(self) -> bytes | None:
        data = self._buffer

        # ------------------------------------------------------------
        # RIFF header
        # ------------------------------------------------------------
        if len(data) < 12:
            return None
        if data[0:4] != b"RIFF":
            raise ValueError("Pocket TTS did not return a RIFF stream.")
        if data[8:12] != b"WAVE":
            raise ValueError("Pocket TTS returned a non-WAVE RIFF stream.")

        # ------------------------------------------------------------
        # Walk RIFF chunks. We only require the complete header of each
        # chunk. We DO NOT wait for the complete data payload.
        # ------------------------------------------------------------
        offset = self._offset

        while True:
            # Need chunk id + chunk size.
            if len(data) < offset + 8:
                return None

            chunk_id = bytes(data[offset:offset + 4])
            chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
            chunk_data_start = offset + 8

            # --------------------------------------------------------
            # FORMAT CHUNK
            # --------------------------------------------------------
            if chunk_id == b"fmt ":
                # Standard PCM fmt chunk requires 16 bytes.
                if chunk_size < 16:
                    raise ValueError("Invalid WAV fmt chunk.")
                if len(data) < chunk_data_start + 16:
                    return None

                audio_format = struct.unpack_from("<H", data, chunk_data_start)[0]
                self.channels = struct.unpack_from("<H", data, chunk_data_start + 2)[0]
                self.sample_rate = struct.unpack_from("<I", data, chunk_data_start + 4)[0]
                bits_per_sample = struct.unpack_from("<H", data, chunk_data_start + 14)[0]
                self.sample_width = bits_per_sample // 8

                if audio_format != 1:
                    raise ValueError("Pocket TTS returned non-PCM WAV audio.")
                if self.channels != 1:
                    raise ValueError("Pocket TTS realtime audio must be mono.")
                if self.sample_width != 2:
                    raise ValueError("Pocket TTS realtime audio must be 16-bit PCM.")

                # Advance to next RIFF chunk.
                offset = chunk_data_start + chunk_size
                if offset % 2:
                    offset += 1
                self._offset = offset
                continue

            # --------------------------------------------------------
            # DATA CHUNK
            # --------------------------------------------------------
            if chunk_id == b"data":
                if self.sample_rate is None or self.channels is None or self.sample_width is None:
                    raise ValueError("WAV data chunk appeared before fmt chunk.")

                # We have found the audio payload. CRITICAL: do NOT check
                # whether the entire declared data chunk has arrived.
                available = bytes(data[chunk_data_start:])

                self._buffer.clear()
                self._audio_started = True
                self._header_parsed = True
                return available

            # --------------------------------------------------------
            # OTHER RIFF CHUNKS
            # --------------------------------------------------------
            next_offset = chunk_data_start + chunk_size
            if next_offset % 2:
                next_offset += 1

            # We need the complete unknown chunk before we can safely skip
            # over it.
            if len(data) < next_offset:
                return None

            offset = next_offset
            self._offset = offset


# ============================================================
# STREAM RAW PCM TO REALTIME PIPELINE
# ============================================================


async def stream_tts_pcm(*, text: str, voice: str = "jane", temperature: float = 0.5) -> AsyncIterator[bytes]:
    """
    Stream Pocket TTS as raw PCM16 mono audio.

    Upstream:   Pocket TTS -> WAV stream
    Basket:     WAV container -> raw PCM
    Downstream: raw PCM -> Quince WebSocket
    """
    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    form_data = {"text": text, "voice_url": voice, "temperature": str(temperature)}
    parser = _StreamingWAVParser()

    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            async with client.stream(
                "POST", POCKET_TTS_TTS_URL, data=form_data, headers={"Accept": "audio/wav"}
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_bytes():
                    if not chunk:
                        continue

                    try:
                        pcm = parser.feed(chunk)
                    except ValueError as exc:
                        raise HTTPException(status_code=502, detail=f"Invalid Pocket TTS stream: {exc}") from exc

                    if pcm:
                        yield bytes(pcm)

    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise _translate_http_error(exc) from exc