@echo off

REM ============================================================
REM
REM  BASKET INFRASTRUCTURE CONFIGURATION
REM
REM  Shared configuration consumed by start.bat.
REM
REM ============================================================


REM ============================================================
REM  PORTS
REM ============================================================

set "BASKET_PORT=7000"
set "LLM_PORT=7001"
set "STT_PORT=7002"
set "TTS_PORT=7003"
set "NGINX_PORT=7004"
set "BASKET_DB_PORT=7005"


REM ============================================================
REM  HOST
REM ============================================================

set "HOST=127.0.0.1"


REM ============================================================
REM  NGINX
REM
REM  Nginx is a shared system service and is already running.
REM  Basket does NOT start or stop Nginx.
REM ============================================================

set "NGINX_DIR=C:\nginx"


REM ============================================================
REM  QWEN3-ASR / LLAMA.CPP
REM
REM  llama-server.exe is available through PATH via WinGet.
REM  Basket therefore does not need to hard-code LLAMA_DIR.
REM
REM  STT is launched CPU-only:
REM      -ngl 0
REM      --mmproj-device none
REM ============================================================

set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\Qwen3-ASR-0.6B-Q8_0.gguf"
set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf"

REM ============================================================
REM  LM STUDIO
REM ============================================================

REM lms is expected to be available in PATH.

set "LLM_MODEL_ID=quince-llm"


REM ============================================================
REM  POCKET TTS
REM
REM  Pocket TTS has its own dedicated virtual environment:
REM      C:\pocket-tts\.venv
REM
REM  The server runs CPU-only.
REM ============================================================

set "POCKET_TTS_ROOT=C:\pocket-tts"


REM ============================================================
REM  BASKET
REM
REM  start.bat is located inside:
REM      Basket\infrastructure\
REM
REM  Therefore %~dp0.. resolves to:
REM      Basket\
REM ============================================================

set "BASKET_ROOT=%~dp0.."


REM ============================================================
REM  BASKET DATABASE
REM
REM  start.bat is located inside:
REM      Basket\infrastructure\
REM
REM  Therefore %~dp0.. resolves to:
REM      Basket\
REM ============================================================

set "MONGODB_PATH=C:\project-data\basket"
set "BASKET_PORT=7000"


REM ============================================================
REM  END CONFIGURATION
REM ============================================================