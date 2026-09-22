@echo off

setlocal

call "%~dp0config.bat"


REM ============================================================
REM
REM  BASKET INFRASTRUCTURE STARTUP
REM
REM  Nginx:
REM      Already running through Windows startup.
REM
REM  Services:
REM
REM      Basket         → 127.0.0.1:%BASKET_PORT%
REM      LLM            → 127.0.0.1:%LLM_PORT%
REM      Nemotron ASR   → 127.0.0.1:%STT_PORT%
REM      Pocket TTS     → 127.0.0.1:%TTS_PORT%
REM      SearXNG        → 127.0.0.1:%SEARXNG_PORT%
REM      MongoDB        → 127.0.0.1:%BASKET_DB_PORT%
REM
REM ============================================================


echo.
echo ============================================================
echo                 BASKET INFRASTRUCTURE
echo ============================================================
echo.


REM ============================================================
REM  [1/7] NGINX
REM ============================================================

echo [1/7] Nginx...
echo.
echo       Using existing Windows startup instance.
echo       Reverse proxy: HTTP / HTTPS
echo.

timeout /t 1 /nobreak >nul


REM ============================================================
REM  [2/7] SEARXNG
REM ============================================================

echo [2/7] Starting SearXNG...
echo.
echo       Root : %SEARXNG_ROOT%
echo       Port : %SEARXNG_PORT%
echo.


REM ------------------------------------------------------------
REM  Check Docker engine
REM ------------------------------------------------------------

docker info >nul 2>&1

if errorlevel 1 (
    echo       Docker engine is not running.
    echo       Starting Docker Desktop in background...
    echo.

    docker desktop start -d

    echo       Waiting for Docker engine...
)


:WAIT_DOCKER

docker info >nul 2>&1

if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto WAIT_DOCKER
)

echo       Docker engine is ready.
echo.


REM ------------------------------------------------------------
REM  Start SearXNG
REM ------------------------------------------------------------

echo       Starting SearXNG containers...

start "Basket - SearXNG" /D "%SEARXNG_ROOT%" cmd /k "docker compose up"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [3/7] QUINCE LLM
REM
REM  Backend : llama.cpp
REM  Device  : CUDA / NVIDIA GPU
REM ============================================================

echo [3/7] Starting Quince LLM...
echo.
echo       Backend  : llama.cpp
echo       Model    : %LLM_MODEL%
echo       Alias    : %LLM_MODEL_ID%
echo       Host     : %HOST%
echo       Port     : %LLM_PORT%
echo       Device   : CUDA
echo       GPU      : %LLM_GPU_LAYERS% layers
echo       Context  : %LLM_CTX_SIZE%
echo       Slots    : %LLM_PARALLEL%
echo       Jinja    : ENABLED
echo.


REM ------------------------------------------------------------
REM  Verify CUDA llama-server executable
REM ------------------------------------------------------------

if not exist "%LLAMA_CUDA_EXE%" (
    echo ERROR: CUDA llama-server.exe was not found:
    echo        %LLAMA_CUDA_EXE%
    echo.
    pause
    exit /b 1
)


REM ------------------------------------------------------------
REM  Verify LLM model
REM ------------------------------------------------------------

if not exist "%LLM_MODEL%" (
    echo ERROR: LLM model was not found:
    echo        %LLM_MODEL%
    echo.
    pause
    exit /b 1
)


REM ------------------------------------------------------------
REM  Start llama.cpp LLM server
REM
REM  IMPORTANT:
REM  Keep this command on ONE LINE because Windows cmd/start
REM  quoting is sensitive.
REM ------------------------------------------------------------

start "Basket - LLM" cmd /k ""%LLAMA_CUDA_EXE%" -m "%LLM_MODEL%" --alias "%LLM_MODEL_ID%" --host %HOST% --port %LLM_PORT% --ctx-size %LLM_CTX_SIZE% --parallel %LLM_PARALLEL% --n-gpu-layers %LLM_GPU_LAYERS% --jinja --flash-attn auto"

echo       llama.cpp LLM server launched.
echo.

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [4/7] NEMOTRON 3.5 ASR
REM
REM  Backend : NeMo-Speech.cpp
REM  Device  : CPU ONLY
REM  Model   : nemotron-3.5
REM  Port    : 127.0.0.1:%STT_PORT%
REM ============================================================

