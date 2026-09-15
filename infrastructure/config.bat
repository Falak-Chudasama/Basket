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
REM  QWEN3-ASR:
REM      Existing llama-server.exe available through PATH
REM      CPU ONLY
REM ============================================================

set "LLAMA_CUDA_EXE=C:\llama-cuda\llama-server.exe"


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
REM  QWEN3-ASR
REM  
REM  SMALLER MODEL
REM  set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\Qwen3-ASR-0.6B-Q8_0.gguf"
REM  set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf"
REM  
REM  BIGGER MODEL
REM  set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-1.7B-GGUF\snapshots\36a678687ba7d07a74ca70ccb0e36902e005fb80\Qwen3-ASR-1.7B-Q8_0.gguf"
REM  set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-1.7B-GGUF\snapshots\36a678687ba7d07a74ca70ccb0e36902e005fb80\mmproj-Qwen3-ASR-1.7B-Q8_0.gguf"
REM ============================================================

set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-1.7B-GGUF\snapshots\36a678687ba7d07a74ca70ccb0e36902e005fb80\Qwen3-ASR-1.7B-Q8_0.gguf"
set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-1.7B-GGUF\snapshots\36a678687ba7d07a74ca70ccb0e36902e005fb80\mmproj-Qwen3-ASR-1.7B-Q8_0.gguf"
@REM  set "ASR_MODEL=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\Qwen3-ASR-0.6B-Q8_0.gguf"
@REM  set "ASR_MMPROJ=C:\Users\ADMIN\.cache\huggingface\hub\models--ggml-org--Qwen3-ASR-0.6B-GGUF\snapshots\928ab958557df9aa2ef1c93e0e83c7ad0933fae2\mmproj-Qwen3-ASR-0.6B-Q8_0.gguf"


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