@echo off
setlocal EnableDelayedExpansion

:: Verifica Administrador silenciosamente
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [Hardware-Erro] Modulo de hardware requer privilegios de Administrador. Ignorando GPU cleanup.
    exit /b 1
)

echo [Hardware] Iniciando limpeza de caches de video do SO...

:: === VERIFICACAO DE ESTADO DO SERVICO DA NVIDIA ===
set "NvidiaServiceWasRunning=0"
sc query NVDisplay.ContainerLocalSystem | find /I "RUNNING" >nul 2>&1

if %errorLevel% equ 0 (
    set "NvidiaServiceWasRunning=1"
    echo [Hardware] Servico NVIDIA detectado em execucao. Parando para liberar arquivos...
    net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
    :: Aguarda 2 segundos para o driver soltar os handles
    timeout /t 2 >nul
) else (
    echo [Hardware] Servico NVIDIA ja esta parado ou inativo. Ignorando 'net stop'.
)

:: === LIMPEZA DE CACHES (NVIDIA E AMD) ===
echo [Hardware] Limpando DXCache e GLCache...
RD /S /Q "%LocalAppData%\NVIDIA\DXCache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\GLCache" >nul 2>&1
RD /S /Q "%LocalAppData%\AMD\DxCache" >nul 2>&1

:: === RESTAURACAO DE ESTADO ===
if "!NvidiaServiceWasRunning!"=="1" (
    echo [Hardware] Restaurando servico NVIDIA ao estado original (Em execucao)...
    net start NVDisplay.ContainerLocalSystem >nul 2>&1
) else (
    echo [Hardware] Servico NVIDIA mantido desligado conforme estado original.
)

echo [Hardware] Modulo de hardware concluido com sucesso.
exit /b 0