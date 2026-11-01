"""主窗口：左侧导航 + 右侧页面。"""
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from .. import config as cfgmod, db, notify, paths, report, scheduler, service
from ..wechat import win32
from ..wechat.reader import Reader
from ..wechat.sender import Sender
from . import theme
from .page_diag import DiagPage
from .page_records import RecordsPage
from .page_settings import SettingsPage
from .page_standards import StandardsPage
from .page_today import TodayPage
from . import tray as tray_mod
from .theme import COLORS, FONTS

NAV = [("today", "今日"), ("records", "记录"), ("standards", "餐标"),
       ("settings", "设置"), ("diag", "诊断")]


class App(tk.Tk):
    def __init__(self, page="today"):
        super().__init__()
        win32.set_dpi_aware()
        self.tk.call("tk", "scaling", 1.333)
        self.title("三餐助手")
        self.geometry("1120x760")
        self.minsize(980, 640)
        self.configure(bg=COLORS["bg"])

        self.cfg = cfgmod.load_config()
        self.plan = cfgmod.load_plan()
        self.sender = Sender(self.cfg)
        self.reader = Reader(self.cfg)

        self._setup_style()
        self._setup_icon()
        self._build()
        self.tray = tray_mod.start(self)
        notify.set_sink(lambda title, msg: self.tray and self.tray.notify(msg, title))
        self._start_scheduler()
        self._current = page
        self.show(page)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.after(4000, self.tick)

    # ---------- 外观 ----------
    def _setup_style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Treeview", background=COLORS["card"], fieldbackground=COLORS["card"],
                     foreground=COLORS["text"], rowheight=30, borderwidth=0,
                     font=FONTS["body"])
        st.configure("Treeview.Heading", background="#F7F9FC", foreground=COLORS["muted"],
                     relief="flat", font=FONTS["small"])
        st.map("Treeview", background=[("selected", "#E8F0FF")],
               foreground=[("selected", COLORS["text"])])
        st.configure("TCombobox", fieldbackground=COLORS["card"], background=COLORS["card"])

    def _setup_icon(self):
        try:
            ico = paths.resource("icon.ico")
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    def _build(self):
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=188)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="三餐助手", font=FONTS["logo"],
                 fg="white", bg=COLORS["sidebar"]).pack(anchor="w", padx=22, pady=(26, 4))
        tk.Label(self.sidebar, text="提醒 · 记录 · 不打扰", font=FONTS["tiny"],
                 fg="#8B95A8", bg=COLORS["sidebar"]).pack(anchor="w", padx=22, pady=(0, 24))

        self.nav_buttons = {}
        for key, text in NAV:
            b = tk.Button(self.sidebar, text="   " + text, anchor="w", relief="flat", bd=0,
                          bg=COLORS["sidebar"], fg="#C7CEDB", font=FONTS["body"],
                          activebackground=COLORS["sidebar_hover"], activeforeground="white",
                          padx=18, pady=10, cursor="hand2",
                          command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = b

        self.dot = tk.Canvas(self.sidebar, width=10, height=10, bg=COLORS["sidebar"],
                             highlightthickness=0)
        self.dot.pack(anchor="w", padx=24, pady=(20, 2))
        self._dot = self.dot.create_oval(1, 1, 9, 9, fill=COLORS["grey"], outline="")

        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)
        self.pages = {}
        for key, cls in (("today", TodayPage), ("records", RecordsPage),
                         ("standards", StandardsPage), ("settings", SettingsPage),
                         ("diag", DiagPage)):
            f = cls(self.content, self)
            self.pages[key] = f

    # ---------- 导航 ----------
    def show(self, key):
        self._current = key
        for k, b in self.nav_buttons.items():
            b.configure(bg=COLORS["sidebar_active"] if k == key else COLORS["sidebar"],
                        fg="white" if k == key else "#C7CEDB")
        for k, f in self.pages.items():
            f.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        if hasattr(self.pages[key], "refresh"):
            self.pages[key].refresh()

    def reload(self):
        self.cfg = cfgmod.load_config()
        self.plan = cfgmod.load_plan()
        self.sender.cfg = self.cfg
        self.sender.dry_run = bool(self.cfg.get("dry_run", True))
        self.reader.cfg = self.cfg
        self.show(self._current or "today")

    # ---------- 调度 ----------
    def _start_scheduler(self):
        self._current = "today"
        self._busy = set()
        self._stop = False
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def remind_now(self):
        """托盘/按钮触发：立刻提醒最近的一顿。"""
        now = datetime.now()
        name = min(self.cfg["meals"],
                   key=lambda k: abs((now.replace(hour=int(self.cfg["meals"][k]["time"][:2]),
                                                 minute=int(self.cfg["meals"][k]["time"][3:5])) - now).total_seconds()))
        import threading
        threading.Thread(target=self._run_one, args=(name,), daemon=True).start()

    def toggle_running(self):
        self.cfg["running"] = not self.cfg.get("running")
        cfgmod.save_config(self.cfg)
        try:
            self.pages["today"]._sig = None
            self.pages["today"].refresh()
        except Exception:
            pass

    def _loop(self):
        last_cleanup = None
        while not self._stop:
            try:
                today = datetime.now().date()
                if last_cleanup != today:
                    db.cleanup(int(self.cfg.get("keep_days", 60)))
                    last_cleanup = today
                if datetime.now().weekday() == 6 and datetime.now().hour >= 20 \
                        and self.cfg.get("last_weekly") != today.isoformat():
                    text = report.weekly_text()
                    self.sender.send(text, "文件传输助手")
                    self.cfg["last_weekly"] = today.isoformat()
                    cfgmod.save_config(self.cfg)
                if self.cfg.get("running"):
                    now = datetime.now()
                    sent = set(db.today_map(now.date().isoformat()).keys())
                    for meal in scheduler.due_meals(now, self.cfg["meals"], sent,
                                                    int(self.cfg.get("wait_minutes", 30))):
                        if meal in self._busy:
                            continue
                        self._busy.add(meal)
                        threading.Thread(target=self._run_one, args=(meal,), daemon=True).start()
            except Exception:
                pass
            time.sleep(20)

    def _run_one(self, meal):
        try:
            service.run_meal(self.cfg, self.plan, meal, self.sender, self.reader)
        finally:
            self._busy.discard(meal)
            try:
                self.pages["today"].refresh()
            except Exception:
                pass

    # ---------- 状态 ----------
    def tick(self):
        try:
            ok = self.sender.available() if not self.sender.dry_run else True
            color = COLORS["green"] if ok else COLORS["red"]
            self.dot.itemconfigure(self._dot, fill=color)
        except Exception:
            pass
        self.after(8000, self.tick)

    def hide_to_tray(self):
        if getattr(self, "tray", None):
            self.withdraw()
        else:
            self.iconify()


def main(page="today"):
    app = App(page)
    app.mainloop()