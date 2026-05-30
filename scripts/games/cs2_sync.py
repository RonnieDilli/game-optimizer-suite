import os
import re
import subprocess
import winreg
import shutil
import logging
import configparser
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# [Base de Conhecimento, get_steam_path, get_current_autologin, parse_loginusers, set_autologin, get_actual_gpu_ids, analyze_cs2_video, apply_selective_cs2_video continuam iguais, vou omitir apenas para focar nas novidades de versionamento. MANTENHA-AS NO SEU CÓDIGO]

CS2_KNOWLEDGE_BASE = {
    "AutoConfig": {"nome": "Auto-Configuração da Engine", "ideal": "0", "impacto": "Critico. Previne resets da Source 2."},
    "setting.r_low_latency": {"nome": "NVIDIA Reflex", "ideal": "2", "impacto": "Alto. Reduz Input Lag (On+Boost)."},
    "setting.cpu_level": {"nome": "Alocação de Threads (CPU)", "ideal": "3", "impacto": "Medio. Melhora paralelismo."},
    "setting.gpu_level": {"nome": "Prioridade de Renderização (GPU)", "ideal": "3", "impacto": "Medio. Evita dormencia da placa."},
    "setting.gpu_mem_level": {"nome": "Alocação de VRAM", "ideal": "3", "impacto": "Alto. Previne engasgos de textura."}
}

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

# ==========================================
# MOTOR GIT (NOVO BACKEND DE VERSIONAMENTO)
# ==========================================
def commit_to_git(repo_dir: Path, account_name: str, message: str = "Backup"):
    """Inicializa o repositório se necessario e cria um commit com as alteracoes."""
    try:
        if not (repo_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info("Repositorio Git inicializado com sucesso.")
            
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if status.stdout.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_msg = f"[{account_name}] {message} - {ts}"
            subprocess.run(["git", "commit", "-m", full_msg], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info(f"Commit Git criado: {full_msg}")
            return True
        else:
            logger.info("Nenhuma alteracao detectada. O Git nao criou um novo commit (Backup ja esta na ultima versao).")
            return False
    except FileNotFoundError:
        logger.warning("Git nao encontrado no sistema. Versionamento ignorado (Apenas copia de arquivos realizada).")
    except Exception as e:
        logger.error(f"Erro no motor Git: {e}")
    return False

def sync_to_repo(cfg_dir: Path, account_name: str, commit_msg: str = "Auto-sync otimizacao"):
    base_repo_path = get_private_repo_path()
    account_repo_dir = base_repo_path / "cs2" / account_name
    account_repo_dir.mkdir(parents=True, exist_ok=True)
    
    for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
        src = cfg_dir / file_name
        dst = account_repo_dir / file_name
        if src.exists(): shutil.copy2(src, dst)
        
    # Chama o Git logo após copiar
    commit_to_git(base_repo_path, account_name, commit_msg)

def get_git_history(account_name: str):
    """Busca os ultimos 15 backups com delimitadores blindados."""
    repo_dir = get_private_repo_path()
    try:
        # Usamos |~| como delimitador para não conflitar com textos normais
        cmd = ["git", "log", "--pretty=format:%h|~|%cd|~|%s", "--date=short", "-n", "15"]
        output = subprocess.check_output(cmd, cwd=repo_dir, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        history = []
        for line in output.split("\n"):
            if line.strip() and f"[{account_name}]" in line:
                parts = line.split("|~|")
                if len(parts) >= 3:
                    # Remove a tag [AccountName] do titulo para deixar a UI mais limpa
                    msg = parts[2].replace(f"[{account_name}] ", "")
                    history.append({"hash": parts[0], "date": parts[1], "msg": msg})
        return history
    except Exception as e:
        logger.error(f"Erro ao buscar historico git: {e}")
        return []

def restore_from_commit(steam_path: Path, account: dict, commit_hash: str):
    """Viaja no tempo, copia os arquivos e REGISTRA o rollback no Git."""
    repo_dir = get_private_repo_path()
    acc_name = account["AccountName"]
    account_repo_dir = repo_dir / "cs2" / acc_name
    
    try:
        # 1. Extrai os arquivos do passado no repo local
        subprocess.run(["git", "checkout", commit_hash, "--", f"cs2/{acc_name}"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 2. Copia de volta para a Steam
        account_id = str(int(account["SteamID"]) - 76561197960265728)
        cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
        
        for file_name in ["cs2_video.txt", "autoexec.cfg", "config.cfg"]:
            src = account_repo_dir / file_name
            dst = cfg_dir / file_name
            if src.exists(): shutil.copy2(src, dst)
            
        # 3. A CORREÇÃO: Em vez de resetar, nós commitamos o Rollback!
        commit_to_git(repo_dir, acc_name, f"Rollback efetuado para o ID {commit_hash}")
        
        logger.info(f"SUCESSO: Configuracoes restauradas para a versao {commit_hash} na conta {acc_name}.")
        return True
    except Exception as e:
        logger.error(f"Erro ao restaurar backup: {e}")
        return False