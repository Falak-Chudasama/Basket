from __future__ import annotations
import asyncio
import io
import logging
import time
import wave
from dataclasses import dataclass
from typing import AsyncIterable, AsyncIterator
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from starlette.datastructures import Headers, UploadFile

from src.clients.llama_stt import _transcribe
from src.clients.lm_studio import streaming_completion
from src.clients.pocket_tts import stream_tts_pcm
from src.schemas.ChatSchema import ChatRequest, Message

logger = logging.getLogger(__name__)


REALTIME_TTS_SAMPLE_RATE = 24_000
REALTIME_TTS_CHANNELS = 1
REALTIME_TTS_SAMPLE_WIDTH = 2

@dataclass(slots=True)
class VoicePipelineConfig:
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


@dataclass(slots=True)
class PipelineEvent:
    type: str
    data: object | None = None

class TextChunker:
    HARD_BOUNDARIES = (".", "?", "!")
    SOFT_BOUNDARIES = (",", ";", ":")

    def __init__(
        self,
        *,
        min_chars: int = 12,
        max_chars: int = 180,
        soft_boundary_min_chars: int = 55,
        first_chunk_min_chars: int = 6,
    ):
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.soft_boundary_min_chars = soft_boundary_min_chars
        self.first_chunk_min_chars = first_chunk_min_chars

        self._buffer = ""
        self._emitted_first_chunk = False

    def add(self, token: str) -> list[str]:
        if not token:
            return []

        self._buffer += token
        chunks: list[str] = []

        while True:
            boundary = self._find_boundary()
            if boundary is None:
                break

            end_index, _ = boundary
            candidate = self._buffer[: end_index + 1].strip()
            if not candidate:
                break

            chunks.append(candidate)
            self._emitted_first_chunk = True
            self._buffer = self._buffer[end_index + 1 :]

        if len(self._buffer) >= self.max_chars:
            split_at = self._find_soft_split()
            if split_at is not None:
                candidate = self._buffer[:split_at].strip()
                if candidate:
                    chunks.append(candidate)
                    self._buffer = self._buffer[split_at:]

        return chunks

    def flush(self) -> str | None:
        value = self._buffer.strip()
        self._buffer = ""
        return value or None

    def _find_boundary(self) -> tuple[int, str] | None:
        active_min_chars = self.first_chunk_min_chars if not self._emitted_first_chunk else self.min_chars

        candidates = [
            (index, ch)
            for ch in self.HARD_BOUNDARIES
            if (index := self._buffer.find(ch)) >= active_min_chars
        ]
        if candidates:
            return min(candidates, key=lambda item: item[0])

        # The first chunk may also fire on a soft boundary (comma, semicolon,
        # colon) using the same relaxed threshold, so a phrase like "Sure, I
        # can help" reaches TTS immediately instead of waiting for a full
        # sentence.
        active_soft_min_chars = self.first_chunk_min_chars if not self._emitted_first_chunk else self.soft_boundary_min_chars

        candidates = [
            (index, ch)
            for ch in self.SOFT_BOUNDARIES
            if (index := self._buffer.find(ch)) >= active_soft_min_chars
        ]
        return min(candidates, key=lambda item: item[0]) if candidates else None

    def _find_soft_split(self) -> int | None:
        upper_bound = min(len(self._buffer), self.max_chars)
        for index in range(upper_bound, self.min_chars, -1):
            if self._buffer[index - 1].isspace():
                return index
        return None


# ============================================================
# PCM -> WAV
# ============================================================

def _pcm_to_wav(pcm_audio: bytes, *, sample_rate: int = 16_000) -> bytes:
    if not pcm_audio:
        raise HTTPException(status_code=400, detail="Audio is empty.")

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

