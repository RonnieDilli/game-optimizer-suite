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
    echo [Hardware] Servico NVIDIA em execucao. Parando para liberar handles...
    net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
    timeout /t 2 >nul
)

:: === VARREDURA ABSOLUTA DE PERFIS (Local e LocalLow) ===
echo [Hardware] Limpando DXCache e GLCache para todos os usuarios...
FOR /D %%U IN ("%SystemDrive%\Users\*") DO (
    :: Limpeza da pasta Local (Padrao)
    if exist "%%U\AppData\Local\NVIDIA\DXCache" RD /S /Q "%%U\AppData\Local\NVIDIA\DXCache" >nul 2>&1
    if exist "%%U\AppData\Local\NVIDIA\GLCache" RD /S /Q "%%U\AppData\Local\NVIDIA\GLCache" >nul 2>&1
    if exist "%%U\AppData\Local\AMD\DxCache" RD /S /Q "%%U\AppData\Local\AMD\DxCache" >nul 2>&1
    
    :: Limpeza da pasta LocalLow (Detectada via Process Explorer)
    if exist "%%U\AppData\LocalLow\NVIDIA\DXCache" RD /S /Q "%%U\AppData\LocalLow\NVIDIA\DXCache" >nul 2>&1
)

:: === RESTAURACAO DE ESTADO ===
if "!NvidiaServiceWasRunning!"=="1" (
    echo [Hardware] Restaurando servico NVIDIA (Em execucao)...
    net start NVDisplay.ContainerLocalSystem >nul 2>&1
)

echo [Hardware] Modulo de hardware concluido com sucesso.
exit /b 0