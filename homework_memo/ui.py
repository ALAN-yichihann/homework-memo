"""大字号作业面板与悬浮球。"""
from __future__ import annotations
import json
import logging
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox
from . import windows
from .core import SUBJECTS, Exporter, Store, atomic_write
from .icons import draw

BG = "#f1f3ec"
PAPER = "#fffef9"
INK = "#263d36"
MUTED = "#6d7e75"
ACCENT = "#305d50"

class ToolTip:
    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        self.timer = self.window = None
        widget.bind("<Enter>", self.schedule, add=True)
        widget.bind("<Leave>", self.hide, add=True)
        widget.bind("<ButtonPress>", self.hide, add=True)
    def schedule(self, _event=None):
        self.hide(); self.timer = self.widget.after(3000, self.show)
    def show(self):
        self.timer = None
        if not self.widget.winfo_viewable(): return
        self.window = tk.Toplevel(self.widget); self.window.overrideredirect(True)
        tk.Label(self.window, text=self.text(), font=("Microsoft YaHei UI", 11), bg=INK, fg="white", padx=14, pady=10, justify="left").pack()
        self.window.update_idletasks()
        left, top, right, bottom = windows.work_area()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        x = max(left, min(right-width, self.widget.winfo_rootx()-width-10)); y = max(top, min(bottom-height, self.widget.winfo_rooty()))
        self.window.geometry(f"+{x}+{y}")
    def hide(self, _event=None):
        if self.timer is not None: self.widget.after_cancel(self.timer); self.timer = None
        if self.window is not None: self.window.destroy(); self.window = None

