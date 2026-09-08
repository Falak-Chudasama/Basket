from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Final

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from src.clients.llama_stt import (
    STREAM_MIN_AUDIO_SECONDS,
    STREAM_PARTIAL_INTERVAL_SECONDS,
    STREAM_SAMPLE_RATE,
    STREAM_SAMPLE_WIDTH,
    STREAM_WINDOW_SECONDS,
    _stream_transcribe_window,
    _timeout,
    stream_audio_duration_seconds,
)
from src.schemas.VoiceSchema import VoiceStartRequest
from src.services.chat.chat_pipeline import (
    PipelineEvent,
    VoicePipelineConfig,
    voice_to_voice,
)

logger = logging.getLogger(__name__)

router = APIRouter()

WS_PATH: Final[str] = "/ws"


# ============================================================
# HELPERS
# ============================================================


def _json_event(event: PipelineEvent) -> dict[str, Any]:
    """
    Convert an internal pipeline event into a JSON-safe event.

    Binary TTS audio is handled separately by the WebSocket
    transport.
    """

    return {
        "type": event.type,
        "data": event.data,
    }


# ============================================================
# WEBSOCKET
# ============================================================


@router.websocket(WS_PATH)
async def stt_stream(
    websocket: WebSocket,
) -> None:
    """
    Basket voice-to-voice WebSocket transport.

    Client -> Server:

        {"type":"start", "application":"quince", ...}
        <binary PCM16 mono 16 kHz frames>
        ...
        {"type":"stop", "application":"quince"}

    Optional:

        {"type":"cancel", "application":"quince"}
        {"type":"ping", "application":"quince"}

    The WebSocket transports data and delegates the actual
    STT -> LLM -> TTS pipeline to chat_pipeline.py.
    """

    await websocket.accept()

    logger.info(
        "=================================================="
    )
    logger.info(
        "VOICE WS CONNECTED"
    )
    logger.info(
        "client=%s path=%s",
        websocket.client,
        WS_PATH,
    )
    logger.info(
        "=================================================="
    )

    started = False

    # Application identity belongs to the WebSocket session.
    # It is established by the first valid start message.
    application: str | None = None

    # Voice configuration belongs to the current voice turn.
    voice_config: VoiceStartRequest | None = None

    # --------------------------------------------------------
    # AUDIO STATE
    # --------------------------------------------------------

    audio_buffer = bytearray()

    # --------------------------------------------------------
    # PARTIAL STT STATE
    # --------------------------------------------------------

    last_partial_audio_bytes = 0

    partial_task: asyncio.Task | None = None

    last_partial_text = ""

    # --------------------------------------------------------
    # SEND CONCURRENCY
    # --------------------------------------------------------

    send_lock = asyncio.Lock()

    def require_voice_config() -> VoiceStartRequest:
        if voice_config is None:
            raise RuntimeError(
                "Voice stream has not been started."
            )

        return voice_config

    async def send_json(
        payload: dict[str, Any],
    ) -> None:

        if application is not None:
            payload = {
                "application": application,
                **payload,
            }

        logger.debug(
            "WS -> JSON: %s",
            payload,
        )

        async with send_lock:
            await websocket.send_json(payload)

    async def send_error(
        code: str,
        message: str,
    ) -> None:

        logger.error(
            "WS ERROR code=%s message=%s",
            code,
            message,
        )

        await send_json(
            {
                "type": "error",
                "code": code,
                "message": message,
            }
        )

    # ========================================================
    # AUDIO SIZING
    # ========================================================

    def window_bytes() -> int:

        config = require_voice_config()

        return int(
            STREAM_WINDOW_SECONDS
            * config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    def min_audio_bytes() -> int:

        config = require_voice_config()

        return int(
            STREAM_MIN_AUDIO_SECONDS
            * config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    def partial_interval_bytes() -> int:

        config = require_voice_config()

        return int(
            STREAM_PARTIAL_INTERVAL_SECONDS
            * config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    # ========================================================
    # LIVE PARTIAL STT
    # ========================================================

    async def run_partial_stt() -> None:

        nonlocal last_partial_audio_bytes
        nonlocal last_partial_text

        config = require_voice_config()

        partial_started_at = time.perf_counter()

        logger.info(
            "PARTIAL STT START"
        )

        current = bytes(
            audio_buffer
        )

        rolling = current[
            -window_bytes():
        ]

        logger.info(
            "PARTIAL STT: total_audio=%d rolling_window=%d",
            len(current),
            len(rolling),
        )

        if len(rolling) < min_audio_bytes():

            logger.info(
                "PARTIAL STT: skipped, insufficient audio"
            )

            return

        try:

            import httpx

            logger.info(
                "PARTIAL STT: calling _stream_transcribe_window()"
            )

            async with httpx.AsyncClient(
                timeout=_timeout()
            ) as client:

                result = (
                    await _stream_transcribe_window(
                        client,
                        rolling,
                        prompt=config.prompt,
                        sample_rate=STREAM_SAMPLE_RATE,
                    )
                )

            logger.info(
                "PARTIAL STT: backend returned after %.3fs",
                time.perf_counter()
                - partial_started_at,
            )

            text = str(
                result.get(
                    "text",
                    "",
                )
                or ""
            ).strip()

            logger.info(
                "PARTIAL STT RESULT: %r",
                text,
            )

            if (
                text
                and text != last_partial_text
            ):

                last_partial_text = text

                await send_json(
                    {
                        "type": "stt.partial",
                        "text": text,
                    }
                )

            last_partial_audio_bytes = (
                len(audio_buffer)
            )

            logger.info(
                "PARTIAL STT COMPLETE in %.3fs",
                time.perf_counter()
                - partial_started_at,
            )

        except asyncio.CancelledError:

            logger.warning(
                "PARTIAL STT CANCELLED"
            )

            raise

        except Exception as exc:

            logger.exception(
                "PARTIAL STT FAILED after %.3fs",
                time.perf_counter()
                - partial_started_at,
            )

            await send_error(
                "asr_partial_failed",
                str(exc),
            )

    def maybe_start_partial_stt() -> None:

        nonlocal partial_task

        config = require_voice_config()

        if not config.stream:
            return

        if partial_task is not None:
            return

        if len(audio_buffer) < min_audio_bytes():
            return

        if (
            len(audio_buffer)
            - last_partial_audio_bytes
            < partial_interval_bytes()
        ):
            return

        logger.info(
            "STARTING PARTIAL STT TASK: buffered=%d bytes",
            len(audio_buffer),
        )

        partial_task = asyncio.create_task(
            run_partial_stt()
        )

        def clear_partial_task(
            task: asyncio.Task,
        ) -> None:

            nonlocal partial_task

            partial_task = None

            if task.cancelled():
                return

            try:

                task.result()

            except Exception:

                logger.exception(
                    "PARTIAL STT TASK CRASHED"
                )

        partial_task.add_done_callback(
            clear_partial_task
        )

    # ========================================================
    # END-TO-END PIPELINE
    # ========================================================

    # ========================================================
    # PARTIAL-STT REUSE THRESHOLD
    #
    # If the audio recorded after the last rolling partial STT
    # pass is short enough, that partial's transcript already
    # covers essentially the whole utterance and we can skip the
    # redundant full-buffer re-transcription on stop entirely.
    # If more than this much *new* audio arrived after the last
    # partial (e.g. the user paused, then kept talking), fall
    # back to a normal full transcribe so nothing gets dropped.
    # ========================================================

    MAX_STALE_TAIL_SECONDS = 1.5

    def stale_tail_bytes() -> int:

        config = require_voice_config()

        return int(
            MAX_STALE_TAIL_SECONDS
            * config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    async def run_pipeline() -> None:

        config_request = require_voice_config()

        pipeline_started_at = time.perf_counter()

        # ----------------------------------------------------
        # Decide whether the last rolling partial STT result
        # can stand in for a fresh full-buffer transcription.
        # ----------------------------------------------------

        untranscribed_tail = (
            len(audio_buffer) - last_partial_audio_bytes
        )

        reuse_partial = bool(
            last_partial_text
            and untranscribed_tail >= 0
            and untranscribed_tail <= stale_tail_bytes()
        )

        logger.info(
            "STT REUSE CHECK: last_partial_text=%r "
            "untranscribed_tail_bytes=%d reuse_partial=%s",
            last_partial_text,
            untranscribed_tail,
            reuse_partial,
        )

        logger.info(
            "--------------------------------------------------"
        )
        logger.info(
            "WS PIPELINE: ENTER"
        )
        logger.info(
            "WS PIPELINE: application=%r",
            application,
        )
        logger.info(
            "WS PIPELINE: audio_bytes=%d duration=%.3fs",
            len(audio_buffer),
            stream_audio_duration_seconds(
                bytes(audio_buffer),
                sample_rate=STREAM_SAMPLE_RATE,
            ),
        )

        logger.info(
            "WS PIPELINE: STT prompt=%r",
            config_request.prompt,
        )

        logger.info(
            "WS PIPELINE: LLM model=%r",
            config_request.llm.model,
        )

        logger.info(
            "WS PIPELINE: LLM temperature=%r top_p=%r "
            "max_tokens=%r stop=%r seed=%r",
            config_request.llm.temperature,
            config_request.llm.top_p,
            config_request.llm.max_tokens,
            config_request.llm.stop,
            config_request.llm.seed,
        )

        logger.info(
            "WS PIPELINE: LLM system_prompt=%r",
            config_request.llm.system_prompt,
        )

        logger.info(
            "WS PIPELINE: LLM messages=%d abstracted=%r",
            len(config_request.llm.messages),
            config_request.llm.abstracted,
        )

        logger.info(
            "WS PIPELINE: TTS voice=%r temperature=%r",
            config_request.tts.voice,
            config_request.tts.temperature,
        )

        async def audio_source():

            logger.info(
                "audio_source(): yielding %d bytes",
                len(audio_buffer),
            )

            if audio_buffer:

                yield bytes(
                    audio_buffer
                )

        pipeline_config = VoicePipelineConfig(

            # ------------------------------------------------
            # STT
            # ------------------------------------------------

            stt_prompt=config_request.prompt,

            # ------------------------------------------------
            # LLM
            # ------------------------------------------------

            system_prompt=(
                config_request.llm.system_prompt
            ),

            model=(
                config_request.llm.model
            ),

            temperature=(
                config_request.llm.temperature
            ),

            top_p=(
                config_request.llm.top_p
            ),

            max_tokens=(
                config_request.llm.max_tokens
            ),

            stop=(
                config_request.llm.stop
            ),

            seed=(
                config_request.llm.seed
            ),

            abstracted=(
                config_request.llm.abstracted
            ),

            # ------------------------------------------------
            # TTS
            # ------------------------------------------------

            voice=(
                config_request.tts.voice
            ),

            tts_temperature=(
                config_request.tts.temperature
            ),
        )

        logger.info(
            "WS PIPELINE: VoicePipelineConfig created"
        )

        logger.info(
            "WS PIPELINE: calling voice_to_voice()"
        )

        event_count = 0
        tts_audio_chunks = 0
        tts_audio_bytes = 0

        try:

            async for event in voice_to_voice(

                audio_stream=audio_source(),

                config=pipeline_config,

                messages=list(
                    config_request.llm.messages
                ),

                final_transcript_hint=(
                    last_partial_text
                    if reuse_partial
                    else None
                ),

            ):

                event_count += 1

                if event.type == "tts.audio":

                    audio = event.data

                    if audio is None:
                        logger.warning(
                            "TTS audio event contained no data."
                        )
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
                        logger.warning(
                            "TTS audio event contained an empty chunk."
                        )
                        continue

                    tts_audio_chunks += 1
                    tts_audio_bytes += len(audio)

                    logger.info(
                        "Sending TTS audio to client: %d bytes",
                        len(audio),
                    )

                    async with send_lock:
                        await websocket.send_bytes(audio)

                    continue

                logger.info(
                    "WS PIPELINE EVENT #%d: type=%s data=%r",
                    event_count,
                    event.type,
                    event.data,
                )

                await send_json(
                    _json_event(event)
                )

        except asyncio.CancelledError:

            logger.warning(
                "WS PIPELINE CANCELLED after %.3fs",
                time.perf_counter()
                - pipeline_started_at,
            )

            raise

        except Exception:

            logger.exception(
                "WS PIPELINE FAILED after %.3fs",
                time.perf_counter()
                - pipeline_started_at,
            )

            raise

        logger.info(
            "WS PIPELINE COMPLETE in %.3fs",
            time.perf_counter()
            - pipeline_started_at,
        )

        logger.info(
            "WS PIPELINE SUMMARY: events=%d "
            "tts_chunks=%d tts_bytes=%d",
            event_count,
            tts_audio_chunks,
            tts_audio_bytes,
        )

    # ========================================================
    # READY
    # ========================================================

    try:

        logger.info(
            "Sending READY event"
        )

        await send_json(
            {
                "type": "ready",
                "protocol": "basket-voice-v1",
                "transport": "websocket",

                "audio_input": {
                    "encoding": "pcm_s16le",
                    "sample_rate": (
                        STREAM_SAMPLE_RATE
                    ),
                    "channels": 1,
                },

                "audio_output": {
                    "encoding": "pcm_s16le",
                    "sample_rate": 24_000,
                    "channels": 1,
                },
            }
        )

        logger.info(
            "READY sent successfully"
        )

        # ====================================================
        # MAIN LOOP
        # ====================================================

        while True:

            logger.debug(
                "WS waiting for next message..."
            )

            message = await websocket.receive()

            # ------------------------------------------------
            # DISCONNECT
            # ------------------------------------------------

            if (
                message.get("type")
                == "websocket.disconnect"
            ):

                logger.info(
                    "VOICE WS DISCONNECTED: client=%s",
                    websocket.client,
                )

                break

            # ------------------------------------------------
            # BINARY AUDIO
            # ------------------------------------------------

            audio = message.get(
                "bytes"
            )

            if audio is not None:

                if not started:

                    await send_error(
                        "stream_not_started",
                        (
                            "Send a start message "
                            "before audio."
                        ),
                    )

                    continue

                if not audio:

                    logger.debug(
                        "Empty audio frame ignored"
                    )

                    continue

                audio_buffer.extend(
                    audio
                )

                logger.debug(
                    (
                        "WS AUDIO: chunk=%d bytes "
                        "total=%d bytes duration=%.3fs"
                    ),
                    len(audio),
                    len(audio_buffer),
                    stream_audio_duration_seconds(
                        bytes(audio_buffer),
                        sample_rate=STREAM_SAMPLE_RATE,
                    ),
                )

                maybe_start_partial_stt()

                continue

            # ------------------------------------------------
            # CONTROL MESSAGE
            # ------------------------------------------------

            text = message.get(
                "text"
            )

            if text is None:

                await send_error(
                    "invalid_message",
                    (
                        "Expected JSON control "
                        "message or binary audio."
                    ),
                )

                continue

            logger.info(
                "WS TEXT RECEIVED: %s",
                text,
            )

            try:

                payload = json.loads(
                    text
                )

            except json.JSONDecodeError:

                logger.exception(
                    "WS JSON DECODE FAILED"
                )

                await send_error(
                    "invalid_json",
                    (
                        "Control message must "
                        "contain valid JSON."
                    ),
                )

                continue

            if not isinstance(
                payload,
                dict,
            ):

                await send_error(
                    "invalid_message",
                    (
                        "Control message must "
                        "be a JSON object."
                    ),
                )

                continue

            message_type = payload.get(
                "type"
            )

            logger.info(
                "WS CONTROL: type=%r",
                message_type,
            )

            # =================================================
            # START
            # =================================================

            if message_type == "start":

                start_received_at = time.perf_counter()

                logger.info(
                    "=================================================="
                )

                logger.info(
                    "START RECEIVED"
                )

                logger.info(
                    "START PAYLOAD: %s",
                    payload,
                )

                logger.info(
                    "=================================================="
                )

                if started:

                    logger.error(
                        "START rejected: already started"
                    )

                    await send_error(
                        "already_started",
                        (
                            "Voice stream is "
                            "already started."
                        ),
                    )

                    continue

                try:

                    request = (
                        VoiceStartRequest.model_validate(
                            payload
                        )
                    )

                except Exception as exc:

                    logger.exception(
                        "START VALIDATION FAILED"
                    )

                    await send_error(
                        "invalid_start",
                        str(exc),
                    )

                    continue

                logger.info(
                    "START validation succeeded"
                )

                if (
                    request.sample_rate
                    != STREAM_SAMPLE_RATE
                ):

                    logger.error(
                        "Unsupported sample rate: %r",
                        request.sample_rate,
                    )

                    await send_error(
                        "unsupported_sample_rate",
                        (
                            "Basket requires "
                            "16,000 Hz PCM16 mono "
                            "input audio."
                        ),
                    )

                    continue

                # ------------------------------------------------
                # APPLICATION IDENTITY
                # ------------------------------------------------

                if (
                    application is not None
                    and request.application != application
                ):

                    logger.error(
                        "START rejected: application mismatch "
                        "existing=%r requested=%r",
                        application,
                        request.application,
                    )

                    await send_error(
                        "application_mismatch",
                        (
                            "Application cannot change "
                            "during a WebSocket connection."
                        ),
                    )

                    continue

                if application is None:
                    application = request.application

                # ------------------------------------------------
                # ACCEPT START
                # ------------------------------------------------

                voice_config = request

                started = True

                audio_buffer.clear()

                last_partial_audio_bytes = 0

                last_partial_text = ""

                logger.info(
                    "START accepted after %.3fs",
                    time.perf_counter()
                    - start_received_at,
                )

                logger.info(
                    "APPLICATION: %r",
                    application,
                )

                logger.info(
                    "VOICE CONFIG:"
                )

                logger.info(
                    "  application=%r",
                    voice_config.application,
                )

                logger.info(
                    "  STT prompt=%r",
                    voice_config.prompt,
                )

                logger.info(
                    "  STT stream=%r",
                    voice_config.stream,
                )

                logger.info(
                    "  sample_rate=%r",
                    voice_config.sample_rate,
                )

                logger.info(
                    "  LLM model=%r",
                    voice_config.llm.model,
                )

                logger.info(
                    "  LLM messages=%d",
                    len(voice_config.llm.messages),
                )

                logger.info(
                    "  LLM temperature=%r",
                    voice_config.llm.temperature,
                )

                logger.info(
                    "  LLM top_p=%r",
                    voice_config.llm.top_p,
                )

                logger.info(
                    "  LLM max_tokens=%r",
                    voice_config.llm.max_tokens,
                )

                logger.info(
                    "  LLM stop=%r",
                    voice_config.llm.stop,
                )

                logger.info(
                    "  LLM seed=%r",
                    voice_config.llm.seed,
                )

                logger.info(
                    "  LLM system_prompt=%r",
                    voice_config.llm.system_prompt,
                )

                logger.info(
                    "  LLM abstracted=%r",
                    voice_config.llm.abstracted,
                )

                logger.info(
                    "  TTS voice=%r",
                    voice_config.tts.voice,
                )

                logger.info(
                    "  TTS temperature=%r",
                    voice_config.tts.temperature,
                )

                await send_json(
                    {
                        "type": "started",
                        "stream": (
                            voice_config.stream
                        ),
                        "sample_rate": (
                            voice_config.sample_rate
                        ),
                    }
                )

                logger.info(
                    "STARTED response sent"
                )

                continue

            # =================================================
            # STOP
            # =================================================

            if message_type == "stop":

                stop_received_at = time.perf_counter()

                logger.info(
                    "=================================================="
                )

                logger.info(
                    "STOP RECEIVED"
                )

                logger.info(
                    "started=%s buffered_bytes=%d",
                    started,
                    len(audio_buffer),
                )

                logger.info(
                    "=================================================="
                )

                if not started:

                    logger.error(
                        "STOP rejected: stream not started"
                    )

                    await send_error(
                        "not_started",
                        (
                            "Voice stream has "
                            "not been started."
                        ),
                    )

                    continue

                started = False

                logger.info(
                    "Final audio duration: %.3fs",
                    stream_audio_duration_seconds(
                        bytes(audio_buffer),
                        sample_rate=STREAM_SAMPLE_RATE,
                    ),
                )

                # ------------------------------------------------
                # Wait for pending partial STT
                # ------------------------------------------------

                if partial_task is not None:

                    logger.info(
                        "Waiting for pending partial STT task..."
                    )

                    try:

                        await partial_task

                    except asyncio.CancelledError:

                        logger.warning(
                            "Pending partial STT was cancelled"
                        )

                    except Exception:

                        logger.exception(
                            "Pending partial STT failed during finalization"
                        )

                    partial_task = None

                    logger.info(
                        "Pending partial STT task resolved"
                    )

                # ------------------------------------------------
                # No audio
                # ------------------------------------------------

                if not audio_buffer:

                    logger.warning(
                        "STOP received with no audio"
                    )

                    await send_json(
                        {
                            "type": "final",
                            "text": "",
                        }
                    )

                    continue

                logger.info(
                    "STOP preprocessing complete after %.3fs",
                    time.perf_counter()
                    - stop_received_at,
                )

                # ------------------------------------------------
                # PIPELINE
                # ------------------------------------------------

                pipeline_started_at = (
                    time.perf_counter()
                )

                logger.info(
                    "=================================================="
                )

                logger.info(
                    "STARTING VOICE PIPELINE"
                )

                logger.info(
                    "=================================================="
                )

                try:

                    await run_pipeline()

                except asyncio.CancelledError:

                    logger.warning(
                        "VOICE PIPELINE CANCELLED after %.3fs",
                        time.perf_counter()
                        - pipeline_started_at,
                    )

                    raise

                except Exception as exc:

                    logger.exception(
                        "VOICE PIPELINE FAILED after %.3fs",
                        time.perf_counter()
                        - pipeline_started_at,
                    )

                    await send_error(
                        "pipeline_failed",
                        str(exc),
                    )

                else:

                    logger.info(
                        "VOICE PIPELINE FINISHED after %.3fs",
                        time.perf_counter()
                        - pipeline_started_at,
                    )

                # ------------------------------------------------
                # RESET TURN STATE
                # ------------------------------------------------

                logger.info(
                    "Resetting voice turn state"
                )

                audio_buffer.clear()

                last_partial_audio_bytes = 0

                last_partial_text = ""

                logger.info(
                    "Voice turn reset complete"
                )

                continue

            # =================================================
            # PING
            # =================================================

            if message_type == "ping":

                logger.info(
                    "PING received"
                )

                await send_json(
                    {
                        "type": "pong",
                    }
                )

                continue

            # =================================================
            # CANCEL
            # =================================================

            if message_type == "cancel":

                logger.info(
                    "CANCEL received"
                )

                if partial_task is not None:

                    logger.info(
                        "Cancelling partial STT task"
                    )

                    partial_task.cancel()

                    try:

                        await partial_task

                    except asyncio.CancelledError:

                        pass

                    except Exception:

                        logger.exception(
                            "Partial STT failed during cancellation"
                        )

                    partial_task = None

                started = False

                audio_buffer.clear()

                last_partial_audio_bytes = 0

                last_partial_text = ""

                await send_json(
                    {
                        "type": "cancelled",
                    }
                )

                logger.info(
                    "CANCEL complete"
                )

                continue

            # =================================================
            # UNKNOWN
            # =================================================

            logger.error(
                "Unknown WS message type: %r",
                message_type,
            )

            await send_error(
                "unknown_message_type",
                (
                    f"Unknown message type: "
                    f"{message_type!r}"
                ),
            )

    except WebSocketDisconnect:

        logger.info(
            "=================================================="
        )

        logger.info(
            "VOICE WS DISCONNECTED"
        )

        logger.info(
            "client=%s",
            websocket.client,
        )

        logger.info(
            "application=%r",
            application,
        )

        logger.info(
            "=================================================="
        )

    except Exception:

        logger.exception(
            "UNHANDLED VOICE WS ERROR"
        )

        if partial_task is not None:

            partial_task.cancel()

        try:

            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR,
                reason="Internal server error",
            )

        except Exception:

            pass

    finally:

        if (
            partial_task is not None
            and not partial_task.done()
        ):

            partial_task.cancel()

        logger.info(
            "VOICE WS SESSION CLOSED: client=%s application=%r",
            websocket.client,
            application,
        )