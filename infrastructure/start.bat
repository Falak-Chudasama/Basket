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
REM      Basket      → 127.0.0.1:%BASKET_PORT%
REM      LM Studio   → 127.0.0.1:%LLM_PORT%
REM      Qwen3-ASR   → 127.0.0.1:%STT_PORT%
REM      Pocket TTS  → 127.0.0.1:%TTS_PORT%
REM      SearXNG     → 127.0.0.1:%SEARXNG_PORT%
REM
REM ============================================================


echo.
echo ============================================================
echo                 BASKET INFRASTRUCTURE
echo ============================================================
echo.


REM ============================================================
REM  [1/5] NGINX
REM ============================================================

echo [1/5] Nginx...
echo.
echo       Using existing Windows startup instance.
echo       Reverse proxy: HTTP / HTTPS
echo.

timeout /t 1 /nobreak >nul


REM ============================================================
REM  [2/5] SEARXNG
REM ============================================================

echo [2/5] Starting SearXNG...
echo.
echo       Host : %HOST%
echo       Port : %SEARXNG_PORT%
echo.

REM ------------------------------------------------------------
REM Replace the following command with your existing SearXNG
REM startup command if your installation uses Docker, WSL,
REM a virtual environment, or another launcher.
REM ------------------------------------------------------------

start "Basket - SearXNG" cmd /k "cd /d "%SEARXNG_ROOT%" && searxng --host %HOST% --port %SEARXNG_PORT%"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [3/5] QWEN3-ASR
REM ============================================================

echo [3/5] Starting Qwen3-ASR...
echo.
echo       Backend : llama.cpp
echo       Host    : %HOST%
echo       Port    : %STT_PORT%
echo       Device  : CPU ONLY
echo.

start "Basket - STT" cmd /k "llama-server.exe -m "%ASR_MODEL%" --mmproj "%ASR_MMPROJ%" --host %HOST% --port %STT_PORT% -ngl 0 --mmproj-device none -c 4096"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [4/5] LM STUDIO
REM ============================================================

echo [4/5] Starting LM Studio...
echo.
echo       Host : %HOST%
echo       Port : %LLM_PORT%
echo.

start "Basket - LM Studio" cmd /k "lms server start --port %LLM_PORT%"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [5/5] POCKET TTS
REM ============================================================

echo [5/5] Starting Pocket TTS...
echo.
echo       Root   : %POCKET_TTS_ROOT%
echo       Host   : %HOST%
echo       Port   : %TTS_PORT%
echo       Device : CPU ONLY
echo.

start "Basket - Pocket TTS" cmd /k "cd /d "%POCKET_TTS_ROOT%" && call .venv\Scripts\activate.bat && pocket-tts serve --host %HOST% --port %TTS_PORT%"

timeout /t 2 /nobreak >nul


REM ============================================================
REM  [6/6] BASKET API
REM ============================================================

echo [6/6] Starting Basket API...
echo.
echo       Root : %BASKET_ROOT%
echo       Host : %HOST%
echo       Port : %BASKET_PORT%
echo.

start "Basket - API" cmd /k "cd /d "%BASKET_ROOT%" && call .venv\Scripts\activate.bat && python run.py"


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
echo      LM Studio   : http://%HOST%:%LLM_PORT%
echo      STT         : http://%HOST%:%STT_PORT%
echo      TTS         : http://%HOST%:%TTS_PORT%
echo      SearXNG     : http://%HOST%:%SEARXNG_PORT%

echo.
echo ============================================================
echo.

endlocal

pause