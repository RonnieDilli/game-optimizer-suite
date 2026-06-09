import os
import re
import subprocess
import winreg
import shutil
import logging
import json
import wmi
import customtkinter as ctk
from pathlib import Path
import core_git

logger = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge" / "cs2_video.json"
LAUNCH_KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge" / "cs2_launch_options.json"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if data is not None else {}
    except: return {}

CS2_KNOWLEDGE_BASE = load_json(KNOWLEDGE_PATH)
CS2_LAUNCH_KNOWLEDGE = load_json(LAUNCH_KNOWLEDGE_PATH)

class LaunchOptionGenerator:
    def __init__(self, catalog_path):
        self.catalog = load_json(catalog_path)

    def process(self, current_options_string):
        """Tokenização inteligente baseada no catálogo."""
        # Divide tudo por espaços para analisar token a token
        raw_tokens = current_options_string.split()
        parsed_options = []

        i = 0
        while i < len(raw_tokens):
            token = raw_tokens[i]

            # Verifica se é um comando (começa com - ou +)
            if token.startswith(('-', '+')):
                info = self.catalog.get(token)

                # Se for um parâmetro, pega o próximo token como valor
                val = ""
                if info and info.get("tipo") == "param":
                    # O valor só é pego se o próximo token NÃO for um comando
                    if i + 1 < len(raw_tokens) and not raw_tokens[i+1].startswith(('-', '+')):
                        val = raw_tokens[i+1]
                        i += 1 # Pula o valor no loop

                parsed_options.append({
                        "cmd": token,
                    "val": val,
                    "is_known": bool(info),
                    "info": info or {}
                })
            else:
                # Caso o token seja um valor órfão (não deveria acontecer se bem parseado)
                # Adiciona como um comando "desconhecido" apenas para não sumir
                parsed_options.append({
                    "cmd": token,
                    "val": "",
                    "is_known": False,
                    "info": {}
            })
            i += 1
        return parsed_options

    def save(self, options_list):
        """options_list: Lista de dicionários {'cmd': '-freq', 'val': '144'}"""
        parts = []
        for o in options_list:
            if o['val']:
                parts.append(f"{o['cmd']} {o['val']}")
        else:
                parts.append(f"{o['cmd']}")
        return " ".join(parts).strip()

def create_manual_restore_point(steam_path: Path, account: dict):
    import datetime
    account_id = str(int(account["SteamID"]) - 76561197960265728)
    cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"

    # Define o caminho do backup
    backup_root = Path(__file__).resolve().parent.parent.parent / "backups"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = backup_root / f"cs2_{account['AccountName']}_{timestamp}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_to_copy = ["cs2_video.txt", "autoexec.cfg", "config.cfg"]
    for f in files_to_copy:
        src = cfg_dir / f
        if src.exists():
            shutil.copy2(src, dest_dir / f)

    return dest_dir

def sync_to_repo(cfg_dir: Path, account_name: str, commit_msg: str = "Backup Manual", launch_options: str = None, game_type: str = "cs2"):
    base_repo = core_git.get_private_repo_path()

    # Estrutura: repo/jogo/conta/...
    account_repo_dir = base_repo / game_type / account_name
    account_repo_dir.mkdir(parents=True, exist_ok=True)

    if game_type == "cs2":
        # Arquivos específicos de CS2
        for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
            src = cfg_dir / file_name
            if src.exists(): shutil.copy2(src, account_repo_dir / file_name)

        # Salva Launch Options separadamente
    if launch_options is not None:
        (account_repo_dir / "launch_options.txt").write_text(launch_options, encoding="utf-8")

    elif game_type == "rl":
        # Arquivos específicos de Rocket League
        if cfg_dir.exists():
            shutil.copy2(cfg_dir, account_repo_dir / "TASystemSettings.ini")

    core_git.commit_to_git(base_repo, f"{game_type.upper()}|{account_name}", commit_msg)

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

