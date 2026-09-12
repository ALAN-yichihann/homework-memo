# 作业记录

作业记录是一个面向班级电脑的轻量 Windows 桌面工具。它用悬浮球保持入口，用大字号分区编辑当天作业，并可按 `作业.docx` 模板生成桌面文档。

## 使用

安装 Python 3.11 或更新版本后双击 `main.py`（或用 Python 文件关联打开）。启动后右上角会出现悬浮球；单击悬浮球进入编辑界面，右侧依次为模式切换、生成文档和开机自启。编辑内容会自动保存在 `%LOCALAPPDATA%\HomeworkMemo\days`。

首次启动默认写入当前用户的开机自启项。要分发给不熟悉 Python 的电脑，可以使用 PyInstaller：

```powershell
pyinstaller --noconsole --onefile --name 作业记录 --add-data "作业.docx;." main.py
```

## 测试

```powershell
python -m unittest discover -s tests -v
python -m compileall -q homework_memo main.py
```

手工测试时依次确认：双击启动、单击悬浮球打开/收起、展示模式不可编辑、另一个窗口打开后应用置底、右键菜单退出、文档导出与 5 秒限流、重启后作业内容仍在、开机自启按钮能在注册表中切换。导出时关闭已打开的 `作业.docx`，否则 Windows 可能拒绝替换文件。

## 许可

项目代码采用 MIT 许可，可自由修改和分发；根目录的 `作业.docx` 是可替换的班级模板。

