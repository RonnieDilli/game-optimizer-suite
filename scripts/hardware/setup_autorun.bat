@echo off
title Setup: Auto-Cleanup on Boot
color 0E

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ===================================================
    echo [ERRO CRITICO] PRIVILEGIOS DE ADMINISTRADOR AUSENTES
    echo ===================================================
    echo O Agendador de Tarefas do Windows exige elevacao.
    echo Feche e execute como Administrador.
    pause
    exit /b 1
)

set "TaskName=GameOpt_GPU_BootCleanup"
set "ScriptPath=%~dp0gpu_os_cleanup.bat"
set "VbsPath=%~dp0run_hidden.vbs"

echo ===================================================
echo    AGENDADOR DE OTIMIZACAO NO BOOT DO WINDOWS
echo ===================================================
echo.

echo [Setup] Gerando launcher silencioso (VBScript)...
echo Set WshShell = CreateObject("WScript.Shell") > "%VbsPath%"
echo WshShell.Run chr(34) ^& "%ScriptPath%" ^& chr(34), 0 >> "%VbsPath%"
echo Set WshShell = Nothing >> "%VbsPath%"

echo [Setup] Registrando tarefa no Windows Task Scheduler...
:: Alterado para rodar na Inicializacao (onstart) e como usuario SYSTEM (/ru SYSTEM)
schtasks /create /tn "%TaskName%" /tr "wscript.exe \"%VbsPath%\"" /sc onstart /ru SYSTEM /rl highest /f

if %errorLevel% equ 0 (
    echo.
    echo [SUCESSO] Tarefa "%TaskName%" agendada com sucesso!
    echo O VBScript garantira que a limpeza ocorra 100%% invisivel na Inicializacao do Sistema (Boot).
) else (
    echo.
    echo [ERRO] Falha ao criar a tarefa. Verifique as permissoes do sistema.
)

echo.
pause
exit