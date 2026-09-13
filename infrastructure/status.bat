@echo off

setlocal

call "%~dp0config.bat"

echo.
echo ==========================================
echo          BASKET INFRA STATUS
echo ==========================================
echo.


REM ============================================================
REM  NGINX
REM ============================================================

echo [Nginx]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port 80 -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  SEARXNG
REM ============================================================

echo [Search - SearXNG]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %SEARXNG_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  STT
REM ============================================================

echo [STT - Qwen3-ASR]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %STT_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  LLM
REM ============================================================

echo [LLM - LM Studio]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %LM_STUDIO_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  TTS
REM ============================================================

echo [TTS - Pocket TTS]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %TTS_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  MONGODB
REM ============================================================

echo [Database - MongoDB]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %BASKET_DB_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  BASKET API
REM ============================================================

echo [API - Basket]

powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%HOST%' -Port %BASKET_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"

echo.


REM ============================================================
REM  SUMMARY
REM ============================================================

echo ==========================================
echo.

echo Host:
echo     %HOST%

echo.
echo Ports:
echo     Basket API : %BASKET_PORT%
echo     LM Studio  : %LM_STUDIO_PORT%
echo     STT        : %STT_PORT%
echo     TTS        : %TTS_PORT%
echo     SearXNG    : %SEARXNG_PORT%
echo     MongoDB    : %BASKET_DB_PORT%
echo     Nginx      : 80

echo.
echo ==========================================
echo.

endlocal

pause