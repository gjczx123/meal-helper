"""诊断：各通道状态 + 最近日志。"""
import tkinter as tk

from .. import db, paths
from ..wechat import win32
from . import widgets as w
from .theme import COLORS, FONTS


class DiagPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app

        head = tk.Frame(self, bg=COLORS["bg"])
        head.pack(fill="x", padx=28, pady=(24, 8))
        w.label(head, "诊断", size="h1", bg="bg").pack(side="left")
        w.ghost(head, "重新检测", self.refresh).pack(side="right")
        self.test_btn = w.primary(head, "测试读取", self.test_read)
        self.test_btn.pack(side="right", padx=8)

        card = w.Card(self, pad=16)
        card.pack(fill="x", padx=24, pady=8)
        self.rows = {}
        for i, key in enumerate(["微信窗口", "屏幕锁定", "读消息", "发送模式", "数据目录"]):
            w.label(card.body, key, size="small", fg="muted").grid(row=i, column=0, sticky="w", pady=6)
            v = w.label(card.body, "—", size="body")
            v.grid(row=i, column=1, sticky="w", padx=16)
            self.rows[key] = v

        logcard = w.Card(self, pad=16)
        logcard.pack(fill="both", expand=True, padx=24, pady=(4, 20))
        w.label(logcard.body, "最近发送记录", size="h2").pack(anchor="w")
        self.log = tk.Text(logcard.body, bg=COLORS["card"], fg=COLORS["text"],
                           font=FONTS["small"], relief="flat", height=12)
        self.log.pack(fill="both", expand=True, pady=(8, 0))

    def test_read(self):
        import threading
        self.rows["读消息"].configure(text="正在读…（要 15~30 秒）", fg=COLORS["muted"])

        def run():
            text, err = self.app.reader.test_read(self.app.cfg.get("target_remark", ""))
            msg = ("她最近一条是：" + text[:60]) if text else ("没读到：" + (err or "未知原因"))
            self.after(0, lambda: self.rows["读消息"].configure(
                text=msg, fg=COLORS["green"] if text else COLORS["amber"]))
        threading.Thread(target=run, daemon=True).start()

    def refresh(self):
        cfg = self.app.cfg
        try:
            hwnd = win32.find_window(cfg["wechat"]["process"], cfg["wechat"]["title"])
            self.rows["微信窗口"].configure(text=f"已找到（{hwnd}）" if hwnd else "没找到，请先打开微信",
                                          fg=COLORS["green"] if hwnd else COLORS["red"])
        except Exception:
            self.rows["微信窗口"].configure(text="检测失败", fg=COLORS["red"])

        try:
            locked = win32.session_locked()
            self.rows["屏幕锁定"].configure(text="已锁定（无法发送）" if locked else "未锁定",
                                          fg=COLORS["red"] if locked else COLORS["green"])
        except Exception:
            pass

        st = self.app.reader.status()
        self.rows["读消息"].configure(
            text="已接通" if st["ready"] else f"未接通：{st['error']}",
            fg=COLORS["green"] if st["ready"] else COLORS["amber"])

        self.rows["发送模式"].configure(
            text="演练（只记录不真发）" if cfg.get("dry_run") else "真实发送",
            fg=COLORS["amber"] if cfg.get("dry_run") else COLORS["text"])

        self.rows["数据目录"].configure(text=str(paths.home()))

        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        for r in db.recent_logs(12):
            self.log.insert("end", f"{r['ts']}  {r['action']}  {'OK' if r['ok'] else 'FAIL'}  "
                                   f"{(r['content'] or '')[:40]}\n")
        self.log.configure(state="disabled")