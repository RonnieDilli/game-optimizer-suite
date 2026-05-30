import os
import re
import subprocess
import shutil
import logging
import json
from pathlib import Path
import core_git

logger = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent.parent / "knowledge" / "rl_video.json"
try:
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        RL_KNOWLEDGE_BASE = json.load(f)
except Exception as e:
    logger.error(f"Erro ao carregar antologia do RL: {e}")
    RL_KNOWLEDGE_BASE = {}

def get_rl_config_path():
    try:
        output = subprocess.check_output('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders" /v Personal', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        docs_path = re.search(r'REG_EXPAND_SZ\s+(.+)', output).group(1).strip()
        return Path(os.path.expandvars(docs_path)) / "My Games" / "Rocket League" / "TAGame" / "Config" / "TASystemSettings.ini"
    except: 
        return None

def analyze_rl_video():
    cfg_path = get_rl_config_path()
    if not cfg_path or not cfg_path.exists(): return []
    content = cfg_path.read_text(encoding="utf-8")
    analysis_data = []
    
    for key, data in RL_KNOWLEDGE_BASE.items():
        match = re.search(fr'^{key}=([A-Za-z0-9]+)', content, re.MULTILINE)
        old_val = match.group(1) if match else "N/A"
        analysis_data.append({
            "key": key, "name": data["nome"], "current": old_val,
            "ideal": data["ideal"], "impact": data["impacto"], "is_ok": old_val.lower() == data["ideal"].lower()
        })
    return analysis_data

def apply_selective_rl_video(selections: dict):
    cfg_path = get_rl_config_path()
    if not cfg_path or not cfg_path.exists(): return False
    content = cfg_path.read_text(encoding="utf-8")
    for key, ideal_val in selections.items():
        if re.search(fr'^{key}=.*', content, re.MULTILINE):
            content = re.sub(fr'^({key})=.*', rf'\1={ideal_val}', content, flags=re.MULTILINE)
        else:
            content += f"\n{key}={ideal_val}"
    cfg_path.write_text(content, encoding="utf-8")
    return cfg_path.parent

def sync_to_repo(commit_msg: str = "Backup Manual"):
    cfg_path = get_rl_config_path()
    if not cfg_path or not cfg_path.exists(): return False
    
    base_repo = core_git.get_private_repo_path()
    rl_repo_dir = base_repo / "rl" / "local"
    rl_repo_dir.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(cfg_path, rl_repo_dir / cfg_path.name)
    core_git.commit_to_git(base_repo, "RL|local", commit_msg)
    return True

def auto_backup_if_changed():
    cfg_path = get_rl_config_path()
    if not cfg_path or not cfg_path.exists(): return False
    
    base_repo = core_git.get_private_repo_path()
    rl_repo_dir = base_repo / "rl" / "local"
    if not (base_repo / ".git").exists(): return False
    
    shutil.copy2(cfg_path, rl_repo_dir / cfg_path.name)
    try:
        subprocess.run(["git", "add", "."], cwd=base_repo, creationflags=subprocess.CREATE_NO_WINDOW)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=base_repo, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if status.stdout.strip():
            core_git.commit_to_git(base_repo, "RL|local", "Auto-Sync || Alterações In-Game detectadas na UE3")
            return True
    except: pass
    return False