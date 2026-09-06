from __future__ import annotations

import io
import logging
import time
import wave
from dataclasses import dataclass
from typing import AsyncIterable, AsyncIterator

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from src.clients.llama_stt import _transcribe
from src.clients.lmstudio import (
    streaming_completion,
)
from src.clients.pockettts import (
    stream_tts_pcm,
)
from src.schemas.ChatSchema import ChatRequest, Message


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

REALTIME_TTS_SAMPLE_RATE = 24_000
REALTIME_TTS_CHANNELS = 1
REALTIME_TTS_SAMPLE_WIDTH = 2


# ============================================================
# PIPELINE CONFIG
# ============================================================


@dataclass(slots=True)
class VoicePipelineConfig:
    """
    Configuration supplied to the voice orchestration pipeline.
    """

    # --------------------------------------------------------
    # STT
    # --------------------------------------------------------

    stt_prompt: str | None = None

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    system_prompt: str | None = None
    model: str | None = None

    temperature: float | None = 0.7
    top_p: float | None = 1.0
    max_tokens: int | None = None
    stop: object | None = None
    seed: int | None = None

    abstracted: bool = True

    # --------------------------------------------------------
    # TTS
    # --------------------------------------------------------

    voice: str = "jane"
    tts_temperature: float = 0.5


# ============================================================
# PIPELINE EVENTS
# ============================================================


@dataclass(slots=True)
class PipelineEvent:
    """
    Normalized internal pipeline event.

    The WebSocket layer determines how these events are
    transported to Quince.
    """

    type: str
    data: object | None = None


# ============================================================
# TEXT CHUNKER
# ============================================================


class TextChunker:
    """
    Converts streamed LLM tokens into TTS-sized phrases.
    """

    HARD_BOUNDARIES = (
        ".",
        "?",
        "!",
    )

    SOFT_BOUNDARIES = (
        ",",
        ";",
        ":",
    )

    def __init__(
        self,
        *,
        min_chars: int = 24,
        max_chars: int = 180,
        soft_boundary_min_chars: int = 55,
    ):

        self.min_chars = min_chars

        self.max_chars = max_chars

        self.soft_boundary_min_chars = (
            soft_boundary_min_chars
        )

        self._buffer = ""

    def add(
        self,
        token: str,
    ) -> list[str]:

        if not token:

            return []

        self._buffer += token

        chunks: list[str] = []

        while True:

            boundary = self._find_boundary()

            if boundary is None:

                break

            end_index, _ = boundary

            candidate = self._buffer[
                :end_index + 1
            ].strip()

            if not candidate:

                break

            chunks.append(
                candidate
            )

            self._buffer = self._buffer[
                end_index + 1:
            ]

        # ----------------------------------------------------
        # Maximum buffer protection
        # ----------------------------------------------------

        if len(self._buffer) >= self.max_chars:

            split_at = self._find_soft_split()

            if split_at is not None:

                candidate = self._buffer[
                    :split_at
                ].strip()

                if candidate:

                    chunks.append(
                        candidate
                    )

                    self._buffer = self._buffer[
                        split_at:
                    ]

        return chunks

    def flush(self) -> str | None:

        value = self._buffer.strip()

        self._buffer = ""

        return value or None

    def _find_boundary(
        self,
    ) -> tuple[int, str] | None:

        candidates = []

        for character in self.HARD_BOUNDARIES:

            index = self._buffer.find(
                character
            )

            if index >= self.min_chars:

                candidates.append(
                    (
                        index,
                        character,
                    )
                )

        if candidates:

            return min(
                candidates,
                key=lambda item: item[0],
            )

        for character in self.SOFT_BOUNDARIES:

            index = self._buffer.find(
                character
            )

            if index >= self.soft_boundary_min_chars:

                candidates.append(
                    (
                        index,
                        character,
                    )
                )

        if candidates:

            return min(
                candidates,
                key=lambda item: item[0],
            )

        return None

    def _find_soft_split(
        self,
    ) -> int | None:

        upper_bound = min(
            len(self._buffer),
            self.max_chars,
        )

        for index in range(
            upper_bound,
            self.min_chars,
            -1,
        ):

            if self._buffer[
                index - 1
            ].isspace():

                return index

        return None


