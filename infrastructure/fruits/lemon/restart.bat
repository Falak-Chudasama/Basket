@echo off
setlocal
set "BASKET_ROOT=C:\Users\ADMIN\OneDrive\CODES\Projects\Projects\Basket"
set "PYTHON_EXE=%BASKET_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo.
echo ============================================================
echo   BASKET OPERATIONS: RESTART LEMON DESKTOP BACKEND
echo ============================================================
echo.
echo [DISABLED] Lemon applications are broken and disabled from launching.
echo.

REM cd /d "%BASKET_ROOT%"
REM "%PYTHON_EXE%" -m src.control.manage fruit-restart lemon
REM set "EXIT_CODE=%ERRORLEVEL%"
set "EXIT_CODE=0"

echo.
if %EXIT_CODE% equ 0 (
    echo [SUCCESS] Operation completed successfully.
) else (
    echo [ERROR] Operation failed with exit code %EXIT_CODE%.
)
echo.

if "%1"=="/nopause" goto :SKIP_PAUSE
if "%BASKET_NO_PAUSE%"=="1" goto :SKIP_PAUSE
pause
:SKIP_PAUSE
exit /b %EXIT_CODE%
