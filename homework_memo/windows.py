"""Windows 工作区、自启、窗口层级与单实例接口。"""
from __future__ import annotations
import ctypes
import os
import subprocess
import sys
import uuid
import winreg
from ctypes import wintypes as wt
from pathlib import Path

APP_NAME = "HomeworkMemo"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
ole32 = ctypes.WinDLL("ole32")

def _declare(library, name, arguments, result):
    function = getattr(library, name)
    function.argtypes = arguments
    function.restype = result
    return function

_declare(user32, "SystemParametersInfoW", [wt.UINT, wt.UINT, wt.LPVOID, wt.UINT], wt.BOOL)
_declare(user32, "GetAncestor", [wt.HWND, wt.UINT], wt.HWND)
_declare(user32, "GetForegroundWindow", [], wt.HWND)
_declare(user32, "GetWindowThreadProcessId", [wt.HWND, ctypes.POINTER(wt.DWORD)], wt.DWORD)
_declare(user32, "SetWindowPos", [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT], wt.BOOL)
_declare(user32, "ShowWindow", [wt.HWND, ctypes.c_int], wt.BOOL)
_declare(user32, "SetForegroundWindow", [wt.HWND], wt.BOOL)
_declare(kernel32, "CreateMutexW", [wt.LPVOID, wt.BOOL, wt.LPCWSTR], wt.HANDLE)
_declare(kernel32, "CreateEventW", [wt.LPVOID, wt.BOOL, wt.BOOL, wt.LPCWSTR], wt.HANDLE)
_declare(kernel32, "SetEvent", [wt.HANDLE], wt.BOOL)
_declare(kernel32, "WaitForSingleObject", [wt.HANDLE, wt.DWORD], wt.DWORD)
_declare(kernel32, "CloseHandle", [wt.HANDLE], wt.BOOL)
_declare(shell32, "SHGetKnownFolderPath", [wt.LPVOID, wt.DWORD, wt.HANDLE, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_long)
_declare(ole32, "CoTaskMemFree", [wt.LPVOID], None)

def enable_dpi() -> None:
    try:
        _declare(user32, "SetProcessDpiAwarenessContext", [wt.HANDLE], wt.BOOL)(-4)
    except AttributeError:
        _declare(user32, "SetProcessDPIAware", [], wt.BOOL)()

def work_area() -> tuple[int, int, int, int]:
    rect = wt.RECT()
    if not user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return rect.left, rect.top, rect.right, rect.bottom

def hwnd(widget) -> int:
    return user32.GetAncestor(widget.winfo_id(), 2)

def foreign_foreground() -> bool:
    process = wt.DWORD()
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(process))
    return process.value != os.getpid()

def lower_window(widget) -> None:
    user32.SetWindowPos(hwnd(widget), 1, 0, 0, 0, 0, 0x0013)

def keep_topmost(widget) -> None:
    """恢复“显示桌面”隐藏的窗口，并保持置顶但不抢焦点。"""
    handle = hwnd(widget)
    user32.ShowWindow(handle, 4)
    user32.SetWindowPos(handle, -1, 0, 0, 0, 0, 0x0013)

def keep_popup_topmost(widget) -> None:
    """仅提升原生弹出菜单，不调用 ShowWindow，避免菜单闪烁。"""
    user32.SetWindowPos(hwnd(widget), -1, 0, 0, 0, 0, 0x0013)

def activate(widget) -> None:
    user32.SetForegroundWindow(hwnd(widget))

def desktop_directory() -> Path:
    folder_id = ctypes.create_string_buffer(uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641").bytes_le)
    pointer = ctypes.c_void_p()
    result = shell32.SHGetKnownFolderPath(folder_id, 0, None, ctypes.byref(pointer))
    if result != 0:
        raise OSError("无法获取系统桌面目录。")
    try:
        return Path(ctypes.wstring_at(pointer))
    finally:
        ole32.CoTaskMemFree(pointer)

def launch_command(startup: bool = False) -> str:
    if getattr(sys, "frozen", False):
        arguments = [sys.executable]
    else:
        executable = Path(sys.executable)
        pythonw = executable.with_name("pythonw.exe")
        arguments = [str(pythonw if pythonw.exists() else executable), str(Path(__file__).resolve().parent.parent / "main.py")]
    if startup:
        arguments.append("--startup")
    return subprocess.list2cmdline(arguments)

def startup_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return value == launch_command(startup=True)
    except FileNotFoundError:
        return False

def set_startup(enabled: bool) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, launch_command(startup=True))
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass

class SingleInstance:
    """用命名事件唤醒已有进程。"""
    def __init__(self):
        self.mutex = kernel32.CreateMutexW(None, False, "Local\\HomeworkMemo.Mutex.v1")
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        self.existing = ctypes.get_last_error() == 183
        self.event = kernel32.CreateEventW(None, False, False, "Local\\HomeworkMemo.Open.v1")
        if not self.event:
            kernel32.CloseHandle(self.mutex)
            raise ctypes.WinError(ctypes.get_last_error())
    def notify(self):
        kernel32.SetEvent(self.event)
    def requested(self) -> bool:
        return kernel32.WaitForSingleObject(self.event, 0) == 0
    def close(self):
        kernel32.CloseHandle(self.event)
        kernel32.CloseHandle(self.mutex)

