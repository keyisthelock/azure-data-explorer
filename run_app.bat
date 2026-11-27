@echo off
REM One-click launcher for Windows: sets up .venv on first run, then starts the app.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto install

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo Python was not found. Install it from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" during setup, then run this file again.
  pause
  exit /b 1
)
echo Creating virtual environment in .venv ...
%PY% -m venv .venv
if errorlevel 1 (
  echo Could not create the virtual environment. See README section 8.
  pause
  exit /b 1
)

:install
echo Installing packages (the first run takes a minute or two) ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo Package install failed. Check your internet connection and see README section 8.
  pause
  exit /b 1
)

echo.
echo Starting Azure Data Explorer. Open http://localhost:8501 in your browser.
echo Press Ctrl+C in this window to stop the app.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true
pause
