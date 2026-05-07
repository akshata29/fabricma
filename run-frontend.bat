@echo off
setlocal

cd /d "%~dp0frontend"

:: Check if node is available
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 20+ from https://nodejs.org and re-run.
    exit /b 1
)

:: Check if npm is available
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm not found. Ensure Node.js is installed correctly.
    exit /b 1
)

:: Run npm install if node_modules is missing or package.json is newer
if not exist "node_modules\" (
    echo [INFO] node_modules not found. Running npm install...
    npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] npm install failed.
        exit /b 1
    )
) else (
    echo [INFO] node_modules found. Skipping npm install.
)

:: Copy .env if missing
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Copying .env.example to .env...
        copy ".env.example" ".env" >nul
        echo [WARN] frontend\.env created from example. Fill in VITE_* values before logging in.
    ) else (
        echo [WARN] No frontend\.env found. MSAL auth will not work until VITE_* vars are set.
    )
)

echo.
echo [INFO] Starting FabricMA frontend on http://localhost:5173
echo [INFO] Press Ctrl+C to stop.
echo.

npm run dev

endlocal
