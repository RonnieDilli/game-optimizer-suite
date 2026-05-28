@echo off
setlocal EnableDelayedExpansion
title Steam Repair and Cache Cleaner
color 0A

:: === VERIFICACAO DE PRIVILEGIOS (ADMIN) ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ===================================================
    echo [ERRO CRITICO] PRIVILEGIOS DE ADMINISTRADOR AUSENTES
    echo ===================================================
    echo As correcoes do VAC e do Servico da Steam exigem 
    echo elevacao de privilegios. Feche esta janela, clique 
    echo com o botao direito no arquivo .bat e selecione 
    echo "Executar como administrador".
    echo ===================================================
    pause
    exit /b 1
)

echo ===================================================
echo      OTIMIZADOR E REPARADOR DA STEAM (Auto-Detect)
echo ===================================================
echo.

:: === FASE 0: DESCOBERTA AUTONOMA DE DIRETORIO ===
echo [Setup] Procurando instalacao da Steam no Registro do Windows...
set "SteamPath="

FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\WOW6432Node\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"

if "!SteamPath!"=="" (
    FOR /F "tokens=2*" %%A IN ('reg query "HKLM\SOFTWARE\Valve\Steam" /v InstallPath 2^>nul') DO SET "SteamPath=%%B"
)

if "!SteamPath!"=="" (
    echo [Aviso] Nao foi possivel localizar o diretorio da Steam automaticamente.
    set /p "SteamPath=Digite o caminho completo da Steam (ex: C:\Program Files (x86)\Steam): "
)

set "SteamPath=!SteamPath:"=!"
if "!SteamPath:~-1!"=="\" set "SteamPath=!SteamPath:~0,-1!"

if not exist "!SteamPath!\Steam.exe" (
    echo [Erro Critico] Steam.exe nao encontrado no diretorio: !SteamPath!
    pause
    exit /b 1
)
echo [Setup] Steam localizada com sucesso em: !SteamPath!
echo.

:: === FASE 1: PERGUNTAS INICIAIS ===
set LIMPAR_LOGIN=N
echo [AVISO] Limpar o login forca reautenticacao com senha e Token do Steam Guard!
set /p LIMPAR_LOGIN="[1] Deseja realmente limpar os dados de login? [S/N] (Padrao: N): "

set CORRIGIR_VAC=N
set /p CORRIGIR_VAC="[2] Aplicar correcoes do VAC (bcdedit)? [S/N] (Padrao: N): "

:: === FASE 2: RESUMO DAS SELECOES ===
echo.
echo ===================================================
echo                RESUMO DAS ESCOLHAS
echo ===================================================
if /I "!LIMPAR_LOGIN!"=="S" (echo - Limpar dados de Login: [ SIM ]) else (echo - Limpar dados de Login: [ NAO ])
if /I "!CORRIGIR_VAC!"=="S" (echo - Aplicar correcao VAC:  [ SIM ]) else (echo - Aplicar correcao VAC:  [ NAO ])
echo ===================================================
echo Pressione qualquer tecla para iniciar o processo...
pause >nul

:: === FASE 3: EXECUCAO ===
echo.
echo [Executando] Fechando a Steam...
taskkill /F /IM Steam.exe >nul 2>&1
timeout /t 2 >nul

echo [Executando] Reparando o Servico da Steam...
"!SteamPath!\bin\SteamService.exe" /repair >nul 2>&1

echo [Executando] Limpando caches da Steam, Jogos e Shaders...
RD /S /Q "!SteamPath!\appcache" >nul 2>&1
RD /S /Q "!SteamPath!\depotcache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\shadercache" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\downloading" >nul 2>&1
RD /S /Q "!SteamPath!\steamapps\temp" >nul 2>&1
:: Mantido o caminho legacy do root folder que a Valve utiliza para o CS2
RD /S /Q "!SteamPath!\steamapps\common\Counter-Strike Global Offensive\game\csgo\cache" >nul 2>&1

RD /S /Q "%LocalAppData%\Steam\htmlcache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\DXCache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\GLCache" >nul 2>&1
RD /S /Q "%LocalAppData%\AMD\DxCache" >nul 2>&1

set "RESULT_LOGIN=Ignorado."
set "RESULT_VAC=Ignorado."

if /I "!LIMPAR_LOGIN!"=="S" (
    echo [Executando] Limpando credenciais...
    del /F /Q "!SteamPath!\config\loginusers.vdf" >nul 2>&1
    del /F /Q "!SteamPath!\ssfn*" >nul 2>&1
    set "RESULT_LOGIN=Executado. Tokens e contas removidos."
)

if /I "!CORRIGIR_VAC!"=="S" (
    echo [Executando] Aplicando correcoes do VAC...
    bcdedit /deletevalue nointegritychecks >nul 2>&1
    bcdedit /deletevalue loadoptions >nul 2>&1
    bcdedit /debug off >nul 2>&1
    :: Correcao aplicada: nx OptIn substitui AlwaysOn para seguranca de drivers
    bcdedit.exe /set {current} nx OptIn >nul 2>&1
    bcdedit /deletevalue nx >nul 2>&1
    set "RESULT_VAC=Comandos enviados ao BCD com sucesso."
)

:: === FASE 4: RESUMO FINAL ===
echo.
echo ===================================================
echo          RESULTADOS ESPERADOS VS ALCANCADOS
echo ===================================================
echo [Localizacao Base] !SteamPath!
echo [Servico ^& Cache] Diretorios limpos e reparados.
echo [Login ^& Guard]   !RESULT_LOGIN!
echo [Correcoes VAC]    !RESULT_VAC!
echo ===================================================

if /I "!CORRIGIR_VAC!"=="S" (
    echo.
    echo [REINICIO NECESSARIO]
    echo As alteracoes no boot do Windows (bcdedit) exigem 
    echo a reinicializacao do computador para fazerem efeito
    echo e resolverem os erros de sessao do VAC.
    echo.
    set /p REBOOT="Deseja reiniciar o PC agora? [S/N]: "
    if /I "!REBOOT!"=="S" shutdown /r /t 0
) else (
    echo Pressione qualquer tecla para iniciar a Steam...
    pause >nul
    start "" "!SteamPath!\Steam.exe" -tcp -clearbeta
)
exit