async def speech_to_text(*, audio: bytes, prompt: str | None = None) -> str:
    started_at = time.perf_counter()
    logger.info("STT START bytes=%d", len(audio))

    if not audio:
        raise HTTPException(status_code=400, detail="No audio was received.")

    wav_bytes = _pcm_to_wav(audio)
    upload = UploadFile(
        file=io.BytesIO(wav_bytes),
        filename="voice.wav",
        headers=Headers({"content-type": "audio/wav"}),
    )

    try:
        result = await _transcribe(file=upload, prompt=prompt)
    except Exception:
        logger.exception("STT FAILED after %.3fs", time.perf_counter() - started_at)
        raise

    if isinstance(result, dict):
        transcript = str(result.get("text", "") or "").strip()
    else:
        transcript = str(result).strip()

    logger.info("STT COMPLETE in %.3fs transcript=%r", time.perf_counter() - started_at, transcript)
    return transcript


# ============================================================
# LLM
# ============================================================

async def stream_llm(*, messages: list[Message], config: VoicePipelineConfig) -> AsyncIterator[str]:
    started_at = time.perf_counter()
    logger.info("LLM START model=%r messages=%d", config.model, len(messages))

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
        response = await streaming_completion(request)
    except Exception:
        logger.exception("LLM REQUEST FAILED after %.3fs", time.perf_counter() - started_at)
        raise

    if not isinstance(response, StreamingResponse):
        raise HTTPException(status_code=502, detail="LLM streaming client returned an unexpected response.")

    token_count = 0
    try:
        async for token in response.body_iterator:
            if token is None:
                continue
            if isinstance(token, bytes):
                token = token.decode("utf-8", errors="replace")

            token = str(token)
            if not token:
                continue

            token_count += 1
            yield token

    except Exception:
        logger.exception("LLM STREAM FAILED after %.3fs", time.perf_counter() - started_at)
        raise

    logger.info("LLM COMPLETE in %.3fs tokens=%d", time.perf_counter() - started_at, token_count)


# ============================================================
# TTS
# ============================================================

async def text_to_speech(*, text: str, config: VoicePipelineConfig) -> AsyncIterator[bytes]:
    text = text.strip()
    if not text:
        return

    started_at = time.perf_counter()
    logger.info("TTS START voice=%r chars=%d", config.voice, len(text))

    try:
        async for audio_chunk in stream_tts_pcm(text=text, voice=config.voice, temperature=config.tts_temperature):
            if not isinstance(audio_chunk, bytes):
                logger.warning("TTS returned %s instead of bytes", type(audio_chunk).__name__)
                continue
            if not audio_chunk:
                continue
            yield audio_chunk

    except Exception:
        logger.exception("TTS FAILED after %.3fs", time.perf_counter() - started_at)
        raise

    logger.info("TTS COMPLETE in %.3fs", time.perf_counter() - started_at)


# ============================================================
# LLM -> TTS STREAM
# ============================================================

_PHRASE_STREAM_DONE = object()


async def llm_to_speech(*, messages: list[Message], config: VoicePipelineConfig) -> AsyncIterator[PipelineEvent]:
    chunker = TextChunker()
    full_text: list[str] = []

    phrase_queue: asyncio.Queue = asyncio.Queue(maxsize=8)
    event_queue: asyncio.Queue = asyncio.Queue()

    producer_error: list[BaseException] = []

    async def producer() -> None:
        try:
            async for token in stream_llm(messages=messages, config=config):
                full_text.append(token)
                await event_queue.put(PipelineEvent(type="llm.token", data=token))

                for phrase in chunker.add(token):
                    await phrase_queue.put(phrase)

            final_phrase = chunker.flush()
            if final_phrase:
                await phrase_queue.put(final_phrase)

            final_text = "".join(full_text).strip()
            await event_queue.put(PipelineEvent(type="llm.final", data=final_text))

        except BaseException as exc:
            producer_error.append(exc)

        finally:
            await phrase_queue.put(_PHRASE_STREAM_DONE)
            await event_queue.put(_PHRASE_STREAM_DONE)

    producer_task = asyncio.create_task(producer())

    try:
        producer_done = False
        consumer_done = False

        while not (producer_done and consumer_done):
            while not event_queue.empty():
                item = event_queue.get_nowait()
                if item is _PHRASE_STREAM_DONE:
                    producer_done = True
                    break
                yield item

            if consumer_done:
                if producer_done:
                    break

                item = await event_queue.get()
                if item is _PHRASE_STREAM_DONE:
                    producer_done = True
                else:
                    yield item
                continue

            phrase = await phrase_queue.get()
            if phrase is _PHRASE_STREAM_DONE:
                consumer_done = True
                continue

            yield PipelineEvent(type="tts.started", data=phrase)

            async for audio_chunk in text_to_speech(text=phrase, config=config):
                yield PipelineEvent(type="tts.audio", data=audio_chunk)

            yield PipelineEvent(type="tts.completed", data=phrase)

        while not event_queue.empty():
            item = event_queue.get_nowait()
            if item is not _PHRASE_STREAM_DONE:
                yield item

    finally:
        if not producer_task.done():
            producer_task.cancel()
            try:
                await producer_task
            except (asyncio.CancelledError, Exception):
                pass

    if producer_error:
        raise producer_error[0]


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
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # TODO: RAG

    conversation = list(messages or [])
    conversation.append(Message(role="user", content=text))

    yield PipelineEvent(type="pipeline.started", data={"mode": "text_to_voice"})

    async for event in llm_to_speech(messages=conversation, config=config):
        yield event

    yield PipelineEvent(type="pipeline.completed", data={"mode": "text_to_voice"})