class App:
    def __init__(self, root: tk.Tk, data_directory: Path, template: Path, instance=None, startup=False, test_mode=False):
        self.root = root; root.withdraw()
        self.data_directory, self.template, self.instance = data_directory, template, instance
        self.test_mode = test_mode; self.store = Store(data_directory / "days"); self.exporter = Exporter()
        self.day = date.today(); self.editing = True; self.visible = False; self.dirty = False
        self.save_timer = None; self.read_error = False; self.area = None; self.tips = []
        self.editors = {}; self.scrollbars = {}; self.font_size = 22; self.sidebar_width = 88
        self.startup_on = False if test_mode else windows.startup_enabled()
        self.board = tk.Toplevel(root); self.board.withdraw(); self.board.overrideredirect(True); self.board.configure(bg=BG)
        self.board.protocol("WM_DELETE_WINDOW", self.hide); self.status = tk.StringVar(value="正在读取作业…")
        self._build_board(); self._build_ball(); self._layout(); self._load_day()
        for widget in (self.board, self.ball):
            widget.bind("<Escape>", lambda _e: self.hide()); widget.bind("<Control-e>", lambda _e: self.toggle_mode()); widget.bind("<Control-s>", self.export)
        root.report_callback_exception = self._report_error
        if not startup: self.show()
        root.after(250, self._poll)
        if not test_mode: root.after(200, self._initialize_startup)

    def _build_board(self):
        self.left = tk.Frame(self.board, bg=BG)
        header = tk.Frame(self.left, bg=BG, height=60); header.pack(fill="x", padx=22, pady=(14,10))
        self.date_label = tk.Label(header, bg=BG, fg=INK, font=("Microsoft YaHei UI",20,"bold")); self.date_label.pack(side="left")
        tk.Label(header, textvariable=self.status, bg=BG, fg=MUTED, font=("Microsoft YaHei UI",11)).pack(side="right")
        grid = tk.Frame(self.left, bg=BG); grid.pack(fill="both", expand=True, padx=14, pady=(0,14))
        for column in range(3): grid.columnconfigure(column, weight=1, uniform="subject")
        for row in range(2): grid.rowconfigure(row, weight=1, uniform="subject")
        for index, subject in enumerate(SUBJECTS[:5]): self._subject(grid, subject, index//3, index%3)
        shared = tk.Frame(grid, bg=BG); shared.grid(row=1,column=2,sticky="nsew"); shared.columnconfigure(0,weight=1)
        shared.rowconfigure(0,weight=1,uniform="shared"); shared.rowconfigure(1,weight=1,uniform="shared")
        self._subject(shared,"生物",0,0); self._subject(shared,"其他",1,0)
        self.sidebar = tk.Frame(self.board, bg="#e4eae0")
        self.mode_button = self._button(self.sidebar,"edit","编辑中",self.toggle_mode,lambda:"切换到展示模式，完整显示作业" if self.editing else "切换到编辑模式，修改各科作业")
        self.export_button = self._button(self.sidebar,"export","生成文档",self.export,lambda:"生成桌面上的作业.docx；同名文件会被覆盖\n两次生成至少间隔 5 秒")
        self.startup_button = self._button(self.sidebar,"power","开机自启",self.toggle_startup,lambda:"关闭开机自启" if self.startup_on else "开启开机自启")
        tk.Button(self.sidebar,text="收起\nEsc",command=self.hide,bg="#e4eae0",fg=MUTED,relief="flat",bd=0,cursor="hand2",font=("Microsoft YaHei UI",11),pady=15).pack(side="bottom",fill="x",padx=6,pady=12)
        self._update_buttons()

    def _subject(self, parent, subject, row, column):
        frame = tk.Frame(parent,bg=PAPER,highlightbackground="#dce3d8",highlightthickness=1); frame.grid(row=row,column=column,sticky="nsew",padx=5,pady=5)
        tk.Label(frame,text=subject,bg=PAPER,fg=ACCENT,anchor="e",font=("Microsoft YaHei UI",16,"bold"),padx=16,pady=9).pack(fill="x")
        body = tk.Frame(frame,bg=PAPER); body.pack(fill="both",expand=True,padx=(12,4),pady=(0,10))
        editor = tk.Text(body,wrap="word",undo=True,maxundo=100,bg=PAPER,fg=INK,insertbackground=ACCENT,selectbackground="#d8e6d7",relief="flat",bd=0,highlightthickness=0,width=1,height=1,padx=4,font=("Microsoft YaHei UI",self.font_size),spacing1=3,spacing3=5)
        scrollbar = tk.Scrollbar(body,width=14,relief="flat",command=editor.yview); editor.configure(yscrollcommand=scrollbar.set)
        editor.pack(side="left",fill="both",expand=True); scrollbar.pack(side="right",fill="y")
        editor.bind("<<Modified>>",self._modified); editor.bind("<Configure>",lambda _e,s=subject:self._schedule_fit(s))
        self.editors[subject] = editor; self.scrollbars[subject] = scrollbar

    def _button(self, parent, kind, label, command, tooltip):
        button = tk.Frame(parent,bg="#e4eae0",cursor="hand2",takefocus=True,highlightthickness=2,highlightbackground="#e4eae0",highlightcolor=ACCENT); button.pack(fill="x",pady=8,padx=4)
        canvas = tk.Canvas(button,width=64,height=64,bg="#e4eae0",highlightthickness=0); canvas.pack()
        text = tk.Label(button,text=label,bg="#e4eae0",fg=ACCENT,font=("Microsoft YaHei UI",10),pady=3); text.pack(fill="x")
        for widget in (button,canvas,text): widget.bind("<Button-1>",lambda _e:command()); self.tips.append(ToolTip(widget,tooltip))
        button.bind("<Return>",lambda _e:command()); button.bind("<space>",lambda _e:command()); draw(canvas,kind)
        return canvas,text

    def _build_ball(self):
        self.ball = tk.Toplevel(self.root); self.ball.overrideredirect(True); self.ball.wm_attributes("-topmost",True)
        try: self.ball.wm_attributes("-toolwindow",True)
        except tk.TclError: pass
        self.ball.configure(bg="#ff00ff"); self.ball.wm_attributes("-transparentcolor","#ff00ff")
        self.ball_canvas = tk.Canvas(self.ball,width=88,height=88,bg="#ff00ff",highlightthickness=0,cursor="hand2"); self.ball_canvas.pack()
        draw(self.ball_canvas,"book"); circle=self.ball_canvas.create_oval(4,4,84,84,fill="#f6f4e7",outline="#c6d6c1",width=2); self.ball_canvas.tag_lower(circle)
        self.ball_canvas.bind("<Button-1>",lambda _e:self.hide() if self.visible else self.show())
        menu=tk.Menu(self.ball,tearoff=False,font=("Microsoft YaHei UI",11)); menu.add_command(label="打开编辑窗口",command=self.show); menu.add_separator(); menu.add_command(label="退出作业记录",command=self.quit)
        def popup(event):
            try: menu.tk_popup(event.x_root,event.y_root); windows.keep_topmost(menu)
            finally: menu.grab_release()
        self.ball_canvas.bind("<Button-3>",popup); self.tips.append(ToolTip(self.ball_canvas,lambda:"单击打开或收起作业\n右键可退出程序"))

    def _layout(self):
        area=windows.work_area()
        if area==self.area:return
        self.area=area; left,top,right,bottom=area; width,height=right-left,bottom-top; side=self.sidebar_width
        self.board.geometry(f"{width}x{height}+{left}+{top}"); self.ball.geometry(f"{side}x{side}+{right-side}+{top}")
        self.left.place(x=0,y=0,width=width-side,height=height); self.sidebar.place(x=width-side,y=side,width=side,height=max(1,height-side))
        self.font_size=max(16,min(28,round((width-side)/57)))
        if self.editing:
            for editor in self.editors.values(): editor.configure(font=("Microsoft YaHei UI",self.font_size))

    def _load_day(self):
        try: homework=self.store.load(self.day)
        except (OSError,ValueError) as error:
            self.read_error=True; self.status.set("数据读取失败，已禁止覆盖"); messagebox.showerror("无法读取作业",f"{error}\n数据目录：{self.store.directory}",parent=self.ball); homework=dict.fromkeys(SUBJECTS,"")
        for subject,editor in self.editors.items():
            editor.configure(state="normal"); editor.delete("1.0","end"); editor.insert("1.0",homework[subject]); editor.edit_reset(); editor.edit_modified(False); editor.configure(state="normal" if self.editing and not self.read_error else "disabled")
        self.date_label.configure(text=f"{self.day.month}月{self.day.day}日 · 今日作业"); self.dirty=False
        if not self.read_error:self.status.set("编辑中 · 自动保存" if self.editing else "展示中 · 不可编辑")

    def snapshot(self): return {subject:editor.get("1.0","end-1c") for subject,editor in self.editors.items()}
    def _modified(self,event):
        editor=event.widget
        if not editor.edit_modified():return
        editor.edit_modified(False)
        if self.read_error:return
        self.dirty=True; self.status.set("正在保存…")
        if self.save_timer is not None:self.root.after_cancel(self.save_timer)
        self.save_timer=self.root.after(500,self.save)
    def save(self):
        if self.save_timer is not None:self.root.after_cancel(self.save_timer); self.save_timer=None
        if not self.dirty or self.read_error:return True
        try:self.store.save(self.day,self.snapshot())
        except OSError:
            logging.exception("保存作业失败"); self.status.set("保存失败，请检查磁盘空间与数据目录权限"); return False
        self.dirty=False; self.status.set("已保存 · 编辑中" if self.editing else "已保存 · 展示中"); return True

    def show(self):
        self._layout(); self.visible=True; self.editing=True; self._apply_mode(); self.board.deiconify(); self.board.lift(); self.ball.lift(); windows.activate(self.board); self.editors["语文"].focus_set()
    def hide(self):
        if not self.save():messagebox.showerror("尚未保存","作业保存失败，请处理后再收起窗口。",parent=self.board);return
        for tip in self.tips:tip.hide()
        self.visible=False; self.board.withdraw()

    def _schedule_fit(self,subject):
        if not self.editing:self.root.after_idle(lambda:self._fit_text(subject))
    def _fit_text(self,subject):
        if self.editing:return
        editor=self.editors[subject]
        if editor.winfo_height()<=1:return
        editor.configure(font=("Microsoft YaHei UI",self.font_size)); editor.update_idletasks()
        chosen=12
        for size in range(self.font_size,11,-1):
            editor.configure(font=("Microsoft YaHei UI",size)); editor.yview_moveto(0); editor.update_idletasks()
            info=editor.dlineinfo("end-1c")
            if info is not None and info[1]+info[3]<=editor.winfo_height()-6: chosen=size; break
        editor.configure(font=("Microsoft YaHei UI",chosen)); editor.yview_moveto(0)

    def _apply_mode(self):
        for subject,editor in self.editors.items():
            if self.editing:
                self.scrollbars[subject].pack(side="right",fill="y"); editor.configure(font=("Microsoft YaHei UI",self.font_size))
            else:self.scrollbars[subject].pack_forget()
            editor.configure(state="normal" if self.editing and not self.read_error else "disabled")
        if not self.read_error:self.status.set("编辑中 · 自动保存" if self.editing else "展示中 · 不可编辑")
        self._update_buttons()
        if not self.editing:
            for subject in self.editors:self.root.after_idle(lambda s=subject:self._fit_text(s))
    def toggle_mode(self):
        if self.save():self.editing=not self.editing;self._apply_mode()
    def _update_buttons(self):
        canvas,label=self.mode_button;draw(canvas,"edit" if self.editing else "display");label.configure(text="编辑中" if self.editing else "展示中")
        canvas,label=self.startup_button;draw(canvas,"power" if self.startup_on else "power-off");label.configure(text="自启已开" if self.startup_on else "自启已关")
    def export(self,_event=None):
        if self.read_error or not self.save():return "break"
        if self.exporter.remaining:self.status.set(f"请等待 {self.exporter.remaining:.0f} 秒后再次生成");return "break"
        try:
            destination=(self.data_directory if self.test_mode else windows.desktop_directory())/"作业.docx";self.exporter.export(self.template,destination,self.snapshot(),self.day)
        except Exception as error:logging.exception("生成作业文档失败");messagebox.showerror("生成失败",f"{error}\n若文件已在 Word/WPS 中打开，请先关闭再重试。",parent=self.board)
        else:self.status.set("已生成作业.docx" if self.test_mode else "已生成桌面上的作业.docx")
        return "break"
    def _initialize_startup(self):
        marker=self.data_directory/"settings.json"
        if marker.exists():return
        try:windows.set_startup(True);self.startup_on=windows.startup_enabled();atomic_write(marker,json.dumps({"initialized":True}).encode("utf-8"))
        except OSError as error:logging.exception("设置默认自启失败");messagebox.showwarning("未能开启自启",f"{error}\n可稍后点击右侧电源按钮重试。",parent=self.ball)
        self._update_buttons()
    def toggle_startup(self):
        if self.test_mode:self.startup_on=not self.startup_on
        else:
            try:windows.set_startup(not self.startup_on);self.startup_on=windows.startup_enabled();atomic_write(self.data_directory/"settings.json",b'{"initialized": true}')
            except OSError as error:messagebox.showerror("无法修改开机自启",str(error),parent=self.board)
        self._update_buttons()
    def _poll(self):
        self._layout()
        if self.instance and self.instance.requested():self.show()
        self.ball.deiconify();windows.keep_topmost(self.ball)
        if self.visible and windows.foreign_foreground():windows.lower_window(self.board)
        if date.today()!=self.day and not self.read_error and self.save():self.day=date.today();self._load_day()
        self.root.after(250,self._poll)
    def _report_error(self,exception,value,traceback):
        logging.error("界面回调异常",exc_info=(exception,value,traceback));messagebox.showerror("操作未完成",f"{value}\n请查看数据目录中的 application.log。",parent=self.ball)
    def quit(self):
        if not self.save():messagebox.showerror("尚未保存","作业保存失败，暂未退出，避免丢失内容。",parent=self.ball);return
        self.root.destroy()


