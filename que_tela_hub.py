# Instale a dependencia antes de rodar: pip install customtkinter
import customtkinter as ctk
import subprocess
import threading
from pathlib import Path

# Configuracao global de tema (Estilo Gamer Dark)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class QueTelaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Que Tela - Game Optimization Hub")
        self.geometry("900x600")
        
        # Grid layout 1x2 (Menu lateral e Area de Conteudo)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== MENU LATERAL ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="QUE TELA", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_hardware = ctk.CTkButton(self.sidebar_frame, text="Sistema & GPU", command=self.show_hardware)
        self.btn_hardware.grid(row=1, column=0, padx=20, pady=10)

        self.btn_steam = ctk.CTkButton(self.sidebar_frame, text="Steam Repair", command=self.show_steam)
        self.btn_steam.grid(row=2, column=0, padx=20, pady=10)

        self.btn_epic_rl = ctk.CTkButton(self.sidebar_frame, text="Epic & Rocket League", command=self.show_epic_rl)
        self.btn_epic_rl.grid(row=3, column=0, padx=20, pady=10)

        self.btn_cs2 = ctk.CTkButton(self.sidebar_frame, text="CS2 Accounts", command=self.show_cs2)
        self.btn_cs2.grid(row=4, column=0, padx=20, pady=10)

        # ==================== AREA PRINCIPAL ====================
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Bem-vindo ao Que Tela", font=ctk.CTkFont(size=20, weight="bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.desc_label = ctk.CTkLabel(self.main_frame, text="Selecione um modulo no menu lateral para iniciar as otimizacoes.", text_color="gray")
        self.desc_label.grid(row=1, column=0, padx=20, pady=0, sticky="w")
        
        # Terminal Integrado (Log Output)
        self.console_textbox = ctk.CTkTextbox(self.main_frame, width=600, height=300, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.console_textbox.insert("0.0", "Console de Otimizacao Pronto...\n")
        self.console_textbox.configure(state="disabled")

        # Inicia na aba de Hardware
        self.show_hardware()

    def log_to_console(self, text):
        """Escreve no console da UI de forma thread-safe."""
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", text + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def run_script_in_thread(self, script_path, args=[]):
        """Roda arquivos .bat ou .py sem travar a interface grafica."""
        def task():
            self.log_to_console(f"\n> Executando: {script_path.name}")
            try:
                # O creationflags=subprocess.CREATE_NO_WINDOW esconde a tela preta do CMD
                process = subprocess.Popen(
                    [str(script_path)] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in process.stdout:
                    self.log_to_console(line.strip())
                self.log_to_console("> Processo Finalizado.")
            except Exception as e:
                self.log_to_console(f"[ERRO] {e}")

        threading.Thread(target=task, daemon=True).start()

    # ==================== TELAS E ACOES ====================
    def show_hardware(self):
        self.header_label.configure(text="Limpeza de Shaders e SO")
        self.desc_label.configure(text="Esvazia caches do DirectX e OpenGL destrancando arquivos de GPU.")
        
        btn_run = ctk.CTkButton(self.main_frame, text="Limpar GPU Agora", 
                                command=lambda: self.run_script_in_thread(Path("scripts/hardware/gpu_os_cleanup.bat"), ["--auto"]))
        btn_run.grid(row=1, column=0, padx=20, pady=30, sticky="e")

    def show_steam(self):
        self.header_label.configure(text="Steam Repair")
        self.desc_label.configure(text="Limpeza de caches e correcoes do erro de VAC.")
        # O botao chamaria a execucao do steam_repair.bat

    def show_epic_rl(self):
        self.header_label.configure(text="Rocket League & Epic")
        self.desc_label.configure(text="Destrava micro-stuttering limpando o EOS Overlay.")

    def show_cs2(self):
        self.header_label.configure(text="CS2 Account Sync")
        self.desc_label.configure(text="Otimizacao de video e backup no repositorio privado.")
        # A UI futuramente contera o Dropdown com as contas lidas do VDF aqui.

if __name__ == "__main__":
    app = QueTelaApp()
    app.mainloop()