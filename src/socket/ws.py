from __future__ import annotations

import asyncio
import json
import logging
from typing import Final

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

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
from src.services.chat_pipeline import (
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


def _json_event(event: PipelineEvent) -> dict:
    """
    Convert an internal pipeline event into a JSON-safe object.

    Binary TTS events are handled separately by the WebSocket
    transport and are never passed through here.
    """

    return {
        "type": event.type,
        "data": event.data,
    }


# ============================================================
# VOICE WEBSOCKET
# ============================================================


@router.websocket(WS_PATH)
async def stt_stream(
    websocket: WebSocket,
) -> None:
    """
    Basket voice-to-voice WebSocket transport.

    Client -> Server:

        {"type":"start", ...}
        <binary PCM16 mono 16 kHz frames>
        ...
        {"type":"stop"}

    Optional control messages:

        {"type":"cancel"}
        {"type":"ping"}

    The start message contains:

        STT:
            prompt
            stream
            sample_rate

        LLM:
            model
            messages
            temperature
            top_p
            max_tokens
            stop
            seed
            system_prompt
            abstracted

        TTS:
            voice
            temperature

    TTS text is intentionally not supplied by the client.
    Basket derives TTS text from the generated LLM response.
    """

    await websocket.accept()

    logger.info(
        "Voice WebSocket connected: client=%s",
        websocket.client,
    )

    started = False

    voice_config = VoiceStartRequest()

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

    async def send_json(
        payload: dict,
    ) -> None:

        async with send_lock:

            await websocket.send_json(
                payload
            )

    async def send_error(
        code: str,
        message: str,
    ) -> None:

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

        return int(
            STREAM_WINDOW_SECONDS
            * voice_config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    def min_audio_bytes() -> int:

        return int(
            STREAM_MIN_AUDIO_SECONDS
            * voice_config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    def partial_interval_bytes() -> int:

        return int(
            STREAM_PARTIAL_INTERVAL_SECONDS
            * voice_config.sample_rate
            * STREAM_SAMPLE_WIDTH
        )

    # ========================================================
    # LIVE PARTIAL STT
    # ========================================================

    async def run_partial_stt() -> None:

        nonlocal last_partial_audio_bytes
        nonlocal last_partial_text

        current = bytes(
            audio_buffer
        )

        rolling = current[
            -window_bytes():
        ]

        if len(rolling) < min_audio_bytes():

            return

        try:

            import httpx

            async with httpx.AsyncClient(
                timeout=_timeout()
            ) as client:

                result = (
                    await _stream_transcribe_window(
                        client,
                        rolling,
                        prompt=voice_config.prompt,
                        sample_rate=voice_config.sample_rate,
                    )
                )

            text = str(
                result.get(
                    "text",
                    "",
                )
                or ""
            ).strip()

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

        except asyncio.CancelledError:

            raise

        except Exception as exc:

            logger.exception(
                "Partial STT failed: client=%s",
                websocket.client,
            )

            await send_error(
                "asr_partial_failed",
                str(exc),
            )

    def maybe_start_partial_stt() -> None:

        nonlocal partial_task

        if not voice_config.stream:

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
                    "Partial STT task crashed."
                )

        partial_task.add_done_callback(
            clear_partial_task
        )

    # ========================================================
    # END-TO-END PIPELINE
    # ========================================================

    async def run_pipeline() -> None:

        async def audio_source():

            if audio_buffer:

                yield bytes(
                    audio_buffer
                )

        config = VoicePipelineConfig(

            # ------------------------------------------------
            # STT
            # ------------------------------------------------

            stt_prompt=voice_config.prompt,

            # ------------------------------------------------
            # LLM
            # ------------------------------------------------

            system_prompt=(
                voice_config.llm.system_prompt
            ),

            model=(
                voice_config.llm.model
            ),

            temperature=(
                voice_config.llm.temperature
            ),

            top_p=(
                voice_config.llm.top_p
            ),

            max_tokens=(
                voice_config.llm.max_tokens
            ),

            stop=(
                voice_config.llm.stop
            ),

            seed=(
                voice_config.llm.seed
            ),

            abstracted=(
                voice_config.llm.abstracted
            ),

            # ------------------------------------------------
            # TTS
            # ------------------------------------------------

            voice=(
                voice_config.tts.voice
            ),

            tts_temperature=(
                voice_config.tts.temperature
            ),
        )

        async for event in voice_to_voice(

            audio_stream=audio_source(),

            config=config,

            messages=list(
                voice_config.llm.messages
            ),
        ):

            # ------------------------------------------------
            # TTS AUDIO
            # ------------------------------------------------

            if event.type == "tts.audio":

                audio = event.data

                if not isinstance(
                    audio,
                    bytes,
                ):

                    continue

                async with send_lock:

                    await websocket.send_bytes(
                        audio
                    )

                continue

            # ------------------------------------------------
            # JSON EVENTS
            # ------------------------------------------------

            await send_json(
                _json_event(event)
            )

    # ========================================================
    # READY
    # ========================================================

    try:

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

        # ====================================================
        # MAIN LOOP
        # ====================================================

        while True:

            message = await websocket.receive()

            # ------------------------------------------------
            # DISCONNECT
            # ------------------------------------------------

            if (
                message.get("type")
                == "websocket.disconnect"
            ):

                logger.info(
                    (
                        "Voice WebSocket disconnected: "
                        "client=%s"
                    ),
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

                    continue

                audio_buffer.extend(
                    audio
                )

                maybe_start_partial_stt()

                continue

            # ------------------------------------------------
            # TEXT / JSON
            # ------------------------------------------------

            text = message.get(
                "text"
            )

            if text is None:

                await send_error(
                    "invalid_message",
                    (
                        "Expected a JSON control "
                        "message or binary audio."
                    ),
                )

                continue

            try:

                payload = json.loads(
                    text
                )

            except json.JSONDecodeError:

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

            # =================================================
            # START
            # =================================================

            if message_type == "start":

                if started:

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

                    await send_error(
                        "invalid_start",
                        str(exc),
                    )

                    continue

                if (
                    request.sample_rate
                    != STREAM_SAMPLE_RATE
                ):

                    await send_error(
                        "unsupported_sample_rate",
                        (
                            "Basket requires "
                            "16,000 Hz PCM16 mono "
                            "input audio."
                        ),
                    )

                    continue

                voice_config = request

                started = True

                audio_buffer.clear()

                last_partial_audio_bytes = 0

                last_partial_text = ""

                logger.info(
                    (
                        "Voice stream started: "
                        "client=%s "
                        "stream=%s "
                        "model=%s "
                        "voice=%s"
                    ),
                    websocket.client,
                    voice_config.stream,
                    voice_config.llm.model,
                    voice_config.tts.voice,
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

                continue

            # =================================================
            # STOP
            # =================================================

            if message_type == "stop":

                if not started:

                    await send_error(
                        "not_started",
                        (
                            "Voice stream has "
                            "not been started."
                        ),
                    )

                    continue

                started = False

                # ------------------------------------------------
                # Finish pending partial STT
                # ------------------------------------------------

                if partial_task is not None:

                    try:

                        await partial_task

                    except asyncio.CancelledError:

                        pass

                    except Exception:

                        logger.exception(
                            (
                                "Partial STT task "
                                "failed during finalization."
                            )
                        )

                    partial_task = None

                logger.info(
                    (
                        "Voice stream stopped: "
                        "client=%s "
                        "audio_seconds=%.2f"
                    ),
                    websocket.client,
                    stream_audio_duration_seconds(
                        bytes(audio_buffer),
                        sample_rate=(
                            voice_config.sample_rate
                        ),
                    ),
                )

                # ------------------------------------------------
                # No audio
                # ------------------------------------------------

                if not audio_buffer:

                    await send_json(
                        {
                            "type": "final",
                            "text": "",
                        }
                    )

                    continue

                # ------------------------------------------------
                # END-TO-END PIPELINE
                # ------------------------------------------------

                try:

                    await run_pipeline()

                except asyncio.CancelledError:

                    raise

                except Exception as exc:

                    logger.exception(
                        (
                            "Voice pipeline failed: "
                            "client=%s"
                        ),
                        websocket.client,
                    )

                    await send_error(
                        "pipeline_failed",
                        str(exc),
                    )

                # ------------------------------------------------
                # Reset utterance state
                # ------------------------------------------------

                audio_buffer.clear()

                last_partial_audio_bytes = 0

                last_partial_text = ""

                continue

            # =================================================
            # PING
            # =================================================

            if message_type == "ping":

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

                if partial_task is not None:

                    partial_task.cancel()

                    try:

                        await partial_task

                    except asyncio.CancelledError:

                        pass

                    except Exception:

                        logger.exception(
                            (
                                "Partial STT task "
                                "failed during cancellation."
                            )
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

                continue

            # =================================================
            # UNKNOWN
            # =================================================

            await send_error(
                "unknown_message_type",
                (
                    f"Unknown message type: "
                    f"{message_type!r}"
                ),
            )

    except WebSocketDisconnect:

        logger.info(
            (
                "Voice WebSocket disconnected "
                "unexpectedly: client=%s"
            ),
            websocket.client,
        )

    except Exception:

        logger.exception(
            (
                "Unhandled Voice WebSocket error: "
                "client=%s"
            ),
            websocket.client,
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
            "Voice WebSocket session closed: client=%s",
            websocket.client,
        )