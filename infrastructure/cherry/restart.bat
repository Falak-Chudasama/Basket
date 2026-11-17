@echo off
setlocal
call "%~dp0..\fruits\cherry\restart.bat" %*
exit /b %ERRORLEVEL%
