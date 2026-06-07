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
try: import cs2_sync
except ImportError: cs2_sync = None
try: import rl_sync
except ImportError: rl_sync = None
try: import core_git
except ImportError: core_git = None

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
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="QUE TELA", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_steam_mgr = ctk.CTkButton(self.sidebar_frame, text="Steam & CS2", command=self.show_steam_manager)
        self.btn_steam_mgr.grid(row=1, column=0, padx=20, pady=10)

        self.btn_epic = ctk.CTkButton(self.sidebar_frame, text="Epic & Rocket League", command=self.show_epic_rl)
        self.btn_epic.grid(row=2, column=0, padx=20, pady=10)

        self.btn_backups = ctk.CTkButton(self.sidebar_frame, text="Central de Backups", fg_color="#8E44AD", hover_color="#732D91", command=self.show_backups)
        self.btn_backups.grid(row=3, column=0, padx=20, pady=20)

        self.btn_hardware = ctk.CTkButton(self.sidebar_frame, text="Limpeza de Sistema", command=self.show_hardware)
        self.btn_hardware.grid(row=4, column=0, padx=20, pady=10)

        self.btn_steam = ctk.CTkButton(self.sidebar_frame, text="Steam Repair (VAC)", command=self.show_steam)
        self.btn_steam.grid(row=5, column=0, padx=20, pady=10)

        monitor_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        monitor_frame.grid(row=8, column=0, padx=20, pady=20, sticky="s")
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

        self.console_textbox = ctk.CTkTextbox(self.content_container, height=180, font=ctk.CTkFont(family="Consolas", size=12))
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
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", f"{prefix}{text}\n", level)
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def clear_view(self):
        for widget in self.view_frame.winfo_children(): widget.destroy()

    def monitor_system_loop(self):
        try:
            output = subprocess.check_output('tasklist', shell=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW).lower()
            self.steam_running, self.cs2_running, self.rl_running = "steam.exe" in output, "cs2.exe" in output, "rocketleague.exe" in output
            self.lbl_steam.configure(text="🔴 Steam Rodando" if self.steam_running else "🟢 Steam Fechada")
            self.lbl_cs2.configure(text="🔴 CS2 Rodando" if self.cs2_running else "⚪ CS2 Inativo")
            self.lbl_rl.configure(text="🔴 RL Rodando" if self.rl_running else "⚪ RL Inativo")
            self.lbl_routine.configure(text="🔴 Manutenção Ativa" if self.routine_running else "🟢 Rotinas Livres", text_color="red" if self.routine_running else "white")
            if hasattr(self, 'btn_start_steam') and self.btn_start_steam.winfo_exists():
                self.btn_start_steam.configure(state="disabled", text="Bloqueado (Rotina)") if self.routine_running else self.btn_start_steam.configure(state="normal", text="Abrir Steam")
        except: pass
        finally: self.after(3000, self.monitor_system_loop)

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
                    else: time.sleep(0.2)
            self.routine_running = False
            self.log_to_console("Tarefa concluída. Trava de segurança liberada.", "INFO")
        if not (self.active_log_watcher and self.active_log_watcher.is_alive()):
            self.active_log_watcher = threading.Thread(target=tail_task, daemon=True)
            self.active_log_watcher.start()

    def run_elevated_script(self, script_name, target_log_file, args=[]):
        script_path = BASE_DIR / "scripts" / script_name
        if not script_path.exists(): return
        self.log_to_console(f"Solicitando permissão UAC para: {script_path.name}", "WARNING")
        args_str = f'/c "cd /d "{BASE_DIR}" & "{script_path}" {" ".join(args)}"'
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", args_str, None, 0)
        if result > 32: self.tail_log_file(BASE_DIR / "logs" / target_log_file)
        else: self.log_to_console("Operacao cancelada no UAC.", "ERROR")

    # ==================== INTERFACE INTERATIVA (MODAL DE DIFF) ====================
    def open_analysis_modal(self, analysis_data, account, is_cs2=True, on_success=None):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Auditoria de Engine: {account.get('PersonaName', 'Local')}")
        modal.geometry("850x600")
        modal.transient(self)
        
        ctk.CTkLabel(modal, text="Selecione as configurações que deseja corrigir:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        scroll_frame = ctk.CTkScrollableFrame(modal)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkboxes = {}
        for item in analysis_data:
            color, status = ("#2ECC71", "OK") if item['is_ok'] else ("#E74C3C", "INADEQUADO")
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
                
            # Mapeia De-Para
            changed_items = []
            for k in selections.keys():
                item_data = next((item for item in analysis_data if item["key"] == k), None)
                if item_data: changed_items.append(f"{item_data['name']} ({item_data['current']} -> {item_data['ideal']})")
            
            detalhes = "Alterado: " + ", ".join(changed_items)
            commit_msg = f"Otimização Completa || {detalhes}" if len(selections) == len(analysis_data) else f"Ajuste Fino Seletivo || {detalhes}"

            if is_cs2:
                force = hasattr(self, 'chk_force_gpu') and self.chk_force_gpu.winfo_exists() and self.chk_force_gpu.get() == 1
                cfg_dir = cs2_sync.apply_selective_cs2_video(cs2_sync.get_steam_path(), account, selections, force)
                if cfg_dir:
                    cs2_sync.sync_to_repo(cfg_dir, account['AccountName'], commit_msg=commit_msg)
                    self.log_to_console("Otimizações do CS2 aplicadas e versionadas com sucesso.", "INFO")
                    if on_success: on_success()
            else:
                if rl_sync and rl_sync.apply_selective_rl_video(selections):
                    rl_sync.sync_to_repo(commit_msg=commit_msg)
                    self.log_to_console("Otimizações do Rocket League aplicadas e versionadas com sucesso.", "INFO")
                    if on_success: on_success()
            modal.destroy()
            
        btn = ctk.CTkButton(modal, text="Aplicar Selecionados & Sincronizar", fg_color="#8E44AD", hover_color="#732D91", command=apply_selections)
        btn.pack(pady=20)

        # ==================== TELAS ====================
    def show_steam_manager(self):
        self.clear_view()
        
        # Header e Status
        header_frame = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Gestão de Contas Steam", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        current_user = cs2_sync.get_current_autologin() if cs2_sync else "N/A"
        badge = ctk.CTkFrame(header_frame, fg_color="#2980B9", corner_radius=15)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=f" Ativo: {current_user} ", font=ctk.CTkFont(size=12, weight="bold")).pack(padx=10, pady=2)

        if not cs2_sync:
            return

        steam_path = cs2_sync.get_steam_path()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        current_user = cs2_sync.get_current_autologin()
        acc = next((a for a in accounts if a['AccountName'] == current_user), None)

        # Seção Launch Options (Nova tela integrada)
        if acc:
            acc_id3 = str(int(acc["SteamID"]) - 76561197960265728)
            launch_opts = cs2_sync.get_launch_options(steam_path, acc_id3)
            hw = cs2_sync.get_hardware_context()

            opts_frame = ctk.CTkFrame(self.view_frame, fg_color="#1E1E1E")
            opts_frame.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(opts_frame, text=f"⚙️ Launch Options ({acc['PersonaName']})", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(opts_frame, text=launch_opts if launch_opts else "(vazio)", font=ctk.CTkFont(family="Consolas", size=11)).pack(anchor="w", padx=10)

            info_row = ctk.CTkFrame(opts_frame, fg_color="transparent")
            info_row.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(info_row, text=f"🖥️ PC: {hw['threads']} Cores | {hw['refresh_rate']}Hz", font=ctk.CTkFont(size=10)).pack(side="left")

            ctk.CTkButton(opts_frame, text="Editar Launch Options", height=28, command=lambda: self.open_launch_options_modal(acc, launch_opts)).pack(anchor="e", padx=10, pady=5)

        # Barra de Ações Rápidas (Steam Control)
        actions_bar = ctk.CTkFrame(self.view_frame, fg_color="#1A1A1A", height=50)
        actions_bar.pack(fill="x", padx=20, pady=10)

        def kill_steam():
            subprocess.run(["taskkill", "/F", "/IM", "Steam.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.log_to_console("Comando para encerrar Steam enviado.", "INFO")

        def start_steam():
            args = ["-tcp", "-clearbeta"] if self.chk_safe_mode.get() == 1 else []
            if steam_path:
                subprocess.Popen([str(steam_path / "Steam.exe")] + args)
                self.log_to_console(f"Iniciando Steam {'(Safe Mode)' if args else ''}...", "INFO")

        ctk.CTkButton(actions_bar, text="ENCERRAR STEAM", fg_color="#C0392B", hover_color="#E74C3C", width=140, font=ctk.CTkFont(weight="bold"), command=kill_steam).pack(side="left", padx=10, pady=10)
        self.btn_start_steam = ctk.CTkButton(actions_bar, text="ABRIR STEAM", fg_color="#27AE60", hover_color="#2ECC71", width=140, font=ctk.CTkFont(weight="bold"), command=start_steam)
        self.btn_start_steam.pack(side="left", padx=5, pady=10)

        self.chk_safe_mode = ctk.CTkCheckBox(actions_bar, text="Modo Seguro (TCP)", font=ctk.CTkFont(size=11))
        self.chk_safe_mode.pack(side="left", padx=15)

        # Seção de Auditoria CS2 (Compacta)
        audit_frame = ctk.CTkFrame(self.view_frame, border_width=1, border_color="#333333")
        audit_frame.pack(fill="x", padx=20, pady=10)

        def trigger_analysis():
            if self.cs2_running:
                self.log_to_console("Feche o CS2 para modificar a Engine.", "WARNING")
                return
            # Pega o usuário logado atualmente para analisar
            user_now = cs2_sync.get_current_autologin()
            acc = next((a for a in accounts if a['AccountName'] == user_now), None)
            if acc:
                data = cs2_sync.analyze_cs2_video(steam_path, acc)
                self.open_analysis_modal(data, acc, is_cs2=True)
            else:
                self.log_to_console("Não foi possível determinar a conta ativa para auditoria.", "ERROR")

        ctk.CTkLabel(audit_frame, text="Configurações de Vídeo (Engine Source 2)", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=15, pady=10)
        self.chk_force_gpu = ctk.CTkCheckBox(audit_frame, text="Forçar HW-ID", font=ctk.CTkFont(size=11))
        self.chk_force_gpu.pack(side="left", padx=10)
        ctk.CTkButton(audit_frame, text="Analisar CS2 Video", width=150, height=28, fg_color="#F39C12", text_color="black", command=trigger_analysis).pack(side="right", padx=15)

        # Galeria de Contas
        ctk.CTkLabel(self.view_frame, text="Selecione um Perfil para Injetar:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=25, pady=(10, 5))

        scroll_acc = ctk.CTkScrollableFrame(self.view_frame, height=320, fg_color="transparent")
        scroll_acc.pack(fill="both", expand=True, padx=20, pady=5)

        # Grid logic
        cols = 2
        for i, acc in enumerate(accounts):
            is_active = acc['AccountName'] == current_user
            card = ctk.CTkFrame(scroll_acc, fg_color="#2C3E50" if not is_active else "#34495E", border_width=2 if is_active else 0, border_color="#2980B9")
            card.grid(row=i//cols, column=i%cols, padx=10, pady=10, sticky="nsew")
            scroll_acc.grid_columnconfigure(i%cols, weight=1)

            info_f = ctk.CTkFrame(card, fg_color="transparent")
            info_f.pack(side="left", padx=15, pady=10, fill="x", expand=True)

            ctk.CTkLabel(info_f, text=acc['PersonaName'], font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info_f, text=f"Login: {acc['AccountName']}", font=ctk.CTkFont(size=12), text_color="#BDC3C7", anchor="w").pack(fill="x")

            def make_inject_cmd(username):
                return lambda: self.inject_and_sync(username, steam_path, accounts)

            btn_color = ("#34495E", "#34495E") if is_active else ("#2980B9", "#3498DB")
            btn_text = "CONTA ATIVA" if is_active else "LOGAR NESTA"

            btn_sel = ctk.CTkButton(card, text=btn_text, width=100, height=35,
                                   fg_color=btn_color[0], hover_color=btn_color[1],
                                   state="disabled" if is_active else "normal",
                                   command=make_inject_cmd(acc['AccountName']))
            btn_sel.pack(side="right", padx=15)

    def inject_and_sync(self, username, steam_path, accounts):
        if self.steam_running:
            self.log_to_console("Feche a Steam antes de trocar de conta!", "WARNING")
            return

        acc = next((a for a in accounts if a['AccountName'] == username), None)
        if not acc: return

        # 1. Troca o Autologin no Registro
        if cs2_sync.set_autologin(username):
            self.log_to_console(f"Perfil {username} injetado com sucesso.", "INFO")

            # 2. Verifica se houve mudanças na conta anterior (Backup Automático)
            if cs2_sync.auto_backup_if_changed(steam_path, acc):
                self.log_to_console(f"Backup de segurança atualizado para {username}.", "INFO")

            # Atualiza a UI
            self.show_steam_manager()
        else:
            self.log_to_console("Falha ao injetar conta no Registro do Windows.", "ERROR")


    def show_epic_rl(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Rocket League Optimizer", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))

        # Ativa o gatilho de Auto-Backup ao abrir a aba
        if rl_sync and rl_sync.auto_backup_if_changed():
            self.log_to_console("NOVA CONFIGURAÇÃO DETECTADA! Backup automático do Rocket League realizado.", "INFO")

        clean_frame = ctk.CTkFrame(self.view_frame)
        clean_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(clean_frame, text="1. Limpeza de Caches (Epic Online Services)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)
        ctk.CTkButton(clean_frame, text="Limpar EOS e Texturas RL", fg_color="#D35400", hover_color="#A04000",
                      command=lambda: self.run_elevated_script("games/epic_rl_repair.bat", "epic_rl_repair.log", ["--auto"])).pack(anchor="w", padx=15, pady=10)

        engine_frame = ctk.CTkFrame(self.view_frame)
        engine_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(engine_frame, text="2. Auditoria da Unreal Engine 3 (RL_VIDEO.JSON)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

        def trigger_rl_analysis():
            if not rl_sync: return
            if self.rl_running:
                self.log_to_console("Feche o Rocket League para modificar o TASystemSettings.ini.", "WARNING")
                return
            data = rl_sync.analyze_rl_video()
            if data: self.open_analysis_modal(data, {"PersonaName": "Rocket League (Local)", "AccountName": "local"}, is_cs2=False)
        ctk.CTkButton(engine_frame, text="Analisar Motor Gráfico (Diff)", fg_color="#8E44AD", hover_color="#732D91", command=trigger_rl_analysis).pack(anchor="w", padx=15, pady=10)
    def show_backups(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Central de Backups (Git)", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))

        # Filtros Superiores
        filters_frame = ctk.CTkFrame(self.view_frame)
        filters_frame.pack(fill="x", padx=20, pady=10)

        self.bck_game_var = ctk.StringVar(value="CS2")
        game_radios = ctk.CTkFrame(filters_frame, fg_color="transparent")
        game_radios.grid(row=0, column=0, padx=15, pady=15)
        ctk.CTkLabel(game_radios, text="Jogo:").pack(side="left", padx=5)

        def update_accounts():
            if self.bck_game_var.get() == "CS2":
                steam_path = cs2_sync.get_steam_path()
                accs = cs2_sync.parse_loginusers(steam_path) if cs2_sync and steam_path else []
                self.bck_accounts = [acc['AccountName'] for acc in accs] if accs else ["Nenhuma"]
            else:
                self.bck_accounts = ["local"] # RL tem perfil local
            self.bck_acc_combo.configure(values=self.bck_accounts)
            if self.bck_accounts: self.bck_acc_combo.set(self.bck_accounts[0])
            load_history()

        ctk.CTkRadioButton(game_radios, text="CS2", variable=self.bck_game_var, value="CS2", command=update_accounts).pack(side="left", padx=10)
        ctk.CTkRadioButton(game_radios, text="Rocket League", variable=self.bck_game_var, value="RL", command=update_accounts).pack(side="left", padx=10)

        self.bck_acc_combo = ctk.CTkComboBox(filters_frame, values=["Carregando..."], width=200, command=lambda _: load_history())
        self.bck_acc_combo.grid(row=0, column=1, padx=15, pady=15)

        # Histórico Git
        self.hist_details = ctk.CTkTextbox(self.view_frame, height=140, fg_color="#2C3E50", text_color="white", font=ctk.CTkFont(size=12))
        self.hist_details.pack(fill="x", padx=20, pady=(10, 15))

        def on_commit_selected(choice):
            self.hist_details.configure(state="normal")
            self.hist_details.delete("0.0", "end")
            try:
                parts = choice.split(" | ", 2)
                title, details = parts[2].split(" - 202")[0].split(" || ") if " || " in parts[2] else (parts[2].split(" - 202")[0], "")
                display = f"📌 ID Snapshot: {parts[0]}\n📅 Data: {parts[1]}\n🏷️ Resumo: {title}\n"
                if details:
                    display += "⚙️ Modificações:\n"
                    for item in details.replace("Alterado: ", "").split(", "): display += f"   └─ {item}\n"
                self.hist_details.insert("0.0", display)
            except: self.hist_details.insert("0.0", choice)
            self.hist_details.configure(state="disabled")

        self.combo_commits = ctk.CTkComboBox(self.view_frame, values=["Selecione o jogo acima..."], width=400, command=on_commit_selected)
        self.combo_commits.pack(anchor="w", padx=20, pady=5)

        def load_history():
            if not core_git: return
            tag = f"{self.bck_game_var.get()}|{self.bck_acc_combo.get()}"
            history = core_git.get_git_history(tag)
            if history:
                opts = [f"{h['hash']} | {h['date']} | {h['msg']}" for h in history]
                self.combo_commits.configure(values=opts)
                self.combo_commits.set(opts[0])
                on_commit_selected(opts[0])
            else:
                self.combo_commits.configure(values=["Nenhum backup encontrado."])
                self.combo_commits.set("Nenhum backup encontrado.")

        # Ações do Backup
        git_actions = ctk.CTkFrame(self.view_frame, fg_color="transparent")
        git_actions.pack(anchor="w", padx=15, pady=20)

        def force_backup():
            if self.bck_game_var.get() == "CS2" and cs2_sync:
                steam_path = cs2_sync.get_steam_path()
                accounts = cs2_sync.parse_loginusers(steam_path)
                acc = next((a for a in accounts if a['AccountName'] == self.bck_acc_combo.get()), None)
                if acc:
                    acc_id = str(int(acc["SteamID"]) - 76561197960265728)
                    cfg_dir = steam_path / "userdata" / acc_id / "730" / "local" / "cfg"
                    # Novo: captura também as launch options
                    launch_opts = cs2_sync.get_launch_options(steam_path, acc_id)
                    cs2_sync.sync_to_repo(cfg_dir, acc['AccountName'], commit_msg="Backup Manual de Segurança", launch_options=launch_opts)
            elif self.bck_game_var.get() == "RL" and rl_sync:
                rl_sync.sync_to_repo(commit_msg="Backup Manual de Segurança (Rocket League)")
            load_history()

        def restore_selected():
            if "Nenhum" in self.combo_commits.get() or not core_git: return
            commit_hash = self.combo_commits.get().split(" | ")[0]
            tag = f"{self.bck_game_var.get()}|{self.bck_acc_combo.get()}"

            if self.bck_game_var.get() == "CS2" and cs2_sync:
                acc = next((a for a in cs2_sync.parse_loginusers(cs2_sync.get_steam_path()) if a['AccountName'] == self.bck_acc_combo.get()), None)
                dest_dir = cs2_sync.get_steam_path() / "userdata" / str(int(acc["SteamID"]) - 76561197960265728) / "730" / "local" / "cfg"
                subpath = f"cs2/{acc['AccountName']}"
            else:
                dest_dir = rl_sync.get_rl_config_path().parent
                subpath = "rl/local"

            if core_git.restore_from_commit(commit_hash, subpath, dest_dir, tag):
                self.log_to_console(f"Rollback efetuado para o ID {commit_hash}.", "INFO")
                load_history()

                ctk.CTkButton(git_actions, text="1. Forçar Backup", command=force_backup).pack(side="left", padx=5)
        ctk.CTkButton(git_actions, text="2. Restaurar Versão", fg_color="#C0392B", hover_color="#922B21", command=restore_selected).pack(side="left", padx=5)
        update_accounts()

    def show_launch_options(self):
        self.clear_view()
        if not cs2_sync: return


        steam_path = cs2_sync.get_steam_path()
        current_user = cs2_sync.get_current_autologin()
        accounts = cs2_sync.parse_loginusers(steam_path) if steam_path else []
        acc = next((a for a in accounts if a['AccountName'] == current_user), None)

        if not acc:
            ctk.CTkLabel(self.view_frame, text="Nenhuma conta ativa detectada para CS2.", text_color="red").pack(pady=20)
            return




        acc_id3 = str(int(acc["SteamID"]) - 76561197960265728)
        current_opts = cs2_sync.get_launch_options(steam_path, acc_id3)
        self.open_launch_options_modal(acc, current_opts)

    def open_launch_options_modal(self, account, current_options):
        """Nova UI focada na gestão de riscos e Launch Options do CS2."""
        modal = ctk.CTkToplevel(self)
        modal.title(f"Launch Options Tuning: {account['PersonaName']}")
        modal.geometry("850x650")
        modal.transient(self)

        # Analise de Hardware Context
        hw_context = cs2_sync.get_hardware_context()

        ctk.CTkLabel(modal, text="Comandos de Inicialização (Steam)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(modal, text=f"Contexto do PC: {hw_context['threads']} Threads Lógicas | Monitor: {hw_context['refresh_rate']}Hz", text_color="#3498DB").pack(pady=(0, 15))

        # Input direto
        entry_var = ctk.StringVar(value=current_options)
        entry = ctk.CTkEntry(modal, textvariable=entry_var, width=700, font=ctk.CTkFont(family="Consolas", size=14))
        entry.pack(pady=10)

        # Scroll de Sugestões Baseado no Tesauro
        scroll_frame = ctk.CTkScrollableFrame(modal)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        tesauro = cs2_sync.CS2_LAUNCH_KNOWLEDGE

        def toggle_command(cmd_string):
            """Adiciona ou remove o comando da barra de texto de forma inteligente."""
            current = entry_var.get().split()
            base_cmd = cmd_string.split()[0] # Pega só o -freq, tirando o 240
            # Remove se existir
            current = [c for c in current if not c.startswith(base_cmd)]
            # Se a string original não estava no input, significa que o usuário quer ativar
            if base_cmd not in entry_var.get():
                current.append(cmd_string)
            entry_var.set(" ".join(current))

        for cmd, data in tesauro.items():
            # Regra de recomendação baseada no Hardware
            sugestao = cmd
            if data.get("depende_hardware") == "MonitorRefreshRate":
                sugestao = f"{cmd} {hw_context['refresh_rate']}"
            elif data.get("depende_hardware") == "CPULogicalCores":
                sugestao = f"{cmd} {hw_context['threads']}"

            is_active = cmd in current_options

            # Badges Visuais
            if "Queda" in str(data['risco']): badge_color = "#E74C3C" # Vermelho
            elif "Estabilidade" in str(data['risco']): badge_color = "#F39C12" # Laranja
            else: badge_color = "#2ECC71" # Verde

            card = ctk.CTkFrame(scroll_frame, fg_color="#2C3E50" if not is_active else "#34495E")
            card.pack(fill="x", pady=5, padx=5)

            header_frame = ctk.CTkFrame(card, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(header_frame, text=sugestao, font=ctk.CTkFont(weight="bold", size=14)).pack(side="left")
            ctk.CTkLabel(header_frame, text=f" Risco: {data['risco']} ", fg_color=badge_color, corner_radius=5, text_color="black").pack(side="right", padx=10)

            ctk.CTkLabel(card, text=data['descricao'], wraplength=700, justify="left", text_color="gray").pack(anchor="w", padx=10, pady=(0, 10))
            ctk.CTkButton(card, text="Adicionar / Remover", width=120, command=lambda c=sugestao: toggle_command(c)).pack(anchor="e", padx=10, pady=(0, 10))

        def save_options():
            acc_id3 = str(int(account["SteamID"]) - 76561197960265728)
            new_opts = entry_var.get()
            if cs2_sync.apply_launch_options(cs2_sync.get_steam_path(), acc_id3, new_opts):
                # Inclui a mudanca no historico Git
                if core_git:
                    core_git.commit_to_git(core_git.get_private_repo_path(), f"CS2|{account['AccountName']}|{account['PersonaName']}|{account['SteamID']}", f"Launch Options Alteradas: {new_opts}")
                self.log_to_console(f"Launch Options salvas e versionadas: {new_opts}", "INFO")
                modal.destroy()

        ctk.CTkButton(modal, text="Salvar na Steam & Versionar no Git", fg_color="#8E44AD", hover_color="#732D91", command=save_options).pack(pady=20)
    def show_hardware(self):

        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Limpeza de Shaders e SO", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkButton(self.view_frame, text="Limpar GPU Agora", command=lambda: self.run_elevated_script("hardware/gpu_os_cleanup.bat", "gpu_cleanup.log", ["--auto"])).pack(anchor="e", padx=20, pady=20)

    def show_steam(self):
        self.clear_view()
        ctk.CTkLabel(self.view_frame, text="Steam Repair", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkButton(self.view_frame, text="Executar Reparo", command=lambda: self.run_elevated_script("games/steam_repair.bat", "steam_repair.log", ["--auto"])).pack(anchor="e", padx=20, pady=20)

if __name__ == "__main__":
    app = QueTelaApp()
    app.mainloop()