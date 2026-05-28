@echo off
setlocal EnableDelayedExpansion

:: === CONFIGURACAO DE LOG E AMBIENTE ===
:: Cria a pasta "logs" na raiz do repositorio, caso nao exista
set "LogDir=%~dp0..\..\logs"
if not exist "!LogDir!" mkdir "!LogDir!"
set "LogFile=!LogDir!\gpu_cleanup.log"

:: Identifica se foi rodado via Task Scheduler/VBS (--auto) ou manualmente
set "AUTO_MODE=0"
if /I "%~1"=="--auto" set "AUTO_MODE=1"

:: Captura Data/Hora (Metodo WMIC, imune a problemas de formato do Windows)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set dt=%%I
set "LogTS=!dt:~0,4!-!dt:~4,2!-!dt:~6,2! !dt:~8,2!:!dt:~10,2!:!dt:~12,2!"

echo ==================================================== >> "!LogFile!"
echo [!LogTS!] INICIO DE EXECUCAO >> "!LogFile!"

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    call :Log "[ERRO] Privilegios de Administrador ausentes. Abortando cleanup."
    if "!AUTO_MODE!"=="0" pause
    exit /b 1
)

call :Log "[INFO] Modulo de hardware iniciado."

:: === ESTADO DO SERVICO DA NVIDIA ===
set "NvidiaServiceWasRunning=0"
sc query NVDisplay.ContainerLocalSystem | find /I "RUNNING" >nul 2>&1
if %errorLevel% equ 0 (
    set "NvidiaServiceWasRunning=1"
    call :Log "[INFO] Servico NVIDIA detectado em execucao. Parando (net stop)..."
    net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
    timeout /t 2 >nul
) else (
    call :Log "[INFO] Servico NVIDIA ja inativo. Ignorando parada."
)

:: === VARREDURA E LIMPEZA DE PERFIS ===
call :Log "[INFO] Escaneando perfis de usuario por arquivos de Shader Cache..."

FOR /D %%U IN ("%SystemDrive%\Users\*") DO (
    call :CleanDir "%%U\AppData\Local\NVIDIA\DXCache"
    call :CleanDir "%%U\AppData\Local\NVIDIA\GLCache"
    call :CleanDir "%%U\AppData\Local\AMD\DxCache"
    call :CleanDir "%%U\AppData\LocalLow\NVIDIA\DXCache"
)

:: === RESTAURACAO DE ESTADO ===
if "!NvidiaServiceWasRunning!"=="1" (
    call :Log "[INFO] Restaurando servico NVIDIA (net start)..."
    net start NVDisplay.ContainerLocalSystem >nul 2>&1
)

call :Log "[SUCESSO] Modulo de hardware finalizado."
echo ==================================================== >> "!LogFile!"

:: === CONTROLE DE TELA (MANUAL VS AUTO) ===
if "!AUTO_MODE!"=="0" (
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
)
exit /b 0


:: ==========================================
:: FUNCOES AUXILIARES (LOG E CONTAGEM)
:: ==========================================
:Log
set "msg=%~1"
:: Printa na tela preta (Console)
echo !msg!
:: Salva no arquivo com nova timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set ts=%%I
set "ts_fmt=!ts:~0,4!-!ts:~4,2!-!ts:~6,2! !ts:~8,2!:!ts:~10,2!:!ts:~12,2!"
echo [!ts_fmt!] !msg! >> "!LogFile!"
exit /b

:CleanDir
set "target=%~1"
if exist "!target!" (
    :: Conta arquivos ANTES
    set "before=0"
    for /f %%A in ('dir /s /b /a-d "!target!" 2^>nul ^| find /c /v ""') do set before=%%A
    
    :: Se a pasta estiver vazia, nem tenta apagar para poluir o log
    if !before! GTR 0 (
        RD /S /Q "!target!" >nul 2>&1
        :: Recria a pasta estruturalmente para o Windows nao reclamar
        mkdir "!target!" >nul 2>&1

        :: Conta arquivos DEPOIS (Verifica os que ficaram travados)
        set "after=0"
        for /f %%A in ('dir /s /b /a-d "!target!" 2^>nul ^| find /c /v ""') do set after=%%A
        
        set /a "deleted=before-after"
        call :Log "  -> [LIMPEZA] !deleted! excluidos em: !target! (Restantes: !after!)"
    )
)
exit /b