from __future__ import annotations

import io
import logging
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

# Basket's realtime audio contract.
#
# Pocket TTS currently emits mono 16-bit PCM and typically
# operates at 24 kHz. The stream_tts_pcm adapter validates the
# incoming WAV format before exposing PCM to this service.
REALTIME_TTS_SAMPLE_RATE = 24_000
REALTIME_TTS_CHANNELS = 1
REALTIME_TTS_SAMPLE_WIDTH = 2


# ============================================================
# PIPELINE CONFIG
# ============================================================


@dataclass(slots=True)
class VoicePipelineConfig:
    """
    Client-supplied configuration for Basket's orchestration
    pipeline.
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
    Normalized internal event.

    The WebSocket layer decides how these events are serialized.
    The service does not know or care whether the caller is
    Quince, Kiwi, another fruit, or an HTTP endpoint.
    """

    type: str
    data: object | None = None


# ============================================================
# TEXT CHUNKER
# ============================================================


class TextChunker:
    """
    Converts an LLM token stream into TTS-sized phrases.

    Punctuation is preferred, but the chunker also prevents
    indefinite waiting when an LLM produces a long sentence
    without punctuation.
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

            end_index, character = boundary

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

        # Hard punctuation can trigger fairly early.
        for character in self.HARD_BOUNDARIES:

            index = self._buffer.find(
                character
            )

            if index >= self.min_chars:

                candidates.append(
                    (index, character)
                )

        if candidates:

            return min(
                candidates,
                key=lambda item: item[0],
            )

        # Soft punctuation needs more text so TTS does not
        # receive tiny fragments such as "Okay,".
        for character in self.SOFT_BOUNDARIES:

            index = self._buffer.find(
                character
            )

            if index >= self.soft_boundary_min_chars:

                candidates.append(
                    (index, character)
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
    """
    Consume Basket's existing LLM streaming client directly.

    No HTTP round-trip through Basket itself.
    """

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
        abstracted=True,
    )

    response = await streaming_completion(
        request
    )

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

    async for token in response.body_iterator:

        if token is None:
            continue

        if isinstance(token, bytes):

            token = token.decode(
                "utf-8",
                errors="replace",
            )

        token = str(token)

        if token:
            yield token


# ============================================================
# SHARED LLM -> TTS
# ============================================================


async def llm_to_tts(
    *,
    messages: list[Message],
    config: VoicePipelineConfig,
) -> AsyncIterator[PipelineEvent]:
    """
    Shared realtime LLM -> TTS pipeline.

            LLM tokens
                 ↓
            text buffer
                 ↓
          natural boundary
                 ↓
              TTS
                 ↓
             PCM audio

    Used by BOTH:

        text -> LLM -> TTS
        voice -> STT -> LLM -> TTS
    """

    chunker = TextChunker()

    full_text: list[str] = []

    logger.debug(
        "Basket LLM -> TTS pipeline started."
    )

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

            yield PipelineEvent(
                type="tts.started",
                data=phrase,
            )

            async for audio_chunk in stream_tts_pcm(
                text=phrase,
                voice=config.voice,
                temperature=config.tts_temperature,
            ):

                yield PipelineEvent(
                    type="tts.audio",
                    data=audio_chunk,
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

        yield PipelineEvent(
            type="tts.started",
            data=final_phrase,
        )

        async for audio_chunk in stream_tts_pcm(
            text=final_phrase,
            voice=config.voice,
            temperature=config.tts_temperature,
        ):

            yield PipelineEvent(
                type="tts.audio",
                data=audio_chunk,
            )

        yield PipelineEvent(
            type="tts.completed",
            data=final_phrase,
        )

    final_text = "".join(
        full_text
    ).strip()

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
    """
    Text -> LLM -> TTS.

    This is the pipeline Quince can use for agentic progress
    updates, notifications, announcements, etc.
    """

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


# ============================================================
# PCM -> WAV
# ============================================================


def _pcm_to_wav(
    pcm_audio: bytes,
    *,
    sample_rate: int = 16_000,
) -> bytes:
    """
    Convert Basket's realtime microphone contract:

        PCM16 mono 16 kHz

    into the WAV file expected by the current llama.cpp
    transcription endpoint.
    """

    if not pcm_audio:

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

    return output.getvalue()


# ============================================================
# VOICE -> VOICE
# ============================================================


async def voice_to_voice(
    *,
    audio_stream: AsyncIterable[bytes],
    config: VoicePipelineConfig,
    messages: list[Message] | None = None,
) -> AsyncIterator[PipelineEvent]:
    """
    Voice -> STT -> LLM -> TTS.

    The WebSocket layer feeds microphone PCM frames into
    audio_stream.

    The current llama.cpp STT backend remains a file-based
    transcription API, so this orchestration stage accumulates
    the utterance and performs one authoritative final STT pass.

    The LLM -> TTS stage is exactly the same implementation
    used by text_to_voice().
    """

    yield PipelineEvent(
        type="pipeline.started",
        data={
            "mode": "voice_to_voice",
        },
    )

    audio_buffer = bytearray()

    # --------------------------------------------------------
    # Collect microphone stream
    # --------------------------------------------------------

    async for chunk in audio_stream:

        if not chunk:
            continue

        audio_buffer.extend(
            chunk
        )

    if not audio_buffer:

        raise HTTPException(
            status_code=400,
            detail="No audio was received.",
        )

    # --------------------------------------------------------
    # Convert PCM -> WAV
    # --------------------------------------------------------

    wav_bytes = _pcm_to_wav(
        bytes(audio_buffer)
    )

    # --------------------------------------------------------
    # Reuse existing STT client
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

    yield PipelineEvent(
        type="stt.started",
    )

    stt_result = await _transcribe(
        file=upload,
        prompt=config.stt_prompt,
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
    # Build LLM conversation
    # --------------------------------------------------------

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
    # Shared LLM -> TTS
    # --------------------------------------------------------

    async for event in llm_to_tts(
        messages=conversation,
        config=config,
    ):

        yield event

    yield PipelineEvent(
        type="pipeline.completed",
        data={
            "mode": "voice_to_voice",
        },
    )