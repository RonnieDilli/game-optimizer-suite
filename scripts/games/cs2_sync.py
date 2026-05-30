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
    # Converte SteamID64 para SteamID3
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
    video_cfg_path = cfg_dir / "cs2_video.txt"
    
    # 1. Carrega as preferencias atuais do usuario para manter resolucao/monitor intactos
    prefs = get_user_video_preferences(video_cfg_path)
    
    # 2. Protecao contra troca de GPU (WMI Check)
    real_vendor, real_device = get_actual_gpu_ids()
    print(f"\n--- Otimizacao de Video CS2 ({account['PersonaName']}) ---")
    
    if real_vendor and real_device:
        if real_vendor != prefs["VendorID"] or real_device != prefs["DeviceID"]:
            print("[\033[93mAVISO\033[0m] Divergencia de hardware (GPU) detectada!")
            ans = input("Atualizar cs2_video.txt com os IDs fisicos reais? (S/N): ")
            if ans.lower() == 's':
                prefs["VendorID"] = real_vendor
                prefs["DeviceID"] = real_device
    
    # 3. Carrega o Template Base
    template_path = Path(__file__).resolve().parent.parent.parent / "docs" / "configs" / "templates" / "cs2_video_base.txt"
    if not template_path.exists():
        print(f"[\033[91mERRO\033[0m] Template nao encontrado em: {template_path}")
        return cfg_dir
        
    template_content = template_path.read_text(encoding="utf-8")
    
    # 4. Injeta as preferencias no Template
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
    print(f"[\033[92mSUCESSO\033[0m] Configuracoes injetadas (AutoConfig=0) em: {video_cfg_path}")
    
    return cfg_dir

def sync_to_repo(cfg_dir: Path, account_name: str):
    repo_cfg_dir = Path(__file__).resolve().parent.parent.parent / "docs" / "configs" / "cs2" / account_name
    repo_cfg_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Sincronizando arquivos para o Git ({account_name}) ---")
    for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
        src = cfg_dir / file_name
        dst = repo_cfg_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"[*] {file_name} copiado para versionamento.")

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