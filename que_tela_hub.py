import customtkinter as ctk
import subprocess
import threading
import ctypes
import sys
import os
import time
import logging
import shutil
from tkinter import filedialog
from pathlib import Path

# ==========================================
# SETUP DE DIRETÓRIO E LOGS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "que_tela_hub.log"

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8')])

sys.path.append(str(BASE_DIR / "scripts" / "games"))
try:
    import cs2_sync
except ImportError:
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
        self.geometry("1050x750")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.steam_running = False
        self.cs2_running = False
        self.rl_running = False
        self.routine_running = False
        self.active_log_watcher = None

        # ==================== MENU LATERAL ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

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

        monitor_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        monitor_frame.grid(row=7, column=0, padx=20, pady=20, sticky="s")
        
        ctk.CTkLabel(monitor_frame, text="STATUS DO SISTEMA", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.lbl_steam = ctk.CTkLabel(monitor_frame, text="⚪ Steam", font=ctk.CTkFont(size=12))
        self.lbl_steam.pack(anchor="w")
        self.lbl_cs2 = ctk.CTkLabel(monitor_frame, text="⚪ CS2", font=ctk.CTkFont(size=12))
        self.lbl_cs2.pack(anchor="w")
        self.lbl_rl = ctk.CTkLabel(monitor_frame, text="⚪ Rocket League", font=ctk.CTkFont(size=12))
        self.lbl_rl.pack(anchor="w")
        self.lbl_routine = ctk.CTkLabel(monitor_frame, text="🟢 Rotinas Livres", font=ctk.CTkFont(size=12))
        self.lbl_routine.pack(anchor="w", pady=(5,0))

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.content_container.grid_rowconfigure(1, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.view_frame = ctk.CTkFrame(self.content_container, corner_radius=10)
        self.view_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=220, font=ctk.CTkFont(family="Consolas", size=12))
        self.console_textbox.grid(row=1, column=0, sticky="nsew")
        
        self.console_textbox.tag_config("ERROR", foreground="#E74C3C")
        self.console_textbox.tag_config("WARNING", foreground="#F39C12")
        self.console_textbox.tag_config("INFO", foreground="#2ECC71")
        self.console_textbox.tag_config("DEBUG", foreground="#95A5A6")
        self.console_textbox.tag_config("BATCH", foreground="#3498DB")
        
        self.console_textbox.insert("0.0", "Que Tela UI Inicializada. Motor de cores ativo.\n", "INFO")
        self.console_textbox.configure(state="disabled")

        self.monitor_system_loop()
        self.show_steam_manager()

    # ==================== FUNÇÕES CORE E LOG WATCHER ====================
    def log_to_console(self, text, level="INFO"):
        prefix = f"[{level}] " if level not in ["BATCH"] else ""
        formatted_text = f"{prefix}{text}"
        
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", formatted_text + "\n", level)
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def clear_view(self):
        for widget in self.view_frame.winfo_children():
            widget.destroy()

    def monitor_system_loop(self):
        """Monitora processos com blindagem contra destruicao de widgets."""
        try:
            output = subprocess.check_output('tasklist', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).lower()
            self.steam_running = "steam.exe" in output
            self.cs2_running = "cs2.exe" in output
            self.rl_running = "rocketleague.exe" in output

            self.lbl_steam.configure(text="🔴 Steam Rodando" if self.steam_running else "🟢 Steam Fechada")
            self.lbl_cs2.configure(text="🔴 CS2 Rodando" if self.cs2_running else "⚪ CS2 Inativo")
            self.lbl_rl.configure(text="🔴 RL Rodando" if self.rl_running else "⚪ RL Inativo")
            self.lbl_routine.configure(text="🔴 Manutenção Ativa" if self.routine_running else "🟢 Rotinas Livres", text_color="red" if self.routine_running else "white")

            # Checa se o botao existe na tela antes de interagir (Isso previne o crash do Tkinter)
            if hasattr(self, 'btn_start_steam') and self.btn_start_steam.winfo_exists():
                if self.routine_running:
                    self.btn_start_steam.configure(state="disabled", text="Bloqueado (Rotina)")
                else:
                    self.btn_start_steam.configure(state="normal", text="Abrir Steam")
        
        except Exception as e:
            # Ignora erros visuais para nao matar o loop
            pass
        finally:
            self.after(3000, self.monitor_system_loop)

    def tail_log_file(self, log_path, seconds=15):
        def tail_task():
            self.routine_running = True
            time.sleep(1) 
            if not os.path.exists(log_path): 
                self.routine_running = False
                return
            
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(0, 2) 
                start_time = time.time()
                while time.time() - start_time < seconds:
                    line = f.readline()
                    if line:
                        self.log_to_console(line.strip(), "BATCH")
                        start_time = time.time()
                    else:
                        time.sleep(0.2)
            self.routine_running = False
            self.log_to_console("Tarefa concluída. Trava de segurança liberada.", "INFO")

        if self.active_log_watcher and self.active_log_watcher.is_alive(): return
        self.active_log_watcher = threading.Thread(target=tail_task, daemon=True)
        self.active_log_watcher.start()

    def run_elevated_script(self, script_name, target_log_file, args=[]):
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists(): return

        self.log_to_console(f"Solicitando permissão UAC para: {script_path.name}", "WARNING")
        args_str = f'/c "cd /d "{BASE_DIR}" & "{script_path}" {" ".join(args)}"'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", args_str, None, 0)
        
        if result > 32:
            self.tail_log_file(BASE_DIR / "logs" / target_log_file)
        else:
            self.log_to_console("Operacao cancelada no UAC.", "ERROR")

    # ==================== INTERFACE INTERATIVA (MODAL DE DIFF) ====================
    def open_analysis_modal(self, analysis_data, account, on_success=None):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Auditoria de Motor Gráfico: {account['PersonaName']}")
        modal.geometry("850x600")
        modal.transient(self)
        
        ctk.CTkLabel(modal, text="Selecione as configurações que deseja corrigir:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        scroll_frame = ctk.CTkScrollableFrame(modal)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkboxes = {}
        for item in analysis_data:
            color = "#2ECC71" if item['is_ok'] else "#E74C3C"
            status = "OK" if item['is_ok'] else "INADEQUADO"
            
            text = f"[{status}] {item['name']}\nAtual: {item['current']} | Recomendado: {item['ideal']}\nImpacto: {item['impact']}"
            
            var = ctk.StringVar(value="0" if item['is_ok'] else "1")
            cb = ctk.CTkCheckBox(scroll_frame, text=text, variable=var, onvalue="1", offvalue="0", text_color=color)
            cb.pack(anchor="w", pady=10, padx=10)
            checkboxes[item['key']] = (var, item['ideal'])
            
        def apply_selections():
            selections = {key: ideal for key, (var, ideal) in checkboxes.items() if var.get() == "1"}
            if not selections:
                modal.destroy()
                return
                
            force = hasattr(self, 'chk_force_gpu') and self.chk_force_gpu.winfo_exists() and self.chk_force_gpu.get() == 1
            cfg_dir = cs2_sync.apply_selective_cs2_video(cs2_sync.get_steam_path(), account, selections, force)
            
            if cfg_dir:
                if len(selections) == len(analysis_data):
                    commit_msg = "Otimizado: Template completo aplicado"
                else:
                    changed_names = [cs2_sync.CS2_KNOWLEDGE_BASE[k]["nome"] for k in selections.keys()]
                    short_summary = ", ".join(changed_names)
                    if len(short_summary) > 40: short_summary = short_summary[:37] + "..."
                    commit_msg = f"Ajuste Fino: {short_summary}"
                
                cs2_sync.sync_to_repo(cfg_dir, account['AccountName'], commit_msg=commit_msg)
                self.log_to_console(f"Otimizações aplicadas e versionadas: {commit_msg}", "INFO")
                
                # A CORREÇÃO: Força a interface a atualizar o Dropdown automaticamente!
                if on_success:
                    on_success()
                    
            modal.destroy()
            
        btn = ctk.CTkButton(modal, text="Aplicar Selecionados & Sincronizar", fg_color="#8E44AD", hover_color="#732D91", command=apply_selections)
        btn.pack(pady=20)

    # ==================== TELAS ====================
    def show_steam_manager(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Manager & Versioning", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        
        if not cs2_sync:
            ctk.CTkLabel(self.view_frame, text="Erro: Módulo cs2_sync.py não encontrado.", text_color="red").pack()
            return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc_names = [f"{acc['PersonaName']} ({acc['AccountName']})" for acc in accounts] if accounts else ["Nenhuma conta encontrada"]
        
        tabs = ctk.CTkTabview(self.view_frame)
        tabs.pack(fill="both", expand=True, padx=20, pady=10)
        
        tab_sessao = tabs.add("Sessões Steam")
        tab_video = tabs.add("Otimização Gráfica")
        tab_git = tabs.add("Backups & Git")

        # --- ABA 1: SESSÕES ---
        ctk.CTkLabel(tab_sessao, text=f"Auto-Login Atual: {cs2_sync.get_current_autologin()}", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.combo_accounts = ctk.CTkComboBox(tab_sessao, values=acc_names, width=300)
        self.combo_accounts.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        actions_frame = ctk.CTkFrame(tab_sessao, fg_color="transparent")
        actions_frame.grid(row=2, column=0, padx=5, pady=10, sticky="w")

        def kill_steam(): subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
        def start_steam(): 
            args = ["-tcp", "-clearbeta"] if self.chk_safe_mode.get() == 1 else []
            if steam_path: subprocess.Popen([str(steam_path / "Steam.exe")] + args)
        def inject_login():
            if not accounts: return
            if self.steam_running:
                self.log_to_console("Feche a Steam primeiro para injetar chaves no Registro!", "WARNING")
                return
            cs2_sync.set_autologin(accounts[acc_names.index(self.combo_accounts.get())]['AccountName'])
            self.show_steam_manager()

        ctk.CTkButton(actions_frame, text="Fechar Steam", width=120, fg_color="#C0392B", hover_color="#922B21", command=kill_steam).grid(row=0, column=0, padx=10)
        ctk.CTkButton(actions_frame, text="Injetar Conta", width=120, command=inject_login).grid(row=0, column=1, padx=10)
        self.btn_start_steam = ctk.CTkButton(actions_frame, text="Abrir Steam", width=120, fg_color="#27AE60", hover_color="#1E8449", command=start_steam)
        self.btn_start_steam.grid(row=0, column=2, padx=10)
        self.chk_safe_mode = ctk.CTkCheckBox(actions_frame, text="Modo Seguro")
        self.chk_safe_mode.grid(row=0, column=3, padx=15)

        # --- ABA 2: VÍDEO ---
        ctk.CTkLabel(tab_video, text="Motor de Análise da Source 2", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.chk_force_gpu = ctk.CTkCheckBox(tab_video, text="Forçar Atualização de WMI (Use se trocou a GPU)")
        self.chk_force_gpu.grid(row=1, column=0, padx=15, pady=5, sticky="w")

        def trigger_analysis():
            if not accounts: return
            if self.cs2_running:
                self.log_to_console("O CS2 está rodando. Feche o jogo para modificar a Engine.", "WARNING")
                return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            data = cs2_sync.analyze_cs2_video(steam_path, acc)
            self.open_analysis_modal(data, acc, on_success=load_history)

        ctk.CTkButton(tab_video, text="Abrir Analisador Visual (Diff)", fg_color="#F39C12", hover_color="#D68910", text_color="black", command=trigger_analysis).grid(row=2, column=0, padx=15, pady=15, sticky="w")

        # --- ABA 3: GIT & METADADOS ---
        hist_frame = ctk.CTkFrame(tab_git, fg_color="transparent")
        hist_frame.pack(fill="x", padx=10, pady=5)
        
        # Painel Rico de Metadados
        self.hist_details = ctk.CTkTextbox(tab_git, height=80, fg_color="#2C3E50", text_color="white")
        self.hist_details.pack(fill="x", padx=15, pady=(5, 15))
        self.hist_details.insert("0.0", "Carregue o historico para ver os detalhes do snapshot.")
        self.hist_details.configure(state="disabled")

        def on_commit_selected(choice):
            self.hist_details.configure(state="normal")
            self.hist_details.delete("0.0", "end")
            try:
                parts = choice.split(" | ")
                self.hist_details.insert("0.0", f"ID Snapshot: {parts[0]}\nData Local: {parts[1]}\nDetalhes: {parts[2]}")
            except:
                self.hist_details.insert("0.0", f"Detalhes do Snapshot:\n{choice}")
            self.hist_details.configure(state="disabled")

        self.combo_commits = ctk.CTkComboBox(hist_frame, values=["Histórico não carregado"], width=400, command=on_commit_selected)
        self.combo_commits.grid(row=0, column=0, padx=5, pady=5)

        def load_history():
            if not accounts: return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            history = cs2_sync.get_git_history(acc['AccountName'])
            if history:
                opts = [f"{h['hash']} | {h['date']} | {h['msg']}" for h in history]
                self.combo_commits.configure(values=opts)
                self.combo_commits.set(opts[0])
                on_commit_selected(opts[0])
                self.log_to_console(f"Histórico Git carregado: {len(history)} backups encontrados.", "INFO")
            else:
                self.log_to_console("Nenhum backup encontrado ou Git ausente.", "WARNING")

        ctk.CTkButton(hist_frame, text="Carregar Histórico", command=load_history).grid(row=0, column=1, padx=10)

        git_actions = ctk.CTkFrame(tab_git, fg_color="transparent")
        git_actions.pack(fill="x", padx=10, pady=0)

        def force_backup():
            if not accounts: return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            account_id = str(int(acc["SteamID"]) - 76561197960265728)
            cfg_dir = steam_path / "userdata" / account_id / "730" / "local" / "cfg"
            cs2_sync.sync_to_repo(cfg_dir, acc['AccountName'], commit_msg="Backup Manual de Segurança")
            load_history()

        def restore_selected():
            if not accounts or "Histórico" in self.combo_commits.get(): return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            commit_hash = self.combo_commits.get().split(" | ")[0]
            if cs2_sync.restore_from_commit(steam_path, acc, commit_hash):
                self.log_to_console(f"Rollback efetuado! Arquivos revertidos para o estado do ID {commit_hash}.", "INFO")

        def export_zip():
            if not accounts: return
            acc = accounts[acc_names.index(self.combo_accounts.get())]
            repo_path = cs2_sync.get_private_repo_path() / "cs2" / acc['AccountName']
            if not repo_path.exists(): return
            save_path = filedialog.asksaveasfilename(defaultextension=".zip", initialfile=f"cs2_configs_{acc['AccountName']}.zip", title="Salvar Backup")
            if save_path:
                shutil.make_archive(save_path.replace('.zip', ''), 'zip', repo_path)
                self.log_to_console(f"Exportado: {save_path}", "INFO")

        ctk.CTkButton(git_actions, text="1. Forçar Backup", command=force_backup).grid(row=0, column=0, padx=5)
        ctk.CTkButton(git_actions, text="2. Restaurar Versão (Rollback)", fg_color="#C0392B", hover_color="#922B21", command=restore_selected).grid(row=0, column=1, padx=5)
        ctk.CTkButton(git_actions, text="3. Exportar (ZIP)", fg_color="#27AE60", hover_color="#1E8449", command=export_zip).grid(row=0, column=2, padx=5)

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