@echo off
setlocal

call "%~dp0config.bat"

echo.
echo ==========================================
echo          BASKET INFRA STATUS
echo ==========================================
echo.

echo [Nginx]
powershell -Command "try { $r=Test-NetConnection %HOST% -Port %NGINX_PORT% -WarningAction SilentlyContinue; if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'} } catch { Write-Host 'OFFLINE' }"

echo.
echo [STT - Qwen3-ASR]
powershell -Command "try { $r=Test-NetConnection %HOST% -Port %STT_PORT% -WarningAction SilentlyContinue; if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'} } catch { Write-Host 'OFFLINE' }"

echo.
echo [LLM - LM Studio]
powershell -Command "try { $r=Test-NetConnection %HOST% -Port %LLM_PORT% -WarningAction SilentlyContinue; if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'} } catch { Write-Host 'OFFLINE' }"

echo.
echo [TTS - Pocket TTS]
powershell -Command "try { $r=Test-NetConnection %HOST% -Port %TTS_PORT% -WarningAction SilentlyContinue; if($r.TcpTestSucceeded){Write-Host 'ONLINE'}else{Write-Host 'OFFLINE'} } catch { Write-Host 'OFFLINE' }"

echo.
echo ==========================================
echo.

endlocal
pause