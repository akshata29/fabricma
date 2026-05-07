@echo off
setlocal

cd /d "%~dp0backend"

:: Check if uv is available
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] uv not found. Installing via pip...
    pip install uv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install uv. Ensure Python and pip are on PATH.
        exit /b 1
    )
)

:: Check if .venv exists; run uv sync if not
if not exist ".venv\" (
    echo [INFO] .venv not found. Running uv sync...
    uv sync
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] uv sync failed.
        exit /b 1
    )
) else (
    echo [INFO] .venv found. Skipping uv sync.
)

:: config.py reads ../.env (repo root .env from backend/ CWD).
:: Abort if that file does not exist.
if not exist "..\.env" (
    echo.
    echo [ERROR] No .env file found at the repo root.
    echo         Copy .env.example to .env and fill in your Azure credentials:
    echo.
    echo           copy ..\.env.example ..\.env
    echo.
    echo         Then re-run this script.
    echo.
    exit /b 1
)

echo.
echo [INFO] Starting FabricMA backend on http://localhost:8000
echo [INFO] Press Ctrl+C to stop.
echo.

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

endlocal
