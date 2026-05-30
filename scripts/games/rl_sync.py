import os
import re
import subprocess
import shutil
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Carrega a Antologia do Rocket League
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
        docs_path = os.path.expandvars(docs_path)
        return Path(docs_path) / "My Games" / "Rocket League" / "TAGame" / "Config" / "TASystemSettings.ini"
    except Exception as e:
        logger.error(f"Caminho do Rocket League nao encontrado: {e}")
        return None

def analyze_rl_video():
    cfg_path = get_rl_config_path()
    if not cfg_path or not cfg_path.exists(): return []
    
    content = cfg_path.read_text(encoding="utf-8")
    analysis_data = []
    
    for key, data in RL_KNOWLEDGE_BASE.items():
        # Busca padrao Chave=Valor
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
            # Insere no final se não achar
            content += f"\n{key}={ideal_val}"
            
    cfg_path.write_text(content, encoding="utf-8")
    return True

# Reaproveitaremos o utilitario de Git que estara centralizado depois, 
# mas por enquanto usamos funcoes locais para isolamento