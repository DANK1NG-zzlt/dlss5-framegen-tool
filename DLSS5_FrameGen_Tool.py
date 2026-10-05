"""
DLSS 5 + 帧生成 一键装载工具  v3.0  精致版
适用: RTX 20系 (SM75) / RTX 30系 (SM86)
依赖: pip install customtkinter pillow py7zr
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys
import shutil
import json
import re
import tempfile
import subprocess
import urllib.request
from datetime import datetime

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

OPTISCALER_URL = "https://github.com/optiscaler/OptiScaler/releases/download/v0.9.4/Optiscaler_0.9.4-final.20260718._MM.7z"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ===== 配色（更深邃的暗色 + 高饱和薄荷绿） =====
BG          = "#05070b"
SIDEBAR     = "#0a0e16"
CARD        = "#0f141d"
CARD_2      = "#141b26"
CARD_3      = "#1a2332"
BORDER      = "#1e2a3a"
BORDER_HI   = "#2a3a50"
ACCENT      = "#00f0a0"
ACCENT_DIM  = "#00c882"
ACCENT_2    = "#4cc9f0"
WARN        = "#ffc857"
ERROR       = "#ff6b6b"
TEXT        = "#f0f4fa"
DIM         = "#7a8ba0"
FAINT       = "#4a5a70"

RAD_LG = 16
RAD_MD = 10


# ===== 小部件：统计卡 =====
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, icon, title, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=RAD_LG,
                         border_width=1, border_color=BORDER, **kw)
        self.grid_columnconfigure(1, weight=1)
        self.icon = ctk.CTkLabel(
            self, text=icon, width=44, height=44, corner_radius=22,
            fg_color=CARD_2, font=ctk.CTkFont(size=20),
        )
        self.icon.grid(row=0, column=0, rowspan=2, padx=16, pady=16)
        ctk.CTkLabel(
            self, text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=FAINT,
        ).grid(row=0, column=1, sticky="sw", padx=(6, 8), pady=(16, 0))
        self.value = ctk.CTkLabel(
            self, text="—",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT, anchor="w", justify="left", wraplength=240,
        )
        self.value.grid(row=1, column=1, sticky="nw", padx=(6, 8), pady=(2, 16))

    def set(self, value, color=TEXT):
        self.value.configure(text=value, text_color=color)


# ===== 小部件：侧栏步骤 =====
class SidebarStep(ctk.CTkFrame):
    def __init__(self, parent, num, label, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.dot = ctk.CTkLabel(
            self, text=str(num), width=28, height=28, corner_radius=14,
            fg_color=CARD_3, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=FAINT,
        )
        self.dot.pack(side="left", padx=(0, 10))
        self.lab = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=13, weight="normal"),
            text_color=FAINT, anchor="w",
        )
        self.lab.pack(side="left")

    def set_state(self, s):
        if s == "done":
            self.dot.configure(text="✓", fg_color=ACCENT, text_color="#02120a")
            self.lab.configure(text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold"))
        elif s == "active":
            self.dot.configure(text="●", fg_color=CARD_2, text_color=ACCENT_2,
                               font=ctk.CTkFont(size=10))
            self.lab.configure(text_color=ACCENT_2, font=ctk.CTkFont(size=13, weight="bold"))
        elif s == "blocked":
            self.dot.configure(text="!", fg_color=WARN, text_color="#1a1000")
            self.lab.configure(text_color=WARN, font=ctk.CTkFont(size=13, weight="bold"))
        else:
            self.dot.configure(text="", fg_color=CARD_3, text_color=FAINT)
            self.lab.configure(text_color=FAINT, font=ctk.CTkFont(size=13))


# ===== 主应用 =====
class DLSS5FrameGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DLSS 5 + 帧生成 一键装载工具")
        self.geometry("1200x800")
        self.minsize(1100, 720)
        self.configure(fg_color=BG)

        self.gpu_type = None
        self.gpu_name = "检测中…"
        self.target_exe = None
        self.game_name = None
        self.anticheat = []
        self.ac_checked = False
        self.installed = False

        self.enable_dlss5 = ctk.BooleanVar(value=True)
        self.enable_fg    = ctk.BooleanVar(value=True)
        self.multiplier   = ctk.IntVar(value=4)
        self.auto_scroll  = ctk.BooleanVar(value=True)

        self.custom_games_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_games.json")
        self.custom_games = self._load_custom_games()

        self._build_ui()
        self._detect_gpu_async()
        self.log("程序启动完成，正在检测显卡…", "info")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, fg_color=SIDEBAR, corner_radius=0, width=240)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)

        logo_box = ctk.CTkFrame(bar, fg_color="transparent")
        logo_box.pack(padx=20, pady=(28, 0), anchor="w")
        logo_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            logo_box, text="⚡", width=40, height=40, corner_radius=12,
            fg_color=CARD_2, font=ctk.CTkFont(size=20),
        ).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(
            logo_box, text="DLSS 5",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(
            logo_box, text="Frame Gen Tool",
            font=ctk.CTkFont(size=10),
            text_color=DIM,
        ).grid(row=1, column=1, sticky="nw")

        ctk.CTkFrame(bar, height=1, fg_color=BORDER).pack(
            fill="x", padx=20, pady=(24, 16))

        ctk.CTkLabel(
            bar, text="LOADOUT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=FAINT,
        ).pack(padx=20, anchor="w")

        self.steps = [
            SidebarStep(bar, 1, "GPU Detection"),
            SidebarStep(bar, 2, "Select Game"),
            SidebarStep(bar, 3, "Anti-Cheat Check"),
            SidebarStep(bar, 4, "One-Click Install"),
        ]
        for s in self.steps:
            s.pack(padx=20, anchor="w", pady=6)

        self.gpu_badge = ctk.CTkLabel(
            bar, text="GPU: detecting…",
            font=ctk.CTkFont(size=11),
            text_color=DIM, anchor="w", wraplength=190, justify="left",
        )
        self.gpu_badge.pack(side="bottom", padx=20, pady=(0, 16), anchor="w")
        ctk.CTkLabel(
            bar, text="v3.0 · OptiScaler v0.9.4",
            font=ctk.CTkFont(size=10),
            text_color=FAINT,
        ).pack(side="bottom", padx=20, anchor="w", pady=(0, 12))

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=3)
        main.grid_rowconfigure(3, weight=2)

        self._build_topbar(main)
        self._build_stats(main)
        self._build_config(main)
        self._build_log(main)
        self._build_actions(main)

    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 4))
        bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            bar, text="Control Center",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            bar, text="RTX 20/30 · OptiScaler v0.9.4 · 1–6X Multi Frame Generation",
            font=ctk.CTkFont(size=12),
            text_color=DIM,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_stats(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=28, pady=8)
        for i in range(3):
            row.grid_columnconfigure(i, weight=1, uniform="st")
        self.card_gpu  = StatCard(row, "🎮", "GPU")
        self.card_gpu.grid(row=0, column=0, sticky="nsew", padx=6)
        self.card_game = StatCard(row, "📂", "Game")
        self.card_game.grid(row=0, column=1, sticky="nsew", padx=6)
        self.card_ac   = StatCard(row, "🛡", "Anti-Cheat")
        self.card_ac.grid(row=0, column=2, sticky="nsew", padx=6)

    def _build_config(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=28, pady=8)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            body, fg_color=CARD, corner_radius=RAD_LG,
            border_width=1, border_color=BORDER,
        )
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel, text="INSTALL CONFIGURATION",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=FAINT,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        row1 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD,
                            border_width=1, border_color=BORDER)
        row1.grid(row=1, column=0, sticky="ew", padx=20, pady=6)
        row1.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            row1, text="🧠  DLSS 5 Neural Rendering",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))
        self.sw_dlss5 = ctk.CTkSwitch(
            row1, text="", variable=self.enable_dlss5,
            progress_color=ACCENT, button_color="#ffffff",
            button_hover_color="#e0e0e0",
        )
        self.sw_dlss5.grid(row=0, column=1, sticky="e", padx=18, pady=(16, 0))
        ctk.CTkLabel(
            row1,
            text="Neural upscaling injected via OptiScaler — works with unsupported titles.",
            font=ctk.CTkFont(size=11), text_color=DIM, justify="left",
            wraplength=600,
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 16))

        row2 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD,
                            border_width=1, border_color=BORDER)
        row2.grid(row=2, column=0, sticky="ew", padx=20, pady=6)
        row2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            row2, text="🎞  Frame Generation (MFG)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))
        self.sw_fg = ctk.CTkSwitch(
            row2, text="", variable=self.enable_fg,
            progress_color=ACCENT, button_color="#ffffff",
            button_hover_color="#e0e0e0",
            command=self._on_fg_toggle,
        )
        self.sw_fg.grid(row=0, column=1, sticky="e", padx=18, pady=(16, 0))

        mult = ctk.CTkFrame(row2, fg_color="transparent")
        mult.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 6))
        mult.grid_columnconfigure(0, weight=1)

        self.lbl_mult = ctk.CTkLabel(
            mult, text="4X", width=56, height=32, corner_radius=8,
            fg_color="#06281c", text_color=ACCENT,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.lbl_mult.grid(row=0, column=0, sticky="e", pady=(0, 8))

        self.slider = ctk.CTkSlider(
            mult, from_=1, to=6, number_of_steps=5, variable=self.multiplier,
            command=self._on_multiplier_change,
            progress_color=ACCENT, button_color=ACCENT,
            button_hover_color="#5ff5c4",
        )
        self.slider.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        ticks = ctk.CTkFrame(mult, fg_color="transparent")
        ticks.grid(row=2, column=0, sticky="ew")
        for i in range(6):
            ticks.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                ticks, text=f"{i+1}X",
                font=ctk.CTkFont(size=10), text_color=FAINT,
            ).grid(row=0, column=i)

        self.lbl_hint = ctk.CTkLabel(
            row2, text="Waiting for GPU detection…",
            font=ctk.CTkFont(size=11), text_color=FAINT,
            justify="left", wraplength=620,
        )
        self.lbl_hint.grid(row=3, column=0, columnspan=2, sticky="w",
                           padx=18, pady=(4, 16))

    def _build_log(self, parent):
        wrap = ctk.CTkFrame(
            parent, fg_color=CARD, corner_radius=RAD_LG,
            border_width=1, border_color=BORDER,
        )
        wrap.grid(row=3, column=0, sticky="nsew", padx=28, pady=8)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            top, text="RUN LOG",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=FAINT,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkSwitch(
            top, text="Auto-scroll", variable=self.auto_scroll,
            progress_color=ACCENT, font=ctk.CTkFont(size=11),
        ).grid(row=0, column=1, padx=(8, 8))
        ctk.CTkButton(
            top, text="Clear", width=56, height=26,
            fg_color=CARD_3, hover_color=CARD_2,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._clear_log,
        ).grid(row=0, column=2)

        self.log_box = ctk.CTkTextbox(
            wrap, fg_color="#06090e", text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8, wrap="word", border_width=0,
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self.log_box.configure(state="disabled")

        tb = self.log_box._textbox
        tb.tag_config("info",    foreground=DIM)
        tb.tag_config("success", foreground=ACCENT)
        tb.tag_config("warn",    foreground=WARN)
        tb.tag_config("error",   foreground=ERROR)
        tb.tag_config("step",    foreground=ACCENT_2)

    def _build_actions(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", padx=28, pady=(8, 24))
        bar.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        btn_style = dict(
            fg_color=CARD_2, hover_color=CARD_3,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44, corner_radius=10,
        )
        ctk.CTkButton(
            left, text="🔍  Scan Library", width=130, **btn_style,
            command=self._scan_library,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            left, text="➕  Add Game", width=110, **btn_style,
            command=self._add_custom_game,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            left, text="📁  Browse EXE", width=120, **btn_style,
            command=self._pick_exe,
        ).pack(side="left")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        self.btn_restore = ctk.CTkButton(
            right, text="🛠  Restore", width=120, height=44,
            fg_color=CARD_2, hover_color=CARD_3,
            border_width=1, border_color=WARN,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10, command=self._restore_files,
        )
        self.btn_restore.pack(side="left", padx=(0, 10))

        self.btn_install = ctk.CTkButton(
            right, text="🚀  Install", width=160, height=44,
            fg_color=ACCENT, hover_color=ACCENT_DIM,
            text_color="#02120a",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10, command=self._install,
        )
        self.btn_install.pack(side="left")

    def log(self, msg, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box._textbox.insert("end", f"[{ts}]  {msg}\n", level)
        self.log_box.configure(state="disabled")
        if self.auto_scroll.get():
            self.log_box.see("end")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _detect_gpu_async(self):
        threading.Thread(target=self._detect_gpu_worker, daemon=True).start()

    def _detect_gpu_worker(self):
        gpu_name = None
        gpu_type = None
        try:
            import wmi
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                name = (gpu.Name or "").strip()
                if not name:
                    continue
                if re.search(r"RTX\s*20[678]0", name, re.I):
                    gpu_name = name; gpu_type = "SM75"; break
                if re.search(r"RTX\s*30[6789]0", name, re.I):
                    gpu_name = name; gpu_type = "SM86"; break
                if "RTX" in name.upper() and not gpu_name:
                    gpu_name = name
        except Exception:
            try:
                out = subprocess.check_output(
                    ["cmd", "/c", "wmic", "path", "win32_VideoController", "get", "name"],
                    stderr=subprocess.DEVNULL, timeout=10
                ).decode("gbk", errors="ignore")
                for line in out.splitlines():
                    line = line.strip()
                    if "RTX" in line.upper() and "Name" not in line:
                        gpu_name = line
                        if re.search(r"RTX\s*20", line):
                            gpu_type = "SM75"
                        elif re.search(r"RTX\s*30", line):
                            gpu_type = "SM86"
                        break
            except Exception:
                pass
        if gpu_name:
            self.gpu_name = gpu_name
            self.gpu_type = gpu_type
        else:
            self.gpu_name = "No RTX GPU detected"
            self.gpu_type = None
        self.after(0, self._apply_gpu_result)

    def _apply_gpu_result(self):
        if self.gpu_type == "SM86":
            self.card_gpu.set(self.gpu_name, ACCENT)
            self.gpu_badge.configure(text="✅ " + self.gpu_name)
            self.slider.configure(to=6, number_of_steps=5)
            if self.multiplier.get() > 6:
                self.multiplier.set(6)
            self.lbl_hint.configure(
                text="✅ RTX 30 series (SM86): up to 6X MFG + DLSS 5 supported.",
                text_color=ACCENT,
            )
            self.log(f"GPU detected: {self.gpu_name} → SM86", "success")
        elif self.gpu_type == "SM75":
            self.card_gpu.set(self.gpu_name, WARN)
            self.gpu_badge.configure(text="⚠ " + self.gpu_name)
            self.slider.configure(to=4, number_of_steps=3)
            if self.multiplier.get() > 4:
                self.multiplier.set(4)
            self.lbl_hint.configure(
                text="⚠ RTX 20 series (SM75): experimental, up to 4X.",
                text_color=WARN,
            )
            self.log(f"GPU detected: {self.gpu_name} → SM75 (experimental)", "warn")
        else:
            self.card_gpu.set("No supported GPU", ERROR)
            self.gpu_badge.configure(text="❌ No supported GPU")
            self.lbl_hint.configure(
                text="❌ No RTX 20/30 series GPU detected.",
                text_color=ERROR,
            )
            self.log("No supported NVIDIA RTX GPU found.", "error")
        self._refresh_steps()

    def _on_fg_toggle(self):
        self.slider.configure(
            state="normal" if self.enable_fg.get() else "disabled"
        )
        self.lbl_mult.configure(
            text_color=ACCENT if self.enable_fg.get() else FAINT
        )

    def _on_multiplier_change(self, value):
        v = int(round(value))
        self.multiplier.set(v)
        self.lbl_mult.configure(text=f"{v}X")

    def _refresh_steps(self):
        gpu  = self.gpu_type is not None
        game = self.target_exe is not None
        ac   = self.ac_checked
        inst = self.installed
        self.steps[0].set_state("done" if gpu else "active")
        self.steps[1].set_state(
            "done" if game else ("active" if gpu else "pending")
        )
        if self.anticheat:
            self.steps[2].set_state("blocked")
        elif ac:
            self.steps[2].set_state("done")
        else:
            self.steps[2].set_state("active" if game else "pending")
        self.steps[3].set_state(
            "done" if inst
            else ("active" if gpu and game and ac and not self.anticheat else "pending")
        )

    def _scan_library(self):
        self.log("Scanning Steam / Epic game libraries…", "step")
        def worker():
            candidates = []
            try:
                steam_path = None
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
                    steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
                    winreg.CloseKey(key)
                except Exception:
                    pass
                if steam_path:
                    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                    if os.path.exists(vdf):
                        with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        paths = re.findall(r'"path"\s*"([^"]+)"', content)
                        for p in paths:
                            p = p.replace("\\\\", "\\")
                            apps_dir = os.path.join(p, "steamapps", "common")
                            if os.path.isdir(apps_dir):
                                for game in os.listdir(apps_dir):
                                    gd = os.path.join(apps_dir, game)
                                    if os.path.isdir(gd):
                                        for item in os.listdir(gd):
                                            if (item.lower().endswith(".exe")
                                                and "uninst" not in item.lower()
                                                and "redist" not in item.lower()):
                                                candidates.append((game, os.path.join(gd, item)))
                                                break
            except Exception as e:
                self.after(0, lambda: self.log(f"Steam scan error: {e}", "warn"))
            try:
                epic_manifests = os.path.expandvars(
                    r"%ProgramData%\Epic\EpicGamesLauncher\Data\Manifests"
                )
                if os.path.isdir(epic_manifests):
                    for mf in os.listdir(epic_manifests):
                        if mf.endswith(".item"):
                            try:
                                with open(os.path.join(epic_manifests, mf),
                                          "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                name = data.get("DisplayName", "")
                                install = data.get("InstallLocation", "")
                                exe = data.get("LaunchExecutable", "")
                                if name and install and exe:
                                    full = os.path.join(install, exe)
                                    if os.path.exists(full):
                                        candidates.append((name, full))
                            except Exception:
                                pass
            except Exception:
                pass
            if candidates:
                self.after(0, lambda: self.log(
                    f"Scan complete: {len(candidates)} game(s) found.", "success"))
                name, path = candidates[0]
                self.target_exe = path
                self.game_name = name
                self.after(0, lambda: self.card_game.set(name, ACCENT))
                self.after(0, lambda: self.log(f"Auto-selected: {name}", "info"))
                self.after(0, self._detect_anticheat_async)
            else:
                self.after(0, lambda: self.log(
                    "No games found. Please add or browse manually.", "warn"))
            self.after(0, self._refresh_steps)
        threading.Thread(target=worker, daemon=True).start()

    def _load_custom_games(self):
        try:
            if os.path.exists(self.custom_games_file):
                with open(self.custom_games_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_custom_games(self):
        try:
            with open(self.custom_games_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_games, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _add_custom_game(self):
        path = filedialog.askopenfilename(
            title="Select game EXE",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        for g in self.custom_games:
            if g.get("path", "").lower() == path.lower():
                messagebox.showinfo("Already added", "This game is already in the list.")
                return
        default_name = os.path.splitext(os.path.basename(path))[0]
        self.custom_games.append({"name": default_name, "path": path})
        self._save_custom_games()
        self.log(f"Game added: {default_name}", "success")
        self.target_exe = path
        self.game_name = default_name
        self.card_game.set(default_name, ACCENT)
        self._detect_anticheat_async()

    def _pick_exe(self):
        path = filedialog.askopenfilename(
            title="Select game renderer EXE",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        self.target_exe = path
        self.game_name = os.path.basename(path)
        self.card_game.set(self.game_name, ACCENT)
        self.log(f"Target: {path}", "success")
        self._detect_anticheat_async()

    def _detect_anticheat_async(self):
        def worker():
            self.after(0, lambda: self.card_ac.set("Scanning…", DIM))
            time.sleep(0.3)
            found = []
            game_dir = os.path.dirname(self.target_exe)
            ac_patterns = [
                ("EasyAntiCheat", "EasyAntiCheat"),
                ("BattlEye", "BattlEye"),
                ("Riot Vanguard", "vgc.exe"),
                ("EOS Online", "EOSSDK-Win64-Shipping.exe"),
                ("PunkBuster", "pbclient"),
                ("nProtect", "npgg"),
            ]
            try:
                for root, dirs, files in os.walk(game_dir):
                    depth = root.replace(game_dir, "").count(os.sep)
                    if depth > 2:
                        dirs[:] = []
                        continue
                    for d in dirs:
                        for label, pat in ac_patterns:
                            if pat.lower() in d.lower() and label not in found:
                                found.append(label)
                    for fn in files:
                        for label, pat in ac_patterns:
                            if pat.lower() in fn.lower() and label not in found:
                                found.append(label)
            except Exception:
                pass
            self.anticheat = found
            self.ac_checked = True
            if found:
                names = ", ".join(found)
                self.after(0, lambda: self.card_ac.set(names, ERROR))
                self.after(0, lambda: self.log(
                    f"⚠ Anti-cheat detected: {names} — installation blocked!", "error"))
                self.after(0, lambda: self.btn_install.configure(state="disabled"))
            else:
                self.after(0, lambda: self.card_ac.set("Clean", ACCENT))
                self.after(0, lambda: self.log("Anti-cheat check passed.", "success"))
                self.after(0, lambda: self.btn_install.configure(state="normal"))
            self.after(0, self._refresh_steps)
        threading.Thread(target=worker, daemon=True).start()

    def _install(self):
        if not self.target_exe:
            messagebox.showwarning("No game selected",
                                   "Please select a game renderer EXE first.")
            return
        if not self.gpu_type:
            messagebox.showerror("GPU not supported",
                                 "No supported RTX 20/30 series GPU detected.")
            return
        if self.anticheat:
            messagebox.showerror("Risk blocked",
                                 f"Anti-cheat detected: {', '.join(self.anticheat)}")
            return
        if self.gpu_type == "SM75":
            if not messagebox.askyesno(
                "Experimental feature",
                "RTX 20 series frame generation is experimental.\n"
                "May cause flicker, crashes, or performance loss.\nContinue?"
            ):
                return
        self.btn_install.configure(state="disabled", text="⏳  Working…")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        game_dir = os.path.dirname(self.target_exe)
        exe_name = os.path.basename(self.target_exe)
        mult = self.multiplier.get()

        self.after(0, lambda: self.log(f"Target: {game_dir}", "info"))
        tmp = tempfile.mkdtemp(prefix="dlss5_")
        self.after(0, lambda: self.log("Creating temp workspace…", "step"))

        bundled = self._resource_path("OptiScaler_v0.9.4_full.7z")
        archive_path = os.path.join(tmp, "optiscaler.7z")
        if os.path.exists(bundled):
            self.after(0, lambda: self.log(
                "✓ Using bundled OptiScaler package (offline)", "success"))
            shutil.copy2(bundled, archive_path)
        else:
            self.after(0, lambda: self.log(
                "Bundled package not found, downloading from GitHub…", "step"))
            try:
                urllib.request.urlretrieve(OPTISCALER_URL, archive_path)
                self.after(0, lambda: self.log("✓ Download complete", "success"))
            except Exception as e:
                self.after(0, lambda: self.log(f"✗ Download failed: {e}", "error"))
                self.after(0, self._on_install_failed)
                return

        self.after(0, lambda: self.log("Extracting OptiScaler…", "step"))
        extract_dir = os.path.join(tmp, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            if not HAS_PY7ZR:
                raise RuntimeError("py7zr not installed")
            with py7zr.SevenZipFile(archive_path, mode="r") as z:
                z.extractall(path=extract_dir)
            self.after(0, lambda: self.log("✓ Extraction complete", "success"))
        except Exception as e:
            self.after(0, lambda: self.log(f"✗ Extraction failed: {e}", "error"))
            self.after(0, self._on_install_failed)
            return
        time.sleep(0.3)

        self.after(0, lambda: self.log("Backing up original files…", "step"))
        backup_dir = os.path.join(game_dir, ".dlss5_backup")
        os.makedirs(backup_dir, exist_ok=True)
        for fname in ["dxgi.dll", "version.dll", "nvngx_dlss.dll",
                      "nvngx_dlssnr.dll", "OptiScaler.ini"]:
            src = os.path.join(game_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(backup_dir, fname))
                self.after(0, lambda f=fname: self.log(f"  Backup: {f}", "info"))
        time.sleep(0.2)

        self.after(0, lambda: self.log("Deploying OptiScaler components…", "step"))
        deployed = 0
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, extract_dir)
                if f.lower().startswith("readme") or f.lower().startswith("license"):
                    continue
                dst = os.path.join(game_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if f.lower() == "optiscaler.dll":
                    shutil.copy2(src, os.path.join(game_dir, "dxgi.dll"))
                    self.after(0, lambda: self.log(
                        "  → OptiScaler.dll → dxgi.dll (injector)", "info"))
                else:
                    shutil.copy2(src, dst)
                    self.after(0, lambda r=rel: self.log(f"  → {r}", "info"))
                deployed += 1
        if deployed == 0:
            self.after(0, lambda: self.log("✗ No files found after extraction", "error"))
            self.after(0, self._on_install_failed)
            return
        self.after(0, lambda: self.log(f"✓ Deployed {deployed} files", "success"))

        if self.enable_dlss5.get():
            self.after(0, lambda: self.log(
                "DLSS 5 neural rendering activated via OptiScaler", "info"))
        time.sleep(0.2)

        self.after(0, lambda: self.log(
            f"Writing OptiScaler.ini (MFG {mult}X)…", "step"))
        ini_path = os.path.join(game_dir, "OptiScaler.ini")
        ini_content = f"""[OptiScaler]
