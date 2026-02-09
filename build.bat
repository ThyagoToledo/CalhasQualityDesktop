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

echo [5/5] Build concluido!

echo.
echo ============================================
echo   Build completo!
echo   Executavel: dist\CalhaGest\CalhaGest.exe
echo ============================================
pause
