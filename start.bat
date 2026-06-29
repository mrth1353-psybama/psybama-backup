@echo off
chcp 65001 >nul
title Psybama - Psybama

echo.
echo  ================================================
echo   Psybama  -  Starting...
echo  ================================================
echo.

:: ---- Find Python ----
set "PYTHON_EXE="

:: Check Python313 direct path (most reliable on this machine)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :FOUND
)

:: Check py launcher
py -3 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=py -3"
    goto :FOUND
)

:: Check python in PATH
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_EXE=python"
    goto :FOUND
)

echo [ERROR] Python not found.
echo Please install Python 3.10+ from python.org
echo.
pause
exit /b 1

:FOUND
echo [OK] Python found.

:: ---- Create data directory ----
if not exist "%~dp0data" mkdir "%~dp0data"

:: ---- Create .env if missing ----
if not exist "%~dp0.env" (
    echo [SETUP] Creating .env from template...
    copy "%~dp0.env.example" "%~dp0.env" >nul
    echo.
    echo  ============================================
    echo   IMPORTANT: .env file created!
    echo   Please open .env and fill in:
    echo   SILICONFLOW_API_KEY = your API key
    echo   ADMIN_PASSWORD      = admin password
    echo  ============================================
    echo.
    pause
    exit /b 0
)

:: ---- Install dependencies ----
echo [1/2] Installing dependencies...
"%PYTHON_EXE%" -m pip install -r "%~dp0backend\requirements.txt" -q --disable-pip-version-check
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] pip install failed. Check internet connection.
    pause
    exit /b 1
)

:: ---- Start server ----
echo [2/2] Starting server...
echo.
echo  ============================================
echo   http://localhost:5000
echo   http://localhost:5000/chat
echo   http://localhost:5000/assessment
echo   http://localhost:5000/admin/
echo   Press Ctrl+C to stop
echo  ============================================
echo.

cd /d "%~dp0backend"
"%PYTHON_EXE%" app.py

cd /d "%~dp0"
echo.
echo Server stopped.
pause