# ============================================================
# LLM STREAM HELPER
# ============================================================


async def _stream_llm_text(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
) -> AsyncIterator[str]:

    started_at = time.perf_counter()

    logger.info(
        "=================================================="
    )

    logger.info(
        "LLM START"
    )

    logger.info(
        "LLM model=%r",
        config.model,
    )

    logger.info(
        "LLM messages=%d",
        len(messages),
    )

    logger.info(
        "LLM temperature=%r top_p=%r max_tokens=%r "
        "stop=%r seed=%r abstracted=%r",
        config.temperature,
        config.top_p,
        config.max_tokens,
        config.stop,
        config.seed,
        config.abstracted,
    )

    logger.info(
        "LLM system_prompt=%r",
        config.system_prompt,
    )

    logger.info(
        "=================================================="
    )

    request = ChatRequest(

        model=config.model,

        messages=messages,

        stream=True,

        temperature=config.temperature,

        top_p=config.top_p,

        max_tokens=config.max_tokens,

        stop=config.stop,

        seed=config.seed,

        system_prompt=config.system_prompt,

        abstracted=config.abstracted,
    )

    logger.info(
        "LLM request object created"
    )

    request_started_at = time.perf_counter()

    logger.info(
        "LLM: calling streaming_completion()"
    )

    try:

        response = await streaming_completion(
            request
        )

    except Exception:

        logger.exception(
            "LLM: streaming_completion() FAILED after %.3fs",
            time.perf_counter()
            - request_started_at,
        )

        raise

    logger.info(
        "LLM: streaming_completion() returned after %.3fs type=%s",
        time.perf_counter()
        - request_started_at,
        type(response).__name__,
    )

    if not isinstance(
        response,
        StreamingResponse,
    ):

        logger.error(
            "LLM: unexpected response type=%s",
            type(response).__name__,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "LLM streaming client returned "
                "an unexpected response."
            ),
        )

    logger.info(
        "LLM: beginning response.body_iterator"
    )

    first_token = True

    token_count = 0

    character_count = 0

    try:

        async for token in response.body_iterator:

            if token is None:

                continue

            if isinstance(
                token,
                bytes,
            ):

                token = token.decode(
                    "utf-8",
                    errors="replace",
                )

            token = str(
                token
            )

            if not token:

                continue

            token_count += 1

            character_count += len(token)

            if first_token:

                first_token = False

                logger.info(
                    "LLM FIRST TOKEN after %.3fs: %r",
                    time.perf_counter()
                    - started_at,
                    token,
                )

            else:

                logger.debug(
                    "LLM TOKEN #%d: %r",
                    token_count,
                    token,
                )

            yield token

    except Exception:

        logger.exception(
            "LLM token stream FAILED after %.3fs",
            time.perf_counter()
            - started_at,
        )

        raise

    logger.info(
        "=================================================="
    )

    logger.info(
        "LLM END"
    )

    logger.info(
        "LLM completed in %.3fs tokens=%d characters=%d",
        time.perf_counter()
        - started_at,
        token_count,
        character_count,
    )

    logger.info(
        "=================================================="
    )


# ============================================================
# SHARED LLM -> TTS
# ============================================================


