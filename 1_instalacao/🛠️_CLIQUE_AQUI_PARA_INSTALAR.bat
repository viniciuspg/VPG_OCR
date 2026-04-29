@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
    py ".\script_instalacao\instalacao_OCR.py"
) else (
    python ".\script_instalacao\instalacao_OCR.py"
)
pause
