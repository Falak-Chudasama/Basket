from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from src.core.configs import STT_HOST, STT_LANGUAGE, STT_PORT, WS_PATH
from src.jobs.refresh_session_job import clear_session
from src.schemas.VoiceSchema import VoiceStartRequest
from src.services.chat.chat_pipeline import PipelineEvent, VoicePipelineConfig, voice_to_voice
from src.services.session.session import create_session
from src.clients.nemotron_stt import NemotronRealtimeSession, STREAM_SAMPLE_RATE, STREAM_SAMPLE_WIDTH

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceSession:
    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket
        self.started = False
        self.application: str | None = "quince"
        self.voice_config: VoiceStartRequest | None = None
        self.audio_buffer = bytearray()
        self.last_partial_text = ""
        self.final_transcript = ""
        self.stt_session: NemotronRealtimeSession | None = None
        self.stt_event_task: asyncio.Task | None = None
        self.send_lock = asyncio.Lock()

    def _json_event(self, event: PipelineEvent) -> dict[str, Any]:
        return {"type": event.type, "data": event.data}

    # I/O helpers

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
        await self.send_json({
            "type": "error",
            "code": code,
            "message": message,
        })

    # Nemotron realtime STT

    async def _start_stt(self, prompt: str | None) -> None:
        cfg = self.require_config()
        session = NemotronRealtimeSession(
            host=STT_HOST,
            port=STT_PORT,
            sample_rate=cfg.sample_rate,
            language=STT_LANGUAGE,
            prompt=prompt,
        )

        await session.connect()
        self.stt_session = session
        self.stt_event_task = asyncio.create_task(
            self._forward_stt_events(session)
        )

    async def _forward_stt_events(self, session: NemotronRealtimeSession) -> None:
        try:
            while True:
                event = await session.events.get()
                event_type = event.get("type", "")

                if event_type == "conversation.item.input_audio_transcription.delta":
                    text = session.partial_text.strip()
                    if text and text != self.last_partial_text:
                        self.last_partial_text = text
                        await self.send_json({
                            "type": "stt.partial",
                            "text": text,
                        })
                    continue

                if event_type == "conversation.item.input_audio_transcription.completed":
                    self.final_transcript = session.final_transcript.strip()
                    continue

                if event_type == "error":
                    message = str(
                        (event.get("error") or {}).get(
                            "message",
                            "Nemotron realtime STT error.",
                        )
                    )
                    logger.error("Nemotron realtime STT error: %s", message)

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Nemotron STT event forwarder failed")

    async def _stop_stt(self, *, commit: bool) -> str:
        session = self.stt_session
        self.stt_session = None

        if session is None:
            return self.final_transcript.strip()

        try:
            if commit and not session.final_event.is_set():
                await session.commit()

            if commit and self.audio_buffer:
                transcript = await session.wait_for_final()
                self.final_transcript = transcript.strip()

            return self.final_transcript.strip()

        finally:
            await session.close()
            await self._cancel_stt_event_task()

    async def _cancel_stt_event_task(self) -> None:
        task = self.stt_event_task
        self.stt_event_task = None

        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Nemotron STT event task failed during cleanup")

    # Full pipeline

    async def run_pipeline(self, final_transcript: str | None) -> None:
        cfg = self.require_config()
        started_at = time.perf_counter()

        logger.info(
            "WS PIPELINE: application=%r audio_bytes=%d final_stt=%s",
            self.application,
            len(self.audio_buffer),
            "nemotron-realtime" if final_transcript else "fallback-full-buffer",
        )

        async def audio_source():
            if self.audio_buffer:
                yield bytes(self.audio_buffer)

        pipeline_config = VoicePipelineConfig(
            application=self.application,
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
                final_transcript_hint=final_transcript,
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
                        logger.exception(
                            "Could not normalize TTS audio event: type=%s",
                            type(audio).__name__,
                        )
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
            logger.warning(
                "WS PIPELINE cancelled after %.3fs",
                time.perf_counter() - started_at,
            )
            raise
        except Exception:
            logger.exception(
                "WS PIPELINE failed after %.3fs",
                time.perf_counter() - started_at,
            )
            raise

        logger.info(
            "WS PIPELINE complete in %.3fs: events=%d tts_chunks=%d tts_bytes=%d",
            time.perf_counter() - started_at,
            event_count,
            tts_chunks,
            tts_bytes,
        )

    # Control-message handlers

    async def handle_start(self, payload: dict[str, Any]) -> None:
        if self.started:
            await self.send_error(
                "already_started",
                "Voice stream is already started.",
            )
            return

        try:
            request = VoiceStartRequest.model_validate(payload)
        except Exception as exc:
            logger.exception("START validation failed")
            await self.send_error("invalid_start", str(exc))
            return

        if request.sample_rate != STREAM_SAMPLE_RATE:
            await self.send_error(
                "unsupported_sample_rate",
                "Basket requires 16,000 Hz PCM16 mono input audio.",
            )
            return

        if self.application is not None and request.application != self.application:
            logger.error(
                "START rejected: application mismatch existing=%r requested=%r",
                self.application,
                request.application,
            )
            await self.send_error(
                "application_mismatch",
                "Application cannot change during a WebSocket connection.",
            )
            return

        if self.application is None:
            self.application = request.application

        self.voice_config = request
        self.audio_buffer.clear()
        self.last_partial_text = ""
        self.final_transcript = ""

        try:
            await self._start_stt(request.prompt)
        except Exception as exc:
            logger.exception("Nemotron STT START failed")
            await self.send_error("stt_unavailable", str(exc))
            self.voice_config = None
            return

        self.started = True

        logger.info(
            "START accepted: application=%r llm_model=%r stt_model=nemotron-3.5",
            self.application,
            request.llm.model,
        )

        await self.send_json({
            "type": "started",
            "stream": request.stream,
            "sample_rate": request.sample_rate,
        })

    async def handle_stop(self) -> None:
        if not self.started:
            await self.send_error(
                "not_started",
                "Voice stream has not been started.",
            )
            return

        self.started = False

        if not self.audio_buffer:
            logger.warning("STOP received with no audio")
            await self._stop_stt(commit=False)
            await self.send_json({"type": "final", "text": ""})
            self._reset_turn_state()
            return

        pipeline_started_at = time.perf_counter()

        try:
            final_transcript = await self._stop_stt(commit=True)

            if final_transcript:
                logger.info(
                    "Nemotron FINAL STT transcript=%r",
                    final_transcript,
                )

            await self.run_pipeline(final_transcript or None)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self.send_error("pipeline_failed", str(exc))
        else:
            logger.info(
                "VOICE PIPELINE finished after %.3fs",
                time.perf_counter() - pipeline_started_at,
            )
        finally:
            self._reset_turn_state()

    async def handle_ping(self) -> None:
        await self.send_json({"type": "pong"})

    async def handle_cancel(self) -> None:
        self.started = False
        session = self.stt_session

        if session is not None:
            try:
                await session.clear()
            except Exception:
                logger.exception(
                    "Failed to clear Nemotron STT buffer during cancellation"
                )

        await self._stop_stt(commit=False)
        self._reset_turn_state()
        await self.send_json({"type": "cancelled"})

    def _reset_turn_state(self) -> None:
        self.audio_buffer.clear()
        self.last_partial_text = ""
        self.final_transcript = ""
        self.voice_config = None

    async def handle_audio_frame(self, audio: bytes) -> None:
        if not self.started:
            await self.send_error(
                "stream_not_started",
                "Send a start message before audio.",
            )
            return

        if not audio:
            return

        if len(audio) % STREAM_SAMPLE_WIDTH != 0:
            await self.send_error(
                "invalid_audio",
                "PCM16 audio must contain an even number of bytes.",
            )
            return

        self.audio_buffer.extend(audio)
        session = self.stt_session

        if session is None:
            await self.send_error(
                "stt_unavailable",
                "Nemotron STT session is not available.",
            )
            return

        await session.send_audio(audio)

    async def handle_control_message(self, text: str) -> None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.exception("WS JSON decode failed")
            await self.send_error(
                "invalid_json",
                "Control message must contain valid JSON.",
            )
            return

        if not isinstance(payload, dict):
            await self.send_error(
                "invalid_message",
                "Control message must be a JSON object.",
            )
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
            await self.send_error(
                "unknown_message_type",
                f"Unknown message type: {message_type!r}",
            )

    async def send_ready(self) -> None:
        await self.send_json({
            "type": "ready",
            "protocol": "basket-voice-v1",
            "transport": "websocket",
            "audio_input": {
                "encoding": "pcm_s16le",
                "sample_rate": STREAM_SAMPLE_RATE,
                "channels": 1,
            },
            "audio_output": {
                "encoding": "pcm_s16le",
                "sample_rate": 24_000,
                "channels": 1,
            },
        })

    async def cleanup(self) -> None:
        self.started = False
        await self._stop_stt(commit=False)
        self._reset_turn_state()


@router.websocket(WS_PATH)
async def stt_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    session = VoiceSession(websocket)

    logger.info("VOICE WS CONNECTED: client=%s", websocket.client)

    clear_session()
    create_session(session.application)

    try:
        await session.send_ready()

        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                logger.info(
                    "VOICE WS DISCONNECTED: client=%s",
                    websocket.client,
                )
                break

            audio = message.get("bytes")

            if audio is not None:
                await session.handle_audio_frame(audio)
                continue

            text = message.get("text")

            if text is None:
                await session.send_error(
                    "invalid_message",
                    "Expected JSON control message or binary audio.",
                )
                continue

            await session.handle_control_message(text)

    except WebSocketDisconnect:
        logger.info(
            "VOICE WS DISCONNECTED: client=%s application=%r",
            websocket.client,
            session.application,
        )

    except Exception:
        logger.exception("UNHANDLED VOICE WS ERROR")

        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Internal server error",
            )
        except Exception:
            pass

    finally:
        await session.cleanup()
        logger.info(
            "VOICE WS SESSION CLOSED: client=%s application=%r",
            websocket.client,
            session.application,
        )