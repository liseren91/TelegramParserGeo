@echo off
REM Telegram Parser - Single Run
REM This script runs the parser once and exits

echo Running Telegram Parser (one-time update)...
cd /d "%~dp0"
python main.py full

echo.
echo Update completed!
pause

