@echo off

REM ============================================================
REM
REM  BASKET INFRASTRUCTURE CONFIGURATION
REM
REM ============================================================


REM ============================================================
REM  PORTS
REM ============================================================

set "BASKET_PORT=7000"
set "LLM_PORT=7001"
set "STT_PORT=7002"
set "TTS_PORT=7003"
set "SEARXNG_PORT=7004"
set "BASKET_DB_PORT=7005"


REM ============================================================
REM  HOST
REM ============================================================

set "HOST=127.0.0.1"


REM ============================================================
REM  NGINX
REM ============================================================

set "NGINX_DIR=C:\nginx"


REM ============================================================
REM  SEARXNG
REM
REM  SearXNG is managed through Docker Compose.
REM ============================================================

set "SEARXNG_ROOT=C:\searxng"


REM ============================================================
REM  LLAMA.CPP
REM
REM  QUINCE LLM:
REM      Explicit CUDA-enabled llama.cpp build
REM      C:\llama-cuda\llama-server.exe
REM
REM  NEMOTRON ASR:
REM      Served by NeMo-Speech.cpp
REM      CPU ONLY
REM ============================================================

set "LLAMA_CUDA_EXE=C:\llama-cuda\llama-server.exe"

REM NeMo-Speech.cpp Windows installation.
set "NEMO_SPEECH_EXE=%LOCALAPPDATA%\Programs\NeMoSpeech\bin\nemo-speech.exe"


REM ============================================================
REM  QUINCE LLM
REM ============================================================

set "LLM_MODEL=C:\Users\ADMIN\models\Qwen3.5-4B-Q4_K_M\Qwen3.5-4B.Q4_K_M.gguf"

set "LLM_MODEL_ID=quince-llm"

REM 16,000 token context.
set "LLM_CTX_SIZE=16000"

REM Maximum GPU layer offload.
set "LLM_GPU_LAYERS=99"

REM One server slot.
REM Quince is a single-user local assistant.
set "LLM_PARALLEL=1"


REM ============================================================
REM  NEMOTRON 3.5 ASR
REM
REM  Model:
REM      nvidia/nemotron-3.5-asr-streaming-0.6b
REM
REM  Short model name:
REM      nemotron-3.5
REM
REM  Backend:
REM      NeMo-Speech.cpp
REM
REM  Device:
REM      CPU ONLY
REM
REM  Download once with:
REM      nemo-speech pull nemotron-3.5
REM
REM  Server:
REM      127.0.0.1:%STT_PORT%
REM ============================================================

set "ASR_MODEL_ID=nemotron-3.5"

REM Finalize an utterance after 800 ms of trailing silence.
set "ASR_ENDPOINTING_EOU_MS=800"


REM ============================================================
REM  POCKET TTS
REM ============================================================

set "POCKET_TTS_ROOT=C:\pocket-tts"


REM ============================================================
REM  BASKET
REM
REM  start.bat is located inside:
REM      Basket\infrastructure\
REM
REM  Therefore:
REM      %~dp0.. = Basket\
REM ============================================================

set "BASKET_ROOT=%~dp0.."


REM ============================================================
REM  BASKET DATABASE
REM ============================================================

set "MONGODB_PATH=C:\project-data\basket"