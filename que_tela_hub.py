import customtkinter as ctk
import subprocess
import threading
import ctypes
import sys
import os
import logging
import argparse
from pathlib import Path

# ==========================================
# 1. BLINDAGEM DE DIRETÓRIO E ARGUMENTOS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

# Parser para saber em qual aba o App deve iniciar (útil para o restart do UAC)
parser = argparse.ArgumentParser()
parser.add_argument("--resume", type=str, default="cs2", help="Aba para abrir ao iniciar")
args, _ = parser.parse_known_args()

# ==========================================
# 2. SISTEMA DE LOGS VERBOSOS
# ==========================================
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

# Adiciona a pasta scripts/games ao PATH para o cs2_sync
sys.path.append(str(BASE_DIR / "scripts" / "games"))
try:
    import cs2_sync
except ImportError as e:
    cs2_sync = None
    logging.error(f"Falha ao importar cs2_sync.py: {e}")

# ==========================================
# 3. VERIFICADOR DE PRIVILÉGIOS (ON-DEMAND)
# ==========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ==========================================
# CONFIGURAÇÃO VISUAL (CustomTkinter)
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QueTelaApp(ctk.CTk):
    def __init__(self, start_tab):
        super().__init__()

        self.title("Que Tela - Game Optimization Hub")
        self.geometry("950x650")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== MENU LATERAL ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="QUE TELA", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_cs2 = ctk.CTkButton(self.sidebar_frame, text="CS2 Accounts", command=self.show_cs2)
        self.btn_cs2.grid(row=1, column=0, padx=20, pady=10)

        self.btn_hardware = ctk.CTkButton(self.sidebar_frame, text="Sistema & GPU", command=self.show_hardware)
        self.btn_hardware.grid(row=2, column=0, padx=20, pady=10)

        self.btn_steam = ctk.CTkButton(self.sidebar_frame, text="Steam Repair", command=self.show_steam)
        self.btn_steam.grid(row=3, column=0, padx=20, pady=10)

        self.btn_epic = ctk.CTkButton(self.sidebar_frame, text="Epic & Rocket League", command=self.show_epic_rl)
        self.btn_epic.grid(row=4, column=0, padx=20, pady=10)

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.content_container.grid_rowconfigure(1, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.view_frame = ctk.CTkFrame(self.content_container, corner_radius=10)
        self.view_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=1, column=0, sticky="nsew")
        
        status_admin = " (Modo Admin)" if is_admin() else ""
        self.console_textbox.insert("0.0", f"Console de Otimizacao Ativo{status_admin}.\n")
        self.console_textbox.configure(state="disabled")

        # Roteamento inicial baseado no argumento
        if start_tab == "hardware": self.show_hardware()
        elif start_tab == "steam": self.show_steam()
        elif start_tab == "epic": self.show_epic_rl()
        else: self.show_cs2()

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

    def request_admin_and_resume(self, tab_name):
        """Pede Admin via UAC e reinicia o App voltando para a aba atual."""
        if not is_admin():
            self.log_to_console("Esta acao requer privilegios de Administrador.", "WARNING")
            self.log_to_console("Solicitando elevacao ao Windows (UAC)...", "INFO")
            
            # Reinicia o App passando a aba atual como argumento para nao perder o fluxo
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}" --resume {tab_name}', None, 1)
            sys.exit()
        return True

    def run_script(self, script_name, args=[]):
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists():
            self.log_to_console(f"Arquivo nao encontrado: {script_path}", "ERROR")
            return

        def task():
            self.log_to_console(f"Iniciando execucao: {script_path.name}")
            try:
                process = subprocess.Popen(
                    [str(script_path)] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in process.stdout:
                    self.log_to_console(line.strip(), "DEBUG")
                self.log_to_console(f"Processo {script_path.name} finalizado com sucesso.", "INFO")
            except Exception as e:
                self.log_to_console(f"Falha na execucao: {e}", "ERROR")

        threading.Thread(target=task, daemon=True).start()

    # ==================== TELAS ====================
    def show_cs2(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="CS2 Account Sync", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Selecione uma conta para injetar configuracoes de desempenho e logar.", text_color="gray").pack(anchor="w", padx=20, pady=0)

        if not cs2_sync:
            ctk.CTkLabel(self.view_frame, text="Erro: Módulo cs2_sync.py não encontrado.", text_color="red").pack(padx=20, pady=20)
            return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc_names = [f"{acc['PersonaName']} ({acc['AccountName']})" for acc in accounts] if accounts else ["Nenhuma conta encontrada"]

        self.combo_accounts = ctk.CTkComboBox(self.view_frame, values=acc_names, width=300)
        self.combo_accounts.pack(anchor="w", padx=20, pady=15)

        def on_sync_click():
            if not accounts: return
            idx = acc_names.index(self.combo_accounts.get())
            acc = accounts[idx]
            
            self.log_to_console(f"Preparando sessao para a conta: {acc['AccountName']}", "INFO")
            subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            cs2_sync.set_autologin(acc['AccountName'])
            self.log_to_console("Chaves de Auto-Login atualizadas no Registro. (Acao não requer Admin)", "INFO")

        # Gerenciamento de contas nao requer Admin! Pode rodar livremente.
        btn = ctk.CTkButton(self.view_frame, text="Trocar Conta e Sincronizar", command=on_sync_click)
        btn.pack(anchor="e", padx=20, pady=20)

    def show_hardware(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Limpeza de Shaders e SO", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Esvazia caches do DirectX e OpenGL destrancando arquivos de GPU.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        def btn_action():
            if self.request_admin_and_resume("hardware"):
                self.run_script("hardware/gpu_os_cleanup.bat", ["--auto"])

        btn = ctk.CTkButton(self.view_frame, text="Limpar GPU Agora", command=btn_action)
        btn.pack(anchor="e", padx=20, pady=20)

    def show_steam(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Repair", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Limpeza de caches temporários da Steam e delegação de limpeza gráfica.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        def btn_action():
            if self.request_admin_and_resume("steam"):
                self.run_script("games/steam_repair.bat", ["--auto"])

        btn = ctk.CTkButton(self.view_frame, text="Executar Reparo", command=btn_action)
        btn.pack(anchor="e", padx=20, pady=20)

    def show_epic_rl(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Rocket League & Epic", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Limpa o Epic Online Services (EOS) e caches de textura do Rocket League.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        def btn_action():
            if self.request_admin_and_resume("epic"):
                self.run_script("games/epic_rl_repair.bat", ["--auto"])

        btn = ctk.CTkButton(self.view_frame, text="Otimizar RL", command=btn_action)
        btn.pack(anchor="e", padx=20, pady=20)

if __name__ == "__main__":
    app = QueTelaApp(start_tab=args.resume)
    app.mainloop()