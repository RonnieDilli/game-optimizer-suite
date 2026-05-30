import os
import re
import subprocess
import winreg
import shutil
import logging
import configparser
from pathlib import Path

logger = logging.getLogger(__name__)

CS2_KNOWLEDGE_BASE = {
    "AutoConfig": {
        "nome": "Auto-Configuração da Engine",
        "ideal": "0",
        "impacto": "Crítico. Se ativado (1 ou 2), a Source 2 ignora o seu arquivo e faz um benchmark oculto no boot, resetando suas configuracoes para os padroes da Valve."
    },
    "setting.r_low_latency": {
        "nome": "NVIDIA Reflex",
        "ideal": "2",
        "impacto": "Alto (Input Lag). O valor '2' (On+Boost) forca a GPU a manter os clocks no maximo, reduzindo a fila de renderizacao entre CPU e GPU para latencias submilisegundo."
    },
    "setting.cpu_level": {
        "nome": "Alocação de Threads (CPU)",
        "ideal": "3",
        "impacto": "Medio (Stuttering). Forca a engine a distribuir a carga fisica e de logica agressivamente em processadores com muitos nucleos."
    },
    "setting.gpu_level": {
        "nome": "Prioridade de Renderização (GPU)",
        "ideal": "3",
        "impacto": "Medio. Garante que a engine utilize o pipeline completo da sua placa de video, evitando quedas de uso (dormencia)."
    },
    "setting.gpu_mem_level": {
        "nome": "Alocação de VRAM",
        "ideal": "3",
        "impacto": "Alto (Texturas). Instrui o jogo a alocar o maior pool de memoria de video possivel, evitando engasgos ao carregar mapas."
    }
}

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

def get_current_autologin():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            val, _ = winreg.QueryValueEx(key, "AutoLoginUser")
            return val
    except Exception:
        return "Nenhuma"

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
        return True
    except Exception as e:
        logger.error(f"Falha ao atualizar registro: {e}")
        return False

def get_actual_gpu_ids():
    try:
        output = subprocess.check_output('wmic path win32_VideoController get PNPDeviceID', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        match = re.search(r"VEN_([0-9A-Fa-f]{4})&DEV_([0-9A-Fa-f]{4})", output)
        if match:
            return str(int(match.group(1), 16)), str(int(match.group(2), 16))
    except Exception:
        pass
    return None, None

def analyze_cs2_video(steam_path: Path, account: dict):
    """Devolve dados estruturados para a UI interativa."""
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    video_cfg_path = steam_path / "userdata" / account_id / "730" / "local" / "cfg" / "cs2_video.txt"
    old_content = video_cfg_path.read_text(encoding="utf-8") if video_cfg_path.exists() else ""
    
    analysis_data = []
    for key, data in CS2_KNOWLEDGE_BASE.items():
        old_match = re.search(fr'"{key}"\s*"(\d+)"', old_content)
        old_val = old_match.group(1) if old_match else "N/A"
        
        analysis_data.append({
            "key": key,
            "name": data["nome"],
            "current": old_val,
            "ideal": data["ideal"],
            "impact": data["impacto"],
            "is_ok": old_val == data["ideal"]
        })
    return analysis_data

def apply_selective_cs2_video(steam_path: Path, account: dict, selections: dict, force_gpu_update=False):
    """Aplica as otimizacoes apenas nas variaveis selecionadas pelo usuario."""
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
    video_cfg_path = cfg_dir / "cs2_video.txt"
    
    if not video_cfg_path.exists():
        logger.error("cs2_video.txt nao encontrado. Abra o jogo ao menos uma vez para cria-lo.")
        return None
        
    content = video_cfg_path.read_text(encoding="utf-8")
    
    for key, ideal_val in selections.items():
        if re.search(fr'"{key}"\s*"\d+"', content):
            content = re.sub(fr'("{key}"\s*)("\d+")', rf'\g<1>"{ideal_val}"', content)
        else:
            # Se a variavel nao existe, injeta antes do fechamento do arquivo
            content = content.replace('\n}', f'\n\t"{key}"\t\t"{ideal_val}"\n}}')

    real_vendor, real_device = get_actual_gpu_ids()
    if force_gpu_update and real_vendor and real_device:
        content = re.sub(r'("VendorID"\s*)("\d+")', rf'\g<1>"{real_vendor}"', content)
        content = re.sub(r'("DeviceID"\s*)("\d+")', rf'\g<1>"{real_device}"', content)

    video_cfg_path.write_text(content, encoding="utf-8")
    return cfg_dir

def get_private_repo_path():
    config_file = Path(__file__).resolve().parent.parent.parent / "local_config.ini"
    config = configparser.ConfigParser()
    if config_file.exists():
        config.read(config_file)
        if 'USER_DATA' in config and 'PrivateRepoPath' in config['USER_DATA']:
            return Path(config['USER_DATA']['PrivateRepoPath'])
    
    default_path = Path.home() / "Documents" / "CS2_Private_Configs"
    default_path.mkdir(parents=True, exist_ok=True)
    config['USER_DATA'] = {'PrivateRepoPath': str(default_path)}
    with open(config_file, 'w') as configfile: config.write(configfile)
    return default_path

def sync_to_repo(cfg_dir: Path, account_name: str):
    base_repo_path = get_private_repo_path()
    account_repo_dir = base_repo_path / "cs2" / account_name
    account_repo_dir.mkdir(parents=True, exist_ok=True)
    for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
        src = cfg_dir / file_name
        dst = account_repo_dir / file_name
        if src.exists(): shutil.copy2(src, dst)