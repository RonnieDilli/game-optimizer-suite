import customtkinter as ctk
import subprocess
import threading
import ctypes
import sys
import os
import logging
from pathlib import Path

# ==========================================
# 1. BLINDAGEM DE DIRETÓRIO E LOGS
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
    logging.error(f"Falha ao importar cs2_sync.py: {e}")

# ==========================================
# CONFIGURAÇÃO VISUAL
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QueTelaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Que Tela - Game Optimization Hub")
        self.geometry("1000x700")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== MENU LATERAL ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="QUE TELA", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_cs2 = ctk.CTkButton(self.sidebar_frame, text="CS2 Manager", command=self.show_cs2)
        self.btn_cs2.grid(row=1, column=0, padx=20, pady=10)

        self.btn_hardware = ctk.CTkButton(self.sidebar_frame, text="Sistema & GPU", command=self.show_hardware)
        self.btn_hardware.grid(row=2, column=0, padx=20, pady=10)

        self.btn_steam = ctk.CTkButton(self.sidebar_frame, text="Steam Repair", command=self.show_steam)
        self.btn_steam.grid(row=3, column=0, padx=20, pady=10)

        self.btn_epic = ctk.CTkButton(self.sidebar_frame, text="Epic & Rocket League", command=self.show_epic_rl)
        self.btn_epic.grid(row=4, column=0, padx=20, pady=10)

        # Status da Steam ao vivo
        self.steam_status_lbl = ctk.CTkLabel(self.sidebar_frame, text="🟢 Monitorando Steam...", text_color="gray", font=ctk.CTkFont(size=11))
        self.steam_status_lbl.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.content_container.grid_rowconfigure(1, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.view_frame = ctk.CTkFrame(self.content_container, corner_radius=10)
        self.view_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=220, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=1, column=0, sticky="nsew")
        self.console_textbox.insert("0.0", "Que Tela UI Inicializada. Ambiente seguro de Usuario.\n")
        self.console_textbox.configure(state="disabled")

        self.steam_is_running = False
        self.check_steam_status_loop()
        self.show_cs2()

    # ==================== FUNÇÕES CORE ====================
    def log_to_console(self, text, level="INFO"):
        formatted_text = f"[{level}] {text}"
        if level == "ERROR": logging.error(text)
        elif level == "WARNING": logging.warning(text)
        elif level == "DEBUG": logging.debug(text)
        else: logging.info(text)

        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", formatted_text + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def clear_view(self):
        for widget in self.view_frame.winfo_children():
            widget.destroy()

    def check_steam_status_loop(self):
        """Loop a cada 3 segundos para atualizar a UI caso a Steam seja aberta/fechada."""
        try:
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq Steam.exe"', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.steam_is_running = "steam.exe" in output.lower()
        except:
            self.steam_is_running = False

        status_text = "🔴 Steam Aberta" if self.steam_is_running else "🟢 Steam Fechada"
        self.steam_status_lbl.configure(text=status_text)
        self.after(3000, self.check_steam_status_loop)

    def run_elevated_script(self, script_name, args=[]):
        """Dispara o UAC e resolve o bug do System32 forcando o CD /D."""
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists():
            self.log_to_console(f"Arquivo nao encontrado: {script_path}", "ERROR")
            return

        self.log_to_console(f"Requisitando permissao de Administrador para o modulo: {script_path.name}", "WARNING")
        
        # O pulo do gato: Força o cmd a navegar para a pasta raiz antes de rodar o .bat
        args_str = f'/c "cd /d "{BASE_DIR}" & "{script_path}" {" ".join(args)}"'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", args_str, None, 0)
        
        if result > 32:
            self.log_to_console(f"Tarefa executada em background.", "INFO")
        else:
            self.log_to_console("Operacao cancelada no UAC.", "ERROR")

    # ==================== TELAS ====================
    def show_cs2(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="CS2 Manager", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        if not cs2_sync:
            ctk.CTkLabel(self.view_frame, text="Erro: cs2_sync.py não encontrado.", text_color="red").pack()
            return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc_names = [f"{acc['PersonaName']} ({acc['AccountName']})" for acc in accounts] if accounts else ["Nenhuma conta encontrada"]
        current_login = cs2_sync.get_current_autologin()

        # ================= SEÇÃO 1: GESTÃO DE SESSÕES =================
        sess_frame = ctk.CTkFrame(self.view_frame)
        sess_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(sess_frame, text="1. Gestão de Contas (Steam)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        ctk.CTkLabel(sess_frame, text=f"Auto-Login Atual: {current_login}", text_color="#F1C40F").grid(row=0, column=1, padx=15, pady=10, sticky="e")

        self.combo_accounts = ctk.CTkComboBox(sess_frame, values=acc_names, width=300)
        self.combo_accounts.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        actions_frame = ctk.CTkFrame(sess_frame, fg_color="transparent")
        actions_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        def kill_steam():
            self.log_to_console("Encerrando Steam...", "INFO")
            subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

        def inject_login():
            if not accounts: return
            if self.steam_is_running:
                self.log_to_console("A Steam precisa estar fechada para alterar o Registro!", "WARNING")
                return
            idx = acc_names.index(self.combo_accounts.get())
            acc = accounts[idx]
            cs2_sync.set_autologin(acc['AccountName'])
            self.show_cs2() # Recarrega a tela para atualizar o Label "Auto-Login Atual"

        def start_steam():
            if steam_path:
                self.log_to_console("Iniciando Steam...", "INFO")
                args = ["-tcp", "-clearbeta"] if self.chk_safe_mode.get() == 1 else []
                subprocess.Popen([str(steam_path / "Steam.exe")] + args)

        ctk.CTkButton(actions_frame, text="Fechar Steam", width=120, fg_color="#C0392B", hover_color="#922B21", command=kill_steam).grid(row=0, column=0, padx=10)
        ctk.CTkButton(actions_frame, text="Injetar Conta", width=120, command=inject_login).grid(row=0, column=1, padx=10)
        ctk.CTkButton(actions_frame, text="Abrir Steam", width=120, fg_color="#27AE60", hover_color="#1E8449", command=start_steam).grid(row=0, column=2, padx=10)
        
        self.chk_safe_mode = ctk.CTkCheckBox(actions_frame, text="Modo Seguro (-tcp -clearbeta)")
        self.chk_safe_mode.grid(row=0, column=3, padx=15)

        # ================= SEÇÃO 2: CONFIGURAÇÕES DE VÍDEO CS2 =================
        cfg_frame = ctk.CTkFrame(self.view_frame)
        cfg_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(cfg_frame, text="2. Otimização de Vídeo e Versionamento (Source 2)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.chk_force_gpu = ctk.CTkCheckBox(cfg_frame, text="Forçar Atualização de WMI (Use apenas se trocou a GPU do PC)")
        self.chk_force_gpu.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        def apply_template():
            if not accounts: return
            idx = acc_names.index(self.combo_accounts.get())
            acc = accounts[idx]
            
            # Chama a otimização rodando numa thread para não congelar a GUI
            def task():
                force = self.chk_force_gpu.get() == 1
                cfg_dir = cs2_sync.optimize_cs2_video(steam_path, acc, force_gpu_update=force)
                if cfg_dir:
                    cs2_sync.sync_to_repo(cfg_dir, acc['AccountName'])
            threading.Thread(target=task, daemon=True).start()

        ctk.CTkButton(cfg_frame, text="Injetar Template Competitivo & Sincronizar", fg_color="#8E44AD", hover_color="#732D91", command=apply_template).grid(row=2, column=0, padx=15, pady=15, sticky="w")

    def show_hardware(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Limpeza de Shaders e SO", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Requer elevacao (UAC) apenas no momento da limpeza.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        btn = ctk.CTkButton(self.view_frame, text="Limpar GPU Agora (Admin)", fg_color="#D35400", hover_color="#A04000",
                            command=lambda: self.run_elevated_script("hardware/gpu_os_cleanup.bat", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

    def show_steam(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Repair", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Requer elevacao (UAC) para reparar o SteamService e limpar a GPU.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        btn = ctk.CTkButton(self.view_frame, text="Executar Reparo (Admin)", fg_color="#D35400", hover_color="#A04000",
                            command=lambda: self.run_elevated_script("games/steam_repair.bat", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

    def show_epic_rl(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Rocket League & Epic", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Requer elevacao (UAC) para matar processos agressivos do EOS.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        btn = ctk.CTkButton(self.view_frame, text="Otimizar RL (Admin)", fg_color="#D35400", hover_color="#A04000",
                            command=lambda: self.run_elevated_script("games/epic_rl_repair.bat", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

if __name__ == "__main__":
    app = QueTelaApp()
    app.mainloop()