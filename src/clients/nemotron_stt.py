from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import wave
from typing import Any

import httpx
import websockets
from fastapi import HTTPException, UploadFile

from src.core.configs import (
    DEFAULT_STT_MODEL,
    STT_HOST,
    STT_LANGUAGE,
    STT_PORT,
    get_stt_speech_contexts,
)

logger = logging.getLogger(__name__)

STT_BASE_URL = f"http://{STT_HOST}:{STT_PORT}"
STT_WS_URL = f"ws://{STT_HOST}:{STT_PORT}/v1/audio/transcriptions/realtime"
STT_TRANSCRIBE_URL = f"{STT_BASE_URL}/v1/audio/transcriptions"
STT_HEALTH_URL = f"{STT_BASE_URL}/health"

STREAM_SAMPLE_RATE = 16_000
STREAM_SAMPLE_WIDTH = 2
STREAM_CHANNELS = 1

STT_CONNECT_TIMEOUT = 10.0
STT_FINAL_TIMEOUT = 12.0


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=30.0)


def _pcm16_to_wav(
    pcm_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> bytes:
    if not pcm_bytes:
        raise ValueError("PCM audio cannot be empty.")

    if len(pcm_bytes) % STREAM_SAMPLE_WIDTH != 0:
        raise ValueError("PCM16 audio has an odd byte length.")

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(STREAM_CHANNELS)
        wav_file.setsampwidth(STREAM_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    return buffer.getvalue()


def _clean_transcription(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""

    marker_match = re.search(r"<asr_text>", text, flags=re.IGNORECASE)
    if marker_match:
        text = text[marker_match.end():].strip()

    return text


def _extract_text(payload: Any) -> str:
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

        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                raise HTTPException(status_code=502, detail=message)

    if isinstance(payload, str):
        return _clean_transcription(payload)

    return ""


async def _health() -> dict[str, Any]:
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


async def _load_model() -> dict[str, Any]:
    health = await _health()
    return {
        "status": "ready",
        "backend": "nemo-speech.cpp",
        "model": DEFAULT_STT_MODEL,
        "host": STT_HOST,
        "port": STT_PORT,
        "health": health,
    }


async def _model_status() -> dict[str, Any]:
    try:
        health = await _health()
        return {
            "available": True,
            "status": "ready",
            "backend": "nemo-speech.cpp",
            "model": DEFAULT_STT_MODEL,
            "health": health,
        }

    except HTTPException as exc:
        return {
            "available": False,
            "status": "offline",
            "backend": "nemo-speech.cpp",
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
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> dict[str, Any]:
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio data is empty.")

    files = {"file": (filename, audio_bytes, content_type)}
    data: dict[str, Any] = {
        "model": DEFAULT_STT_MODEL,
        "language": STT_LANGUAGE,
        "response_format": "json",
        "automatic_punctuation": "true",
        "speech_contexts": json.dumps(get_stt_speech_contexts()),
    }

    # NeMo uses prompt differently from Qwen, so the old prompt is ignored.
    _ = prompt

    try:
        response = await client.post(STT_TRANSCRIBE_URL, files=files, data=data)
        response.raise_for_status()

        payload = response.json()
        text = _extract_text(payload)

        if isinstance(payload, dict):
            result = dict(payload)
            result["text"] = text
            return result

        return {"text": text}

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"STT backend returned {exc.response.status_code}: "
                f"{exc.response.text}"
            ),
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

    async with httpx.AsyncClient(timeout=_timeout()) as client:
        return await _transcribe_bytes(
            client,
            audio_bytes,
            filename=file.filename or "audio.wav",
            content_type=file.content_type or "audio/wav",
            prompt=prompt,
        )


def stream_audio_duration_seconds(
    audio_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> float:
    bytes_per_second = sample_rate * STREAM_SAMPLE_WIDTH * STREAM_CHANNELS
    return len(audio_bytes) / bytes_per_second if bytes_per_second else 0.0


def make_stream_wav(
    pcm_bytes: bytes,
    sample_rate: int = STREAM_SAMPLE_RATE,
) -> bytes:
    return _pcm16_to_wav(pcm_bytes, sample_rate=sample_rate)


class NemotronRealtimeSession:
    """One native NeMo-Speech.cpp realtime ASR session for one voice turn."""

    def __init__(
        self,
        *,
        host: str = STT_HOST,
        port: int = STT_PORT,
        sample_rate: int = STREAM_SAMPLE_RATE,
        language: str = STT_LANGUAGE,
        prompt: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.language = language
        self.prompt = prompt
        self.websocket = None
        self.reader_task: asyncio.Task | None = None
        self.events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.partial_text = ""
        self.final_transcript = ""
        self.error: str | None = None
        self.final_event = asyncio.Event()
        self.closed = False

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}/v1/audio/transcriptions/realtime"

    async def connect(self) -> None:
        if self.websocket is not None:
            return

        try:
            self.websocket = await websockets.connect(
                self.url,
                open_timeout=STT_CONNECT_TIMEOUT,
                close_timeout=5.0,
                ping_interval=20.0,
                max_size=None,
            )

            raw = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=STT_CONNECT_TIMEOUT,
            )
            event = self._parse_event(raw)

            if event.get("type") == "error":
                raise RuntimeError(self._event_error_message(event))

            if event.get("type") != "session.created":
                raise RuntimeError(
                    "Nemotron realtime server did not return session.created. "
                    f"Received: {event.get('type')!r}"
                )

            session: dict[str, Any] = {
                "sample_rate": self.sample_rate,
                "language": self.language,
                "automatic_punctuation": True,
                "verbatim": False,
                "speech_contexts": get_stt_speech_contexts(),
            }

            await self.websocket.send(
                json.dumps({"type": "session.update", "session": session})
            )

            self.reader_task = asyncio.create_task(self._reader_loop())

            logger.info(
                "Nemotron realtime STT connected: url=%s sample_rate=%d language=%s",
                self.url,
                self.sample_rate,
                self.language,
            )

        except Exception as exc:
            await self.close()
            raise HTTPException(
                status_code=502,
                detail=f"Could not connect to Nemotron STT: {exc}",
            ) from exc

    async def send_audio(self, pcm_bytes: bytes) -> None:
        if not pcm_bytes:
            return

        if self.websocket is None or self.closed:
            raise RuntimeError("Nemotron realtime STT session is not connected.")

        if len(pcm_bytes) % STREAM_SAMPLE_WIDTH != 0:
            raise ValueError("PCM16 audio has an odd byte length.")

        await self.websocket.send(pcm_bytes)

    async def commit(self) -> None:
        if self.websocket is None or self.closed:
            return

        await self.websocket.send(
            json.dumps({"type": "input_audio_buffer.commit"})
        )

    async def clear(self) -> None:
        if self.websocket is None or self.closed:
            return

        await self.websocket.send(
            json.dumps({"type": "input_audio_buffer.clear"})
        )

    async def wait_for_final(
        self,
        timeout: float = STT_FINAL_TIMEOUT,
    ) -> str:
        if self.final_transcript:
            return self.final_transcript

        try:
            await asyncio.wait_for(self.final_event.wait(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail=(
                    "Nemotron STT did not produce a final transcript "
                    f"within {timeout:.1f} seconds."
                ),
            ) from exc

        if self.error:
            raise HTTPException(
                status_code=502,
                detail=f"Nemotron STT realtime error: {self.error}",
            )

        return self.final_transcript.strip()

    async def close(self) -> None:
        if self.closed:
            return

        self.closed = True
        reader = self.reader_task
        self.reader_task = None

        if reader is not None and not reader.done():
            reader.cancel()
            try:
                await reader
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Nemotron realtime reader failed during close"
                )

        websocket = self.websocket
        self.websocket = None

        if websocket is not None:
            try:
                await websocket.close()
            except Exception:
                logger.exception("Failed to close Nemotron realtime socket")

    async def _reader_loop(self) -> None:
        websocket = self.websocket
        if websocket is None:
            return

        try:
            async for raw in websocket:
                event = self._parse_event(raw)
                await self.events.put(event)

                event_type = event.get("type", "")

                if event_type == "conversation.item.input_audio_transcription.delta":
                    delta = str(event.get("delta", "") or "")
                    if delta:
                        self.partial_text += delta

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = _clean_transcription(
                        str(event.get("transcript", "") or "")
                    )
                    self.final_transcript = (
                        transcript or self.partial_text.strip()
                    )
                    self.final_event.set()

                elif event_type == "error":
                    self.error = self._event_error_message(event)
                    self.final_event.set()

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            self.error = str(exc)
            self.final_event.set()
            await self.events.put({
                "type": "error",
                "error": {"message": str(exc)},
            })

    @staticmethod
    def _parse_event(raw: Any) -> dict[str, Any]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        if not isinstance(raw, str):
            return {"type": "unknown", "data": raw}

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            return {"type": "unknown", "data": raw}

        if isinstance(event, dict):
            return event

        return {"type": "unknown", "data": event}

    @staticmethod
    def _event_error_message(event: dict[str, Any]) -> str:
        error = event.get("error")

        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                return message

        message = event.get("message")
        if isinstance(message, str) and message:
            return message

        return "Unknown Nemotron realtime error."