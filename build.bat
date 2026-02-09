@echo off
REM CalhaGest - Build Script
REM Gera o executável e o instalador

echo ============================================
echo   CalhaGest - Build Script v1.1.0
echo ============================================
echo.

REM Limpar builds antigos
echo [1/5] Limpando builds antigos...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo OK!

REM Instalar dependências
echo [2/5] Instalando/atualizando dependências...
pip install --upgrade pyinstaller fpdf2 customtkinter pillow matplotlib defusedxml fonttools darkdetect
echo OK!

REM Compilar com PyInstaller
echo [3/5] Compilando com PyInstaller...
pyinstaller build_config.spec --distpath dist --noconfirm
echo OK!

REM Verificar se o build foi criado
if not exist "dist\CalhaGest\CalhaGest.exe" (
    echo ERRO: Build falhou! CalhaGest.exe nao foi gerado.
    pause
    exit /b 1
)

echo [4/5] Build gerado com sucesso em dist\CalhaGest\

REM Verificar se Inno Setup está instalado
where iscc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [5/5] Gerando instalador com Inno Setup...
    iscc CalhaGest_installer.iss
    echo Instalador gerado!
) else (
    if exist "C:\Program Files (x86)\Inno Setup 6\iscc.exe" (
        echo [5/5] Gerando instalador com Inno Setup...
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe" CalhaGest_installer.iss
        echo Instalador gerado!
    ) else (
        echo [5/5] Inno Setup nao encontrado. Instale: https://jrsoftware.org/isinfo.php
        echo Pule este passo - o executavel esta em dist\CalhaGest\
    )
)

echo.
echo ============================================
echo   Build completo!
echo   Executavel: dist\CalhaGest\CalhaGest.exe
echo ============================================
pause
