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
from src.clients.lmstudio import streaming_completion
from src.clients.pockettts import stream_tts_pcm
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
    """Configuration supplied to the voice pipeline."""

    # STT
    stt_prompt: str | None = None

    # LLM
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = 0.7
    top_p: float | None = 1.0
    max_tokens: int | None = None
    stop: object | None = None
    seed: int | None = None
    abstracted: bool = True

    # TTS
    voice: str = "jane"
    tts_temperature: float = 0.5


# ============================================================
# PIPELINE EVENTS
# ============================================================


@dataclass(slots=True)
class PipelineEvent:
    """Normalized internal pipeline event."""

    type: str
    data: object | None = None


# ============================================================
# TEXT CHUNKER
# ============================================================


class TextChunker:

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

            chunks.append(candidate)

            self._buffer = self._buffer[
                end_index + 1:
            ]

        if len(self._buffer) >= self.max_chars:

            split_at = self._find_soft_split()

            if split_at is not None:

                candidate = self._buffer[
                    :split_at
                ].strip()

                if candidate:

                    chunks.append(candidate)

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

            index = self._buffer.find(character)

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

            index = self._buffer.find(character)

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

            if self._buffer[index - 1].isspace():

                return index

        return None


# ============================================================
# PCM -> WAV
# ============================================================


def _pcm_to_wav(
    pcm_audio: bytes,
    *,
    sample_rate: int = 16_000,
) -> bytes:

    if not pcm_audio:

        raise HTTPException(
            status_code=400,
            detail="Audio is empty.",
        )

    output = io.BytesIO()

    with wave.open(output, "wb") as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_audio)

    return output.getvalue()


# ============================================================
# STT
# ============================================================


async def speech_to_text(
    *,
    audio: bytes,
    prompt: str | None = None,
) -> str:

    started_at = time.perf_counter()

    logger.info(
        "STT START bytes=%d",
        len(audio),
    )

    if not audio:

        raise HTTPException(
            status_code=400,
            detail="No audio was received.",
        )

    wav_bytes = _pcm_to_wav(audio)

    upload = UploadFile(
        file=io.BytesIO(wav_bytes),
        filename="voice.wav",
        headers=Headers({
            "content-type": "audio/wav",
        }),
    )

    try:

        result = await _transcribe(
            file=upload,
            prompt=prompt,
        )

    except Exception:

        logger.exception(
            "STT FAILED after %.3fs",
            time.perf_counter() - started_at,
        )

        raise

    if isinstance(result, dict):

        transcript = str(
            result.get(
                "text",
                "",
            )
            or ""
        ).strip()

    else:

        transcript = str(result).strip()

    logger.info(
        "STT COMPLETE in %.3fs transcript=%r",
        time.perf_counter() - started_at,
        transcript,
    )

    return transcript


# ============================================================
# LLM
# ============================================================


