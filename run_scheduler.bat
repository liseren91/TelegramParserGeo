@echo off
REM Telegram Parser Scheduler Runner
REM This script runs the scheduler in the background

echo Starting Telegram Parser Scheduler...
cd /d "%~dp0"
python scheduler.py

pause

