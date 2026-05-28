@echo off
title Setup: Auto-Cleanup on Boot
color 0E

:: Verifica Administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ===================================================
    echo [ERRO] PRIVILEGIOS DE ADMINISTRADOR AUSENTES
    echo ===================================================
    echo O Agendador de Tarefas do Windows exige elevacao.
    echo Feche e execute como Administrador.
    pause
    exit /b 1
)

set "TaskName=GameOpt_GPU_BootCleanup"
set "ScriptPath=%~dp0gpu_os_cleanup.bat"

:: Comando encapsulado em PowerShell para garantir que rode de forma totalmente invisivel
set "TaskCommand=powershell.exe -WindowStyle Hidden -Command \"& '%ScriptPath%'\""

echo ===================================================
echo    AGENDADOR DE OTIMIZACAO NO BOOT DO WINDOWS
echo ===================================================
echo.
echo Este script criara uma rotina invisivel que roda
echo a limpeza de Shaders (NVIDIA/AMD) sempre que voce
echo fizer login no Windows, garantindo que os caches
echo sejam apagados antes que os apps em segundo plano
echo bloqueiem os arquivos.
echo.

schtasks /query /tn "%TaskName%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [Aviso] A tarefa ja existe. Sobrescrevendo...
)

echo [Setup] Registrando tarefa no Windows Task Scheduler...
schtasks /create /tn "%TaskName%" /tr "%TaskCommand%" /sc onlogon /rl highest /f >nul 2>&1

if %errorLevel% equ 0 (
    echo.
    echo [SUCESSO] Tarefa "%TaskName%" agendada!
    echo Ela rodara invisivelmente com privilegios maximos no proximo boot.
) else (
    echo.
    echo [ERRO] Falha ao criar a tarefa. Verifique as permissoes do sistema.
)

echo.
pause
exit
