import os
import subprocess
import configparser
import logging
import shutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def get_private_repo_path():
    config_file = Path(__file__).resolve().parent.parent.parent / "local_config.ini"
    config = configparser.ConfigParser()
    if config_file.exists():
        config.read(config_file)
        if 'USER_DATA' in config and 'PrivateRepoPath' in config['USER_DATA']:
            return Path(config['USER_DATA']['PrivateRepoPath'])
    
    # Novo repositório unificado para todos os jogos
    default_path = Path.home() / "Documents" / "QueTela_Configs"
    default_path.mkdir(parents=True, exist_ok=True)
    config['USER_DATA'] = {'PrivateRepoPath': str(default_path)}
    with open(config_file, 'w') as configfile: 
        config.write(configfile)
    return default_path

def commit_to_git(repo_dir: Path, tag: str, message: str):
    try:
        if not (repo_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if status.stdout.strip():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_msg = f"[{tag}] {message} - {ts}"
            cmd = ["git", "-c", "i18n.commitEncoding=utf-8", "commit", "-m", full_msg]
            subprocess.run(cmd, cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        return False
    except Exception as e:
        logger.error(f"Erro no motor Git: {e}")
    return False

def get_git_history(tag: str):
    repo_dir = get_private_repo_path()
    try:
        cmd = ["git", "-c", "i18n.logOutputEncoding=utf-8", "log", "--pretty=format:%h|~|%cd|~|%s", "--date=short", "-n", "15"]
        output = subprocess.check_output(cmd, cwd=repo_dir, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW)
        history = []
        for line in output.split("\n"):
            if line.strip() and f"[{tag}]" in line:
                parts = line.split("|~|")
                if len(parts) >= 3:
                    msg = parts[2].replace(f"[{tag}] ", "")
                    history.append({"hash": parts[0], "date": parts[1], "msg": msg})
        return history
    except: 
        return []

def restore_from_commit(commit_hash: str, subpath: str, dest_dir: Path, tag: str):
    repo_dir = get_private_repo_path()
    try:
        subprocess.run(["git", "checkout", commit_hash, "--", subpath], cwd=repo_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        src_dir = repo_dir / subpath
        if src_dir.exists():
            for file_name in os.listdir(src_dir):
                src = src_dir / file_name
                if src.is_file(): 
                    shutil.copy2(src, dest_dir / file_name)
                    
        commit_to_git(repo_dir, tag, f"Rollback efetuado para o ID {commit_hash}")
        return True
    except Exception as e:
        logger.error(f"Erro no rollback: {e}")
        return False