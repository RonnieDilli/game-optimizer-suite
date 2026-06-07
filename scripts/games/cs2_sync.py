import os
import re
import subprocess
import winreg
import shutil
import logging
import configparser
from pathlib import Path
import core_git
import json

logger = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge" / "cs2_video.json"
LAUNCH_KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge" / "cs2_launch_options.json"

try:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        CS2_KNOWLEDGE_BASE = json.load(f)
except Exception as e:
    CS2_KNOWLEDGE_BASE = {}

try:
    with open(LAUNCH_KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        CS2_LAUNCH_KNOWLEDGE = json.load(f)
except Exception as e:
    CS2_LAUNCH_KNOWLEDGE = {}


def sync_to_repo(cfg_dir: Path, account_name: str, commit_msg: str = "Backup Manual"):
    base_repo = core_git.get_private_repo_path()
    account_repo_dir = base_repo / "cs2" / account_name
    account_repo_dir.mkdir(parents=True, exist_ok=True) # Garante a pasta
    
    for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
        src = cfg_dir / file_name
        dst = account_repo_dir / file_name
        if src.exists(): shutil.copy2(src, dst)
        
    core_git.commit_to_git(base_repo, f"CS2|{account_name}", commit_msg)

def auto_backup_if_changed(steam_path: Path, account: dict):
    base_repo = core_git.get_private_repo_path()
    acc_name = account["AccountName"]
    account_repo_dir = base_repo / "cs2" / acc_name
    
    # CORREÇÃO: Garante que a pasta do Git existe antes de copiar
    if not account_repo_dir.exists():
        account_repo_dir.mkdir(parents=True, exist_ok=True)
    
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
    
    # Verifica se os arquivos de origem existem
    changed = False
    for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
        src = cfg_dir / file_name
        if src.exists():
            shutil.copy2(src, account_repo_dir / file_name)
            changed = True
            
    if not changed: return False
        
    try:
        # Usa o core_git para verificar status e commitar
        return core_git.commit_to_git(base_repo, f"CS2|{acc_name}", "Auto-Sync || Alterações In-Game detectadas")
    except Exception as e:
        logger.error(f"Erro no auto-backup: {e}")
        return False

def get_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "InstallPath")
        return Path(path)
    except:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return Path(path)
        except: return None

def get_current_autologin():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            val, _ = winreg.QueryValueEx(key, "AutoLoginUser")
            return val
    except: return "Nenhuma"

def parse_loginusers(steam_path: Path):
    vdf_path = steam_path / "config" / "loginusers.vdf"
    accounts = []
    if not vdf_path.exists(): return accounts
    content = vdf_path.read_text(encoding="utf-8")
    for match in re.finditer(r'"(\d{17})"\s*\{([^}]+)\}', content):
        acc_name = re.search(r'"AccountName"\s*"([^"]+)"', match.group(2))
        persona_name = re.search(r'"PersonaName"\s*"([^"]+)"', match.group(2))
        if acc_name:
            accounts.append({
                "SteamID": match.group(1),
                "AccountName": acc_name.group(1),
                "PersonaName": persona_name.group(1) if persona_name else "Desconhecido"
            })
    return accounts

def set_autologin(account_name: str):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "AutoLoginUser", 0, winreg.REG_SZ, account_name)
            winreg.SetValueEx(key, "RememberPassword", 0, winreg.REG_DWORD, 1)
        return True
    except Exception as e:
        logger.error(f"Falha ao atualizar registro: {e}")
        return False

