@echo off
setlocal EnableDelayedExpansion
title Epic Games ^& Rocket League Optimizer
color 0B

:: === CONFIGURACAO DE LOG E AMBIENTE ===
set "LogDir=%~dp0..\..\logs"
if not exist "!LogDir!" mkdir "!LogDir!"
set "LogFile=!LogDir!\epic_rl_repair.log"

set "AUTO_MODE=0"
if /I "%~1"=="--auto" set "AUTO_MODE=1"

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set "LogTS=!dt:~0,4!-!dt:~4,2!-!dt:~6,2! !dt:~8,2!:!dt:~10,2!:!dt:~12,2!"

echo ==================================================== >> "!LogFile!"
echo [!LogTS!] INICIO DE EXECUCAO - EPIC ^& RL REPAIR >> "!LogFile!"

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    call :Log "[ERRO] Privilegios de Administrador ausentes. Abortando cleanup."
    if "!AUTO_MODE!"=="0" pause
    exit /b 1
)

:: === DESCOBERTA DE DIRETORIO DOS DOCUMENTOS ===
FOR /F "tokens=3*" %%A IN ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Personal 2^>nul') DO SET "DocsPath=%%B"
call set "DocsPath=!DocsPath!"
call :Log "[INFO] Diretorio de Documentos detectado em: !DocsPath!"

:: === PERGUNTAS INICIAIS (Protegidas no modo Auto) ===
set "LIMPAR_LOGIN_EPIC=N"
set "LIMPAR_REPLAYS_RL=N"

if "!AUTO_MODE!"=="0" (
    echo ===================================================
    echo     OTIMIZADOR EPIC GAMES E ROCKET LEAGUE
    echo ===================================================
    echo.
    set /p LIMPAR_LOGIN_EPIC="[1] Forcar limpeza profunda da Epic (exige novo login)? [S/N] (Padrao N): "
    set /p LIMPAR_REPLAYS_RL="[2] Apagar TODOS os Replays salvos do Rocket League? [S/N] (Padrao N): "
    echo.
) else (
    call :Log "[INFO] Execucao automatica detectada. Pulando prompts interativos (Default: N)."
)

:: === EXECUCAO ===
call :Log "[INFO] Encerrando processos Epic e Rocket League..."
taskkill /F /IM EpicGamesLauncher.exe >nul 2>&1
taskkill /F /IM RocketLeague.exe >nul 2>&1
timeout /t 2 >nul

call :Log "[INFO] Limpando caches seguros (Epic e EOS Overlay)..."
call :CleanDir "%LocalAppData%\EpicGamesLauncher\Saved\Crashes"
call :CleanDir "%LocalAppData%\EpicGamesLauncher\Saved\Logs"
call :CleanDir "%LocalAppData%\Epic Games\EOSOverlay\BrowserCache"

if /I "!LIMPAR_LOGIN_EPIC!"=="S" (
    call :Log "[AVISO] Limpeza profunda de WebCache solicitada (Desconexao)..."
    call :CleanDir "%LocalAppData%\EpicGamesLauncher\Saved\webcache"
    call :CleanDir "%LocalAppData%\EpicGamesLauncher\Saved\webcache_4147"
    call :CleanDir "%LocalAppData%\EpicGamesLauncher\Saved\webcache_4430"
)

call :Log "[INFO] Limpando Caches de Textura do Rocket League..."
call :CleanDir "!DocsPath!\My Games\Rocket League\TAGame\Cache"
call :CleanDir "!DocsPath!\My Games\Rocket League\TAGame\Logs"

if /I "!LIMPAR_REPLAYS_RL!"=="S" (
    call :Log "[AVISO] Excluindo permanentemente todos os arquivos de Replay (Demos)..."
    del /F /Q "!DocsPath!\My Games\Rocket League\TAGame\Demos\*.replay" >nul 2>&1
)

:: === CHAMADA DO MODULO DE HARDWARE ===
set "HardwareScript=%~dp0..\hardware\gpu_os_cleanup.bat"
if exist "!HardwareScript!" (
    call :Log "[INFO] Delegando limpeza de GPU ao modulo de hardware..."
    call "!HardwareScript!" --auto
) else (
    call :Log "[AVISO] Modulo de hardware nao encontrado em !HardwareScript!"
)

call :Log "[SUCESSO] Modulo Epic/RL finalizado."
echo ==================================================== >> "!LogFile!"

:: === ENCERRAMENTO ===
if "!AUTO_MODE!"=="0" (
    echo.
    echo Processo finalizado com sucesso! Consulte o arquivo de log para detalhes.
    echo Pressione qualquer tecla para sair...
    pause >nul
)
exit /b 0

:: ==========================================
:: FUNCOES AUXILIARES (LOG E CONTAGEM)
:: ==========================================
:Log
set "msg=%~1"
if "!AUTO_MODE!"=="0" echo !msg!
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set ts=%%I
set "ts_fmt=!ts:~0,4!-!ts:~4,2!-!ts:~6,2! !ts:~8,2!:!ts:~10,2!:!ts:~12,2!"
echo [!ts_fmt!] !msg! >> "!LogFile!"
exit /b

:CleanDir
set "target=%~1"
if exist "!target!" (
    set "before=0"
    for /f %%A in ('dir /s /b /a-d "!target!" 2^>nul ^| find /c /v ""') do set before=%%A
    
    if !before! GTR 0 (
        RD /S /Q "!target!" >nul 2>&1
        mkdir "!target!" >nul 2>&1
        set "after=0"
        for /f %%A in ('dir /s /b /a-d "!target!" 2^>nul ^| find /c /v ""') do set after=%%A
        set /a "deleted=before-after"
        call :Log "  -> [LIMPEZA] !deleted! excluidos em: !target! (Restantes: !after!)"
    )
)
exit /b