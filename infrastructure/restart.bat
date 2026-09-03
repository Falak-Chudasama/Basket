@echo off

echo.
echo Restarting Basket infrastructure...
echo.

call "%~dp0stop.bat"

timeout /t 2 /nobreak >nul

call "%~dp0start.bat"

echo.
echo Restart complete.
echo.

pause