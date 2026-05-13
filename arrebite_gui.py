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

THEMES = {
    "light": {
        "bg": "#f8f9fa",
        "card_bg": "#ffffff",
        "card_border": "#e5e7eb",
        "title_fg": "#111827",
        "subtitle_fg": "#6b7280",
        "log_bg": "#1f2937",
        "log_fg": "#d1d5db",
        "log_insert": "#f9fafb",
        "log_header_fg": "#374151",
        "sep": "#e5e7eb",
        "btn_ativar_bg": "#4f46e5",
        "btn_ativar_active": "#4338ca",
        "btn_sair_bg": "#f3f4f6",
        "btn_sair_fg": "#374151",
        "btn_sair_active_bg": "#e5e7eb",
        "btn_sair_active_fg": "#111827",
        "led_off": "#ef4444",
        "led_on": "#22c55e",
        "status_inactive_fg": "#6b7280",
        "status_active_fg": "#16a34a",
    },
    "dark": {
        "bg": "#1e1e2e",
        "card_bg": "#2d2d44",
        "card_border": "#3d3d5c",
        "title_fg": "#e0e0e0",
        "subtitle_fg": "#a0a0b0",
        "log_bg": "#0d1117",
        "log_fg": "#c9d1d9",
        "log_insert": "#c9d1d9",
        "log_header_fg": "#c0c0d0",
        "sep": "#3d3d5c",
        "btn_ativar_bg": "#6366f1",
        "btn_ativar_active": "#5558e6",
        "btn_sair_bg": "#374151",
        "btn_sair_fg": "#d1d5db",
        "btn_sair_active_bg": "#4b5563",
        "btn_sair_active_fg": "#f9fafb",
        "led_off": "#ef4444",
        "led_on": "#22c55e",
        "status_inactive_fg": "#a0a0a0",
        "status_active_fg": "#4ade80",
    },
}


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
        self.log_visible = False
        self.dark_mode = False
        self.current_theme = THEMES["light"]
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
        T = self.current_theme

        self._container = tk.Frame(root, bg=T["bg"], padx=32, pady=28)
        self._container.pack(fill=tk.BOTH, expand=True)

        self._header_frame = tk.Frame(self._container, bg=T["bg"])
        self._header_frame.pack(fill=tk.X)

        self._title_label = tk.Label(
            self._header_frame,
            text="Arrebite",
            font=("Segoe UI", 22, "bold"),
            fg=T["title_fg"],
            bg=T["bg"],
            anchor=tk.W,
        )
        self._title_label.pack(side=tk.LEFT)

        self.btn_toggle_theme = tk.Button(
            self._header_frame,
            text="\u263e",
            font=("Segoe UI", 16),
            bg=T["bg"],
            fg=T["subtitle_fg"],
            relief=tk.FLAT,
            padx=4,
            pady=0,
            cursor="hand2",
            border=0,
            command=self._toggle_theme,
        )
        self.btn_toggle_theme.pack(side=tk.RIGHT)

        self._subtitle_label = tk.Label(
            self._container,
            text="Mantenha seu notebook acordado",
            font=("Segoe UI", 10),
            fg=T["subtitle_fg"],
            bg=T["bg"],
            anchor=tk.W,
        )
        self._subtitle_label.pack(fill=tk.X, pady=(0, 24))

        self._status_card = tk.Frame(
            self._container,
            bg=T["card_bg"],
            highlightbackground=T["card_border"],
            highlightthickness=1,
            padx=20,
            pady=18,
        )
        self._status_card.pack(fill=tk.X, pady=(0, 20))

        self._status_row = tk.Frame(self._status_card, bg=T["card_bg"])
        self._status_row.pack(fill=tk.X)

        self.led = tk.Canvas(
            self._status_row, width=14, height=14, bg=T["card_bg"], highlightthickness=0
        )
        self.led.pack(side=tk.LEFT, padx=(0, 10))
        self.led_dot = self.led.create_oval(1, 1, 13, 13, fill=T["led_off"], outline="")

        self.status_label = tk.Label(
            self._status_row,
            text="Inativo",
            font=("Segoe UI", 12),
            fg=T["status_inactive_fg"],
            bg=T["card_bg"],
        )
        self.status_label.pack(side=tk.LEFT)

        self._btn_frame = tk.Frame(self._container, bg=T["bg"])
        self._btn_frame.pack(fill=tk.X, pady=(0, 18))

        self.btn_ativar = tk.Button(
            self._btn_frame,
            text="Ativar modo anti-sono",
            font=("Segoe UI", 11, "bold"),
            bg=T["btn_ativar_bg"],
            fg="white",
            activebackground=T["btn_ativar_active"],
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
            self._btn_frame,
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

        self._sep = tk.Frame(self._container, bg=T["sep"], height=1)
        self._sep.pack(fill=tk.X, pady=(0, 10))

        self._log_header = tk.Frame(self._container, bg=T["bg"])
        self._log_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            self._log_header,
            text="Log",
            font=("Segoe UI", 10, "bold"),
            fg=T["log_header_fg"],
            bg=T["bg"],
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        self.btn_toggle_log = tk.Button(
            self._log_header,
            text="\u25b6",
            font=("Segoe UI", 8),
            bg=T["bg"],
            fg=T["log_header_fg"],
            relief=tk.FLAT,
            padx=4,
            pady=0,
            cursor="hand2",
            border=0,
            command=self._toggle_log,
        )
        self.btn_toggle_log.pack(side=tk.RIGHT)

        self.log_area = scrolledtext.ScrolledText(
            self._container,
            height=8,
            font=("Consolas", 10),
            bg=T["log_bg"],
            fg=T["log_fg"],
            insertbackground=T["log_insert"],
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=12,
            state=tk.DISABLED,
        )

        self._exit_frame = tk.Frame(self._container, bg=T["bg"])
        self._exit_frame.pack(fill=tk.X, pady=(14, 0))

        self.btn_sair = tk.Button(
            self._exit_frame,
            text="Sair",
            font=("Segoe UI", 10),
            bg=T["btn_sair_bg"],
            fg=T["btn_sair_fg"],
            activebackground=T["btn_sair_active_bg"],
            activeforeground=T["btn_sair_active_fg"],
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
        T = self.current_theme
        if self.modo_ativo:
            self.btn_ativar.config(state=tk.DISABLED, bg="#9ca3af")
            self.btn_restaurar.config(state=tk.NORMAL, bg="#f59e0b")
            self.led.itemconfig(self.led_dot, fill=T["led_on"])
            self.status_label.config(text="Ativo", fg=T["status_active_fg"])
        else:
            self.btn_ativar.config(state=tk.NORMAL, bg=T["btn_ativar_bg"])
            self.btn_restaurar.config(state=tk.DISABLED, bg="#9ca3af")
            self.led.itemconfig(self.led_dot, fill=T["led_off"])
            self.status_label.config(text="Inativo", fg=T["status_inactive_fg"])

    def _toggle_log(self):
        if self.log_visible:
            self.log_area.pack_forget()
            self.btn_toggle_log.config(text="\u25b6")
        else:
            self.log_area.pack(fill=tk.BOTH, expand=True, before=self._exit_frame)
            self.btn_toggle_log.config(text="\u25bc")
        self.log_visible = not self.log_visible

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.current_theme = THEMES["dark" if self.dark_mode else "light"]
        self._apply_theme()

    def _apply_theme(self):
        T = self.current_theme
        self.root.configure(bg=T["bg"])
        for w in [self._container, self._header_frame,
                  self._btn_frame, self._log_header, self._exit_frame]:
            w.configure(bg=T["bg"])
        self._title_label.configure(bg=T["bg"], fg=T["title_fg"])
        self._subtitle_label.configure(bg=T["bg"], fg=T["subtitle_fg"])
        self._status_card.configure(bg=T["card_bg"], highlightbackground=T["card_border"])
        self._status_row.configure(bg=T["card_bg"])
        self.led.configure(bg=T["card_bg"])
        self.status_label.configure(bg=T["card_bg"])
        self._sep.configure(bg=T["sep"])
        self.log_area.configure(bg=T["log_bg"], fg=T["log_fg"], insertbackground=T["log_insert"])
        self.btn_sair.configure(
            bg=T["btn_sair_bg"], fg=T["btn_sair_fg"],
            activebackground=T["btn_sair_active_bg"],
            activeforeground=T["btn_sair_active_fg"],
        )
        self.btn_toggle_theme.configure(
            text="\u2600" if self.dark_mode else "\u263e",
            bg=T["bg"], fg=T["subtitle_fg"],
        )
        self.btn_toggle_log.configure(bg=T["bg"], fg=T["log_header_fg"])
        self._update_buttons()

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
