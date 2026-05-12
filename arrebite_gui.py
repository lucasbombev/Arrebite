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
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#1f2937",
            foreground="#f9fafb",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ArrebiteGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arrebite")
        self.root.geometry("480x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#f8f9fa")

        self.center_window()

        self.modo_ativo = False
        self._build_ui()
        self._update_buttons()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self):
        self.root.update_idletasks()
        w = 480
        h = 480
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        root = self.root

        container = tk.Frame(root, bg="#f8f9fa", padx=32, pady=28)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Arrebite",
            font=("Segoe UI", 22, "bold"),
            fg="#111827",
            bg="#f8f9fa",
            anchor=tk.W,
        ).pack(fill=tk.X)

        tk.Label(
            container,
            text="Mantenha seu notebook acordado",
            font=("Segoe UI", 10),
            fg="#6b7280",
            bg="#f8f9fa",
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 24))

        status_card = tk.Frame(
            container,
            bg="#ffffff",
            highlightbackground="#e5e7eb",
            highlightthickness=1,
            padx=20,
            pady=18,
        )
        status_card.pack(fill=tk.X, pady=(0, 20))

        status_row = tk.Frame(status_card, bg="#ffffff")
        status_row.pack(fill=tk.X)

        self.led = tk.Canvas(
            status_row, width=14, height=14, bg="#ffffff", highlightthickness=0
        )
        self.led.pack(side=tk.LEFT, padx=(0, 10))
        self.led_dot = self.led.create_oval(1, 1, 13, 13, fill="#ef4444", outline="")

        self.status_label = tk.Label(
            status_row,
            text="Inativo",
            font=("Segoe UI", 12),
            fg="#6b7280",
            bg="#ffffff",
        )
        self.status_label.pack(side=tk.LEFT)

        btn_frame = tk.Frame(container, bg="#f8f9fa")
        btn_frame.pack(fill=tk.X, pady=(0, 18))

        self.btn_ativar = tk.Button(
            btn_frame,
            text="Ativar modo anti-sono",
            font=("Segoe UI", 11, "bold"),
            bg="#4f46e5",
            fg="white",
            activebackground="#4338ca",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=12,
            cursor="hand2",
            border=0,
            command=self.on_ativar,
        )
        self.btn_ativar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ToolTip(self.btn_ativar, "Desabilita suspensão automática e bloqueio de tela")

        self.btn_restaurar = tk.Button(
            btn_frame,
            text="Restaurar padrões",
            font=("Segoe UI", 11, "bold"),
            bg="#f59e0b",
            fg="white",
            activebackground="#d97706",
            activeforeground="white",
            relief=tk.FLAT,
            padx=16,
            pady=12,
            cursor="hand2",
            border=0,
            command=self.on_restaurar,
        )
        self.btn_restaurar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        ToolTip(self.btn_restaurar, "Restaura as configurações originais de energia")

        sep = tk.Frame(container, bg="#e5e7eb", height=1)
        sep.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            container,
            text="Log",
            font=("Segoe UI", 10, "bold"),
            fg="#374151",
            bg="#f8f9fa",
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 8))

        self.log_area = scrolledtext.ScrolledText(
            container,
            height=8,
            font=("Consolas", 10),
            bg="#1f2937",
            fg="#d1d5db",
            insertbackground="#f9fafb",
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=12,
            state=tk.DISABLED,
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        exit_frame = tk.Frame(container, bg="#f8f9fa")
        exit_frame.pack(fill=tk.X, pady=(14, 0))

        self.btn_sair = tk.Button(
            exit_frame,
            text="Sair",
            font=("Segoe UI", 10),
            bg="#f3f4f6",
            fg="#374151",
            activebackground="#e5e7eb",
            activeforeground="#111827",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
            border=0,
            command=self.on_close,
        )
        self.btn_sair.pack(side=tk.RIGHT)
        ToolTip(self.btn_sair, "Fecha o programa")

        self.log("Programa iniciado. Pronto para agir!")

    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def _update_buttons(self):
        if self.modo_ativo:
            self.btn_ativar.config(state=tk.DISABLED, bg="#9ca3af")
            self.btn_restaurar.config(state=tk.NORMAL, bg="#f59e0b")
            self.led.itemconfig(self.led_dot, fill="#22c55e")
            self.status_label.config(text="Ativo", fg="#16a34a")
        else:
            self.btn_ativar.config(state=tk.NORMAL, bg="#4f46e5")
            self.btn_restaurar.config(state=tk.DISABLED, bg="#9ca3af")
            self.led.itemconfig(self.led_dot, fill="#ef4444")
            self.status_label.config(text="Inativo", fg="#6b7280")

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