def get_actual_gpu_ids():
    try:
        output = subprocess.check_output('wmic path win32_VideoController get PNPDeviceID', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        match = re.search(r"VEN_([0-9A-Fa-f]{4})&DEV_([0-9A-Fa-f]{4})", output)
        if match: return str(int(match.group(1), 16)), str(int(match.group(2), 16))
    except: pass
    return None, None

def analyze_cs2_video(steam_path: Path, account: dict):
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    video_cfg_path = steam_path / "userdata" / account_id / "730" / "local" / "cfg" / "cs2_video.txt"
    old_content = video_cfg_path.read_text(encoding="utf-8") if video_cfg_path.exists() else ""
    analysis_data = []
    for key, data in CS2_KNOWLEDGE_BASE.items():
        old_match = re.search(fr'"{key}"\s*"(\d+)"', old_content)
        old_val = old_match.group(1) if old_match else "N/A"
        analysis_data.append({
            "key": key, "name": data["nome"], "current": old_val,
            "ideal": data["ideal"], "impact": data["impacto"], "is_ok": old_val == data["ideal"]
        })
    return analysis_data

def apply_selective_cs2_video(steam_path: Path, account: dict, selections: dict, force_gpu_update=False):
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
    video_cfg_path = cfg_dir / "cs2_video.txt"
    if not video_cfg_path.exists(): return None
    content = video_cfg_path.read_text(encoding="utf-8")
    for key, ideal_val in selections.items():
        if re.search(fr'"{key}"\s*"\d+"', content):
            content = re.sub(fr'("{key}"\s*)("\d+")', rf'\g<1>"{ideal_val}"', content)
        else: content = content.replace('\n}', f'\n\t"{key}"\t\t"{ideal_val}"\n}}')
    real_vendor, real_device = get_actual_gpu_ids()
    if force_gpu_update and real_vendor and real_device:
        content = re.sub(r'("VendorID"\s*)("\d+")', rf'\g<1>"{real_vendor}"', content)
        content = re.sub(r'("DeviceID"\s*)("\d+")', rf'\g<1>"{real_device}"', content)
    video_cfg_path.write_text(content, encoding="utf-8")
    return cfg_dir

def get_launch_options(steam_path: Path, account: dict):
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    vdf_path = steam_path / "userdata" / account_id / "config" / "localconfig.vdf"
    if not vdf_path.exists(): return ""
    
    content = vdf_path.read_text(encoding="utf-8")
    # Tenta encontrar a seção do CS2 (AppID 730) e extrair LaunchOptions
    # A estrutura é hierárquica, mas um regex simples pode funcionar se formos específicos
    # Procuramos por "730" e depois o primeiro "LaunchOptions" que vier
    match_730 = re.search(r'"730"\s*\{[^}]*"LaunchOptions"\s*"([^"]*)"', content, re.DOTALL)
    if match_730:
        return match_730.group(1)
    return ""

def set_launch_options(steam_path: Path, account: dict, options_str: str):
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    vdf_path = steam_path / "userdata" / account_id / "config" / "localconfig.vdf"
    if not vdf_path.exists(): return False
    
    content = vdf_path.read_text(encoding="utf-8")
    
    # Se já existe a chave LaunchOptions para o app 730
    if re.search(r'"730"\s*\{[^}]*"LaunchOptions"', content, re.DOTALL):
        # Substitui apenas dentro do bloco "730"
        def replace_launch(m):
            block = m.group(0)
            if '"LaunchOptions"' in block:
                return re.sub(r'("LaunchOptions"\s*)"([^"]*)"', rf'\1"{options_str}"', block)
            return block
        
        new_content = re.sub(r'"730"\s*\{[^}]*\}', replace_launch, content, flags=re.DOTALL)
    else:
        # Se não existe, precisamos inserir. Isso é mais complexo sem um parser VDF real.
        # Vamos tentar inserir logo após a abertura do bloco "730"
        new_content = re.sub(r'("730"\s*\{)', rf'\1\n\t\t\t\t\t"LaunchOptions"\t\t"{options_str}"', content)

    vdf_path.write_text(new_content, encoding="utf-8")
    return True

def analyze_launch_options(current_options: str):
    analysis = []
    current_list = current_options.split()
    
    for opt, data in CS2_LAUNCH_KNOWLEDGE.items():
        is_active = any(opt in current_list for current_list in [current_options.split()]) # Simplificado
        # Melhor checagem de presença
        is_active = opt in current_options
        
        analysis.append({
            "key": opt,
            "name": data["nome"],
            "active": is_active,
            "desc": data["descricao"],
            "vantagem": data["vantagem"],
            "risco": data["risco"],
            "recomenda": data["recomendacao"],
            "cat": data["categoria"]
        })
    return analysis