# ============================================================
# VOICE -> VOICE
# ============================================================

async def voice_to_voice(
    *,
    audio_stream: AsyncIterable[bytes],
    config: VoicePipelineConfig,
    messages: list[Message] | None = None,
    final_transcript_hint: str | None = None,
    tail_audio_hint: bytes | None = None,
) -> AsyncIterator[PipelineEvent]:
    """
    final_transcript_hint:
        If the caller (the WS layer) already has a fresh rolling
        partial-STT transcript covering essentially the whole utterance,
        pass it here. When present, Basket skips the redundant full-buffer
        re-transcription entirely and uses this transcript directly, which
        removes a full STT pass (often multiple seconds on CPU) from the
        critical path on every turn.

    tail_audio_hint:
        Optional. If the caller only wants to transcribe the *new* audio
        since the last partial (rather than reusing the partial's text
        outright), pass just the tail bytes here instead of
        `final_transcript_hint`. Basket will run STT on this short tail
        only, instead of the full buffer. Ignored if `final_transcript_hint`
        is provided.
    """
    pipeline_started_at = time.perf_counter()
    yield PipelineEvent(type="pipeline.started", data={"mode": "voice_to_voice"})

    # --------------------------------------------------------
    # COLLECT AUDIO
    # --------------------------------------------------------

    audio_buffer = bytearray()
    async for chunk in audio_stream:
        if chunk:
            audio_buffer.extend(chunk)

    if not audio_buffer and not final_transcript_hint:
        raise HTTPException(status_code=400, detail="No audio was received.")

    # --------------------------------------------------------
    # STT
    # --------------------------------------------------------

    yield PipelineEvent(type="stt.started")

    if final_transcript_hint is not None:
        transcript = final_transcript_hint.strip()
    elif tail_audio_hint is not None:
        transcript = await speech_to_text(audio=tail_audio_hint, prompt=config.stt_prompt)
    else:
        transcript = await speech_to_text(audio=bytes(audio_buffer), prompt=config.stt_prompt)

    yield PipelineEvent(type="stt.final", data=transcript)

    if not transcript:
        yield PipelineEvent(type="pipeline.completed", data={"mode": "voice_to_voice", "empty_transcript": True})
        return

    # --------------------------------------------------------
    # BUILD CONVERSATION
    # --------------------------------------------------------

    # TODO: RAG

    conversation = list(messages or [])
    conversation.append(Message(role="user", content=transcript))

    # --------------------------------------------------------
    # LLM -> TTS
    # --------------------------------------------------------

    async for event in llm_to_speech(messages=conversation, config=config):
        yield event

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    yield PipelineEvent(type="pipeline.completed", data={"mode": "voice_to_voice"})
    logger.info("VOICE_TO_VOICE COMPLETE in %.3fs", time.perf_counter() - pipeline_started_at)