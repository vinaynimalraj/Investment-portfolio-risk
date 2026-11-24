@echo off
setlocal
cd /d "%~dp0"
set "DASHBOARD_PYTHON=%LOCALAPPDATA%\venvs\investment-risk\Scripts\python.exe"
if not exist "%DASHBOARD_PYTHON%" (
  echo The investment-risk Python environment was not found.
  echo Follow the installation steps in DASHBOARD_README.md.
  pause
  exit /b 1
)
"%DASHBOARD_PYTHON%" -m streamlit run "%~dp0app.py" --server.headless true --server.address 127.0.0.1 --browser.gatherUsageStats false
pause
