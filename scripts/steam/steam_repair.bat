@echo off
setlocal EnableDelayedExpansion
title Steam Repair and Cache Cleaner
color 0A

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO CRITICO] Execute como administrador.
    pause
    exit /b 1
)

echo ===================================================
echo      OTIMIZADOR E REPARADOR DA STEAM
echo ===================================================
echo.

set "SteamPath="
FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"
if "!SteamPath!"=="" FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"

if "!SteamPath!"=="" set /p "SteamPath=Digite o caminho da Steam: "
set "SteamPath=!SteamPath:"=!"
if "!SteamPath:~-1!"=="\" set "SteamPath=!SteamPath:~0,-1!"

if not exist "!SteamPath!\Steam.exe" (echo Steam.exe nao encontrado. & pause & exit /b 1)

set LIMPAR_LOGIN=N
set /p LIMPAR_LOGIN="[1] Limpar login (forca nova autenticacao 2FA)? [S/N]: "
set CORRIGIR_VAC=N
set /p CORRIGIR_VAC="[2] Aplicar correcoes VAC (bcdedit)? [S/N]: "

echo.
echo [Steam] Fechando aplicacao...
taskkill /F /IM Steam.exe >nul 2>&1
timeout /t 2 >nul

echo [Steam] Reparando servico...
"!SteamPath!\bin\SteamService.exe" /repair >nul 2>&1

echo [Steam] Limpando caches de jogos e navegador interno...
RD /S /Q "!SteamPath!\appcache" >nul 2>&1
RD /S /Q "!SteamPath!\depotcache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\shadercache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\downloading" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\temp" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\common\Counter-Strike Global Offensive\game\csgo\cache" >nul 2>&1
RD /S /Q "%LocalAppData%\Steam\htmlcache" >nul 2>&1

if /I "!LIMPAR_LOGIN!"=="S" (
    del /F /Q "!SteamPath!\config\loginusers.vdf" >nul 2>&1
    del /F /Q "!SteamPath!\ssfn*" >nul 2>&1
)

if /I "!CORRIGIR_VAC!"=="S" (
    bcdedit /deletevalue nointegritychecks >nul 2>&1
    bcdedit /deletevalue loadoptions >nul 2>&1
    bcdedit /debug off >nul 2>&1
    bcdedit.exe /set {current} nx OptIn >nul 2>&1
    bcdedit /deletevalue nx >nul 2>&1
)

echo.
:: === CHAMADA DO MODULO DE HARDWARE ===
set "HardwareScript=%~dp0..\hardware\gpu_os_cleanup.bat"
if exist "!HardwareScript!" (
    call "!HardwareScript!"
) else (
    echo [Aviso] Modulo de hardware nao encontrado em !HardwareScript!
)

echo.
echo Processo finalizado!
if /I "!CORRIGIR_VAC!"=="S" (
    set /p REBOOT="[VAC] Reinicio necessario. Reiniciar agora? [S/N]: "
    if /I "!REBOOT!"=="S" shutdown /r /t 0
) else (
    pause
    start "" "!SteamPath!\Steam.exe" -tcp -clearbeta
)
exit
