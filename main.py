"""程序入口；桌面图标打开编辑窗口，开机启动只显示悬浮球。"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="班级作业记录")
    parser.add_argument("--startup", action="store_true", help="仅显示悬浮球")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("此应用需要 Windows 10 或 Windows 11。")

    import tkinter as tk
    from tkinter import messagebox

    from homework_memo import windows
    from homework_memo.ui import App

    windows.enable_dpi()
    instance = windows.SingleInstance()
    try:
        if instance.existing:
            if not args.startup:
                instance.notify()
            return
        root = tk.Tk()
        root.withdraw()
        data_directory = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HomeworkMemo"
        try:
            data_directory.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                handlers=[RotatingFileHandler(data_directory / "application.log", maxBytes=500_000,
                                              backupCount=2, encoding="utf-8")],
                level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
            )
            base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
            App(root, data_directory, base / "作业.docx", instance, startup=args.startup)
        except Exception as error:
            logging.exception("程序启动失败")
            messagebox.showerror("无法启动作业记录", str(error), parent=root)
            root.destroy()
            return
        root.mainloop()
    finally:
        instance.close()


if __name__ == "__main__":
    main()