def get_hardware_context():
    """Lê informações do hardware."""
    import platform
    import psutil
    hw_context = {
        "threads": os.cpu_count(),
        "refresh_rate": 144,
        "os": platform.system() + " " + platform.release(),
        "ram": f"{round(psutil.virtual_memory().total / (1024**3))}GB"
    }
    try:
        c = wmi.WMI()
        monitors = c.Win32_VideoController()
        rates = [int(m.CurrentRefreshRate) for m in monitors if m.CurrentRefreshRate]
        if rates: hw_context["refresh_rate"] = max(rates)

        gpu = c.Win32_VideoController()[0].Name
        hw_context["gpu"] = gpu
    except:
        hw_context["gpu"] = "Desconhecido"

    return hw_context

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

def get_launch_options(steam_path: Path, account_id3: str):
    """Lê o localconfig.vdf da Steam para extrair as Launch Options atuais."""
    vdf_path = steam_path / "userdata" / account_id3 / "config" / "localconfig.vdf"
    if not vdf_path.exists(): return ""

    content = vdf_path.read_text(encoding="utf-8", errors="ignore")
    # Busca o bloco do App 730 e sua LaunchOption
    match = re.search(r'"730"\s*\{[^}]*"LaunchOptions"\s*"([^"]*)"', content, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else ""

def apply_launch_options(steam_path: Path, account_id3: str, new_options: str):
    """Injeta as novas opções no localconfig.vdf com segurança."""
    vdf_path = steam_path / "userdata" / account_id3 / "config" / "localconfig.vdf"
    if not vdf_path.exists(): return False

    content = vdf_path.read_text(encoding="utf-8", errors="ignore")

    # Se já existir a chave "LaunchOptions" dentro de "730"
    if re.search(r'("730"\s*\{[^}]*"LaunchOptions"\s*")([^"]*)(")', content, re.IGNORECASE | re.DOTALL):
        content = re.sub(r'("730"\s*\{[^}]*"LaunchOptions"\s*")([^"]*)(")', rf'\g<1>{new_options}\g<3>', content, flags=re.IGNORECASE | re.DOTALL)
    # Se a chave "730" existe mas sem "LaunchOptions"
    elif re.search(r'("730"\s*\{)', content, re.IGNORECASE):
        content = re.sub(r'("730"\s*\{)', rf'\g<1>\n\t\t\t\t\t\t"LaunchOptions"\t\t"{new_options}"', content, flags=re.IGNORECASE)

    vdf_path.write_text(content, encoding="utf-8")
    return True

def analyze_launch_options(current_options: str):
    """
    Função adaptadora para manter compatibilidade com testes e UI.
    """
    generator = LaunchOptionGenerator(LAUNCH_KNOWLEDGE_PATH)
    options = generator.process(current_options)

    analysis = []
    for opt in options:
        if opt["is_known"]:
            analysis.append({
                "key": opt["cmd"],
                "name": opt["info"].get("nome", "Desconhecido"),
            "active": True,
                "risco": opt["info"].get("risco", "Nenhum"),
                "recomenda": opt["info"].get("recomendacao", ""),
                "desc": opt["info"].get("descricao", ""),
                "cat": opt["info"].get("categoria", "Outros")
        })
    else:
            analysis.append({
                "key": opt["cmd"],
                "name": "Comando Avançado/Desconhecido",
                "active": True,
                "risco": "Desconhecido (Use com cautela)",
                "recomenda": "Remover se não souber o que faz",
                "desc": "Comando não catalogado. Inserido manualmente.",
                "cat": "Avançado"
            })
    return analysis

def update_launch_options_string(current_options: str, target_opt: str, new_value: str = None, remove: bool = False):
    """
    Agora utiliza o gerador para manter a consistência da estrutura.
    """
    generator = LaunchOptionGenerator(LAUNCH_KNOWLEDGE_PATH)
    options = generator.process(current_options)

    if remove:
        # Filtra mantendo apenas os comandos que não são o alvo
        options = [o for o in options if o["cmd"] != target_opt]
    else:
        found = False
        for o in options:
            if o["cmd"] == target_opt:
                o["val"] = new_value if new_value is not None else o["val"]
                found = True
                break
        if not found:
            options.append({"cmd": target_opt, "val": new_value if new_value is not None else ""})

    return generator.save(options)

