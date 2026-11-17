@echo off
setlocal
call "%~dp0..\fruits\cherry\start.bat" %*
exit /b %ERRORLEVEL%
