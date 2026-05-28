@echo off
setlocal EnableDelayedExpansion
title Epic Games ^& Rocket League Optimizer
color 0B

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO CRITICO] Execute como administrador.
    pause
    exit /b 1
)

echo ===================================================
echo     OTIMIZADOR EPIC GAMES E ROCKET LEAGUE
echo ===================================================
echo.

FOR /F "tokens=3*" %%A IN ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Personal 2^>nul') DO SET "DocsPath=%%B"
call set "DocsPath=!DocsPath!"

set LIMPAR_LOGIN_EPIC=N
set /p LIMPAR_LOGIN_EPIC="[1] Forcar limpeza profunda da Epic (exige novo login)? [S/N]: "
set LIMPAR_REPLAYS_RL=N
set /p LIMPAR_REPLAYS_RL="[2] Apagar TODOS os Replays salvos do Rocket League? [S/N]: "

echo.
echo [Epic/RL] Encerrando processos...
taskkill /F /IM EpicGamesLauncher.exe >nul 2>&1
taskkill /F /IM RocketLeague.exe >nul 2>&1
timeout /t 2 >nul

echo [Epic] Limpando caches e EOS Overlay...
RD /S /Q "%LocalAppData%\EpicGamesLauncher\Saved\Crashes" >nul 2>&1
RD /S /Q "%LocalAppData%\EpicGamesLauncher\Saved\Logs" >nul 2>&1
RD /S /Q "%LocalAppData%\Epic Games\EOSOverlay\BrowserCache" >nul 2>&1

if /I "!LIMPAR_LOGIN_EPIC!"=="S" (
    RD /S /Q "%LocalAppData%\EpicGamesLauncher\Saved\webcache" >nul 2>&1
    RD /S /Q "%LocalAppData%\EpicGamesLauncher\Saved\webcache_4147" >nul 2>&1
    RD /S /Q "%LocalAppData%\EpicGamesLauncher\Saved\webcache_4430" >nul 2>&1
)

echo [RL] Limpando Caches de Textura...
RD /S /Q "!DocsPath!\My Games\Rocket League\TAGame\Cache" >nul 2>&1
RD /S /Q "!DocsPath!\My Games\Rocket League\TAGame\Logs" >nul 2>&1

if /I "!LIMPAR_REPLAYS_RL!"=="S" (
    del /F /Q "!DocsPath!\My Games\Rocket League\TAGame\Demos\*.replay" >nul 2>&1
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
echo Processo finalizado com sucesso!
pause >nul
exit
