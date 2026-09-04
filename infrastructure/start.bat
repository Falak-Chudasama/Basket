@echo off
setlocal

call "%~dp0config.bat"

echo.
echo ==========================================
echo          BASKET INFRASTRUCTURE
echo ==========================================
echo.

echo [1/4] Starting Nginx...

start "Basket - Nginx" cmd /k "cd /d %NGINX_DIR% && nginx.exe -c "%NGINX_DIR%\conf\nginx.conf" -p "%NGINX_DIR%""

timeout /t 1 /nobreak >nul

echo [2/4] Starting Qwen3-ASR (CPU ONLY)...

start "Basket - STT" cmd /k "llama-server.exe -m "%ASR_MODEL%" --mmproj "%ASR_MMPROJ%" --host %HOST% --port %STT_PORT% -ngl 0 --mmproj-device none -c 4096"

timeout /t 2 /nobreak >nul

echo [3/4] Starting LM Studio server...
start "Basket - LM Studio" cmd /k "lms server start --port %LLM_PORT%"

timeout /t 2 /nobreak >nul

echo [4/4] Starting Pocket TTS (CPU ONLY)...

start "Basket - Pocket TTS" cmd /k "cd /d C:\pocket-tts && call .venv\Scripts\activate.bat && pocket-tts serve --host %HOST% --port %TTS_PORT%"

echo.
echo ==========================================
echo Infrastructure launch commands sent.
echo ==========================================
echo.

endlocal
pause