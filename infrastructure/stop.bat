@echo off
setlocal

call "%~dp0config.bat"

echo.
echo ==========================================
echo          STOPPING BASKET INFRA
echo ==========================================
echo.

echo Stopping Nginx...
taskkill /F /IM nginx.exe >nul 2>&1

echo Stopping llama-server...
taskkill /F /IM llama-server.exe >nul 2>&1

echo Stopping Pocket TTS...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Basket - Pocket TTS*" >nul 2>&1

echo Stopping LM Studio server...
lms server stop >nul 2>&1

echo.
echo Infrastructure stop commands completed.
echo.

endlocal
pause