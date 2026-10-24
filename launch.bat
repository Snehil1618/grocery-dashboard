@echo off
title Domestic Gc Analyst
cd /d "%~dp0"
echo Starting... all output is also written to launch.log in this folder.
call :main > launch.log 2>&1
echo.
echo ---- launch.log ----
type launch.log
echo.
echo The launcher has stopped. Leave this window open and tell Claude.
pause
exit /b

:main
echo [%date% %time%] launch.bat started in %cd%
set "PY="
for %%P in ("%USERPROFILE%\anaconda3\python.exe" "%USERPROFILE%\miniconda3\python.exe" "%LOCALAPPDATA%\anaconda3\python.exe" "C:\ProgramData\anaconda3\python.exe" "C:\ProgramData\miniconda3\python.exe") do (
  if not defined PY if exist %%P set "PY=%%~P"
)
if not defined PY (
  py -3 --version >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
echo PY=%PY%
if not defined PY (
  echo ERROR: no working Python found.
  where python
  where py
  exit /b 1
)
%PY% --version
%PY% -c "import sys; print(sys.executable)"

echo [%time%] Installing packages...
%PY% -m pip install --upgrade streamlit pandas supabase plotly thefuzz
if errorlevel 1 (
  echo ERROR: pip install failed with code %errorlevel%
  exit /b 1
)
echo [%time%] Install finished. Launching Streamlit on http://localhost:8501
%PY% -m streamlit run app.py
echo [%time%] Streamlit exited with code %errorlevel%
exit /b
