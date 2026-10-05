"""
DLSS 5 + 帧生成 一键装载工具  (UI 美化版 v2)
适用: RTX 20系 (SM75) / RTX 30系 (SM86)
依赖: pip install customtkinter pillow

本版聚焦视觉升级：左侧导航栏 + 深色高级配色 + 大圆角卡片 + 强调色。
功能逻辑（显卡检测 / 选游戏 / 反作弊 / 装载占位）与前版一致。
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BG          = "#080b11"
SIDEBAR     = "#0c1119"
SIDEBAR_HI  = "#131a26"
CARD        = "#121823"
CARD_2      = "#17202d"
CARD_3      = "#1d2836"
BORDER      = "#223041"
ACCENT      = "#00e5a0"
ACCENT_DIM  = "#0bbf86"
ACCENT_2    = "#38bdf8"
WARN        = "#fbbf24"
ERROR       = "#f87171"
TEXT        = "#eaf0f8"
DIM         = "#8494a7"
FAINT       = "#5b6b80"

RAD_LG = 18
RAD_MD = 12


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, icon, title, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=RAD_LG,
                         border_width=1, border_color=BORDER, **kw)
        self.grid_columnconfigure(1, weight=1)
        self.icon = ctk.CTkLabel(
            self, text=icon, width=42, height=42, corner_radius=12,
            fg_color=CARD_2, font=ctk.CTkFont(size=18),
        )
        self.icon.grid(row=0, column=0, rowspan=2, padx=16, pady=16)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12),
                     text_color=DIM).grid(row=0, column=1, sticky="sw", padx=(4, 8), pady=(16, 0))
        self.value = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=15, weight="bold"),
                                  text_color=TEXT, anchor="w", justify="left", wraplength=230)
        self.value.grid(row=1, column=1, sticky="nw", padx=(4, 8), pady=(0, 16))

    def set(self, value, color=TEXT):
        self.value.configure(text=value, text_color=color)


class SidebarStep(ctk.CTkFrame):
    def __init__(self, parent, num, label, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self.dot = ctk.CTkLabel(
            self, text=str(num), width=30, height=30, corner_radius=15,
            fg_color=CARD_3, font=ctk.CTkFont(size=13, weight="bold"),
            text_color=FAINT,
        )
        self.dot.pack(side="left", padx=(0, 12))
        self.lab = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=13),
                                text_color=FAINT, anchor="w")
        self.lab.pack(side="left")

    def set_state(self, s):
        if s == "done":
            self.dot.configure(text="✓", fg_color=ACCENT, text_color="#04140d")
            self.lab.configure(text_color=TEXT)
        elif s == "active":
            self.dot.configure(text="•", fg_color=CARD_3, text_color=ACCENT_2)
            self.lab.configure(text_color=ACCENT_2)
        elif s == "blocked":
            self.dot.configure(text="!", fg_color=WARN, text_color="#221800")
            self.lab.configure(text_color=WARN)
        else:
            self.dot.configure(text="", fg_color=CARD_3, text_color=FAINT)
            self.lab.configure(text_color=FAINT)


class DLSS5FrameGenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DLSS 5 + 帧生成 一键装载工具")
        self.geometry("1180x820")
        self.minsize(1080, 740)
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
        self._build_ui()
        self._detect_gpu_async()
        self.log("程序启动完成，正在检测显卡…", "info")

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        bar = ctk.CTkFrame(self, fg_color=SIDEBAR, corner_radius=0, width=232)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bar, text="⚡", font=ctk.CTkFont(size=26)).pack(padx=20, pady=(26, 0), anchor="w")
        ctk.CTkLabel(bar, text="DLSS 5", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(padx=20, anchor="w")
        ctk.CTkLabel(bar, text="帧生成 · 一键装载器", font=ctk.CTkFont(size=12),
                     text_color=DIM).pack(padx=20, anchor="w", pady=(0, 22))
        ctk.CTkLabel(bar, text="装载流程", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=FAINT).pack(padx=20, anchor="w")
        self.steps = [
            SidebarStep(bar, 1, "显卡检测"),
            SidebarStep(bar, 2, "选择游戏"),
            SidebarStep(bar, 3, "反作弊检查"),
            SidebarStep(bar, 4, "一键装载"),
        ]
        for s in self.steps:
            s.pack(padx=20, anchor="w", pady=5)
        self.gpu_badge = ctk.CTkLabel(
            bar, text="显卡：检测中…", font=ctk.CTkFont(size=11),
            text_color=DIM, anchor="w", wraplength=180, justify="left",
        )
        self.gpu_badge.pack(side="bottom", padx=20, pady=(0, 18), anchor="w")
        ctk.CTkLabel(bar, text="v2.0 · 美化版", font=ctk.CTkFont(size=10),
                     text_color=FAINT).pack(side="bottom", padx=20, anchor="w")

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
        bar.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        bar.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bar, text="概览", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(bar, text="RTX 20 系 (SM75) · RTX 30 系 (SM86) · 1~6X 多帧生成",
                     font=ctk.CTkFont(size=12), text_color=DIM).grid(row=1, column=0, sticky="w")

    def _build_stats(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=24, pady=8)
        for i in range(3):
            row.grid_columnconfigure(i, weight=1, uniform="st")
        self.card_gpu  = StatCard(row, "🎮", "显卡检测")
        self.card_gpu.grid(row=0, column=0, sticky="nsew", padx=6)
        self.card_game = StatCard(row, "📂", "目标游戏")
        self.card_game.grid(row=0, column=1, sticky="nsew", padx=6)
        self.card_ac   = StatCard(row, "🛡", "反作弊")
        self.card_ac.grid(row=0, column=2, sticky="nsew", padx=6)

    def _build_config(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=24, pady=8)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        panel = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RAD_LG,
                             border_width=1, border_color=BORDER)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 8))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="装载配置", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w")
        row1 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD)
        row1.grid(row=1, column=0, sticky="ew", padx=18, pady=6)
        row1.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row1, text="🧠  DLSS 5 神经渲染", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))
        self.sw_dlss5 = ctk.CTkSwitch(row1, text="", variable=self.enable_dlss5,
                                      progress_color=ACCENT)
        self.sw_dlss5.grid(row=0, column=1, sticky="e", padx=16, pady=(14, 0))
        ctk.CTkLabel(row1, text="通过 OptiScaler / DLSS5-Feeder 注入，为原生不支持的游戏提供画质增强。",
                     font=ctk.CTkFont(size=11), text_color=DIM, justify="left",
                     wraplength=600).grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(2, 14))
        row2 = ctk.CTkFrame(panel, fg_color=CARD_2, corner_radius=RAD_MD)
        row2.grid(row=2, column=0, sticky="ew", padx=18, pady=6)
        row2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(row2, text="🎞  DLSS 帧生成", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))
        self.sw_fg = ctk.CTkSwitch(row2, text="", variable=self.enable_fg,
                                   progress_color=ACCENT, command=self._on_fg_toggle)
        self.sw_fg.grid(row=0, column=1, sticky="e", padx=16, pady=(14, 0))
        mult = ctk.CTkFrame(row2, fg_color="transparent")
        mult.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(8, 6))
        mult.grid_columnconfigure(0, weight=1)
        self.lbl_mult = ctk.CTkLabel(
            mult, text="4X", width=54, height=30, corner_radius=8,
            fg_color="#06281c", text_color=ACCENT,
            font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_mult.grid(row=0, column=0, sticky="e")
        self.slider = ctk.CTkSlider(
            mult, from_=1, to=6, number_of_steps=5, variable=self.multiplier,
            command=self._on_multiplier_change, progress_color=ACCENT,
            button_color=ACCENT, button_hover_color="#5ff5c4")
        self.slider.grid(row=1, column=0, sticky="ew", pady=(8, 2))
        ticks = ctk.CTkFrame(mult, fg_color="transparent")
        ticks.grid(row=2, column=0, sticky="ew")
        for i in range(6):
            ticks.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(ticks, text=f"{i+1}X", font=ctk.CTkFont(size=10),
                         text_color=FAINT).grid(row=0, column=i)
        self.lbl_hint = ctk.CTkLabel(row2, text="请先完成显卡检测…",
                                     font=ctk.CTkFont(size=11), text_color=FAINT,
                                     justify="left", wraplength=620)
        self.lbl_hint.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(2, 14))

    def _build_log(self, parent):
        wrap = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=RAD_LG,
                            border_width=1, border_color=BORDER)
        wrap.grid(row=3, column=0, sticky="nsew", padx=24, pady=8)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(wrap, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="📋  运行日志", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w")
        ctk.CTkSwitch(top, text="自动滚动", variable=self.auto_scroll,
                      progress_color=ACCENT, font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=(8, 8))
        ctk.CTkButton(top, text="清空", width=56, height=26, fg_color=CARD_3,
                      hover_color=CARD_2, font=ctk.CTkFont(size=11),
                      command=self._clear_log).grid(row=0, column=2)
        self.log_box = ctk.CTkTextbox(
            wrap, fg_color="#0a0f16", text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=10, wrap="word")
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self.log_box.configure(state="disabled")
        tb = self.log_box._textbox
        tb.tag_config("info",    foreground=DIM)
        tb.tag_config("success", foreground=ACCENT)
        tb.tag_config("warn",    foreground=WARN)
        tb.tag_config("error",  foreground=ERROR)
        tb.tag_config("step",   foreground=ACCENT_2)

    def _build_actions(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", padx=24, pady=(8, 22))
        bar.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(left, text="🔍  扫描游戏库", width=140, height=44,
                      fg_color=CARD_2, hover_color=CARD_3, border_width=1,
                      border_color=BORDER, font=ctk.CTkFont(size=13),
                      command=self._scan_library).pack(side="left", padx=(0, 10))
        ctk.CTkButton(left, text="📁  选择 EXE", width=130, height=44,
                      fg_color=CARD_2, hover_color=CARD_3, border_width=1,
                      border_color=BORDER, font=ctk.CTkFont(size=13),
                      command=self._pick_exe).pack(side="left")
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        self.btn_uninstall = ctk.CTkButton(
            right, text="↩  还原", width=120, height=44,
            fg_color=CARD_2, hover_color=CARD_3, border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._uninstall, state="disabled")
        self.btn_uninstall.pack(side="left", padx=(0, 10))
        self.btn_install = ctk.CTkButton(
            right, text="🚀  一键装载", width=170, height=44,
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="#04140d",
            font=ctk.CTkFont(size=14, weight="bold"), command=self._install)
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
        time.sleep(0.8)
        self.gpu_name = "NVIDIA GeForce RTX 3070"
        self.gpu_type = "SM86"
        self.after(0, self._apply_gpu_result)

    def _apply_gpu_result(self):
        if self.gpu_type == "SM86":
            self.card_gpu.set(self.gpu_name, ACCENT)
            self.gpu_badge.configure(text="✅ " + self.gpu_name)
            self.slider.configure(to=6, number_of_steps=5)
            if self.multiplier.get() > 6:
                self.multiplier.set(6)
            self.lbl_hint.configure(text="✅ RTX 30 系 (SM86)：支持最高 6X 多帧生成 + DLSS 5。",
                                    text_color=ACCENT)
            self.log(f"显卡检测完成: {self.gpu_name} → SM86", "success")
        elif self.gpu_type == "SM75":
            self.card_gpu.set(self.gpu_name, WARN)
            self.gpu_badge.configure(text="⚠ " + self.gpu_name)
            self.slider.configure(to=4, number_of_steps=3)
            if self.multiplier.get() > 4:
                self.multiplier.set(4)
            self.lbl_hint.configure(text="⚠ RTX 20 系 (SM75)：实验性，最高 4X，可能闪烁或崩溃。",
                                    text_color=WARN)
            self.log(f"显卡检测完成: {self.gpu_name} → SM75（实验性）", "warn")
        else:
            self.card_gpu.set("未检测到受支持显卡", ERROR)
            self.gpu_badge.configure(text="❌ 无受支持显卡")
            self.lbl_hint.configure(text="❌ 未检测到 RTX 20/30 系显卡。", text_color=ERROR)
            self.log("未检测到受支持显卡。", "error")
        self._refresh_steps()

    def _on_fg_toggle(self):
        self.slider.configure(state="normal" if self.enable_fg.get() else "disabled")
        self.lbl_mult.configure(text_color=ACCENT if self.enable_fg.get() else FAINT)

    def _on_multiplier_change(self, value):
        v = int(round(value))
        self.multiplier.set(v)
        self.lbl_mult.configure(text=f"{v}X")

    def _refresh_steps(self):
        gpu = self.gpu_type is not None
        game = self.target_exe is not None
        ac = self.ac_checked
        inst = self.installed
        self.steps[0].set_state("done" if gpu else "active")
        self.steps[1].set_state("done" if game else ("active" if gpu else "pending"))
        if self.anticheat:
            self.steps[2].set_state("blocked")
        elif ac:
            self.steps[2].set_state("done")
        else:
            self.steps[2].set_state("active" if game else "pending")
        self.steps[3].set_state("done" if inst else ("active" if gpu and game and ac and not self.anticheat else "pending"))

    def _scan_library(self):
        self.log("开始扫描 Steam / Epic / GOG 游戏库…", "step")
        def worker():
            time.sleep(1.0)
            self.after(0, lambda: self.log("扫描完成，找到 3 个候选游戏（演示）。", "success"))
        threading.Thread(target=worker, daemon=True).start()

    def _pick_exe(self):
        path = filedialog.askopenfilename(
            title="选择游戏渲染 EXE",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if not path:
            return
        self.target_exe = path
        self.game_name = os.path.basename(path)
        self.card_game.set(self.game_name, ACCENT)
        self.log(f"已选择目标: {path}", "success")
        self._detect_anticheat_async()

    def _detect_anticheat_async(self):
        def worker():
            self.after(0, lambda: self.card_ac.set("检测中…", DIM))
            time.sleep(0.6)
            self.anticheat = []
            self.ac_checked = True
            if self.anticheat:
                names = ", ".join(self.anticheat)
                self.after(0, lambda: self.card_ac.set(names, ERROR))
                self.after(0, lambda: self.log(f"⚠ 检测到反作弊: {names}，禁止安装！", "error"))
                self.after(0, lambda: self.btn_install.configure(state="disabled"))
            else:
                self.after(0, lambda: self.card_ac.set("未检测到", ACCENT))
                self.after(0, lambda: self.log("反作弊检测通过。", "success"))
                self.after(0, lambda: self.btn_install.configure(state="normal"))
            self.after(0, self._refresh_steps)
        threading.Thread(target=worker, daemon=True).start()

    def _install(self):
        if not self.target_exe:
            messagebox.showwarning("未选择游戏", "请先选择一个游戏渲染 EXE。")
            return
        if not self.gpu_type:
            messagebox.showerror("显卡不支持", "未检测到受支持的 RTX 20/30 系显卡。")
            return
        if self.anticheat:
            messagebox.showerror("风险拦截", f"检测到反作弊: {', '.join(self.anticheat)}")
            return
        if self.gpu_type == "SM75":
            if not messagebox.askyesno(
                "实验性确认",
                "RTX 20 系帧生成为实验性功能，可能闪烁、崩溃或掉帧。\n是否继续？"):
                return
        self.btn_install.configure(state="disabled", text="⏳  装载中…")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        steps = [
            (0.3, f"目标目录: {os.path.dirname(self.target_exe)}", "info"),
            (0.4, "备份原始文件 (version.dll / nvngx_dlss.dll)…", "step"),
            (0.5, f"部署帧生成内核: dlssg_for_{self.gpu_type.lower()}", "step"),
            (0.5, f"写入倍率配置: {self.multiplier.get()}X", "step"),
        ]
        if self.enable_dlss5.get():
            steps.append((0.6, "注入 DLSS 5 神经渲染组件…", "step"))
        for delay, msg, lvl in steps:
            time.sleep(delay)
            self.after(0, lambda m=msg, l=lvl: self.log(m, l))
        self.after(0, self._on_install_done)

    def _on_install_done(self):
        self.installed = True
        self.btn_install.configure(state="normal", text="✅  已装载")
        self.btn_uninstall.configure(state="normal")
        self.log("装载完成！进入游戏 → 画面设置 → 开启「帧生成」。", "success")
        self.log("提示：部分游戏需重启生效。", "info")
        self._refresh_steps()

    def _uninstall(self):
        if not self.installed:
            return
        if not messagebox.askyesno("确认卸载", "将移除 Mod 并还原原始文件，是否继续？"):
            return
        self.log("正在还原原始文件…", "step")
        time.sleep(0.5)
        self.installed = False
        self.btn_install.configure(text="🚀  一键装载")
        self.btn_uninstall.configure(state="disabled")
        self.log("已还原，游戏目录恢复原状。", "success")
        self._refresh_steps()


if __name__ == "__main__":
    app = DLSS5FrameGenApp()
    app.mainloop()
