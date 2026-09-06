@echo off

setlocal

echo.
echo ==========================================
echo        BASKET INFRASTRUCTURE RESTART
echo ==========================================
echo.

echo [1/2] Stopping Basket infrastructure...
echo.

call "%~dp0stop.bat"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to stop Basket infrastructure.
    echo.
    pause
    exit /b 1
)

echo.
echo Waiting for services to shut down...
timeout /t 2 /nobreak >nul

echo.
echo [2/2] Starting Basket infrastructure...
echo.

call "%~dp0start.bat"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Basket infrastructure.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo          RESTART COMPLETE
echo ==========================================
echo.

endlocal

pause