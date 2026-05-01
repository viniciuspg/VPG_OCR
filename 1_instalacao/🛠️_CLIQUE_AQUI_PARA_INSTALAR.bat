@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================================================
echo VPG_OCR - INSTALADOR
echo ================================================================
echo.
echo IMPORTANTE:
echo 1. Se o Windows mostrar a janela de seguranca deste arquivo .bat,
echo    clique em EXECUTAR.
echo 2. Se desejar, marque a opcao para nao mostrar novamente.
echo 3. Se o Python nao estiver instalado, o instalador tentara instalar
echo    automaticamente o Python 3.14 usando winget.
echo.

where py >nul 2>&1
if %errorlevel% neq 0 (
    echo Python nao foi encontrado neste computador.
    echo O instalador vai tentar instalar automaticamente o Python 3.14...
    echo.
    winget install --id Python.Python.3.14 -e --source winget --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo.
        echo ERRO: nao foi possivel instalar o Python automaticamente.
        echo Tente instalar o Python manualmente e execute este arquivo novamente.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Python instalado com sucesso.
    echo.
)

where py >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERRO: o comando 'py' ainda nao foi encontrado.
    echo Feche esta janela, abra novamente o arquivo .bat e tente de novo.
    echo.
    pause
    exit /b 1
)

echo O instalador do VPG_OCR sera executado agora.
echo.
py ".\script_instalacao\instalacao_OCR.py"

echo.
pause
