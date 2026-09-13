@echo off

REM ============================================================
REM  PORTS
REM ============================================================

set "BASKET_PORT=7000"
set "LLM_PORT=7001"
set "STT_PORT=7002"
set "TTS_PORT=7003"
set "SEARXNG_PORT=7004"
set "BASKET_DB_PORT=7005"
set "LM_STUDIO_PORT=7006"


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
REM  QWEN3-ASR / LLAMA.CPP
REM ============================================================

set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\Qwen3-ASR-0.6B-Q8_0.gguf"
set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf"


REM ============================================================
REM  LM STUDIO
REM ============================================================

set "LLM_MODEL_ID=quince-llm"


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