from __future__ import annotations
import asyncio
import json
import logging
import time
import httpx
from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.core.configs import WS_PATH
from src.schemas.VoiceSchema import VoiceStartRequest
from src.services.chat.chat_pipeline import PipelineEvent,VoicePipelineConfig,voice_to_voice
from src.clients.llama_stt import (
    STREAM_MIN_AUDIO_SECONDS,
    STREAM_PARTIAL_INTERVAL_SECONDS,
    STREAM_SAMPLE_RATE,
    STREAM_SAMPLE_WIDTH,
    STREAM_WINDOW_SECONDS,
    _stream_transcribe_window,
    _timeout
)

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_STALE_TAIL_SECONDS = 1.5

class VoiceSession:
    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket
        self.started = False
        self.application: str | None = None
        self.voice_config: VoiceStartRequest | None = None

        self.audio_buffer = bytearray()
        self.last_partial_audio_bytes = 0
        self.last_partial_text = ""
        self.partial_task: asyncio.Task | None = None

        self.send_lock = asyncio.Lock()

    def _json_event(self, event: PipelineEvent) -> dict[str, Any]:
        return {"type": event.type, "data": event.data}

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def require_config(self) -> VoiceStartRequest:
        if self.voice_config is None:
            raise RuntimeError("Voice stream has not been started.")
        return self.voice_config

    async def send_json(self, payload: dict[str, Any]) -> None:
        if self.application is not None:
            payload = {"application": self.application, **payload}
        async with self.send_lock:
            await self.ws.send_json(payload)

    async def send_error(self, code: str, message: str) -> None:
        logger.error("WS ERROR code=%s message=%s", code, message)
        await self.send_json({"type": "error", "code": code, "message": message})

    # ------------------------------------------------------------------
    # Audio sizing (all derived from the active voice_config)
    # ------------------------------------------------------------------

    def window_bytes(self) -> int:
        cfg = self.require_config()
        return int(STREAM_WINDOW_SECONDS * cfg.sample_rate * STREAM_SAMPLE_WIDTH)

    def min_audio_bytes(self) -> int:
        cfg = self.require_config()
        return int(STREAM_MIN_AUDIO_SECONDS * cfg.sample_rate * STREAM_SAMPLE_WIDTH)

    def partial_interval_bytes(self) -> int:
        cfg = self.require_config()
        return int(STREAM_PARTIAL_INTERVAL_SECONDS * cfg.sample_rate * STREAM_SAMPLE_WIDTH)

    def stale_tail_bytes(self) -> int:
        cfg = self.require_config()
        return int(MAX_STALE_TAIL_SECONDS * cfg.sample_rate * STREAM_SAMPLE_WIDTH)

    # ------------------------------------------------------------------
    # Rolling partial STT
    # ------------------------------------------------------------------

    async def run_partial_stt(self) -> None:
        cfg = self.require_config()
        started_at = time.perf_counter()

        snapshot_length = len(self.audio_buffer)
        current = bytes(self.audio_buffer)
        rolling = current[-self.window_bytes():]
        if len(rolling) < self.min_audio_bytes():
            return

        try:
            async with httpx.AsyncClient(timeout=_timeout()) as client:
                result = await _stream_transcribe_window(client, rolling, prompt=cfg.prompt, sample_rate=STREAM_SAMPLE_RATE)

            text = str(result.get("text", "") or "").strip()
            if text and text != self.last_partial_text:
                self.last_partial_text = text
                await self.send_json({"type": "stt.partial", "text": text})

            self.last_partial_audio_bytes = snapshot_length
            logger.info("PARTIAL STT complete in %.3fs: %r", time.perf_counter() - started_at, text)

        except asyncio.CancelledError:
            logger.warning("PARTIAL STT cancelled")
            raise
        except Exception as exc:
            logger.exception("PARTIAL STT failed after %.3fs", time.perf_counter() - started_at)
            await self.send_error("asr_partial_failed", str(exc))

    def maybe_start_partial_stt(self) -> None:
        cfg = self.require_config()
        if (
            not cfg.stream
            or self.partial_task is not None
            or len(self.audio_buffer) < self.min_audio_bytes()
            or len(self.audio_buffer) - self.last_partial_audio_bytes < self.partial_interval_bytes()
        ):
            return

        self.partial_task = asyncio.create_task(self.run_partial_stt())

        def _clear(task: asyncio.Task) -> None:
            self.partial_task = None
            if task.cancelled():
                return
            try:
                task.result()
            except Exception:
                logger.exception("PARTIAL STT task crashed")

        self.partial_task.add_done_callback(_clear)

    async def _drain_partial_task(self) -> None:
        if self.partial_task is None:
            return
        try:
            await self.partial_task
        except asyncio.CancelledError:
            logger.warning("Pending partial STT was cancelled")
        except Exception:
            logger.exception("Pending partial STT failed during finalization")
        self.partial_task = None

    # ------------------------------------------------------------------
    # Full pipeline (STT reuse decision -> LLM -> TTS)
    # ------------------------------------------------------------------

    async def run_pipeline(self) -> None:
        cfg = self.require_config()
        started_at = time.perf_counter()
        logger.info(
            "WS PIPELINE: application=%r audio_bytes=%d final_stt=full_buffer",
            self.application,
            len(self.audio_buffer),
        )

        async def audio_source():
            if self.audio_buffer:
                yield bytes(self.audio_buffer)

        pipeline_config = VoicePipelineConfig(
            stt_prompt=cfg.prompt,
            system_prompt=cfg.llm.system_prompt,
            model=cfg.llm.model,
            temperature=cfg.llm.temperature,
            top_p=cfg.llm.top_p,
            max_tokens=cfg.llm.max_tokens,
            stop=cfg.llm.stop,
            seed=cfg.llm.seed,
            abstracted=cfg.llm.abstracted,
            voice=cfg.tts.voice,
            tts_temperature=cfg.tts.temperature,
        )

        event_count = 0
        tts_chunks = 0
        tts_bytes = 0

        try:
            async for event in voice_to_voice(
                audio_stream=audio_source(),
                config=pipeline_config,
                messages=list(cfg.llm.messages),
                final_transcript_hint=None,
            ):
                event_count += 1

                if event.type == "tts.audio":
                    audio = event.data
                    if audio is None:
                        logger.warning("TTS audio event contained no data.")
                        continue
                    try:
                        audio = bytes(audio)
                    except Exception:
                        logger.exception("Could not normalize TTS audio event: type=%s", type(audio).__name__)
                        continue
                    if not audio:
                        continue

                    tts_chunks += 1
                    tts_bytes += len(audio)
                    async with self.send_lock:
                        await self.ws.send_bytes(audio)
                    continue

                await self.send_json(self._json_event(event))

        except asyncio.CancelledError:
            logger.warning("WS PIPELINE cancelled after %.3fs", time.perf_counter() - started_at)
            raise
        except Exception:
            logger.exception("WS PIPELINE failed after %.3fs", time.perf_counter() - started_at)
            raise

        logger.info(
            "WS PIPELINE complete in %.3fs: events=%d tts_chunks=%d tts_bytes=%d",
            time.perf_counter() - started_at, event_count, tts_chunks, tts_bytes,
        )

    # ------------------------------------------------------------------
    # Control-message handlers
    # ------------------------------------------------------------------

    async def handle_start(self, payload: dict[str, Any]) -> None:
        if self.started:
            await self.send_error("already_started", "Voice stream is already started.")
            return

        try:
            request = VoiceStartRequest.model_validate(payload)
        except Exception as exc:
            logger.exception("START validation failed")
            await self.send_error("invalid_start", str(exc))
            return

        if request.sample_rate != STREAM_SAMPLE_RATE:
            await self.send_error("unsupported_sample_rate", "Basket requires 16,000 Hz PCM16 mono input audio.")
            return

        if self.application is not None and request.application != self.application:
            logger.error("START rejected: application mismatch existing=%r requested=%r",self.application, request.application)
            await self.send_error("application_mismatch", "Application cannot change during a WebSocket connection.")
            return

        if self.application is None:
            self.application = request.application

        self.voice_config = request
        self.started = True
        self.audio_buffer.clear()
        self.last_partial_audio_bytes = 0
        self.last_partial_text = ""

        logger.info("START accepted: application=%r model=%r", self.application, request.llm.model)
        await self.send_json({"type": "started", "stream": request.stream, "sample_rate": request.sample_rate})

    async def handle_stop(self) -> None:
        if not self.started:
            await self.send_error("not_started", "Voice stream has not been started.")
            return

        self.started = False
        await self._drain_partial_task()

        if not self.audio_buffer:
            logger.warning("STOP received with no audio")
            await self.send_json({"type": "final", "text": ""})
            return

        pipeline_started_at = time.perf_counter()
        try:
            await self.run_pipeline()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self.send_error("pipeline_failed", str(exc))
        else:
            logger.info("VOICE PIPELINE finished after %.3fs", time.perf_counter() - pipeline_started_at)

        self._reset_turn_state()

    async def handle_ping(self) -> None:
        await self.send_json({"type": "pong"})

    async def handle_cancel(self) -> None:
        if self.partial_task is not None:
            self.partial_task.cancel()
            try:
                await self.partial_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Partial STT failed during cancellation")
            self.partial_task = None

        self.started = False
        self._reset_turn_state()
        await self.send_json({"type": "cancelled"})

    def _reset_turn_state(self) -> None:
        self.audio_buffer.clear()
        self.last_partial_audio_bytes = 0
        self.last_partial_text = ""

    async def handle_audio_frame(self, audio: bytes) -> None:
        if not self.started:
            await self.send_error("stream_not_started", "Send a start message before audio.")
            return
        if not audio:
            return

        self.audio_buffer.extend(audio)
        self.maybe_start_partial_stt()

    async def handle_control_message(self, text: str) -> None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.exception("WS JSON decode failed")
            await self.send_error("invalid_json", "Control message must contain valid JSON.")
            return

        if not isinstance(payload, dict):
            await self.send_error("invalid_message", "Control message must be a JSON object.")
            return

        message_type = payload.get("type")

        if message_type == "start":
            await self.handle_start(payload)
        elif message_type == "stop":
            await self.handle_stop()
        elif message_type == "ping":
            await self.handle_ping()
        elif message_type == "cancel":
            await self.handle_cancel()
        else:
            logger.error("Unknown WS message type: %r", message_type)
            await self.send_error("unknown_message_type", f"Unknown message type: {message_type!r}")

    async def send_ready(self) -> None:
        await self.send_json({
            "type": "ready",
            "protocol": "basket-voice-v1",
            "transport": "websocket",
            "audio_input": {"encoding": "pcm_s16le", "sample_rate": STREAM_SAMPLE_RATE, "channels": 1},
            "audio_output": {"encoding": "pcm_s16le", "sample_rate": 24_000, "channels": 1},
        })

    def cleanup(self) -> None:
        if self.partial_task is not None and not self.partial_task.done():
            self.partial_task.cancel()


@router.websocket(WS_PATH)
async def stt_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    session = VoiceSession(websocket)
    logger.info("VOICE WS CONNECTED: client=%s", websocket.client)

    try:
        await session.send_ready()
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                logger.info("VOICE WS DISCONNECTED: client=%s", websocket.client)
                break
            audio = message.get("bytes")
            if audio is not None:
                await session.handle_audio_frame(audio)
                continue
            text = message.get("text")
            if text is None:
                await session.send_error("invalid_message", "Expected JSON control message or binary audio.")
                continue

            await session.handle_control_message(text)

    except WebSocketDisconnect:
        logger.info("VOICE WS DISCONNECTED: client=%s application=%r",websocket.client, session.application)

    except Exception:
        logger.exception("UNHANDLED VOICE WS ERROR")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except Exception:
            pass

    finally:
        session.cleanup()
        logger.info("VOICE WS SESSION CLOSED: client=%s application=%r",websocket.client, session.application)