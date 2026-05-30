import os
import re
import subprocess
import winreg
import shutil
from pathlib import Path

def get_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "InstallPath")
        return Path(path)
    except FileNotFoundError:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return Path(path)
        except FileNotFoundError:
            return None

def parse_loginusers(steam_path: Path):
    vdf_path = steam_path / "config" / "loginusers.vdf"
    accounts = []
    if not vdf_path.exists(): return accounts
    content = vdf_path.read_text(encoding="utf-8")
    
    user_blocks = re.finditer(r'"(\d{17})"\s*\{([^}]+)\}', content)
    for match in user_blocks:
        steam_id = match.group(1)
        block_data = match.group(2)
        acc_name = re.search(r'"AccountName"\s*"([^"]+)"', block_data)
        persona_name = re.search(r'"PersonaName"\s*"([^"]+)"', block_data)
        if acc_name:
            accounts.append({
                "SteamID": steam_id,
                "AccountName": acc_name.group(1),
                "PersonaName": persona_name.group(1) if persona_name else "Desconhecido"
            })
    return accounts

def set_autologin(account_name: str):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "AutoLoginUser", 0, winreg.REG_SZ, account_name)
            winreg.SetValueEx(key, "RememberPassword", 0, winreg.REG_DWORD, 1)
        print(f"[\033[92mSUCESSO\033[0m] Registro atualizado. Proximo login: {account_name}")
    except Exception as e:
        print(f"[\033[91mERRO\033[0m] Falha ao atualizar registro: {e}")

def get_actual_gpu_ids():
    try:
        output = subprocess.check_output('wmic path win32_VideoController get PNPDeviceID', shell=True, text=True)
        match = re.search(r"VEN_([0-9A-Fa-f]{4})&DEV_([0-9A-Fa-f]{4})", output)
        if match:
            return str(int(match.group(1), 16)), str(int(match.group(2), 16))
    except Exception: pass
    return None, None

def get_user_video_preferences(video_cfg_path: Path):
    """Extrai configuracoes de monitor e GPU atuais do usuario para nao quebra-las."""
    prefs = {
        "VendorID": "4318",
        "DeviceID": "8710",
        "setting.defaultres": "2560",
        "setting.defaultresheight": "1440",
        "setting.refreshrate_numerator": "239761",
        "setting.refreshrate_denominator": "1000",
        "setting.fullscreen": "1",
        "setting.monitor_index": "0"
    }
    
    if video_cfg_path.exists():
        content = video_cfg_path.read_text(encoding="utf-8")
        for key in prefs.keys():
            # Busca o valor numerico associado a chave
            match = re.search(fr'"{key}"\s*"(\d+)"', content)
            if match:
                prefs[key] = match.group(1)
    return prefs

def optimize_cs2_video(steam_path: Path, account: dict):
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
    video_cfg_path = cfg_dir / "cs2_video.txt"
    
    prefs = get_user_video_preferences(video_cfg_path)
    real_vendor, real_device = get_actual_gpu_ids()
    
    print(f"\n--- Otimizacao de Video CS2 ({account['PersonaName']}) ---")
    
    if real_vendor and real_device:
        if real_vendor != prefs["VendorID"] or real_device != prefs["DeviceID"]:
            print("[\033[93mAVISO\033[0m] Divergencia de hardware (GPU) detectada!")
            ans = input("Atualizar cs2_video.txt com os IDs fisicos reais? (S/N): ")
            if ans.lower() == 's':
                prefs["VendorID"] = real_vendor
                prefs["DeviceID"] = real_device
    
    template_path = Path(__file__).resolve().parent.parent.parent / "docs" / "configs" / "templates" / "cs2_video_base.txt"
    if not template_path.exists():
        print(f"[\033[91mERRO\033[0m] Template nao encontrado em: {template_path}")
        return cfg_dir
        
    template_content = template_path.read_text(encoding="utf-8")
    
    # --- NOVO: LÓGICA DE AUDITORIA E EXPLICAÇÃO ---
    print("\n[\033[96mAUDITORIA E APLICAÇÃO DE CONFIGURAÇÕES\033[0m]")
    
    # Lendo arquivo atual para comparar
    old_content = video_cfg_path.read_text(encoding="utf-8") if video_cfg_path.exists() else ""
    
    explanations = {
        "AutoConfig": ("0", "Desabilita benchmark oculto da Source 2 no boot. Blinda o arquivo contra resets automaticos do jogo."),
        "setting.r_low_latency": ("2", "Ativa NVIDIA Reflex no modo 'On + Boost'. Mantem clocks da GPU no maximo para reduzir fila de quadros e input lag."),
        "setting.cpu_level": ("3", "Forca uso maximo/paralelizacao agressiva de threads de CPU."),
        "setting.gpu_level": ("3", "Forca engine a utilizar potencia total de renderizacao da GPU."),
        "setting.gpu_mem_level": ("3", "Aloca todo o pool de memoria de video disponivel (VRAM) para evitar stuttering de texturas.")
    }
    
    for key, (target_val, reason) in explanations.items():
        # Busca como estava antes
        old_match = re.search(fr'"{key}"\s*"(\d+)"', old_content)
        old_val = old_match.group(1) if old_match else "N/A"
        
        # Só exibe se houve mudança ou se estava indefinido
        if old_val != target_val:
            print(f"[*] {key}: {old_val} -> \033[92m{target_val}\033[0m")
            print(f"    └─ Motivo: {reason}")
        else:
            print(f"[-] {key} ja estava otimizado (\033[92m{target_val}\033[0m).")
    print("---------------------------------------------------")
    
    # Injeta as preferencias no Template
    new_content = template_content.format(
        res_w=prefs["setting.defaultres"],
        res_h=prefs["setting.defaultresheight"],
        refresh_num=prefs["setting.refreshrate_numerator"],
        refresh_den=prefs["setting.refreshrate_denominator"],
        fullscreen=prefs["setting.fullscreen"],
        monitor_idx=prefs["setting.monitor_index"],
        vendor_id=prefs["VendorID"],
        device_id=prefs["DeviceID"]
    )
    
    cfg_dir.mkdir(parents=True, exist_ok=True)
    video_cfg_path.write_text(new_content, encoding="utf-8")
    print(f"[\033[92mSUCESSO\033[0m] Template aplicado em: {video_cfg_path}")
    
    return cfg_dir

