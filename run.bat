@echo off
setlocal enabledelayedexpansion
title NetScope - Network Discovery ^& Monitoring

echo ============================================================
echo   Starting NetScope Local Network Discovery Tool
echo ============================================================

REM Check if virtual environment python exists
if exist venv\Scripts\python.exe (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" run.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] NetScope exited with an error.
    pause
)
