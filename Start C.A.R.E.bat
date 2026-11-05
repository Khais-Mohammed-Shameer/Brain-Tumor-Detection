@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  py -3 serve.py
  goto :eof
)
where python >nul 2>nul
if %errorlevel% equ 0 (
  python serve.py
  goto :eof
)
echo Python 3 is required for the portable launcher. No Python packages are needed.
pause
