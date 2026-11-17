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
REM  FRUITS ECOSYSTEM
REM ============================================================

echo [Fruit - Plum]
powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%PLUM_HOST%' -Port %PLUM_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"
echo.

echo [Fruit - Kiwi]
powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%KIWI_HOST%' -Port %KIWI_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"
echo.

echo [Fruit - Banana]
powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%BANANA_HOST%' -Port %BANANA_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"
echo.

echo [Fruit - Lemon]
powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%LEMON_HOST%' -Port %LEMON_PORT% -WarningAction SilentlyContinue; ^
    if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'}"
echo.

echo [Fruit - Cherry]
powershell -NoProfile -Command ^
    "$r=Test-NetConnection '%CHERRY_HOST%' -Port %CHERRY_PORT% -WarningAction SilentlyContinue; ^
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
echo     Plum       : %PLUM_PORT% (%PLUM_HOST%)
echo     Kiwi       : %KIWI_PORT% (%KIWI_HOST%)
echo     Banana     : %BANANA_PORT% (%BANANA_HOST%)
echo     Lemon      : %LEMON_PORT% (%LEMON_HOST%)
echo     Cherry     : %CHERRY_PORT% (%CHERRY_HOST%)

echo.
echo ==========================================
echo.

endlocal

pause