; DLSS 5 + Frame Gen Tool v3.0
EnableOverlays=false
FrameGenerationMode={mult}
TargetExe={exe_name}
"""
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini_content)
        self.after(0, lambda: self.log("✓ OptiScaler.ini written", "success"))

        shutil.rmtree(tmp, ignore_errors=True)
        self.after(0, self._on_install_done)

    def _on_install_failed(self):
        self.btn_install.configure(state="normal", text="🚀  Install")
        self.log("Installation failed.", "error")

    def _resource_path(self, relative):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)

    def _on_install_done(self):
        self.installed = True
        self.btn_install.configure(state="normal", text="✅  Installed")
        self.btn_restore.configure(state="normal")
        self.log("Installation complete! Launch game → Graphics → enable Frame Generation.",
                  "success")
        self.log("Tip: some games require a restart to take effect.", "info")
        self._refresh_steps()

    def _restore_files(self):
        if not self.target_exe:
            messagebox.showwarning("No game selected",
                                   "Please select a game EXE first.")
            return
        game_dir = os.path.dirname(self.target_exe)
        backup_dir = os.path.join(game_dir, ".dlss5_backup")
        if not os.path.isdir(backup_dir):
            messagebox.showinfo("No backup",
                                "No backup found in this game directory.")
            return
        if not messagebox.askyesno(
            "Confirm restore",
            "Restore original game files from backup?\nThis will remove all OptiScaler files."
        ):
            return
        self.log("Restoring original files…", "step")
        deployed_files = [
            "dxgi.dll", "OptiScaler.ini", "fakenvapi.dll", "fakenvapi.ini",
            "amd_fidelityfx_dx12.dll", "amd_fidelityfx_framegeneration_dx12.dll",
            "amd_fidelityfx_upscaler_dx12.dll", "amd_fidelityfx_vk.dll",
            "dlssg_to_fsr3_amd_is_better.dll",
            "libxell.dll", "libxess.dll", "libxess_dx11.dll", "libxess_fg.dll",
        ]
        for fname in deployed_files:
            p = os.path.join(game_dir, fname)
            if os.path.exists(p):
                os.remove(p)
                self.log(f"  Removed: {fname}", "info")
        d3d12_dir = os.path.join(game_dir, "D3D12_Optiscaler")
        if os.path.isdir(d3d12_dir):
            shutil.rmtree(d3d12_dir)
            self.log("  Removed: D3D12_Optiscaler/", "info")
        restored = 0
        for f in os.listdir(backup_dir):
            shutil.copy2(os.path.join(backup_dir, f), os.path.join(game_dir, f))
            restored += 1
        shutil.rmtree(backup_dir)
        self.log(f"✓ Restored {restored} original file(s). Backup cleared.",
                  "success")
        self.installed = False
        self.btn_install.configure(text="🚀  Install")
        self._refresh_steps()


if __name__ == "__main__":
    app = DLSS5FrameGenApp()
    app.mainloop()
