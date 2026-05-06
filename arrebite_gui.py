#!/usr/bin/env python3
"""
arrebite_gui.py - Interface gráfica para o programa Arrebite.
Mantém o notebook acordado, evitando suspensão e bloqueio de tela.
Compatível com Linux e Windows.
Requer apenas tkinter (padrão do Python) e bibliotecas da stdlib.
"""

import os
import sys
import json
import platform
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


# =============================================================================
# NÚCLEO - LÓGICA ORIGINAL (adaptada para não usar print)
# =============================================================================

@dataclass
class SavedSettings:
    settings: Dict[str, Optional[str]] = field(default_factory=dict)

    SAVE_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".arrebite_saved.json"
    )

    def save(self) -> None:
        try:
            with open(self.SAVE_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
        except OSError:
            pass

    def load(self) -> bool:
        try:
            with open(self.SAVE_FILE, "r") as f:
                self.settings = json.load(f)
            return True
        except (OSError, json.JSONDecodeError):
            self.settings = {}
            return False

    def clear(self) -> None:
        self.settings = {}
        try:
            os.remove(self.SAVE_FILE)
        except OSError:
            pass

    def add(self, key: str, value: Optional[str]) -> None:
        if value is not None:
            self.settings[key] = value


saved = SavedSettings()


def detect_desktop() -> str:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if "gnome" in desktop or "unity" in desktop:
        return "gnome"
    if "kde" in desktop or "plasma" in desktop:
        return "kde"
    if "xfce" in desktop:
        return "xfce"
    return "generic"


def run_cmd(cmd: list, check: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            cmd, returncode=-1, stdout="", stderr="command not found"
        )
    except subprocess.CalledProcessError as e:
        return e


def get_gsetting(schema: str, key: str) -> Optional[str]:
    r = run_cmd(["gsettings", "get", schema, key])
    if r.returncode == 0:
        return r.stdout.strip().strip("'")
    return None


def set_gsetting(schema: str, key: str, value: str) -> bool:
    r = run_cmd(["gsettings", "set", schema, key, value])
    return r.returncode == 0


def has_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def disable_sleep_linux() -> str:
    methods = []
    if detect_desktop() == "gnome" and has_cmd("gsettings"):
        val = get_gsetting(
            "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout"
        )
        saved.add("gsettings_sleep_ac", val)
        set_gsetting(
            "org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "0"
        )
        val = get_gsetting(
            "org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-timeout"
        )
        saved.add("gsettings_sleep_bat", val)
        set_gsetting(
            "org.gnome.settings-daemon.plugins.power",
            "sleep-inactive-battery-timeout",
            "0",
        )
        methods.append("gsettings")
    if os.environ.get("DISPLAY") and has_cmd("xset"):
        saved.add("xset_s_off", "applied")
        run_cmd(["xset", "s", "off"])
        methods.append("xset")
    return f"Suspensão desabilitada ({', '.join(methods) or 'nenhum método'})"


def disable_sleep_windows() -> str:
    methods = []
    r = run_cmd(["powercfg", "/change", "standby-timeout-ac", "0"])
    if r.returncode == 0:
        saved.add("windows_standby_ac", "0")
        methods.append("standby-ac")
    r = run_cmd(["powercfg", "/change", "standby-timeout-dc", "0"])
    if r.returncode == 0:
        saved.add("windows_standby_dc", "0")
        methods.append("standby-dc")
    return f"Suspensão desabilitada ({', '.join(methods) or 'nenhum método'})"


def disable_screen_linux() -> str:
    methods = []
    if detect_desktop() == "gnome" and has_cmd("gsettings"):
        val = get_gsetting("org.gnome.desktop.screensaver", "lock-enabled")
        saved.add("gsettings_lock_enabled", val)
        set_gsetting("org.gnome.desktop.screensaver", "lock-enabled", "false")
        val = get_gsetting("org.gnome.desktop.session", "idle-delay")
        saved.add("gsettings_idle_delay", val)
        set_gsetting("org.gnome.desktop.session", "idle-delay", "0")
        val = get_gsetting(
            "org.gnome.desktop.screensaver", "idle-activation-enabled"
        )
        saved.add("gsettings_screensaver_idle", val)
        set_gsetting(
            "org.gnome.desktop.screensaver", "idle-activation-enabled", "false"
        )
        methods.append("gsettings")
    if os.environ.get("DISPLAY") and has_cmd("xset"):
        saved.add("xset_dpms", "disabled")
        run_cmd(["xset", "-dpms"])
        methods.append("xset-dpms")
    return f"Tela não apaga/bloqueia ({', '.join(methods) or 'nenhum método'})"


def disable_screen_windows() -> str:
    methods = []
    r = run_cmd(["powercfg", "/change", "monitor-timeout-ac", "0"])
    if r.returncode == 0:
        saved.add("windows_monitor_ac", "0")
        methods.append("monitor-ac")
    r = run_cmd(["powercfg", "/change", "monitor-timeout-dc", "0"])
    if r.returncode == 0:
        saved.add("windows_monitor_dc", "0")
        methods.append("monitor-dc")
    return f"Tela não apaga ({', '.join(methods) or 'nenhum método'})"


def restore_linux() -> str:
    methods = []
    if detect_desktop() == "gnome" and has_cmd("gsettings"):
        val = saved.settings.get("gsettings_sleep_ac")
        if val is not None:
            set_gsetting(
                "org.gnome.settings-daemon.plugins.power",
                "sleep-inactive-ac-timeout",
                val,
            )
            methods.append("sleep-ac")
        val = saved.settings.get("gsettings_sleep_bat")
        if val is not None:
            set_gsetting(
                "org.gnome.settings-daemon.plugins.power",
                "sleep-inactive-battery-timeout",
                val,
            )
            methods.append("sleep-bat")
        val = saved.settings.get("gsettings_lock_enabled")
        if val is not None:
            set_gsetting("org.gnome.desktop.screensaver", "lock-enabled", val)
            methods.append("lock")
        val = saved.settings.get("gsettings_idle_delay")
        if val is not None:
            set_gsetting("org.gnome.desktop.session", "idle-delay", val)
            methods.append("idle-delay")
        val = saved.settings.get("gsettings_screensaver_idle")
        if val is not None:
            set_gsetting(
                "org.gnome.desktop.screensaver", "idle-activation-enabled", val
            )
            methods.append("screensaver-idle")
    if os.environ.get("DISPLAY") and has_cmd("xset"):
        run_cmd(["xset", "s", "on"])
        run_cmd(["xset", "+dpms"])
        methods.append("xset")
    return f"Configurações restauradas ({', '.join(methods) or 'nenhum método'})"


def restore_windows() -> str:
    methods = []
    for key, default in [
        ("windows_standby_ac", "30"),
        ("windows_standby_dc", "15"),
        ("windows_hibernate_ac", "0"),
        ("windows_hibernate_dc", "0"),
        ("windows_monitor_ac", "10"),
        ("windows_monitor_dc", "5"),
    ]:
        val = saved.settings.get(key, default)
        if val is not None:
            setting_name = key.replace("windows_", "").replace("_", "-") + " " + val
            run_cmd(["powercfg", "/change", setting_name])
            methods.append(key.replace("windows_", ""))
    return f"Configurações restauradas ({', '.join(methods) or 'nenhum método'})"


def activate_mode() -> tuple:
    """Ativa modo anti-sono. Retorna (sucesso: bool, mensagens: list)."""
    system = platform.system()
    msgs = []
    try:
        if system == "Linux":
            msgs.append(disable_sleep_linux())
            msgs.append(disable_screen_linux())
        elif system == "Windows":
            msgs.append(disable_sleep_windows())
            msgs.append(disable_screen_windows())
        else:
            return False, [f"Sistema não suportado: {system}"]
        saved.save()
        msgs.insert(0, ">>> Modo ANTI-SONO ativado!")
        return True, msgs
    except Exception as e:
        return False, [f"Erro ao ativar modo: {e}"]


def restore_defaults() -> tuple:
    """Restaura configurações. Retorna (sucesso: bool, mensagens: list)."""
    system = platform.system()
    msgs = []
    try:
        if not saved.load() or not saved.settings:
            msgs.append("Nenhum backup anterior encontrado; restaurando com valores padrão.")
        if system == "Linux":
            msgs.append(restore_linux())
        elif system == "Windows":
            msgs.append(restore_windows())
        else:
            return False, [f"Sistema não suportado: {system}"]
        saved.clear()
        msgs.insert(0, ">>> Configurações restauradas!")
        return True, msgs
    except Exception as e:
        return False, [f"Erro ao restaurar: {e}"]


# =============================================================================
# INTERFACE GRÁFICA (tkinter)
# =============================================================================


class ToolTip:
    """Tooltip simples que aparece ao passar o mouse sobre um widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("sans-serif", 9),
        )
        label.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ArrebiteGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arrebite - Mantenha seu notebook acordado")
        self.root.geometry("520x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        self.center_window()

        self.modo_ativo = False
        self._build_ui()
        self._update_buttons()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self):
        self.root.update_idletasks()
        w = 520
        h = 400
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        root = self.root

        # ---- Frame principal ----
        main = tk.Frame(root, bg="#f0f0f0", padx=20, pady=15)
        main.pack(fill=tk.BOTH, expand=True)

        # ---- Título decorativo ----
        title_frame = tk.Frame(main, bg="#f0f0f0")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(
            title_frame,
            text="⚡ Arrebite",
            font=("sans-serif", 18, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0",
        ).pack(side=tk.LEFT)
        tk.Label(
            title_frame,
            text="mantenha seu notebook acordado",
            font=("sans-serif", 9),
            fg="#7f8c8d",
            bg="#f0f0f0",
        ).pack(side=tk.LEFT, padx=(8, 0), pady=(6, 0))

        # ---- Indicador LED + Status ----
        status_frame = tk.Frame(main, bg="#f0f0f0")
        status_frame.pack(fill=tk.X, pady=(0, 12))

        self.led = tk.Canvas(status_frame, width=16, height=16, bg="#f0f0f0", highlightthickness=0)
        self.led.pack(side=tk.LEFT, padx=(0, 6))
        self.led_dot = self.led.create_oval(2, 2, 14, 14, fill="#e74c3c", outline="")

        self.status_label = tk.Label(
            status_frame,
            text="Modo inativo",
            font=("sans-serif", 10, "italic"),
            fg="#7f8c8d",
            bg="#f0f0f0",
        )
        self.status_label.pack(side=tk.LEFT)

        # ---- Botões principais ----
        btn_frame = tk.Frame(main, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.btn_ativar = tk.Button(
            btn_frame,
            text="🛌 ATIVAR MODO ANTI-SONO",
            font=("sans-serif", 11, "bold"),
            bg="#27ae60",
            fg="white",
            activebackground="#2ecc71",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=12,
            cursor="hand2",
            border=0,
            command=self.on_ativar,
        )
        self.btn_ativar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ToolTip(self.btn_ativar, "Desabilita suspensão automática e bloqueio de tela")

        self.btn_restaurar = tk.Button(
            btn_frame,
            text="↩ RESTAURAR PADRÕES",
            font=("sans-serif", 11, "bold"),
            bg="#e67e22",
            fg="white",
            activebackground="#f39c12",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=12,
            cursor="hand2",
            border=0,
            command=self.on_restaurar,
        )
        self.btn_restaurar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        ToolTip(self.btn_restaurar, "Restaura as configurações originais de energia")

        # ---- Botão Sair ----
        sair_frame = tk.Frame(main, bg="#f0f0f0")
        sair_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_sair = tk.Button(
            sair_frame,
            text="Sair",
            font=("sans-serif", 10),
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=20,
            pady=6,
            cursor="hand2",
            border=0,
            command=self.on_close,
        )
        self.btn_sair.pack()
        ToolTip(self.btn_sair, "Fecha o programa (pergunta antes de restaurar)")

        # ---- Área de log ----
        log_label = tk.Label(
            main,
            text="📋 Log de eventos:",
            font=("sans-serif", 9, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0",
            anchor=tk.W,
        )
        log_label.pack(fill=tk.X)

        self.log_area = scrolledtext.ScrolledText(
            main,
            height=7,
            font=("Consolas", 9),
            bg="#1a1a2e",
            fg="#00ff88",
            insertbackground="white",
            relief=tk.SUNKEN,
            borderwidth=2,
            state=tk.DISABLED,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.log("Programa iniciado. Pronto para agir!")

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _update_buttons(self):
        if self.modo_ativo:
            self.btn_ativar.config(state=tk.DISABLED, bg="#95a5a6")
            self.btn_restaurar.config(state=tk.NORMAL, bg="#e67e22")
            self.led.itemconfig(self.led_dot, fill="#2ecc71")
            self.status_label.config(text="Modo ativo  💪", fg="#27ae60")
        else:
            self.btn_ativar.config(state=tk.NORMAL, bg="#27ae60")
            self.btn_restaurar.config(state=tk.DISABLED, bg="#95a5a6")
            self.led.itemconfig(self.led_dot, fill="#e74c3c")
            self.status_label.config(text="Modo inativo", fg="#7f8c8d")

    def on_ativar(self):
        success, msgs = activate_mode()
        for m in msgs:
            self.log(m)
        if success:
            self.modo_ativo = True
            self._update_buttons()
        else:
            self.log("Falha ao ativar modo anti-sono.")

    def on_restaurar(self):
        success, msgs = restore_defaults()
        for m in msgs:
            self.log(m)
        if success:
            self.modo_ativo = False
            self._update_buttons()
        else:
            self.log("Falha ao restaurar configurações.")

    def on_close(self):
        if self.modo_ativo:
            resp = messagebox.askyesno(
                "Restaurar configurações?",
                "O modo anti-sono está ativo.\nDeseja restaurar as configurações "
                "originais antes de sair?",
            )
            if resp:
                self.on_restaurar()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    try:
        app = ArrebiteGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao iniciar a interface:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
