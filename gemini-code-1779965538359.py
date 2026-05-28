import os
import subprocess
from pathlib import Path

def create_game_opt_suite(base_dir: str):
    """Cria a estrutura modular do repositorio."""
    base_path = Path(base_dir).resolve()
    print(f"Iniciando scaffold do repositorio modular em: {base_path}")

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
        print(f"Criado diretorio: {dir_path}")

    files_content = {
        # ==========================================
        # CONFIGURAÇÕES E DOCUMENTAÇÃO
        # ==========================================
        ".gitignore": r"""*.log
*.tmp
*.bak
.DS_Store
venv/
.env/
__pycache__/
local_config.ini
""",
        "README.md": r"""# Game Optimization Suite

Coletanea de scripts e especificacoes (SDD) para otimizacao de ambiente Windows, servicos de jogos e tuning de hardware.

## Arquitetura Modular
- **`scripts/hardware/`**: Rotinas base do sistema operacional, limpeza de shaders (NVIDIA/AMD) e gerenciamento de servicos.
- **`scripts/steam/`**: Manutencao especifica da Steam, dependente dos scripts de hardware.
- **`scripts/games/`**: Otimizacoes para Epic Games e Rocket League, dependentes dos scripts de hardware.
""",
        
        # ==========================================
        # SPECS (GHERKIN / BDD)
        # ==========================================
        "docs/specs/gpu_os_cleanup.feature": r"""Feature: Limpeza de Shaders e SO (Modulo Base)
  Para garantir frametimes consistentes e evitar stuttering
  Como um modulo central de manutencao
  Eu quero parar os servicos de video temporariamente para liberar o lock de arquivos de cache

  Scenario: Limpeza profunda de Shaders (NVIDIA/AMD)
    Given que o script e executado com privilegios de Administrador
    When a rotina de limpeza de hardware e chamada
    Then o servico "NVDisplay.ContainerLocalSystem" deve ser interrompido
    And os diretorios "DXCache" e "GLCache" da NVIDIA devem ser deletados
    And o diretorio "DxCache" da AMD deve ser deletado
    And o servico "NVDisplay.ContainerLocalSystem" deve ser reiniciado
""",
        "docs/specs/steam_repair.feature": r"""Feature: Steam Repair Modular
  Para limpar caches acumulados e reparar a Steam
  Eu quero executar uma rotina que delegue a limpeza de GPU para o modulo de hardware

  Scenario: Chamada de Modulo Externo
    Given que a limpeza especifica da Steam foi concluida
    When o script atinge a fase de limpeza de hardware
    Then ele deve invocar "scripts\hardware\gpu_os_cleanup.bat"
    And aguardar o retorno da execucao antes de exibir o resumo final
""",
        "docs/specs/epic_rl_repair.feature": r"""Feature: Epic Games e Rocket League Optimizer
  Para resolver problemas de micro-stuttering e limpar o EOS Overlay
  Eu quero limpar o webcache e delegar a limpeza grafica ao modulo de hardware

  Scenario: Limpeza do Epic Online Services
    Given que a Epic Games Launcher nao esta em execucao
    When eu rodo a limpeza padrao
    Then o cache do "EOSOverlay" deve ser deletado obrigatoriamente
    And os Demos do Rocket League so devem ser apagados mediante confirmacao explicita (Y/N)
""",

        # ==========================================
        # SCRIPTS BATCH (LÓGICA MODULAR)
        # ==========================================
        
        # 1. Módulo Central de Hardware
        "scripts/hardware/gpu_os_cleanup.bat": r"""@echo off
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
""",

        # 2. Módulo da Steam
        "scripts/steam/steam_repair.bat": r"""@echo off
setlocal EnableDelayedExpansion
title Steam Repair and Cache Cleaner
color 0A

:: === VERIFICACAO DE PRIVILEGIOS ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO CRITICO] Execute como administrador.
    pause
    exit /b 1
)

echo ===================================================
echo      OTIMIZADOR E REPARADOR DA STEAM
echo ===================================================
echo.

set "SteamPath="
FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"
if "!SteamPath!"=="" FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"

if "!SteamPath!"=="" set /p "SteamPath=Digite o caminho da Steam: "
set "SteamPath=!SteamPath:"=!"
if "!SteamPath:~-1!"=="\" set "SteamPath=!SteamPath:~0,-1!"

if not exist "!SteamPath!\Steam.exe" (echo Steam.exe nao encontrado. & pause & exit /b 1)

set LIMPAR_LOGIN=N
set /p LIMPAR_LOGIN="[1] Limpar login (forca nova autenticacao 2FA)? [S/N]: "
set CORRIGIR_VAC=N
set /p CORRIGIR_VAC="[2] Aplicar correcoes VAC (bcdedit)? [S/N]: "

echo.
echo [Steam] Fechando aplicacao...
taskkill /F /IM Steam.exe >nul 2>&1
timeout /t 2 >nul

echo [Steam] Reparando servico...
"!SteamPath!\bin\SteamService.exe" /repair >nul 2>&1

echo [Steam] Limpando caches de jogos e navegador interno...
RD /S /Q "!SteamPath!\appcache" >nul 2>&1
RD /S /Q "!SteamPath!\depotcache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\shadercache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\downloading" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\temp" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\common\Counter-Strike Global Offensive\game\csgo\cache" >nul 2>&1
RD /S /Q "%LocalAppData%\Steam\htmlcache" >nul 2>&1

if /I "!LIMPAR_LOGIN!"=="S" (
    del /F /Q "!SteamPath!\config\loginusers.vdf" >nul 2>&1
    del /F /Q "!SteamPath!\ssfn*" >nul 2>&1
)

if /I "!CORRIGIR_VAC!"=="S" (
    bcdedit /deletevalue nointegritychecks >nul 2>&1
    bcdedit /deletevalue loadoptions >nul 2>&1
    bcdedit /debug off >nul 2>&1
    bcdedit.exe /set {current} nx OptIn >nul 2>&1
    bcdedit /deletevalue nx >nul 2>&1
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
echo Processo finalizado!
if /I "!CORRIGIR_VAC!"=="S" (
    set /p REBOOT="[VAC] Reinicio necessario. Reiniciar agora? [S/N]: "
    if /I "!REBOOT!"=="S" shutdown /r /t 0
) else (
    pause
    start "" "!SteamPath!\Steam.exe" -tcp -clearbeta
)
exit
""",

        # 3. Módulo Epic e Rocket League
        "scripts/games/epic_rl_repair.bat": r"""@echo off
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
"""
    }

    for file_path_str, content in files_content.items():
        target_file = base_path / file_path_str
        target_file.write_text(content, encoding='utf-8')
        print(f"Criado/Atualizado: {file_path_str}")

if __name__ == "__main__":
    target_directory = input("Digite o caminho destino para o repositorio (Ex: C:\\projetos\\game-opt-suite): ")
    if target_directory.strip():
        create_game_opt_suite(target_directory)
    else:
        print("Caminho invalido.")