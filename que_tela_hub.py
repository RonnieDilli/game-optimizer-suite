import customtkinter as ctk
import subprocess
import threading
import ctypes
import sys
import os
import logging
from pathlib import Path

# ==========================================
# 1. BLINDAGEM DE DIRETÓRIO (Fix PATH)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

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

# Adiciona scripts/games ao PATH para o módulo cs2_sync
sys.path.append(str(BASE_DIR / "scripts" / "games"))
try:
    import cs2_sync
except ImportError as e:
    cs2_sync = None
    logging.error(f"Falha ao importar cs2_sync.py: {e}")

# ==========================================
# CONFIGURAÇÃO VISUAL (CustomTkinter)
# ==========================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QueTelaApp(ctk.CTk):
    def __init__(self):
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

        # A aba CS2 agora é a principal (Home)
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

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=200, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=1, column=0, sticky="nsew")
        self.console_textbox.insert("0.0", "Que Tela UI Inicializada. Ambiente de Usuario (Sem UAC Global).\n")
        self.console_textbox.configure(state="disabled")

        # Inicia na gestão de contas
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

    def is_process_running(self, process_name):
        """Verifica de forma leve se um processo (ex: Steam.exe) esta rodando."""
        try:
            # shell=True no Windows com FINDSTR é extremamente rápido
            output = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {process_name}"', shell=True, text=True)
            return process_name.lower() in output.lower()
        except:
            return False

    def run_elevated_script(self, script_name, args=[]):
        """Dispara o UAC nativo do Windows apenas para o script .bat solicitado."""
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists():
            self.log_to_console(f"Arquivo nao encontrado: {script_path}", "ERROR")
            return

        self.log_to_console(f"Requisitando permissao de Administrador para: {script_path.name}", "WARNING")
        
        # O 0 no final significa SW_HIDE (Oculta a janela preta do CMD)
        args_str = f'/c "{script_path}" {" ".join(args)}'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", args_str, None, 0)
        
        # Valores de retorno <= 32 indicam erro ou cancelamento no UAC
        if result > 32:
            self.log_to_console(f"Tarefa elevada aceita. Executando em background...", "INFO")
            self.log_to_console(f"Verifique o arquivo 'logs/{script_name.replace('.bat', '.log').split('/')[-1]}' para auditoria.", "DEBUG")
        else:
            self.log_to_console("Operacao cancelada no UAC ou falha na elevacao.", "ERROR")

    # ==================== TELAS ====================
    def show_cs2(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="CS2 Account Sync", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Gestao de sessoes da Steam. Ambiente seguro, nao requer elevacao.", text_color="gray").pack(anchor="w", padx=20, pady=0)

        if not cs2_sync:
            ctk.CTkLabel(self.view_frame, text="Erro: cs2_sync.py não encontrado.", text_color="red").pack()
            return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc_names = [f"{acc['PersonaName']} ({acc['AccountName']})" for acc in accounts] if accounts else ["Nenhuma conta encontrada"]

        # Dropdown de Contas
        self.combo_accounts = ctk.CTkComboBox(self.view_frame, values=acc_names, width=300)
        self.combo_accounts.pack(anchor="w", padx=20, pady=(20, 10))

        # Painel de Ações Segmentado
        actions_frame = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        actions_frame.pack(anchor="w", padx=20, pady=10, fill="x")

        # 1. Fechar Steam
        def kill_steam():
            self.log_to_console("Encerrando Steam...", "INFO")
            subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log_to_console("Steam fechada.", "DEBUG")

        btn_kill = ctk.CTkButton(actions_frame, text="1. Fechar Steam", width=140, fg_color="#C0392B", hover_color="#922B21", command=kill_steam)
        btn_kill.grid(row=0, column=0, padx=(0, 10))

        # 2. Injetar Login
        def inject_login():
            if not accounts: return
            idx = acc_names.index(self.combo_accounts.get())
            acc = accounts[idx]
            
            if self.is_process_running("Steam.exe"):
                self.log_to_console("AVISO: A Steam esta rodando! Clique em 'Fechar Steam' primeiro.", "WARNING")
                return

            self.log_to_console(f"Injetando chaves para: {acc['PersonaName']}", "INFO")
            cs2_sync.set_autologin(acc['AccountName'])
            # Aqui podemos adicionar a chamada futura para otimizar_cs2_video(acc)

        btn_inject = ctk.CTkButton(actions_frame, text="2. Injetar Conta", width=140, command=inject_login)
        btn_inject.grid(row=0, column=1, padx=10)

        # 3. Abrir Steam
        def start_steam():
            if steam_path:
                self.log_to_console("Iniciando Steam...", "INFO")
                # Usa Popen para nao travar o Python esperando a Steam fechar
                subprocess.Popen([str(steam_path / "Steam.exe"), "-tcp", "-clearbeta"])

        btn_start = ctk.CTkButton(actions_frame, text="3. Iniciar Steam", width=140, fg_color="#27AE60", hover_color="#1E8449", command=start_steam)
        btn_start.grid(row=0, column=2, padx=10)

        # Dica UX
        ctk.CTkLabel(self.view_frame, text="* Dica: Feche a Steam, injete a conta e inicie novamente.", text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=10)

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
        ctk.CTkLabel(self.view_frame, text="Requer elevacao (UAC) para rodar SteamService /repair e limpar GPU.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        btn = ctk.CTkButton(self.view_frame, text="Executar Reparo (Admin)", fg_color="#D35400", hover_color="#A04000",
                            command=lambda: self.run_elevated_script("games/steam_repair.bat", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

    def show_epic_rl(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Rocket League & Epic", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.view_frame, text="Requer elevacao (UAC) para matar processos e limpar GPU em sequencia.", text_color="gray").pack(anchor="w", padx=20, pady=0)
        
        btn = ctk.CTkButton(self.view_frame, text="Otimizar RL (Admin)", fg_color="#D35400", hover_color="#A04000",
                            command=lambda: self.run_elevated_script("games/epic_rl_repair.bat", ["--auto"]))
        btn.pack(anchor="e", padx=20, pady=20)

if __name__ == "__main__":
    app = QueTelaApp()
    app.mainloop()