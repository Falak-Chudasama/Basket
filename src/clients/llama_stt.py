from __future__ import annotations

import asyncio
import io
import logging
import re
import time
import wave

import httpx
from fastapi import HTTPException, UploadFile

from src.core.configs import DEFAULT_STT_MODEL, STT_HOST, STT_PORT

logger = logging.getLogger(__name__)


STT_BASE_URL = f"http://{STT_HOST}:{STT_PORT}"
STT_TRANSCRIBE_URL = f"{STT_BASE_URL}/v1/audio/transcriptions"
STT_HEALTH_URL = f"{STT_BASE_URL}/health"

STREAM_SAMPLE_RATE = 16_000
STREAM_SAMPLE_WIDTH = 2
STREAM_WINDOW_SECONDS = 8.0
STREAM_MIN_AUDIO_SECONDS = 1.5
STREAM_PARTIAL_INTERVAL_SECONDS = 0.75


def _timeout():
    return httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=30.0)


def _pcm16_to_wav(pcm_bytes: bytes, sample_rate: int = STREAM_SAMPLE_RATE) -> bytes:
    if not pcm_bytes:
        raise ValueError("PCM audio cannot be empty.")

    if len(pcm_bytes) % STREAM_SAMPLE_WIDTH != 0:
        # Never silently lose a sample. A malformed trailing byte is better
        # treated as an explicit error than as an accidental time shift.
        raise ValueError("PCM16 audio has an odd byte length.")

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(STREAM_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    return buffer.getvalue()


def _clean_transcription(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    # Qwen/llama.cpp integrations can expose the transcript after an
    # <asr_text> marker. Keep everything after that marker.
    marker_match = re.search(r"<asr_text>", text, flags=re.IGNORECASE)
    if marker_match:
        text = text[marker_match.end():].strip()

    # Remove an optional language prefix only when it appears at the start.
    text = re.sub(
        r"^language\s+(?:english|en)\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    return text


def _extract_text(payload) -> str:
    if isinstance(payload, dict):
        value = payload.get("text")
        if isinstance(value, str):
            return _clean_transcription(value)

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                text = first.get("text")
                if isinstance(text, str):
                    return _clean_transcription(text)

                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return _clean_transcription(content)

    if isinstance(payload, str):
        return _clean_transcription(payload)

    return ""


async def _health():
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.get(STT_HEALTH_URL)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"STT health check failed: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to STT service: {exc}",
        ) from exc


async def _load_model():
    health = await _health()
    return {
        "status": "ready",
        "backend": "llama.cpp",
        "model": DEFAULT_STT_MODEL,
        "host": STT_HOST,
        "port": STT_PORT,
        "health": health,
    }


async def _model_status():
    try:
        await _health()
        return {
            "available": True,
            "status": "ready",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
        }
    except HTTPException as exc:
        return {
            "available": False,
            "status": "offline",
            "backend": "llama.cpp",
            "model": DEFAULT_STT_MODEL,
            "error": exc.detail,
        }


async def _transcribe_bytes(
    client: httpx.AsyncClient,
    audio_bytes: bytes,
    *,
    filename: str = "audio.wav",
    content_type: str = "audio/wav",
    prompt: str | None = None,
) -> dict:
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio data is empty.")

    files = {"file": (filename, audio_bytes, content_type)}

    # Qwen3-ASR's documented preprocessing targets mono 16 kHz. Do not
    # add application-side EQ, AGC, denoising, or resampling here.
    data = {
        "model": DEFAULT_STT_MODEL,
        "language": "en",
        "response_format": "json",
        "prompt": (
            prompt
            or "Transcribe the spoken audio accurately in English. "
               "Return only the words that were spoken. "
               "Do not translate, summarize, or invent words."
        ),
    }

    try:
        response = await client.post(
            STT_TRANSCRIBE_URL,
            files=files,
            data=data,
        )
        response.raise_for_status()

        payload = response.json()
        text = _extract_text(payload)

        # Keep the raw backend fields available for debugging while exposing
        # a normalized `text` field to Basket.
        if isinstance(payload, dict):
            result = dict(payload)
            result["text"] = text
            return result

        return {"text": text}

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"STT backend returned {exc.response.status_code}: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not connect to STT backend: {exc}",
        ) from exc


async def _transcribe(file: UploadFile, prompt: str | None = None):
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty.")

    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            return await _transcribe_bytes(
                client,
                audio_bytes,
                filename=file.filename or "audio.wav",
                content_type=file.content_type or "audio/wav",
                prompt=prompt,
            )
    except HTTPException:
        raise


def stream_audio_duration_seconds(
    audio_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> float:
    bytes_per_second = sample_rate * STREAM_SAMPLE_WIDTH
    return len(audio_bytes) / bytes_per_second if bytes_per_second else 0.0


def make_stream_wav(
    pcm_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> bytes:
    return _pcm16_to_wav(pcm_bytes, sample_rate=sample_rate)


async def _stream_transcribe_window(
    client: httpx.AsyncClient,
    pcm_bytes: bytes,
    *,
    prompt: str | None = None,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> dict:
    wav_bytes = _pcm16_to_wav(pcm_bytes, sample_rate=sample_rate)
    return await _transcribe_bytes(
        client,
        wav_bytes,
        filename="stream.wav",
        content_type="audio/wav",
        prompt=prompt,
    )


class LlamaRealtimeSession:
    def __init__(
        self,
        *,
        host: str = STT_HOST,
        port: int = STT_PORT,
        sample_rate: int = STREAM_SAMPLE_RATE,
        language: str = "en",
        prompt: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.language = language
        self.prompt = prompt
        self.audio_buffer = bytearray()
        self.final_transcript = ""
        self.final_event = asyncio.Event()
        self.error: str | None = None
        self.closed = False

    async def connect(self) -> None:
        if self.closed:
            raise RuntimeError("Qwen3-ASR session is closed.")

        # Fail START immediately if the llama.cpp ASR server is unavailable.
        await _health()

        logger.info(
            "Qwen3-ASR session connected: backend=llama.cpp url=%s:%d "
            "sample_rate=%d model=%s",
            self.host,
            self.port,
            self.sample_rate,
            DEFAULT_STT_MODEL,
        )

    async def send_audio(self, pcm_bytes: bytes) -> None:
        if not pcm_bytes:
            return
        if self.closed:
            raise RuntimeError("Qwen3-ASR session is closed.")
        if len(pcm_bytes) % STREAM_SAMPLE_WIDTH != 0:
            raise ValueError("PCM16 audio has an odd byte length.")

        self.audio_buffer.extend(pcm_bytes)

    async def commit(self) -> None:
        """Mark the current turn ready for final full-buffer transcription."""
        return

    async def clear(self) -> None:
        if self.closed:
            return
        self.audio_buffer.clear()
        self.final_transcript = ""
        self.error = None
        self.final_event.clear()

    async def wait_for_final(self, timeout: float = 120.0) -> str:
        if self.final_transcript:
            return self.final_transcript

        audio_bytes = bytes(self.audio_buffer)
        if not audio_bytes:
            self.final_event.set()
            return ""

        started_at = time.perf_counter()
        try:
            wav_bytes = _pcm16_to_wav(
                audio_bytes,
                sample_rate=self.sample_rate,
            )

            async with httpx.AsyncClient(timeout=_timeout()) as client:
                result = await asyncio.wait_for(
                    _transcribe_bytes(
                        client,
                        wav_bytes,
                        filename="voice.wav",
                        content_type="audio/wav",
                        prompt=self.prompt,
                    ),
                    timeout=timeout,
                )

            self.final_transcript = str(result.get("text", "") or "").strip()
            logger.info(
                "Qwen3-ASR FINAL in %.3fs: bytes=%d transcript=%r",
                time.perf_counter() - started_at,
                len(audio_bytes),
                self.final_transcript,
            )
            return self.final_transcript

        except asyncio.TimeoutError as exc:
            self.error = f"Qwen3-ASR timed out after {timeout:.1f}s."
            raise HTTPException(status_code=504, detail=self.error) from exc
        except HTTPException:
            raise
        except Exception as exc:
            self.error = str(exc)
            logger.exception("Qwen3-ASR final transcription failed")
            raise HTTPException(
                status_code=502,
                detail=f"Qwen3-ASR transcription failed: {exc}",
            ) from exc
        finally:
            self.final_event.set()

    async def close(self) -> None:
        self.closed = True
        self.audio_buffer.clear()