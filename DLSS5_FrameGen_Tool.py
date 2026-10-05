"""
DLSS 5 + 帧生成 一键装载工具  v3.3  一键丢入版
适用: RTX 20系 (SM75) / RTX 30系 (SM86)
依赖: pip install customtkinter pillow wmi
运行时用内置 7zr.exe 解压官方 OptiScaler v0.9.4 包
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

OPTISCALER_URL = "https://github.com/optiscaler/OptiScaler/releases/download/v0.9.4/Optiscaler_0.9.4-final.20260718._MM.7z"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG          = "#05070b"
SIDEBAR     = "#0a0e16"
CARD        = "#0f141d"
CARD_2      = "#141b26"
CARD_3      = "#1a2332"
BORDER      = "#1e2a3a"
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

I18N = {
    "zh": {
        "app_title": "DLSS 5 + 帧生成 一键装载工具",
        "brand_sub": "Frame Gen Tool",
        "loadout": "装载流程",
        "step1": "显卡检测", "step2": "选择游戏", "step3": "反作弊检查", "step4": "一键丢入",
        "control_center": "控制面板",
        "subtitle": "RTX 20/30 系 · OptiScaler v0.9.4 · FSR3 帧生成 + XeSS 插帧",
        "gpu": "显卡", "game": "游戏", "anticheat": "反作弊",
        "no_supported_gpu": "未检测到受支持显卡",
        "install_config": "装载配置",
        "dlss5_render": "神经画质增强 (FSR3/XeSS)",
        "dlss5_desc": "通过 OptiScaler 注入 FSR3.1 帧生成 + XeSS 超分，为原生不支持的游戏开启插帧。",
        "frame_gen": "帧生成 (MFG)",
        "waiting_gpu": "等待显卡检测…",
        "rtx30_ok": "✅ RTX 30 系 (SM86)：FSR3 帧生成 + XeSS 插帧可用，最高 4X。",
        "rtx20_warn": "⚠ RTX 20 系 (SM75)：实验性支持，最高 2X，可能闪烁或崩溃。",
        "gpu_error": "❌ 未检测到 RTX 20/30 系显卡。",
        "run_log": "运行日志", "auto_scroll": "自动滚动", "clear": "清空",
        "scan_lib": "🔍  扫描游戏库", "add_game": "➕  添加游戏", "browse_exe": "📁  选择 EXE",
        "restore": "🛠  还原", "install": "🚀  一键丢入",
        "installed": "✅  已丢入", "working": "⏳  丢入中…",
        "startup": "程序启动完成，正在检测显卡…",
        "gpu_not_found": "未检测到受支持的 NVIDIA RTX 显卡。",
        "gpu_detected": "显卡检测完成",
        "scan_start": "开始扫描 Steam / Epic 游戏库…",
        "scan_done": "扫描完成，找到 {n} 个游戏。",
        "scan_none": "未找到游戏，请手动添加或选择 EXE。",
        "auto_selected": "已自动选择",
        "game_added": "已添加游戏",
        "game_exists": "该游戏已在列表中。", "game_exists_title": "已存在",
        "target": "已选择目标",
        "ac_scanning": "检测中…", "ac_clean": "未检测到",
        "ac_passed": "反作弊检测通过。",
        "ac_found": "⚠ 检测到反作弊", "ac_blocked": "禁止丢入！",
        "no_game": "请先选择一个游戏渲染 EXE。", "no_game_title": "未选择游戏",
        "gpu_unsupported": "未检测到受支持的 RTX 20/30 系显卡。",
        "gpu_unsup_title": "显卡不支持",
        "risk_blocked": "检测到反作弊", "risk_title": "风险拦截",
        "experimental": "实验性确认",
        "experimental_msg": "RTX 20 系帧生成为实验性功能，可能闪烁、崩溃或掉帧。\n是否继续？",
        "target_dir": "目标目录", "tmp_workspace": "准备临时目录…",
        "bundled_found": "✓ 读取内置 OptiScaler 包",
        "bundled_missing": "未找到内置包，从 GitHub 下载…",
        "download_done": "✓ 下载完成", "download_fail": "✗ 下载失败",
        "extracting": "解压 OptiScaler…", "extract_done": "✓ 解压完成", "extract_fail": "✗ 解压失败",
        "backup": "备份原始文件…",
        "deploying": "丢入游戏目录…",
        "deploy_injector": "→ dxgi.dll (DXGI 注入器)",
        "deployed": "✓ 已丢入 {n} 个文件",
        "writing_ini": "配置帧生成 {mult}X…",
        "ini_done": "✓ OptiScaler.ini 已配置",
        "install_complete": "✅ 丢入完成！进游戏按 Insert 呼出菜单开帧生成。",
        "install_tip": "快捷键：Insert=菜单，PageUp=FPS 叠加。",
        "install_failed": "丢入失败。",
        "restore_title": "确认还原",
        "restore_msg": "将从备份恢复游戏目录的原始文件，是否继续？",
        "restore_start": "开始还原文件…",
        "restore_done": "✓ 已还原 {n} 个原始文件，备份已清除",
        "no_backup": "该游戏目录没有找到备份，无需还原。",
        "no_backup_title": "无备份",
        "removed": "已删除",
        "version": "v3.3 · 一键丢入",
        "gpu_badge": "显卡：",
        "lang_btn": "EN",
    },
    "en": {
        "app_title": "DLSS 5 + Frame Gen One-Click Installer",
        "brand_sub": "Frame Gen Tool",
        "loadout": "LOADOUT",
        "step1": "GPU Detection", "step2": "Select Game", "step3": "Anti-Cheat Check", "step4": "Drop In",
        "control_center": "Control Center",
        "subtitle": "RTX 20/30 · OptiScaler v0.9.4 · FSR3 FG + XeSS",
        "gpu": "GPU", "game": "Game", "anticheat": "Anti-Cheat",
        "no_supported_gpu": "No supported GPU",
        "install_config": "CONFIGURATION",
        "dlss5_render": "Neural Upscaling (FSR3/XeSS)",
        "dlss5_desc": "Inject FSR3.1 Frame Generation + XeSS upscaling via OptiScaler.",
        "frame_gen": "Frame Generation (MFG)",
        "waiting_gpu": "Waiting for GPU detection…",
        "rtx30_ok": "✅ RTX 30 (SM86): FSR3 FG + XeSS up to 4X.",
        "rtx20_warn": "⚠ RTX 20 (SM75): experimental, up to 2X.",
        "gpu_error": "❌ No RTX 20/30 GPU detected.",
        "run_log": "RUN LOG", "auto_scroll": "Auto-scroll", "clear": "Clear",
        "scan_lib": "🔍  Scan Library", "add_game": "➕  Add Game", "browse_exe": "📁  Browse EXE",
        "restore": "🛠  Restore", "install": "🚀  Drop In",
        "installed": "✅  Dropped In", "working": "⏳  Dropping…",
        "startup": "Program started, detecting GPU…",
        "gpu_not_found": "No supported NVIDIA RTX GPU found.",
        "gpu_detected": "GPU detected",
        "scan_start": "Scanning Steam / Epic game libraries…",
        "scan_done": "Scan complete: {n} game(s) found.",
        "scan_none": "No games found. Please add or browse manually.",
        "auto_selected": "Auto-selected",
        "game_added": "Game added",
        "game_exists": "This game is already in the list.", "game_exists_title": "Already added",
        "target": "Target",
        "ac_scanning": "Scanning…", "ac_clean": "Clean",
        "ac_passed": "Anti-cheat check passed.",
        "ac_found": "⚠ Anti-cheat detected", "ac_blocked": "Drop-in blocked!",
        "no_game": "Please select a game renderer EXE first.", "no_game_title": "No game selected",
        "gpu_unsupported": "No supported RTX 20/30 GPU detected.",
        "gpu_unsup_title": "GPU not supported",
        "risk_blocked": "Anti-cheat detected", "risk_title": "Risk blocked",
        "experimental": "Experimental feature",
        "experimental_msg": "RTX 20 series frame generation is experimental.\nMay cause flicker or crashes. Continue?",
        "target_dir": "Target", "tmp_workspace": "Preparing temp dir…",
        "bundled_found": "✓ Loaded bundled OptiScaler package",
        "bundled_missing": "Bundled package not found, downloading…",
        "download_done": "✓ Download complete", "download_fail": "✗ Download failed",
        "extracting": "Extracting OptiScaler…", "extract_done": "✓ Extraction complete", "extract_fail": "✗ Extraction failed",
        "backup": "Backing up original files…",
        "deploying": "Dropping files into game dir…",
        "deploy_injector": "→ dxgi.dll (DXGI injector)",
        "deployed": "✓ Dropped {n} files",
        "writing_ini": "Configuring frame gen {mult}X…",
        "ini_done": "✓ OptiScaler.ini configured",
        "install_complete": "✅ Done! Press Insert in-game to open the OptiScaler menu and enable FG.",
        "install_tip": "Hotkeys: Insert = menu, PageUp = FPS overlay.",
        "install_failed": "Drop-in failed.",
        "restore_title": "Confirm restore",
        "restore_msg": "Restore original game files from backup?",
        "restore_start": "Restoring original files…",
        "restore_done": "✓ Restored {n} original file(s). Backup cleared.",
        "no_backup": "No backup found in this game directory.",
        "no_backup_title": "No backup",
        "removed": "Removed",
        "version": "v3.3 · Drop In",
        "gpu_badge": "GPU: ",
        "lang_btn": "中",
    },
}


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, icon, title_key, app, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=RAD_LG, border_width=1, border_color=BORDER, **kw)
        self.app = app; self.title_key = title_key
        self.grid_columnconfigure(1, weight=1)
        self.icon = ctk.CTkLabel(self, text=icon, width=44, height=44, corner_radius=22, fg_color=CARD_2, font=ctk.CTkFont(size=20))
        self.icon.grid(row=0, column=0, rowspan=2, padx=16, pady=16)
        self.title_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color=FAINT)
        self.title_lbl.grid(row=0, column=1, sticky="sw", padx=(6, 8), pady=(16, 0))
        self.value = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT, anchor="w", justify="left", wraplength=240)
        self.value.grid(row=1, column=1, sticky="nw", padx=(6, 8), pady=(2, 16))
        self.refresh_text()
    def refresh_text(self):
        self.title_lbl.configure(text=self.app.t(self.title_key).upper())
    def set(self, value, color=TEXT):
        self.value.configure(text=value, text_color=color)


class SidebarStep(ctk.CTkFrame):
    def __init__(self, parent, num, label_key, app, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.app = app; self.label_key = label_key
        self.dot = ctk.CTkLabel(self, text=str(num), width=28, height=28, corner_radius=14, fg_color=CARD_3, font=ctk.CTkFont(size=12, weight="bold"), text_color=FAINT)
        self.dot.pack(side="left", padx=(0, 10))
        self.lab = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13), text_color=FAINT, anchor="w")
        self.lab.pack(side="left")
        self.refresh_text()
    def refresh_text(self):
        self.lab.configure(text=self.app.t(self.label_key))
    def set_state(self, s):
        if s == "done":
            self.dot.configure(text="✓", fg_color=ACCENT, text_color="#02120a")
            self.lab.configure(text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold"))
        elif s == "active":
            self.dot.configure(text="●", fg_color=CARD_2, text_color=ACCENT_2, font=ctk.CTkFont(size=10))
            self.lab.configure(text_color=ACCENT_2, font=ctk.CTkFont(size=13, weight="bold"))
        elif s == "blocked":
            self.dot.configure(text="!", fg_color=WARN, text_color="#1a1000")
            self.lab.configure(text_color=WARN, font=ctk.CTkFont(size=13, weight="bold"))
        else:
            self.dot.configure(text="", fg_color=CARD_3, text_color=FAINT)
            self.lab.configure(text_color=FAINT, font=ctk.CTkFont(size=13))


class DLSS5FrameGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.lang = ctk.StringVar(value="zh")
        self.gpu_type = None; self.gpu_name = "..."
        self.target_exe = None; self.game_name = None
        self.anticheat = []; self.ac_checked = False; self.installed = False
        self.enable_dlss5 = ctk.BooleanVar(value=True)
        self.enable_fg = ctk.BooleanVar(value=True)
        self.multiplier = ctk.IntVar(value=4)
        self.auto_scroll = ctk.BooleanVar(value=True)
        self.custom_games_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_games.json")
        self.custom_games = self._load_custom_games()
        self._build_ui()
        self._detect_gpu_async()
        self.log("startup", "info")

    def t(self, key):
        return I18N[self.lang.get()].get(key, key)

    def _build_ui(self):
        for w in self.winfo_children(): w.destroy()
        self.title(self.t("app_title"))
        self.geometry("1200x800"); self.minsize(1100, 720)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self._build_sidebar(); self._build_main()

    def _toggle_lang(self):
        new = "en" if self.lang.get() == "zh" else "zh"
        self.lang.set(new); self._build_ui()
        self._apply_gpu_result(); self._refresh_steps()
        if self.target_exe: self.card_game.set(self.game_name, ACCENT)
        if self.anticheat: self.card_ac.set(", ".join(self.anticheat), ERROR)
        elif self.ac_checked: self.card_ac.set(self.t("ac_clean"), ACCENT)
        self.btn_install.configure(text=self.t("installed") if self.installed else self.t("install"))

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, fg_color=SIDEBAR, corner_radius=0, width=240)
        bar.grid(row=0, column=0, sticky="nsw"); bar.grid_propagate(False)
        lb = ctk.CTkFrame(bar, fg_color="transparent")
        lb.pack(padx=20, pady=(28, 0), anchor="w"); lb.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(lb, text="⚡", width=40, height=40, corner_radius=12, fg_color=CARD_2, font=ctk.CTkFont(size=20)).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(lb, text="DLSS 5", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(lb, text=self.t("brand_sub"), font=ctk.CTkFont(size=10), text_color=DIM).grid(row=1, column=1, sticky="nw")
        ctk.CTkFrame(bar, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=(24, 16))
        ctk.CTkLabel(bar, text=self.t("loadout"), font=ctk.CTkFont(size=10, weight="bold"), text_color=FAINT).pack(padx=20, anchor="w")
        self.steps = [SidebarStep(bar, 1, "step1", self), SidebarStep(bar, 2, "step2", self), SidebarStep(bar, 3, "step3", self), SidebarStep(bar, 4, "step4", self)]
        for s in self.steps: s.pack(padx=20, anchor="w", pady=6)
        ctk.CTkButton(bar, text=self.t("lang_btn"), width=60, height=28, fg_color=CARD_2, hover_color=CARD_3, border_width=1, border_color=BORDER, font=ctk.CTkFont(size=12, weight="bold"), command=self._toggle_lang).pack(side="bottom", padx=20, pady=(0, 8), anchor="w")
        self.gpu_badge = ctk.CTkLabel(bar, text=self.t("gpu_badge") + self.gpu_name, font=ctk.CTkFont(size=11), text_color=DIM, anchor="w", wraplength=190, justify="left")
        self.gpu_badge.pack(side="bottom", padx=20, pady=(0, 8), anchor="w")
        ctk.CTkLabel(bar, text=self.t("version"), font=ctk.CTkFont(size=10), text_color=FAINT).pack(side="bottom", padx=20, anchor="w", pady=(0, 12))

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=3); main.grid_rowconfigure(3, weight=2)
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 4)); bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bar, text=self.t("control_center"), font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(bar, text=self.t("subtitle"), font=ctk.CTkFont(size=12), text_color=DIM).grid(row=1, column=0, sticky="w", pady=(2, 0))
        row = ctk.CTkFrame(main, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=28, pady=8)
        for i in range(3): row.grid_columnconfigure(i, weight=1, uniform="st")
        self.card_gpu = StatCard(row, "🎮", "gpu", self); self.card_gpu.grid(row=0, column=0, sticky="nsew", padx=6)
        self.card_game = StatCard(row, "📂", "game", self); self.card_game.grid(row=0, column=1, sticky="nsew", padx=6)
        self.card_ac = StatCard(row, "🛡", "anticheat", self); self.card_ac.grid(row=0, column=2, sticky="nsew", padx=6)
        body = ctk.CTkFrame(main, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=28, pady=8)
        body.grid_columnconfigure(0, weight=1); body.grid_rowconfigure(0, weight=1)
        panel = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RAD_LG, border_width=1, border_color=BORDER)
        panel.grid(row=0, column=0, sticky="nsew"); panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text=self.t("install_config"), font=ctk.CTkFont(size=10, weight="bold"), text_color=FAINT).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))
        row1 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD, border_width=1, border_color=BORDER)
        row1.grid(row=1, column=0, sticky="ew", padx=20, pady=6); row1.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row1, text="🧠  " + self.t("dlss5_render"), font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))
        self.sw_dlss5 = ctk.CTkSwitch(row1, text="", variable=self.enable_dlss5, progress_color=ACCENT, button_color="#ffffff", button_hover_color="#e0e0e0")
        self.sw_dlss5.grid(row=0, column=1, sticky="e", padx=18, pady=(16, 0))
        ctk.CTkLabel(row1, text=self.t("dlss5_desc"), font=ctk.CTkFont(size=11), text_color=DIM, justify="left", wraplength=600).grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 16))
        row2 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD, border_width=1, border_color=BORDER)
        row2.grid(row=2, column=0, sticky="ew", padx=20, pady=6); row2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row2, text="🎞  " + self.t("frame_gen"), font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))
        self.sw_fg = ctk.CTkSwitch(row2, text="", variable=self.enable_fg, progress_color=ACCENT, button_color="#ffffff", button_hover_color="#e0e0e0", command=self._on_fg_toggle)
        self.sw_fg.grid(row=0, column=1, sticky="e", padx=18, pady=(16, 0))
        mult = ctk.CTkFrame(row2, fg_color="transparent")
        mult.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 6)); mult.grid_columnconfigure(0, weight=1)
        self.lbl_mult = ctk.CTkLabel(mult, text="4X", width=56, height=32, corner_radius=8, fg_color="#06281c", text_color=ACCENT, font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_mult.grid(row=0, column=0, sticky="e", pady=(0, 8))
        self.slider = ctk.CTkSlider(mult, from_=1, to=6, number_of_steps=5, variable=self.multiplier, command=self._on_multiplier_change, progress_color=ACCENT, button_color=ACCENT, button_hover_color="#5ff5c4")
        self.slider.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        ticks = ctk.CTkFrame(mult, fg_color="transparent"); ticks.grid(row=2, column=0, sticky="ew")
        for i in range(6):
            ticks.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(ticks, text=f"{i+1}X", font=ctk.CTkFont(size=10), text_color=FAINT).grid(row=0, column=i)
        self.lbl_hint = ctk.CTkLabel(row2, text=self.t("waiting_gpu"), font=ctk.CTkFont(size=11), text_color=FAINT, justify="left", wraplength=620)
        self.lbl_hint.grid(row=3, column=0, columnspan=2, sticky="w", padx=18, pady=(4, 16))
        wrap = ctk.CTkFrame(main, fg_color=CARD, corner_radius=RAD_LG, border_width=1, border_color=BORDER)
        wrap.grid(row=3, column=0, sticky="nsew", padx=28, pady=8)
        wrap.grid_columnconfigure(0, weight=1); wrap.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4)); top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=self.t("run_log"), font=ctk.CTkFont(size=10, weight="bold"), text_color=FAINT).grid(row=0, column=0, sticky="w")
        ctk.CTkSwitch(top, text=self.t("auto_scroll"), variable=self.auto_scroll, progress_color=ACCENT, font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=(8, 8))
        ctk.CTkButton(top, text=self.t("clear"), width=56, height=26, fg_color=CARD_3, hover_color=CARD_2, font=ctk.CTkFont(size=11, weight="bold"), command=self._clear_log).grid(row=0, column=2)
        self.log_box = ctk.CTkTextbox(wrap, fg_color="#06090e", text_color=TEXT, font=ctk.CTkFont(family="Consolas", size=12), corner_radius=8, wrap="word", border_width=0)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self.log_box.configure(state="disabled")
        tb = self.log_box._textbox
        tb.tag_config("info", foreground=DIM); tb.tag_config("success", foreground=ACCENT)
        tb.tag_config("warn", foreground=WARN); tb.tag_config("error", foreground=ERROR); tb.tag_config("step", foreground=ACCENT_2)
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", padx=28, pady=(8, 24))
        left = ctk.CTkFrame(bar, fg_color="transparent"); left.grid(row=0, column=0, sticky="w")
        bs = dict(fg_color=CARD_2, hover_color=CARD_3, border_width=1, border_color=BORDER, font=ctk.CTkFont(size=13, weight="bold"), height=44, corner_radius=10)
        ctk.CTkButton(left, text=self.t("scan_lib"), width=130, **bs, command=self._scan_library).pack(side="left", padx=(0, 6))
        ctk.CTkButton(left, text=self.t("add_game"), width=110, **bs, command=self._add_custom_game).pack(side="left", padx=(0, 6))
        ctk.CTkButton(left, text=self.t("browse_exe"), width=120, **bs, command=self._pick_exe).pack(side="left")
        right = ctk.CTkFrame(bar, fg_color="transparent"); right.grid(row=0, column=1, sticky="e")
        self.btn_restore = ctk.CTkButton(right, text=self.t("restore"), width=100, height=44, fg_color=CARD_2, hover_color=CARD_3, border_width=1, border_color=WARN, font=ctk.CTkFont(size=13, weight="bold"), corner_radius=10, command=self._restore_files)
        self.btn_restore.pack(side="left", padx=(0, 10))
        self.btn_install = ctk.CTkButton(right, text=self.t("install"), width=160, height=44, fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#02120a", font=ctk.CTkFont(size=14, weight="bold"), corner_radius=10, command=self._install)
        self.btn_install.pack(side="left")

    def log(self, msg_or_key, level="info", **fmt):
        if msg_or_key in I18N["zh"] or msg_or_key in I18N["en"]:
            msg = self.t(msg_or_key)
            if fmt: msg = msg.format(**fmt)
        else:
            msg = msg_or_key
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box._textbox.insert("end", f"[{ts}]  {msg}\n", level)
        self.log_box.configure(state="disabled")
        if self.auto_scroll.get(): self.log_box.see("end")

    def _clear_log(self):
        self.log_box.configure(state="normal"); self.log_box.delete("1.0", "end"); self.log_box.configure(state="disabled")

    def _detect_gpu_async(self):
        threading.Thread(target=self._detect_gpu_worker, daemon=True).start()

    def _detect_gpu_worker(self):
        gpu_name = None; gpu_type = None
        try:
            import wmi; c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                name = (gpu.Name or "").strip()
                if not name: continue
                if re.search(r"RTX\s*20[678]0", name, re.I): gpu_name = name; gpu_type = "SM75"; break
                if re.search(r"RTX\s*30[6789]0", name, re.I): gpu_name = name; gpu_type = "SM86"; break
                if "RTX" in name.upper() and not gpu_name: gpu_name = name
        except Exception:
            try:
                out = subprocess.check_output(["cmd", "/c", "wmic", "path", "win32_VideoController", "get", "name"], stderr=subprocess.DEVNULL, timeout=10).decode("gbk", errors="ignore")
                for line in out.splitlines():
                    line = line.strip()
                    if "RTX" in line.upper() and "Name" not in line:
                        gpu_name = line
                        if re.search(r"RTX\s*20", line): gpu_type = "SM75"
                        elif re.search(r"RTX\s*30", line): gpu_type = "SM86"
                        break
            except Exception: pass
        self.gpu_name = gpu_name or self.t("no_supported_gpu")
        self.gpu_type = gpu_type
        self.after(0, self._apply_gpu_result)

    def _apply_gpu_result(self):
        if self.gpu_type == "SM86":
            self.card_gpu.set(self.gpu_name, ACCENT)
            self.gpu_badge.configure(text="✅ " + self.gpu_name)
            self.slider.configure(to=6, number_of_steps=5)
            if self.multiplier.get() > 6: self.multiplier.set(6)
            self.lbl_hint.configure(text=self.t("rtx30_ok"), text_color=ACCENT)
            self.log("gpu_detected", "success")
        elif self.gpu_type == "SM75":
            self.card_gpu.set(self.gpu_name, WARN)
            self.gpu_badge.configure(text="⚠ " + self.gpu_name)
            self.slider.configure(to=4, number_of_steps=3)
            if self.multiplier.get() > 4: self.multiplier.set(4)
            self.lbl_hint.configure(text=self.t("rtx20_warn"), text_color=WARN)
            self.log("gpu_detected", "warn")
        else:
            self.card_gpu.set(self.t("no_supported_gpu"), ERROR)
            self.gpu_badge.configure(text="❌ " + self.t("no_supported_gpu"))
            self.lbl_hint.configure(text=self.t("gpu_error"), text_color=ERROR)
            self.log("gpu_not_found", "error")
        self._refresh_steps()

    def _on_fg_toggle(self):
        self.slider.configure(state="normal" if self.enable_fg.get() else "disabled")
        self.lbl_mult.configure(text_color=ACCENT if self.enable_fg.get() else FAINT)

    def _on_multiplier_change(self, value):
        v = int(round(value)); self.multiplier.set(v); self.lbl_mult.configure(text=f"{v}X")

    def _refresh_steps(self):
        gpu = self.gpu_type is not None; game = self.target_exe is not None
        ac = self.ac_checked; inst = self.installed
        self.steps[0].set_state("done" if gpu else "active")
        self.steps[1].set_state("done" if game else ("active" if gpu else "pending"))
        if self.anticheat: self.steps[2].set_state("blocked")
        elif ac: self.steps[2].set_state("done")
        else: self.steps[2].set_state("active" if game else "pending")
        self.steps[3].set_state("done" if inst else ("active" if gpu and game and ac and not self.anticheat else "pending"))

    def _scan_library(self):
        self.log("scan_start", "step")
        def worker():
            candidates = []
            try:
                steam_path = None
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
                    steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
                    winreg.CloseKey(key)
                except Exception: pass
                if steam_path:
                    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                    if os.path.exists(vdf):
                        with open(vdf, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
                        paths = re.findall(r'"path"\s*"([^"]+)"', content)
                        for p in paths:
                            p = p.replace("\\\\", "\\")
                            apps_dir = os.path.join(p, "steamapps", "common")
                            if os.path.isdir(apps_dir):
                                for game in os.listdir(apps_dir):
                                    gd = os.path.join(apps_dir, game)
                                    if os.path.isdir(gd):
                                        for item in os.listdir(gd):
                                            if item.lower().endswith(".exe") and "uninst" not in item.lower() and "redist" not in item.lower():
                                                candidates.append((game, os.path.join(gd, item))); break
            except Exception as e:
                self.after(0, lambda: self.log(f"Steam scan error: {e}", "warn"))
            try:
                epic_manifests = os.path.expandvars(r"%ProgramData%\Epic\EpicGamesLauncher\Data\Manifests")
                if os.path.isdir(epic_manifests):
                    for mf in os.listdir(epic_manifests):
                        if mf.endswith(".item"):
                            try:
                                with open(os.path.join(epic_manifests, mf), "r", encoding="utf-8") as f: data = json.load(f)
                                name = data.get("DisplayName", ""); install = data.get("InstallLocation", ""); exe = data.get("LaunchExecutable", "")
                                if name and install and exe:
                                    full = os.path.join(install, exe)
                                    if os.path.exists(full): candidates.append((name, full))
                            except Exception: pass
            except Exception: pass
            if candidates:
                self.after(0, lambda: self.log("scan_done", "success", n=len(candidates)))
                name, path = candidates[0]
                self.target_exe = path; self.game_name = name
                self.after(0, lambda: self.card_game.set(name, ACCENT))
                self.after(0, lambda: self.log("auto_selected", "info"))
                self.after(0, self._detect_anticheat_async)
            else:
                self.after(0, lambda: self.log("scan_none", "warn"))
            self.after(0, self._refresh_steps)
        threading.Thread(target=worker, daemon=True).start()

    def _load_custom_games(self):
        try:
            if os.path.exists(self.custom_games_file):
                with open(self.custom_games_file, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: pass
        return []

    def _save_custom_games(self):
        try:
            with open(self.custom_games_file, "w", encoding="utf-8") as f: json.dump(self.custom_games, f, ensure_ascii=False, indent=2)
        except Exception: pass

    def _add_custom_game(self):
        path = filedialog.askopenfilename(title="Select game EXE", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if not path: return
        for g in self.custom_games:
            if g.get("path", "").lower() == path.lower():
                messagebox.showinfo(self.t("game_exists_title"), self.t("game_exists")); return
        default_name = os.path.splitext(os.path.basename(path))[0]
        self.custom_games.append({"name": default_name, "path": path})
        self._save_custom_games()
        self.log("game_added", "success")
        self.target_exe = path; self.game_name = default_name
        self.card_game.set(default_name, ACCENT)
        self._detect_anticheat_async()

    def _pick_exe(self):
        path = filedialog.askopenfilename(title="Select game renderer EXE", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if not path: return
        self.target_exe = path
        self.game_name = os.path.basename(path)
        self.card_game.set(self.game_name, ACCENT)
        self.log("target", "success")
        self._detect_anticheat_async()

    def _detect_anticheat_async(self):
        def worker():
            self.after(0, lambda: self.card_ac.set(self.t("ac_scanning"), DIM))
            time.sleep(0.3)
            found = []; game_dir = os.path.dirname(self.target_exe)
            ac_patterns = [("EasyAntiCheat", "EasyAntiCheat"), ("BattlEye", "BattlEye"),
                            ("Riot Vanguard", "vgc.exe"), ("EOS Online", "EOSSDK-Win64-Shipping.exe"),
                            ("PunkBuster", "pbclient"), ("nProtect", "npgg")]
            try:
                for root, dirs, files in os.walk(game_dir):
                    depth = root.replace(game_dir, "").count(os.sep)
                    if depth > 2: dirs[:] = []; continue
                    for d in dirs:
                        for label, pat in ac_patterns:
                            if pat.lower() in d.lower() and label not in found: found.append(label)
                    for fn in files:
                        for label, pat in ac_patterns:
                            if pat.lower() in fn.lower() and label not in found: found.append(label)
            except Exception: pass
            self.anticheat = found; self.ac_checked = True
            if found:
                names = ", ".join(found)
                self.after(0, lambda: self.card_ac.set(names, ERROR))
                self.after(0, lambda: self.log("ac_found", "error"))
                self.after(0, lambda: self.btn_install.configure(state="disabled"))
            else:
                self.after(0, lambda: self.card_ac.set(self.t("ac_clean"), ACCENT))
                self.after(0, lambda: self.log("ac_passed", "success"))
                self.after(0, lambda: self.btn_install.configure(state="normal"))
            self.after(0, self._refresh_steps)
        threading.Thread(target=worker, daemon=True).start()

    def _install(self):
        if not self.target_exe:
            messagebox.showwarning(self.t("no_game_title"), self.t("no_game")); return
        if not self.gpu_type:
            messagebox.showerror(self.t("gpu_unsup_title"), self.t("gpu_unsupported")); return
        if self.anticheat:
            messagebox.showerror(self.t("risk_title"), f"{self.t('risk_blocked')}: {', '.join(self.anticheat)}"); return
        if self.gpu_type == "SM75":
            if not messagebox.askyesno(self.t("experimental"), self.t("experimental_msg")): return
        self.btn_install.configure(state="disabled", text=self.t("working"))
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        game_dir = os.path.dirname(self.target_exe)
        mult = self.multiplier.get()
        tmp = tempfile.mkdtemp(prefix="dlss5_")
        bundled = self._resource_path("OptiScaler_v0.9.4_full.7z")
        archive_path = os.path.join(tmp, "optiscaler.7z")
        if os.path.exists(bundled):
            self.after(0, lambda: self.log("bundled_found", "success"))
            shutil.copy2(bundled, archive_path)
        else:
            self.after(0, lambda: self.log("bundled_missing", "step"))
            try:
                urllib.request.urlretrieve(OPTISCALER_URL, archive_path)
                self.after(0, lambda: self.log("download_done", "success"))
            except Exception as e:
                self.after(0, lambda: self.log(f"{self.t('download_fail')}: {e}", "error"))
                self.after(0, self._on_install_failed); return
        self.after(0, lambda: self.log("extracting", "step"))
        extract_dir = os.path.join(tmp, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        seven_zip = self._resource_path("7zr.exe")
        if not os.path.exists(seven_zip):
            seven_zip = os.path.join(tmp, "7zr.exe")
            try:
                urllib.request.urlretrieve("https://www.7-zip.org/a/7zr.exe", seven_zip)
            except Exception as e:
                self.after(0, lambda: self.log(f"7zr.exe download failed: {e}", "error"))
                self.after(0, self._on_install_failed); return
        try:
            result = subprocess.run([seven_zip, "x", "-y", f"-o{extract_dir}", archive_path], capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(result.stderr[-500:] if result.stderr else "7zr failed")
            self.after(0, lambda: self.log("extract_done", "success"))
        except Exception as e:
            self.after(0, lambda: self.log(f"{self.t('extract_fail')}: {e}", "error"))
            self.after(0, self._on_install_failed); return
        time.sleep(0.2)
        self.after(0, lambda: self.log("backup", "step"))
        backup_dir = os.path.join(game_dir, ".dlss5_backup")
        os.makedirs(backup_dir, exist_ok=True)
        for fname in ["dxgi.dll", "version.dll", "nvngx_dlss.dll", "nvngx_dlssnr.dll", "OptiScaler.ini"]:
            src = os.path.join(game_dir, fname)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(backup_dir, fname))
        self.after(0, lambda: self.log("deploying", "step"))
        deployed = 0
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                src = os.path.join(root, f); rel = os.path.relpath(src, extract_dir)
                low = f.lower()
                if low.startswith("readme") or low.startswith("license") or low.startswith("setup_"): continue
                dst = os.path.join(game_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if low == "optiscaler.dll":
                    shutil.copy2(src, os.path.join(game_dir, "dxgi.dll"))
                else:
                    shutil.copy2(src, dst)
                deployed += 1
        if deployed == 0:
            self.after(0, lambda: self.log("extract_fail", "error"))
            self.after(0, self._on_install_failed); return
        self.after(0, lambda: self.log("deployed", "success", n=deployed))
        self.after(0, lambda: self.log("deploy_injector", "info"))
        self.after(0, lambda: self.log("writing_ini", "step", mult=mult))
        ini_path = os.path.join(game_dir, "OptiScaler.ini")
        if not os.path.exists(ini_path):
            self.after(0, lambda: self.log("OptiScaler.ini missing", "error"))
            self.after(0, self._on_install_failed); return
        try:
            with open(ini_path, "r", encoding="utf-8") as f: lines = f.readlines()
            interp = max(1, min(3, mult - 1))
            patches = {
                ("FrameGen", "Enabled"): "true",
                ("FrameGen", "FGInput"): "fsrfg",
                ("FrameGen", "FGOutput"): "fsrfg",
                ("Menu", "OverlayMenu"): "true",
                ("Menu", "ShowFps"): "true",
                ("XeFG", "InterpolationCount"): str(interp),
                ("Hotfix", "DisableOverlays"): "true",
            }
            current_section = None; out = []; patched = set()
            for line in lines:
                stripped = line.strip()
                m = re.match(r"^\[(.+)\]\s*$", stripped)
                if m:
                    current_section = m.group(1); out.append(line); continue
                kv = re.match(r"^([^=;]+)=(.*)$", stripped)
                if kv and current_section:
                    key = kv.group(1).strip()
                    if (current_section, key) in patches:
                        out.append(f"{key}={patches[(current_section, key)]}\n")
                        patched.add((current_section, key)); continue
                out.append(line)
            for (sec, key), val in patches.items():
                if (sec, key) not in patched:
                    out.append(f"\n[{sec}]\n{key}={val}\n")
            with open(ini_path, "w", encoding="utf-8") as f: f.writelines(out)
            self.after(0, lambda: self.log("ini_done", "success"))
        except Exception as e:
            self.after(0, lambda: self.log(f"ini patch failed: {e}", "error"))
            self.after(0, self._on_install_failed); return
        shutil.rmtree(tmp, ignore_errors=True)
        self.after(0, self._on_install_done)

    def _on_install_failed(self):
        self.btn_install.configure(state="normal", text=self.t("install"))
        self.log("install_failed", "error")

    def _resource_path(self, relative):
        if hasattr(sys, "_MEIPASS"): return os.path.join(sys._MEIPASS, relative)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)

    def _on_install_done(self):
        self.installed = True
        self.btn_install.configure(state="normal", text=self.t("installed"))
        self.btn_restore.configure(state="normal")
        self.log("install_complete", "success"); self.log("install_tip", "info")
        self._refresh_steps()

    def _restore_files(self):
        if not self.target_exe:
            messagebox.showwarning(self.t("no_game_title"), self.t("no_game")); return
        game_dir = os.path.dirname(self.target_exe)
        backup_dir = os.path.join(game_dir, ".dlss5_backup")
        if not os.path.isdir(backup_dir):
            messagebox.showinfo(self.t("no_backup_title"), self.t("no_backup")); return
        if not messagebox.askyesno(self.t("restore_title"), self.t("restore_msg")): return
        self.log("restore_start", "step")
        deployed_files = ["dxgi.dll", "OptiScaler.ini", "fakenvapi.dll", "fakenvapi.ini",
                         "amd_fidelityfx_dx12.dll", "amd_fidelityfx_framegeneration_dx12.dll",
                         "amd_fidelityfx_upscaler_dx12.dll", "amd_fidelityfx_vk.dll",
                         "dlssg_to_fsr3_amd_is_better.dll",
                         "libxell.dll", "libxess.dll", "libxess_dx11.dll", "libxess_fg.dll"]
        for fname in deployed_files:
            p = os.path.join(game_dir, fname)
            if os.path.exists(p):
                os.remove(p)
                self.log(f"  {self.t('removed')}: {fname}", "info")
        d3d12_dir = os.path.join(game_dir, "D3D12_Optiscaler")
        if os.path.isdir(d3d12_dir):
            shutil.rmtree(d3d12_dir)
            self.log("  Removed: D3D12_Optiscaler/", "info")
        restored = 0
        for f in os.listdir(backup_dir):
            shutil.copy2(os.path.join(backup_dir, f), os.path.join(game_dir, f))
            restored += 1
        shutil.rmtree(backup_dir)
        self.log("restore_done", "success", n=restored)
        self.installed = False
        self.btn_install.configure(text=self.t("install"))
        self._refresh_steps()


if __name__ == "__main__":
    app = DLSS5FrameGenApp()
    app.mainloop()
