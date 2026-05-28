import os
import subprocess
from pathlib import Path

def create_game_opt_suite(base_dir: str):
    """Cria a estrutura modular do repositorio, incluindo agendamento de boot."""
    base_path = Path(base_dir).resolve()
    print(f"Atualizando scaffold do repositorio modular em: {base_path}")

    directories = [
        "docs/specs",
        "scripts/steam",
        "scripts/hardware",
        "scripts/games",
        "tests"
    ]

    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

    files_content = {
        # ==========================================
        # SPECS (GHERKIN / BDD) - ADIÇÃO DO AUTORUN
        # ==========================================
        "docs/specs/autorun_scheduler.feature": r"""Feature: Agendamento de Limpeza no Boot
  Para contornar o bloqueio de arquivos (File Lock) feito pelo DWM.exe e Windows Explorer
  Eu quero agendar a limpeza de GPU para ocorrer automaticamente no logon do sistema

  Scenario: Criacao de Tarefa Oculta no Task Scheduler
    Given que o script de setup e executado como Administrador
    When a rotina de agendamento e chamada
    Then uma tarefa chamada "GameOpt_GPU_BootCleanup" deve ser criada no Windows
    And o gatilho deve ser "Ao fazer logon" (ONLOGON)
    And a execucao deve ocorrer com privilegios maximos (Highest)
    And a chamada deve ser encapsulada em um PowerShell Hidden para nao exibir janelas
""",

        # ==========================================
        # SCRIPTS BATCH - NOVO INSTALADOR DE BOOT
        # ==========================================
        "scripts/hardware/setup_autorun.bat": r"""@echo off
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
""",

        # Mantendo o módulo de hardware base (Apenas garantindo que esteja atualizado)
        "scripts/hardware/gpu_os_cleanup.bat": r"""@echo off
setlocal EnableDelayedExpansion
net session >nul 2>&1
if %errorLevel% neq 0 exit /b 1

net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
timeout /t 1 >nul

RD /S /Q "%LocalAppData%\NVIDIA\DXCache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\GLCache" >nul 2>&1
RD /S /Q "%LocalAppData%\AMD\DxCache" >nul 2>&1

net start NVDisplay.ContainerLocalSystem >nul 2>&1
exit /b 0
"""
    }

    # Atualizando apenas os arquivos do escopo desta melhoria
    for file_path_str, content in files_content.items():
        target_file = base_path / file_path_str
        target_file.write_text(content, encoding='utf-8')
        print(f"Criado/Atualizado: {file_path_str}")

if __name__ == "__main__":
    target_directory = input("Digite o caminho destino para o repositorio: ")
    if target_directory.strip():
        create_game_opt_suite(target_directory)
    else:
        print("Caminho invalido.")