import configparser

def get_private_repo_path():
    """Lê ou cria a configuração do repositório privado do usuário."""
    config_file = Path(__file__).resolve().parent.parent.parent / "local_config.ini"
    config = configparser.ConfigParser()
    
    if config_file.exists():
        config.read(config_file)
        if 'USER_DATA' in config and 'PrivateRepoPath' in config['USER_DATA']:
            return Path(config['USER_DATA']['PrivateRepoPath'])
            
    # Se não existir, configura no primeiro uso
    print("\n[\033[96mSETUP INICIAL\033[0m] Repositorio de Dados Privado")
    print("Para manter seus dados separados do codigo da aplicacao, informe")
    print("o caminho da pasta onde seu repositorio privado do Git esta localizado.")
    path_str = input("Caminho (ex: C:\\Users\\ronni\\OneDrive\\CS2_Configs): ")
    
    private_path = Path(path_str.strip('\"\''))
    private_path.mkdir(parents=True, exist_ok=True)
    
    config['USER_DATA'] = {'PrivateRepoPath': str(private_path)}
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        
    return private_path

def sync_to_repo(cfg_dir: Path, account_name: str):
    """Sincroniza os arquivos para o repositório PRIVADO do usuário."""
    base_repo_path = get_private_repo_path()
    account_repo_dir = base_repo_path / "cs2" / account_name
    account_repo_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Sincronizando arquivos para Git Privado ({account_name}) ---")
    print(f"Destino: {account_repo_dir}")
    
    files_to_sync = ["cs2_video.txt", "autoexec.cfg", "config.cfg"]
    for file_name in files_to_sync:
        src = cfg_dir / file_name
        dst = account_repo_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"[*] {file_name} copiado com sucesso.")
        else:
            print(f"[-] {file_name} nao encontrado. Ignorando.")

def main():
    print("===================================================")
    print("       CS2 ACCOUNT & CONFIG SYNC MANAGER")
    print("===================================================\n")
    
    steam_path = get_steam_path()
    if not steam_path: return

    accounts = parse_loginusers(steam_path)
    
    print("Selecione a conta para login:")
    for i, acc in enumerate(accounts):
        print(f"[{i+1}] {acc['PersonaName']} (Account: {acc['AccountName']})")
    print(f"[{len(accounts)+1}] Inserir login manualmente")
    
    try:
        choice = int(input("\nOpcao: "))
        selected_account = None
        
        if 1 <= choice <= len(accounts):
            selected_account = accounts[choice-1]
            acc_login = selected_account['AccountName']
        elif choice == len(accounts) + 1:
            acc_login = input("Digite o Login da conta: ")
        else: return

        print("\n[\033[94mExecutando\033[0m] Fechando a Steam...")
        subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        set_autologin(acc_login)
        
        if selected_account:
            opt = input("\nAplicar otimizacoes de video CS2 e sincronizar repositório? (S/N): ")
            if opt.lower() == 's':
                cfg_dir = optimize_cs2_video(steam_path, selected_account)
                sync_to_repo(cfg_dir, selected_account['AccountName'])

        print("\nProcesso concluido! Pressione ENTER para abrir a Steam...")
        input()
        subprocess.Popen([str(steam_path / "Steam.exe"), "-tcp", "-clearbeta"])
        
    except ValueError:
        print("Entrada invalida.")

if __name__ == "__main__":
    main()