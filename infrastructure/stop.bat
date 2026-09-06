@echo off

setlocal

call "%~dp0config.bat"

echo.
echo ==========================================
echo          STOPPING BASKET INFRA
echo ==========================================
echo.


REM ============================================================
REM  [1/6] BASKET API
REM ============================================================

echo [1/6] Stopping Basket API...

taskkill /F /FI "WINDOWTITLE eq Basket - API*" /IM cmd.exe >nul 2>&1

if errorlevel 1 (
    echo       Basket API was not running.
) else (
    echo       Basket API stopped.
)

echo.


REM ============================================================
REM  [2/6] MONGODB
REM ============================================================

echo [2/6] Stopping MongoDB...

taskkill /F /IM mongod.exe >nul 2>&1

if errorlevel 1 (
    echo       MongoDB was not running.
) else (
    echo       MongoDB stopped.
)

echo.


REM ============================================================
REM  [3/6] POCKET TTS
REM ============================================================

echo [3/6] Stopping Pocket TTS...

taskkill /F /FI "WINDOWTITLE eq Basket - Pocket TTS*" /IM cmd.exe >nul 2>&1

if errorlevel 1 (
    echo       Pocket TTS was not running.
) else (
    echo       Pocket TTS stopped.
)

echo.


REM ============================================================
REM  [4/6] LM STUDIO
REM ============================================================

echo [4/6] Stopping LM Studio server...

lms server stop >nul 2>&1

if errorlevel 1 (
    echo       LM Studio server was not running.
) else (
    echo       LM Studio server stopped.
)

echo.


REM ============================================================
REM  [5/6] QWEN3-ASR / LLAMA.CPP
REM ============================================================

echo [5/6] Stopping Qwen3-ASR...

taskkill /F /IM llama-server.exe >nul 2>&1

if errorlevel 1 (
    echo       llama-server was not running.
) else (
    echo       Qwen3-ASR stopped.
)

echo.


REM ============================================================
REM  [6/6] SEARXNG
REM ============================================================

echo [6/6] Stopping SearXNG...

docker compose -f "%SEARXNG_ROOT%\docker-compose.yml" down >nul 2>&1

if errorlevel 1 (
    echo       SearXNG was not running or Docker was unavailable.
) else (
    echo       SearXNG stopped.
)

echo.


REM ============================================================
REM  NGINX
REM ============================================================

echo Stopping Nginx...

taskkill /F /IM nginx.exe >nul 2>&1

if errorlevel 1 (
    echo       Nginx was not running.
) else (
    echo       Nginx stopped.
)

echo.
echo ==========================================
echo       INFRASTRUCTURE STOP COMPLETE
echo ==========================================
echo.

endlocal

pause