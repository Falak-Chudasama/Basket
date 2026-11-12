@echo off
setlocal
set "BASKET_ROOT=C:\Users\ADMIN\OneDrive\CODES\Projects\Projects\Basket"
set "PYTHON_EXE=%BASKET_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo.
echo ============================================================
echo   BASKET OPERATIONS: END / STOP QUINCE LLM (llama.cpp CUDA)
echo ============================================================
echo.

cd /d "%BASKET_ROOT%"
"%PYTHON_EXE%" -m src.control.manage end llm-llama
set "EXIT_CODE=%ERRORLEVEL%"

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
