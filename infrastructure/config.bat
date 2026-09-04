@echo off

REM ============================================================
REM Basket Infrastructure Configuration
REM ============================================================

REM ---------- Ports ----------
set "BASKET_PORT=7000"
set "LLM_PORT=7001"
set "STT_PORT=7002"
set "TTS_PORT=7003"
set "NGINX_PORT=7004"

REM ---------- Hosts ----------
set "HOST=127.0.0.1"

REM ---------- Nginx ----------
REM Change this to the folder containing nginx.exe
set "NGINX_DIR=C:\nginx"

REM ---------- llama.cpp ----------
REM Change this to the folder containing llama-server.exe
set "LLAMA_DIR=C:\llama.cpp\build\bin"

REM ---------- Qwen3-ASR ----------
REM Put your actual GGUF paths here.
set ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\Qwen3-ASR-0.6B-Q8_0.gguf
set ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf

REM ---------- LM Studio ----------
REM lms is assumed to be available in PATH.
REM Change this identifier after confirming the actual model ID.
set "LLM_MODEL_ID=quince-llm"

REM ---------- Pocket TTS ----------
REM Assumes pocket-tts is available in PATH / current Python environment.

REM ---------- Basket ----------
set "BASKET_ROOT=%~dp0.."

REM ============================================================