async def llm_to_tts(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
) -> AsyncIterator[PipelineEvent]:

    started_at = time.perf_counter()

    logger.info(
        "=================================================="
    )

    logger.info(
        "LLM -> TTS START"
    )

    logger.info(
        "TTS voice=%r temperature=%r",
        config.voice,
        config.tts_temperature,
    )

    logger.info(
        "=================================================="
    )

    chunker = TextChunker()

    full_text: list[str] = []

    phrase_count = 0

    audio_chunk_count = 0

    audio_byte_count = 0

    async for token in _stream_llm_text(
        messages=messages,
        config=config,
    ):

        full_text.append(
            token
        )

        yield PipelineEvent(
            type="llm.token",
            data=token,
        )

        for phrase in chunker.add(
            token
        ):

            phrase_count += 1

            logger.info(
                "TTS PHRASE #%d READY: %r",
                phrase_count,
                phrase,
            )

            yield PipelineEvent(
                type="tts.started",
                data=phrase,
            )

            tts_started_at = (
                time.perf_counter()
            )

            logger.info(
                "TTS: starting phrase #%d",
                phrase_count,
            )

            try:

                async for audio_chunk in stream_tts_pcm(

                    text=phrase,

                    voice=config.voice,

                    temperature=config.tts_temperature,

                ):

                    if isinstance(
                        audio_chunk,
                        bytes,
                    ):

                        audio_chunk_count += 1

                        audio_byte_count += (
                            len(audio_chunk)
                        )

                        logger.debug(
                            "TTS AUDIO CHUNK #%d size=%d",
                            audio_chunk_count,
                            len(audio_chunk),
                        )

                    else:

                        logger.error(
                            "TTS returned %s instead of bytes",
                            type(audio_chunk).__name__,
                        )

                    yield PipelineEvent(
                        type="tts.audio",
                        data=audio_chunk,
                    )

            except Exception:

                logger.exception(
                    "TTS FAILED for phrase #%d after %.3fs",
                    phrase_count,
                    time.perf_counter()
                    - tts_started_at,
                )

                raise

            logger.info(
                "TTS: phrase #%d completed in %.3fs",
                phrase_count,
                time.perf_counter()
                - tts_started_at,
            )

            yield PipelineEvent(
                type="tts.completed",
                data=phrase,
            )

    # --------------------------------------------------------
    # Flush final LLM fragment
    # --------------------------------------------------------

    final_phrase = chunker.flush()

    if final_phrase:

        phrase_count += 1

        logger.info(
            "TTS FINAL PHRASE #%d READY: %r",
            phrase_count,
            final_phrase,
        )

        yield PipelineEvent(
            type="tts.started",
            data=final_phrase,
        )

        tts_started_at = (
            time.perf_counter()
        )

        try:

            async for audio_chunk in stream_tts_pcm(

                text=final_phrase,

                voice=config.voice,

                temperature=config.tts_temperature,

            ):

                if isinstance(
                    audio_chunk,
                    bytes,
                ):

                    audio_chunk_count += 1

                    audio_byte_count += (
                        len(audio_chunk)
                    )

                    logger.debug(
                        "TTS AUDIO CHUNK #%d size=%d",
                        audio_chunk_count,
                        len(audio_chunk),
                    )

                else:

                    logger.error(
                        "TTS returned %s instead of bytes",
                        type(audio_chunk).__name__,
                    )

                yield PipelineEvent(
                    type="tts.audio",
                    data=audio_chunk,
                )

        except Exception:

            logger.exception(
                "TTS FINAL PHRASE FAILED after %.3fs",
                time.perf_counter()
                - tts_started_at,
            )

            raise

        logger.info(
            "TTS: final phrase completed in %.3fs",
            time.perf_counter()
            - tts_started_at,
        )

        yield PipelineEvent(
            type="tts.completed",
            data=final_phrase,
        )

    final_text = "".join(
        full_text
    ).strip()

    logger.info(
        "LLM FINAL TEXT: %r",
        final_text,
    )

    yield PipelineEvent(
        type="llm.final",
        data=final_text,
    )

    logger.info(
        "=================================================="
    )

    logger.info(
        "LLM -> TTS END"
    )

    logger.info(
        "LLM -> TTS completed in %.3fs "
        "phrases=%d audio_chunks=%d audio_bytes=%d "
        "text_chars=%d",
        time.perf_counter()
        - started_at,
        phrase_count,
        audio_chunk_count,
        audio_byte_count,
        len(final_text),
    )

    logger.info(
        "=================================================="
    )


# ============================================================
# TEXT -> VOICE
# ============================================================


async def text_to_voice(
    *,
    text: str,
    config: VoicePipelineConfig,
    messages: list[Message] | None = None,
) -> AsyncIterator[PipelineEvent]:

    text = text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty.",
        )

    conversation = list(
        messages or []
    )

    conversation.append(
        Message(
            role="user",
            content=text,
        )
    )

    logger.info(
        "TEXT -> VOICE START text_chars=%d messages=%d",
        len(text),
        len(conversation),
    )

    yield PipelineEvent(
        type="pipeline.started",
        data={
            "mode": "text_to_voice",
        },
    )

    async for event in llm_to_tts(
        messages=conversation,
        config=config,
    ):

        yield event

    yield PipelineEvent(
        type="pipeline.completed",
        data={
            "mode": "text_to_voice",
        },
    )

    logger.info(
        "TEXT -> VOICE COMPLETE"
    )


