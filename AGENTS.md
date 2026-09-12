# 开发约定

- 对话、文档和代码注释统一使用简体中文。
- 修改前先阅读相关实现；复杂变更先提交计划并获得确认。
- 应用运行仅依赖 Python 标准库，支持 Windows 10/11 和 Python 3.11 及以上。
- 界面代码放在 `homework_memo/ui.py`，数据及导出放在 `core.py`，Windows 系统接口放在 `windows.py`。
- 所有 Win32 接口显式声明参数与返回类型，避免 64 位句柄截断。
- 用户数据存放在 LOCALAPPDATA，测试必须使用临时目录，不修改真实自启或桌面文件。
- 保留根目录的 Word 模板；导出只能写入目标副本。
- 提交前运行 `python -m unittest discover -s tests -v` 与 `python -m compileall -q homework_memo main.py`。
- 阶段性提交使用简体中文说明，不提交个人数据、临时文件或测试生成物。

