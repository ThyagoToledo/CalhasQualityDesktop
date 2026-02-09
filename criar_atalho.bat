@echo off
title Criar Atalho CalhaGest
echo Criando atalho do CalhaGest na Area de Trabalho...

set "SCRIPT_DIR=%~dp0"
set "TARGET=%SCRIPT_DIR%CalhaGest.bat"
set "ICON=%SCRIPT_DIR%icon\CalhaGest.ico"

:: Criar atalho usando PowerShell com caminho correto da area de trabalho
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$Desktop = [Environment]::GetFolderPath('Desktop'); ^
$WS = New-Object -ComObject WScript.Shell; ^
$SC = $WS.CreateShortcut(\"$Desktop\CalhaGest.lnk\"); ^
$SC.TargetPath = '%TARGET%'; ^
$SC.WorkingDirectory = '%SCRIPT_DIR%'; ^
$SC.IconLocation = '%ICON%'; ^
$SC.Save(); ^
Write-Host 'Atalho criado em:' $Desktop"

echo.
echo Atalho criado com sucesso!
echo.
pause