async def stream_llm(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
) -> AsyncIterator[str]:

    started_at = time.perf_counter()

    logger.info(
        "LLM START model=%r messages=%d",
        config.model,
        len(messages),
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

    try:

        response = await streaming_completion(
            request
        )

    except Exception:

        logger.exception(
            "LLM REQUEST FAILED after %.3fs",
            time.perf_counter() - started_at,
        )

        raise

    if not isinstance(
        response,
        StreamingResponse,
    ):

        raise HTTPException(
            status_code=502,
            detail=(
                "LLM streaming client returned "
                "an unexpected response."
            ),
        )

    token_count = 0

    try:

        async for token in response.body_iterator:

            if token is None:
                continue

            if isinstance(token, bytes):

                token = token.decode(
                    "utf-8",
                    errors="replace",
                )

            token = str(token)

            if not token:
                continue

            token_count += 1

            yield token

    except Exception:

        logger.exception(
            "LLM STREAM FAILED after %.3fs",
            time.perf_counter() - started_at,
        )

        raise

    logger.info(
        "LLM COMPLETE in %.3fs tokens=%d",
        time.perf_counter() - started_at,
        token_count,
    )


# ============================================================
# TTS
# ============================================================


async def text_to_speech(
    *,
    text: str,
    config: VoicePipelineConfig,
) -> AsyncIterator[bytes]:

    text = text.strip()

    if not text:
        return

    started_at = time.perf_counter()

    logger.info(
        "TTS START voice=%r chars=%d",
        config.voice,
        len(text),
    )

    try:

        async for audio_chunk in stream_tts_pcm(
            text=text,
            voice=config.voice,
            temperature=config.tts_temperature,
        ):

            if not isinstance(
                audio_chunk,
                bytes,
            ):

                logger.warning(
                    "TTS returned %s instead of bytes",
                    type(audio_chunk).__name__,
                )

                continue

            if not audio_chunk:
                continue

            yield audio_chunk

    except Exception:

        logger.exception(
            "TTS FAILED after %.3fs",
            time.perf_counter() - started_at,
        )

        raise

    logger.info(
        "TTS COMPLETE in %.3fs",
        time.perf_counter() - started_at,
    )


# ============================================================
# LLM -> TTS STREAM
# ============================================================


async def llm_to_speech(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
) -> AsyncIterator[PipelineEvent]:
    chunker = TextChunker()
    full_text: list[str] = []

    async for token in stream_llm(
        messages=messages,
        config=config,
    ):

        full_text.append(token)

        yield PipelineEvent(
            type="llm.token",
            data=token,
        )

        for phrase in chunker.add(token):

            yield PipelineEvent(
                type="tts.started",
                data=phrase,
            )

            async for audio_chunk in text_to_speech(
                text=phrase,
                config=config,
            ):

                yield PipelineEvent(
                    type="tts.audio",
                    data=audio_chunk,
                )

            yield PipelineEvent(
                type="tts.completed",
                data=phrase,
            )

    final_phrase = chunker.flush()

    if final_phrase:

        yield PipelineEvent(
            type="tts.started",
            data=final_phrase,
        )

        async for audio_chunk in text_to_speech(
            text=final_phrase,
            config=config,
        ):

            yield PipelineEvent(
                type="tts.audio",
                data=audio_chunk,
            )

        yield PipelineEvent(
            type="tts.completed",
            data=final_phrase,
        )

    final_text = "".join(full_text).strip()

    yield PipelineEvent(
        type="llm.final",
        data=final_text,
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

    yield PipelineEvent(
        type="pipeline.started",
        data={
            "mode": "text_to_voice",
        },
    )

    async for event in llm_to_speech(
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

    yield PipelineEvent(
        type="pipeline.started",
        data={
            "mode": "voice_to_voice",
        },
    )

    # --------------------------------------------------------
    # COLLECT AUDIO
    # --------------------------------------------------------

    audio_buffer = bytearray()

    async for chunk in audio_stream:

        if chunk:

            audio_buffer.extend(chunk)

    if not audio_buffer:

        raise HTTPException(
            status_code=400,
            detail="No audio was received.",
        )

    # --------------------------------------------------------
    # STT
    # --------------------------------------------------------

    yield PipelineEvent(
        type="stt.started",
    )

    transcript = await speech_to_text(
        audio=bytes(audio_buffer),
        prompt=config.stt_prompt,
    )

    yield PipelineEvent(
        type="stt.final",
        data=transcript,
    )

    if not transcript:

        yield PipelineEvent(
            type="pipeline.completed",
            data={
                "mode": "voice_to_voice",
                "empty_transcript": True,
            },
        )

        return

    # --------------------------------------------------------
    # BUILD CONVERSATION
    # --------------------------------------------------------

    # TODO: RAG

    conversation = list(
        messages or []
    )

    conversation.append(
        Message(
            role="user",
            content=transcript,
        )
    )

    # --------------------------------------------------------
    # LLM -> TTS
    # --------------------------------------------------------

    async for event in llm_to_speech(
        messages=conversation,
        config=config,
    ):

        yield event

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    yield PipelineEvent(
        type="pipeline.completed",
        data={
            "mode": "voice_to_voice",
        },
    )

    logger.info(
        "VOICE_TO_VOICE COMPLETE in %.3fs",
        time.perf_counter()
        - pipeline_started_at,
    )