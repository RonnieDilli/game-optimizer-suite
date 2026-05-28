@echo off
setlocal EnableDelayedExpansion
title Steam Repair and Cache Cleaner
color 0A

:: === CONFIGURACAO DE LOG E AMBIENTE ===
set "LogDir=%~dp0..\..\logs"
if not exist "!LogDir!" mkdir "!LogDir!"
set "LogFile=!LogDir!\steam_repair.log"

set "AUTO_MODE=0"
if /I "%~1"=="--auto" set "AUTO_MODE=1"

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set "LogTS=!dt:~0,4!-!dt:~4,2!-!dt:~6,2! !dt:~8,2!:!dt:~10,2!:!dt:~12,2!"

echo ==================================================== >> "!LogFile!"
echo [!LogTS!] INICIO DE EXECUCAO - STEAM REPAIR >> "!LogFile!"

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    call :Log "[ERRO] Privilegios de Administrador ausentes. Abortando cleanup."
    if "!AUTO_MODE!"=="0" pause
    exit /b 1
)

:: === DESCOBERTA DE DIRETORIO ===
set "SteamPath="
FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"
if "!SteamPath!"=="" FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"

if "!SteamPath!"=="" (
    if "!AUTO_MODE!"=="1" (
        call :Log "[ERRO] Steam nao localizada no modo automatico. Abortando."
        exit /b 1
    )
    set /p "SteamPath=Digite o caminho da Steam: "
)

set "SteamPath=!SteamPath:"=!"
if "!SteamPath:~-1!"=="\" set "SteamPath=!SteamPath:~0,-1!"

if not exist "!SteamPath!\Steam.exe" (
    call :Log "[ERRO CRITICO] Steam.exe nao encontrado no diretorio: !SteamPath!"
    if "!AUTO_MODE!"=="0" pause
    exit /b 1
)
call :Log "[INFO] Steam localizada em: !SteamPath!"

:: === PERGUNTAS INICIAIS (Protegidas no modo Auto) ===
set "LIMPAR_LOGIN=N"
set "CORRIGIR_VAC=N"

if "!AUTO_MODE!"=="0" (
    echo ===================================================
    echo      OTIMIZADOR E REPARADOR DA STEAM
    echo ===================================================
    echo.
    set /p LIMPAR_LOGIN="[1] Limpar login (forca nova autenticacao 2FA)? [S/N] (Padrao N): "
    set /p CORRIGIR_VAC="[2] Aplicar correcoes VAC (bcdedit)? [S/N] (Padrao N): "
    echo.
) else (
    call :Log "[INFO] Execucao automatica detectada. Pulando prompts interativos (Default: N)."
)

:: === EXECUCAO ===
call :Log "[INFO] Fechando aplicacao..."
taskkill /F /IM Steam.exe >nul 2>&1
timeout /t 2 >nul

call :Log "[INFO] Reparando servico SteamService.exe..."
"!SteamPath!\bin\SteamService.exe" /repair >nul 2>&1

call :Log "[INFO] Iniciando limpeza de caches (Diretorios)..."
call :CleanDir "!SteamPath!\appcache"
call :CleanDir "!SteamPath!\depotcache"
call :CleanDir "!SteamPath!\steamapps\shadercache"
call :CleanDir "!SteamPath!\steamapps\downloading"
call :CleanDir "!SteamPath!\steamapps\temp"
call :CleanDir "!SteamPath!\steamapps\common\Counter-Strike Global Offensive\game\csgo\cache"
call :CleanDir "%LocalAppData%\Steam\htmlcache"

if /I "!LIMPAR_LOGIN!"=="S" (
    call :Log "[AVISO] Removendo credenciais de login e tokens Steam Guard..."
    del /F /Q "!SteamPath!\config\loginusers.vdf" >nul 2>&1
    del /F /Q "!SteamPath!\ssfn*" >nul 2>&1
)

if /I "!CORRIGIR_VAC!"=="S" (
    call :Log "[AVISO] Aplicando correcoes no BCD para prevencao do erro de VAC..."
    bcdedit /deletevalue nointegritychecks >nul 2>&1
    bcdedit /deletevalue loadoptions >nul 2>&1
    bcdedit /debug off >nul 2>&1
    bcdedit.exe /set {current} nx OptIn >nul 2>&1
    bcdedit /deletevalue nx >nul 2>&1
)

:: === CHAMADA DO MODULO DE HARDWARE ===
set "HardwareScript=%~dp0..\hardware\gpu_os_cleanup.bat"
if exist "!HardwareScript!" (
    call :Log "[INFO] Delegando limpeza de GPU ao modulo de hardware..."
    call "!HardwareScript!" --auto
) else (
    call :Log "[AVISO] Modulo de hardware nao encontrado em !HardwareScript!"
)

call :Log "[SUCESSO] Modulo Steam finalizado."
echo ==================================================== >> "!LogFile!"

:: === ENCERRAMENTO ===
if "!AUTO_MODE!"=="0" (
    echo.
    echo Processo finalizado com sucesso! Consulte o arquivo de log para detalhes.
    if /I "!CORRIGIR_VAC!"=="S" (
        set /p REBOOT="[VAC] As alteracoes no BCD exigem reinicio. Reiniciar agora? [S/N]: "
        if /I "!REBOOT!"=="S" shutdown /r /t 0
    ) else (
        echo Pressione qualquer tecla para iniciar a Steam...
        pause >nul
        start "" "!SteamPath!\Steam.exe" -tcp -clearbeta
    )
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