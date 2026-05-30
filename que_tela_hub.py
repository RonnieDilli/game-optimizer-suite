import customtkinter as ctk
import subprocess
import threading
import ctypes
import sys
import os
import time
import logging
from pathlib import Path

# ==========================================
# BLINDAGEM DE DIRETÓRIO E LOGS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "que_tela_hub.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

sys.path.append(str(BASE_DIR / "scripts" / "games"))
try:
    import cs2_sync
except ImportError as e:
    cs2_sync = None

# ==========================================
# CONFIGURAÇÃO VISUAL
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QueTelaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Que Tela - Game Optimization Hub")
        self.geometry("1000x750")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== MENU LATERAL ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="QUE TELA", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_steam_mgr = ctk.CTkButton(self.sidebar_frame, text="Steam Manager", command=self.show_steam_manager)
        self.btn_steam_mgr.grid(row=1, column=0, padx=20, pady=10)

        self.btn_hardware = ctk.CTkButton(self.sidebar_frame, text="Sistema & GPU", command=self.show_hardware)
        self.btn_hardware.grid(row=2, column=0, padx=20, pady=10)

        self.btn_steam = ctk.CTkButton(self.sidebar_frame, text="Steam Repair", command=self.show_steam)
        self.btn_steam.grid(row=3, column=0, padx=20, pady=10)

        self.btn_epic = ctk.CTkButton(self.sidebar_frame, text="Epic & Rocket League", command=self.show_epic_rl)
        self.btn_epic.grid(row=4, column=0, padx=20, pady=10)

        self.steam_status_lbl = ctk.CTkLabel(self.sidebar_frame, text="🟢 Monitorando...", text_color="gray", font=ctk.CTkFont(size=11))
        self.steam_status_lbl.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.content_container.grid_rowconfigure(1, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.view_frame = ctk.CTkFrame(self.content_container, corner_radius=10)
        self.view_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=1, column=0, sticky="nsew")
        self.console_textbox.insert("0.0", "Que Tela UI Inicializada. Aguardando comandos...\n")
        self.console_textbox.configure(state="disabled")

        self.steam_is_running = False
        self.active_log_watcher = None
        self.check_steam_status_loop()
        self.show_steam_manager()

    # ==================== FUNÇÕES CORE E LOG WATCHER ====================
    def log_to_console(self, text, level="INFO"):
        prefix = f"[{level}] " if level not in ["RAW", "BATCH"] else ""
        formatted_text = f"{prefix}{text}"
        
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", formatted_text + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def clear_view(self):
        for widget in self.view_frame.winfo_children():
            widget.destroy()

    def check_steam_status_loop(self):
        try:
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq Steam.exe"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.steam_is_running = "steam.exe" in output.lower()
        except:
            self.steam_is_running = False

        status_text = "🔴 Steam Aberta" if self.steam_is_running else "🟢 Steam Fechada"
        self.steam_status_lbl.configure(text=status_text)
        self.after(3000, self.check_steam_status_loop)

    def tail_log_file(self, log_path, seconds=15):
        """Ouve o arquivo de log gerado pelo .bat e joga na UI em tempo real."""
        def tail_task():
            time.sleep(1) # Aguarda o .bat criar o arquivo
            if not os.path.exists(log_path): return
            
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2) # Pula para o final (ler so novidades)
                start_time = time.time()
                self.log_to_console(f"--- Interceptando saida do modulo via {Path(log_path).name} ---", "INFO")
                
                while time.time() - start_time < seconds:
                    line = f.readline()
                    if line:
                        self.log_to_console(line.strip(), "BATCH")
                        start_time = time.time() # Reseta o timeout se teve atividade
                    else:
                        time.sleep(0.2)
                self.log_to_console("--- Leitura do modulo concluida ---", "INFO")

        if self.active_log_watcher and self.active_log_watcher.is_alive():
            return
        self.active_log_watcher = threading.Thread(target=tail_task, daemon=True)
        self.active_log_watcher.start()

    def run_elevated_script(self, script_name, target_log_file, args=[]):
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists(): return

        self.log_to_console(f"Solicitando UAC para: {script_path.name}", "WARNING")
        args_str = f'/c "cd /d "{BASE_DIR}" & "{script_path}" {" ".join(args)}"'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", args_str, None, 0)
        
        if result > 32:
            # UAC Aceito! Inicia o espião no arquivo de log do respectivo .bat
            log_path = BASE_DIR / "logs" / target_log_file
            self.tail_log_file(log_path)
        else:
            self.log_to_console("Operacao cancelada no UAC.", "ERROR")

    # ==================== TELAS ====================
    def show_steam_manager(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Manager", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        if not cs2_sync: return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc_names = [f"{acc['PersonaName']} ({acc['AccountName']})" for acc in accounts] if accounts else ["Nenhuma conta encontrada"]
        
        # --- BLOCO 1: Gestão de Sessões ---
        sess_frame = ctk.CTkFrame(self.view_frame)
        sess_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(sess_frame, text="1. Sessões (Auto-Login Atual: {})".format(cs2_sync.get_current_autologin()), font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.combo_accounts = ctk.CTkComboBox(sess_frame, values=acc_names, width=300)
        self.combo_accounts.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        actions_frame = ctk.CTkFrame(sess_frame, fg_color="transparent")
        actions_frame.grid(row=2, column=0, padx=5, pady=10, sticky="w")

        def kill_steam(): subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
        def start_steam(): 
            args = ["-tcp", "-clearbeta"] if self.chk_safe_mode.get() == 1 else []
            if steam_path: subprocess.Popen([str(steam_path / "Steam.exe")] + args)
        def inject_login():
            if not accounts: return
            if self.steam_is_running:
                self.log_to_console("Feche a Steam primeiro para injetar o login!", "WARNING")
                return
            idx = acc_names.index(self.combo_accounts.get())
            cs2_sync.set_autologin(accounts[idx]['AccountName'])
            self.show_steam_manager()

        ctk.CTkButton(actions_frame, text="Fechar Steam", width=120, fg_color="#C0392B", hover_color="#922B21", command=kill_steam).grid(row=0, column=0, padx=10)
        ctk.CTkButton(actions_frame, text="Injetar Conta", width=120, command=inject_login).grid(row=0, column=1, padx=10)
        ctk.CTkButton(actions_frame, text="Abrir Steam", width=120, fg_color="#27AE60", hover_color="#1E8449", command=start_steam).grid(row=0, column=2, padx=10)
        self.chk_safe_mode = ctk.CTkCheckBox(actions_frame, text="Modo Seguro")
        self.chk_safe_mode.grid(row=0, column=3, padx=15)

        # --- BLOCO 2: Conhecimento e Configs ---
        cfg_frame = ctk.CTkFrame(self.view_frame)
        cfg_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(cfg_frame, text="2. Motor de Otimização e Versionamento (CS2)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.chk_force_gpu = ctk.CTkCheckBox(cfg_frame, text="Forçar Atualização de WMI (Em caso de troca física de GPU)")
        self.chk_force_gpu.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        cfg_actions = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        cfg_actions.grid(row=2, column=0, padx=5, pady=10, sticky="w")

        def analyze_configs():
            if not accounts: return
            idx = acc_names.index(self.combo_accounts.get())
            acc = accounts[idx]
            
            self.log_to_console(f"\n================ AUDITORIA DA ENGINE: {acc['PersonaName']} ================", "RAW")
            report, has_changes = cs2_sync.analyze_cs2_video(steam_path, acc)
            self.log_to_console(report, "RAW")
            if has_changes:
                self.log_to_console("Veredito: Foram encontradas configuracoes subotimizadas. Recomendado aplicar o template.", "WARNING")
            else:
                self.log_to_console("Veredito: Configuracoes estao perfeitamente alinhadas com a base de conhecimento.", "INFO")

        def apply_template():
            if not accounts: return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            force = self.chk_force_gpu.get() == 1
            cfg_dir = cs2_sync.optimize_cs2_video(steam_path, acc, force_gpu_update=force)
            if cfg_dir:
                cs2_sync.sync_to_repo(cfg_dir, acc['AccountName'])
                self.log_to_console(f"Otimizacao de {acc['PersonaName']} finalizada e versionada.", "INFO")

        ctk.CTkButton(cfg_actions, text="Analisar Configurações (Diff)", fg_color="#F39C12", hover_color="#D68910", text_color="black", command=analyze_configs).grid(row=0, column=0, padx=10)
        ctk.CTkButton(cfg_actions, text="Aplicar Otimização & Sincronizar", fg_color="#8E44AD", hover_color="#732D91", command=apply_template).grid(row=0, column=1, padx=10)

    # As outras telas apenas chamam o UAC passando o nome do log correto para a UI espionar
    def show_hardware(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Limpeza de Shaders e SO", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        btn = ctk.CTkButton(self.view_frame, text="Limpar GPU Agora", command=lambda: self.run_elevated_script("hardware/gpu_os_cleanup.bat", "gpu_cleanup.log", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

    def show_steam(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Repair", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        btn = ctk.CTkButton(self.view_frame, text="Executar Reparo", command=lambda: self.run_elevated_script("games/steam_repair.bat", "steam_repair.log", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

    def show_epic_rl(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Rocket League & Epic", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        btn = ctk.CTkButton(self.view_frame, text="Otimizar RL", command=lambda: self.run_elevated_script("games/epic_rl_repair.bat", "epic_rl_repair.log", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

if __name__ == "__main__":
    app = QueTelaApp()
    app.mainloop()