echo [4/7] Starting Nemotron 3.5 ASR...
echo.
echo       Backend : NeMo-Speech.cpp
echo       Model   : %ASR_MODEL_ID%
echo       Host    : %HOST%
echo       Port    : %STT_PORT%
echo       Device  : CPU ONLY
echo.


REM ------------------------------------------------------------
REM  Verify NeMo-Speech.cpp executable
REM ------------------------------------------------------------

if not exist "%NEMO_SPEECH_EXE%" (
    echo ERROR: nemo-speech.exe was not found:
    echo        %NEMO_SPEECH_EXE%
    echo.
    echo       Install NeMo-Speech.cpp first.
    echo.
    echo       Expected:
    echo       %LOCALAPPDATA%\Programs\NeMoSpeech\bin\nemo-speech.exe
    echo.
    pause
    exit /b 1
)


REM ------------------------------------------------------------
REM  Start Nemotron 3.5 ASR server
REM
REM  CPU ONLY:
REM      --asr.backend.gpu -1
REM
REM  Endpointing:
REM      Finalize an utterance after trailing silence.
REM
REM  IMPORTANT:
REM  Keep this command on ONE LINE because Windows cmd/start
REM  quoting is sensitive.
REM ------------------------------------------------------------

start "Basket - STT" cmd /k ""%NEMO_SPEECH_EXE%" serve --asr-model "%ASR_MODEL_ID%" --asr.backend.gpu -1 --host %HOST% --port %STT_PORT%"

echo       Nemotron 3.5 ASR server launched.
echo.

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [5/7] POCKET TTS
REM ============================================================

echo [5/7] Starting Pocket TTS...
echo.
echo       Root   : %POCKET_TTS_ROOT%
echo       Host   : %HOST%
echo       Port   : %TTS_PORT%
echo       Device : CPU ONLY
echo.

start "Basket - Pocket TTS" /D "%POCKET_TTS_ROOT%" cmd /k "call .venv\Scripts\activate.bat && pocket-tts serve --host %HOST% --port %TTS_PORT%"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [6/7] MONGODB
REM ============================================================

echo [6/7] Starting Basket Database...
echo.
echo       Path : %MONGODB_PATH%
echo       Host : %HOST%
echo       Port : %BASKET_DB_PORT%
echo.


REM ------------------------------------------------------------
REM  Start MongoDB
REM ------------------------------------------------------------

start "Basket - MongoDB" /D "%MONGODB_PATH%" cmd /k "mongod --port %BASKET_DB_PORT% --dbpath ."

echo       Waiting for MongoDB...
echo.


:WAIT_MONGODB

powershell -NoProfile -Command "$t = Test-NetConnection -ComputerName '%HOST%' -Port %BASKET_DB_PORT% -WarningAction SilentlyContinue; if ($t.TcpTestSucceeded) { exit 0 } else { exit 1 }" >nul 2>&1

if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT_MONGODB
)

echo       MongoDB is ready.
echo.


REM ============================================================
REM  [7/7] BASKET API
REM ============================================================

echo [7/7] Starting Basket API...
echo.
echo       Root : %BASKET_ROOT%
echo       Host : %HOST%
echo       Port : %BASKET_PORT%
echo.

start "Basket - API" /D "%BASKET_ROOT%" cmd /k "call .venv\Scripts\activate.bat && python run.py"


REM ============================================================
REM  COMPLETE
REM ============================================================

echo.
echo ============================================================
echo              BASKET SERVICES STARTED
echo ============================================================
echo.

echo  Nginx:
echo      http://api.basket.com
echo      http://lms.com
echo      http://llama.cpp.com
echo      http://pockettts.com
echo      http://searxng.com

echo.
echo  Direct service endpoints:
echo      Basket      : http://%HOST%:%BASKET_PORT%
echo      LLM         : http://%HOST%:%LLM_PORT%
echo      STT         : http://%HOST%:%STT_PORT%
echo      TTS         : http://%HOST%:%TTS_PORT%
echo      SearXNG     : http://%HOST%:%SEARXNG_PORT%
echo      MongoDB     : mongodb://%HOST%:%BASKET_DB_PORT%

echo.
echo  LLM API:
echo      Chat        : http://%HOST%:%LLM_PORT%/v1/chat/completions
echo      Models      : http://%HOST%:%LLM_PORT%/v1/models
echo      Health      : http://%HOST%:%LLM_PORT%/health

echo.
echo ============================================================
echo.

endlocal

pause