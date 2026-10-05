# DLSS 5 + 帧生成 一键装载工具

为 RTX 20 / 30 系显卡注入 DLSS 5 神经渲染与多帧生成（1~6X）的可视化工具。

## 功能
- 自动检测显卡（SM75 / SM86）
- 选择游戏 EXE，自动检测反作弊
- 一键装载 / 还原
- 可视化运行日志

## 本地运行
```bash
pip install customtkinter pillow
python DLSS5_FrameGen_Tool.py
```

## 打包成 EXE
在 Windows 上双击 `build_exe.bat`，自动生成 `dist\DLSS5_FrameGen_Tool.exe`。

## 网站
开启 GitHub Pages 后，访问 `https://DANK1NG-zzlt.github.io/dlss5-framegen-tool/` 即可看到下载页。

> 仅供学习交流，不官方、与 NVIDIA 无关。