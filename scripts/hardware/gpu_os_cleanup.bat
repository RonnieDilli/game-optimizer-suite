@echo off
setlocal EnableDelayedExpansion

:: Verifica Administrador silenciosamente (quem chama geralmente ja verificou, mas protege execucao avulsa)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [Hardware-Erro] Modulo de hardware requer privilegios de Administrador. Ignorando GPU cleanup.
    exit /b 1
)

echo [Hardware] Iniciando limpeza de caches de video do SO...

echo [Hardware] Parando servicos da NVIDIA para liberar arquivos...
net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
timeout /t 2 >nul

echo [Hardware] Limpando DXCache e GLCache...
RD /S /Q "%LocalAppData%\NVIDIA\DXCache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\GLCache" >nul 2>&1
RD /S /Q "%LocalAppData%\AMD\DxCache" >nul 2>&1

echo [Hardware] Reiniciando servicos de video...
net start NVDisplay.ContainerLocalSystem >nul 2>&1

echo [Hardware] Modulo de hardware concluido com sucesso.
exit /b 0