# ============================================================
# PCM -> WAV
# ============================================================


def _pcm_to_wav(
    pcm_audio: bytes,
    *,
    sample_rate: int = 16_000,
) -> bytes:

    logger.info(
        "PCM -> WAV: input_bytes=%d sample_rate=%d",
        len(pcm_audio),
        sample_rate,
    )

    if not pcm_audio:

        logger.error(
            "PCM -> WAV: empty audio"
        )

        raise HTTPException(
            status_code=400,
            detail="Audio is empty.",
        )

    output = io.BytesIO()

    with wave.open(
        output,
        "wb",
    ) as wav_file:

        wav_file.setnchannels(
            1
        )

        wav_file.setsampwidth(
            2
        )

        wav_file.setframerate(
            sample_rate
        )

        wav_file.writeframes(
            pcm_audio
        )

    wav_bytes = output.getvalue()

    logger.info(
        "PCM -> WAV COMPLETE: output_bytes=%d",
        len(wav_bytes),
    )

    return wav_bytes


# ============================================================
# VOICE -> VOICE
# ============================================================


async def voice_to_voice(
    *,
    audio_stream: AsyncIterable[bytes],
    config: VoicePipelineConfig,
    messages: list[Message] | None = None,
) -> AsyncIterator[PipelineEvent]:

    pipeline_started_at = time.perf_counter()

    logger.info(
        "##################################################"
    )

    logger.info(
        "VOICE_TO_VOICE START"
    )

    logger.info(
        "STT prompt=%r",
        config.stt_prompt,
    )

    logger.info(
        "LLM model=%r temperature=%r top_p=%r "
        "max_tokens=%r stop=%r seed=%r "
        "abstracted=%r",
        config.model,
        config.temperature,
        config.top_p,
        config.max_tokens,
        config.stop,
        config.seed,
        config.abstracted,
    )

    logger.info(
        "LLM system_prompt=%r",
        config.system_prompt,
    )

    logger.info(
        "incoming messages=%d",
        len(messages or []),
    )

    logger.info(
        "TTS voice=%r temperature=%r",
        config.voice,
        config.tts_temperature,
    )

    logger.info(
        "##################################################"
    )

    yield PipelineEvent(
        type="pipeline.started",
        data={
            "mode": "voice_to_voice",
        },
    )

    logger.info(
        "VOICE_TO_VOICE: pipeline.started emitted"
    )

    audio_buffer = bytearray()

    chunk_count = 0

    # --------------------------------------------------------
    # COLLECT AUDIO
    # --------------------------------------------------------

    logger.info(
        "VOICE_TO_VOICE: collecting audio..."
    )

    try:

        async for chunk in audio_stream:

            if not chunk:

                continue

            chunk_count += 1

            audio_buffer.extend(
                chunk
            )

            logger.debug(
                "VOICE_TO_VOICE AUDIO #%d size=%d total=%d",
                chunk_count,
                len(chunk),
                len(audio_buffer),
            )

    except Exception:

        logger.exception(
            "VOICE_TO_VOICE: audio collection FAILED"
        )

        raise

    logger.info(
        "VOICE_TO_VOICE: audio collection complete "
        "chunks=%d bytes=%d",
        chunk_count,
        len(audio_buffer),
    )

    if not audio_buffer:

        logger.error(
            "VOICE_TO_VOICE: NO AUDIO"
        )

        raise HTTPException(
            status_code=400,
            detail="No audio was received.",
        )

    audio_seconds = (
        len(audio_buffer)
        / (
            16_000
            * 2
        )
    )

    logger.info(
        "VOICE_TO_VOICE: input duration=%.3fs",
        audio_seconds,
    )

    # --------------------------------------------------------
    # PCM -> WAV
    # --------------------------------------------------------

    wav_started_at = time.perf_counter()

    logger.info(
        "VOICE_TO_VOICE: converting PCM -> WAV"
    )

    wav_bytes = _pcm_to_wav(
        bytes(audio_buffer)
    )

    logger.info(
        "VOICE_TO_VOICE: WAV conversion took %.3fs",
        time.perf_counter()
        - wav_started_at,
    )

    # --------------------------------------------------------
    # STT UPLOAD
    # --------------------------------------------------------

    upload = UploadFile(
        file=io.BytesIO(
            wav_bytes
        ),
        filename="voice.wav",
        headers=Headers({
            "content-type": "audio/wav",
        }),
    )

    logger.info(
        "VOICE_TO_VOICE: UploadFile created"
    )

    # --------------------------------------------------------
    # STT
    # --------------------------------------------------------

    logger.info(
        "=================================================="
    )

    logger.info(
        "STT START"
    )

    logger.info(
        "STT: calling _transcribe()"
    )

    logger.info(
        "STT: prompt=%r wav_bytes=%d",
        config.stt_prompt,
        len(wav_bytes),
    )

    yield PipelineEvent(
        type="stt.started",
    )

    stt_started_at = time.perf_counter()

    try:

        stt_result = await _transcribe(
            file=upload,
            prompt=config.stt_prompt,
        )

    except Exception:

        logger.exception(
            "STT FAILED after %.3fs",
            time.perf_counter()
            - stt_started_at,
        )

        raise

    logger.info(
        "STT backend returned after %.3fs",
        time.perf_counter()
        - stt_started_at,
    )

    logger.info(
        "STT result type=%s",
        type(stt_result).__name__,
    )

    transcript = ""

    if isinstance(
        stt_result,
        dict,
    ):

        transcript = str(
            stt_result.get(
                "text",
                "",
            )
            or ""
        ).strip()

    else:

        transcript = str(
            stt_result
        ).strip()

    logger.info(
        "STT FINAL TRANSCRIPT: %r",
        transcript,
    )

    logger.info(
        "STT COMPLETE in %.3fs",
        time.perf_counter()
        - stt_started_at,
    )

    logger.info(
        "=================================================="
    )

    yield PipelineEvent(
        type="stt.final",
        data=transcript,
    )

    if not transcript:

        logger.warning(
            "VOICE_TO_VOICE: empty transcript"
        )

        yield PipelineEvent(
            type="pipeline.completed",
            data={
                "mode": "voice_to_voice",
                "empty_transcript": True,
            },
        )

        logger.info(
            "VOICE_TO_VOICE COMPLETE in %.3fs "
            "(empty transcript)",
            time.perf_counter()
            - pipeline_started_at,
        )

        return

    # --------------------------------------------------------
    # LLM CONVERSATION
    # --------------------------------------------------------

    conversation = list(
        messages or []
    )

    logger.info(
        "VOICE_TO_VOICE: existing conversation messages=%d",
        len(conversation),
    )

    conversation.append(
        Message(
            role="user",
            content=transcript,
        )
    )

    logger.info(
        "VOICE_TO_VOICE: final LLM conversation messages=%d",
        len(conversation),
    )

    logger.debug(
        "VOICE_TO_VOICE: conversation=%r",
        conversation,
    )

    # --------------------------------------------------------
    # LLM -> TTS
    # --------------------------------------------------------

    logger.info(
        "VOICE_TO_VOICE: entering llm_to_tts()"
    )

    llm_tts_started_at = (
        time.perf_counter()
    )

    try:

        async for event in llm_to_tts(
            messages=conversation,
            config=config,
        ):

            logger.debug(
                "VOICE_TO_VOICE: yielded event=%s",
                event.type,
            )

            yield event

    except Exception:

        logger.exception(
            "VOICE_TO_VOICE: llm_to_tts() FAILED "
            "after %.3fs",
            time.perf_counter()
            - llm_tts_started_at,
        )

        raise

    logger.info(
        "VOICE_TO_VOICE: llm_to_tts() completed in %.3fs",
        time.perf_counter()
        - llm_tts_started_at,
    )

    yield PipelineEvent(
        type="pipeline.completed",
        data={
            "mode": "voice_to_voice",
        },
    )

    logger.info(
        "##################################################"
    )

    logger.info(
        "VOICE_TO_VOICE COMPLETE in %.3fs",
        time.perf_counter()
        - pipeline_started_at,
    )

    logger.info(
        "##################################################"
    )