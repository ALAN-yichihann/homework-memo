"""数据持久化与 Word 模板导出；不依赖图形界面。"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from datetime import date
from pathlib import Path
from xml.dom import minidom
from zipfile import ZipFile

SUBJECTS = ("语文", "数学", "英语", "物理", "化学", "生物", "其他")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def atomic_write(path: Path, data: bytes) -> None:
    """先写同目录临时文件再替换，写入失败时保留原文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


class Store:
    def __init__(self, directory: Path):
        self.directory = directory

    def load(self, day: date) -> dict[str, str]:
        path = self.directory / f"{day.isoformat()}.json"
        if not path.exists():
            return dict.fromkeys(SUBJECTS, "")
        # 不静默吞掉损坏数据，否则下一次自动保存会覆盖原始内容。
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or any(
            not isinstance(data.get(subject, ""), str) for subject in SUBJECTS
        ):
            raise ValueError("作业数据格式错误，请先备份并检查数据文件。")
        return {subject: data.get(subject, "") for subject in SUBJECTS}

    def save(self, day: date, homework: dict[str, str]) -> None:
        data = json.dumps(homework, ensure_ascii=False, indent=2).encode("utf-8")
        atomic_write(self.directory / f"{day.isoformat()}.json", data)


def _text(node) -> str:
    return "".join(
        child.data
        for tag in node.getElementsByTagNameNS(W_NS, "t")
        for child in tag.childNodes
        if child.nodeType == child.TEXT_NODE
    )


def _paragraph(document, prototype, content: str):
    """复制段落与首个文字格式，去除旧内容及模板的自动编号。"""
    paragraph = prototype.cloneNode(deep=True)
    runs = paragraph.getElementsByTagNameNS(W_NS, "rPr")
    run_properties = runs[-1].cloneNode(deep=True) if runs else None
    for child in list(paragraph.childNodes):
        if child.nodeName != "w:pPr":
            paragraph.removeChild(child)
    for numbering in list(paragraph.getElementsByTagNameNS(W_NS, "numPr")):
        numbering.parentNode.removeChild(numbering)
    # 克隆段落不能复用 WPS/Word 的唯一段落标识。
    for attribute in ("w14:paraId", "w14:textId"):
        if paragraph.hasAttribute(attribute):
            paragraph.removeAttribute(attribute)
    run = document.createElementNS(W_NS, "w:r")
    if run_properties is not None:
        run.appendChild(run_properties)
    text = document.createElementNS(W_NS, "w:t")
    text.setAttribute("xml:space", "preserve")
    text.appendChild(document.createTextNode(content))
    run.appendChild(text)
    paragraph.appendChild(run)
    return paragraph


def export_docx(template: Path, destination: Path, homework: dict[str, str], day: date) -> None:
    if template.resolve() == destination.resolve():
        raise ValueError("导出位置不能覆盖原始模板。")
    with ZipFile(template) as archive:
        document = minidom.parseString(archive.read("word/document.xml"))
        body = document.getElementsByTagNameNS(W_NS, "body")[0]
        paragraphs = [node for node in body.childNodes if node.nodeName == "w:p"]
        if not paragraphs:
            raise ValueError("模板缺少正文段落。")
        headings = {}
        contents = {}
        current = None
        order = []
        for paragraph in paragraphs[1:]:
            value = _text(paragraph).strip()
            subject = value.rstrip("：:")
            if subject in SUBJECTS:
                current = subject
                headings[subject] = paragraph
                order.append(subject)
            elif current and value and current not in contents:
                contents[current] = paragraph
        if not headings or not contents:
            raise ValueError("模板需要包含科目标题及至少一条示例作业。")
        title = paragraphs[0]
        blank = next((p for p in paragraphs if not _text(p)), title)
        default_heading = next(iter(headings.values()))
        default_content = next(iter(contents.values()))
        for paragraph in paragraphs:
            body.removeChild(paragraph)
        section = next((node for node in body.childNodes if node.nodeName == "w:sectPr"), None)

        def append(prototype, value):
            # XML 1.0 不允许控制字符；换行在下方拆成独立段落。
            value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff]", "", value)
            body.insertBefore(_paragraph(document, prototype, value), section)

        append(title, f"{day.month}.{day.day}作业：")
        append(blank, "")
        for subject in order + [s for s in SUBJECTS if s not in order]:
            append(headings.get(subject, default_heading), subject + "：")
            for line in homework.get(subject, "").splitlines() or [""]:
                append(contents.get(subject, default_content), line)
            append(blank, "")

        # 只替换正文 XML，其他 ZIP 成员（样式、页边距引用等）原样保留。
        import io

        output = io.BytesIO()
        with ZipFile(output, "w") as result:
            for entry in archive.infolist():
                result.writestr(
                    entry,
                    document.toxml(encoding="UTF-8")
                    if entry.filename == "word/document.xml"
                    else archive.read(entry.filename),
                )
    atomic_write(destination, output.getvalue())


class Exporter:
    def __init__(self):
        self.last_success = float("-inf")

    @property
    def remaining(self) -> float:
        return max(0.0, 5.0 - (time.monotonic() - self.last_success))

    def export(self, template: Path, destination: Path, homework: dict[str, str], day: date):
        if self.remaining:
            raise ValueError("请等待至少 5 秒后再次生成。")
        export_docx(template, destination, homework, day)
        self.last_success = time.monotonic()
