@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
    py ".\scripts_OCR\5_OCR_MENU.py"
) else (
    python ".\scripts_OCR\5_OCR_MENU.py"
)
pause
