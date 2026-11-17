@echo off
setlocal enabledelayedexpansion
title NetScope - Network Discovery ^& Monitoring

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    if "%~1" neq "--no-elevate" (
        echo ============================================================
        echo   Administrator privileges are recommended on Windows 11
        echo   to perform raw ARP network packet capture with Scapy.
        echo ============================================================
        echo Requesting Windows Administrator elevation...
        powershell -Command "Start-Process cmd.exe -ArgumentList '/k \"\"%~f0\" --no-elevate %*\"' -Verb RunAs"
        if %errorlevel% equ 0 exit /b
        echo Elevation was cancelled. Continuing in standard user mode...
        echo ============================================================
    )
)

echo ============================================================
echo   Starting NetScope Local Network Discovery Tool
echo ============================================================

REM Set working directory to script location
cd /d "%~dp0"

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
