"""记录：左列表 + 右详情。"""
import threading
import tkinter as tk
from tkinter import ttk

from .. import db
from . import widgets as w
from .theme import COLORS, FONTS, status_color, status_text


class RecordsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app

        head = tk.Frame(self, bg=COLORS["bg"])
        head.pack(fill="x", padx=28, pady=(24, 8))
        w.label(head, "记录", size="h1", bg="bg").pack(side="left")
        w.ghost(head, "刷新", self.refresh).pack(side="right")
        w.primary(head, "看周报", self.show_weekly).pack(side="right", padx=8)
        w.ghost(head, "补录一条", self.open_manual).pack(side="right", padx=8)
        w.ghost(head, "扫描聊天", self.scan_chat).pack(side="right", padx=8)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(6, 20))

        left = w.Card(body, pad=8)
        left.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(left.body, columns=("date", "meal", "status", "text"),
                                 show="headings", selectmode="browse")
        for col, txt, width in (("date", "日期", 90), ("meal", "餐次", 60),
                                ("status", "判定", 70), ("text", "她说的", 220)):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = w.Card(body, pad=16)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        w.label(right.body, "详情", size="h2").pack(anchor="w")
        self.detail = tk.Text(right.body, bg=COLORS["card"], fg=COLORS["text"],
                              font=FONTS["body"], relief="flat", wrap="word", height=18)
        self.detail.pack(fill="both", expand=True, pady=(8, 0))
        self.rows = {}

    def scan_chat(self):
        """翻聊天记录，找她在我那条提醒之后的回复。"""
        from ..wechat import history
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", "正在扫描微信聊天窗口…（约 5 秒）")

        def run():
            ask = self.app.cfg["meals"]["午餐"]["ask_text"]
            replies, err = history.find_replies(self.app.cfg, ask)
            def done():
                self.detail.delete("1.0", "end")
                if replies:
                    self.detail.insert("1.0", "扫描到她的回复：\n\n" + "\n".join("· " + t for t in replies))
                else:
                    self.detail.insert("1.0", "没找到：" + (err or "未知原因") +
                                       "\n\n截图已存到 logs/last_scan.png，可以看看抓到的画面")
            self.after(0, done)
        threading.Thread(target=run, daemon=True).start()

    def open_manual(self):
        from datetime import date
        from tkinter import ttk
        from .. import service

        top = tk.Toplevel(self)
        top.title("补录一条")
        top.configure(bg=COLORS["card"])
        top.geometry("520x330")
        top.transient(self)

        d_var = tk.StringVar(value=date.today().isoformat())
        m_var = tk.StringVar(value="午餐")
        text_box = tk.Text(top, height=8, font=FONTS["body"], relief="flat",
                           bg="#F7F9FC", highlightthickness=1,
                           highlightbackground=COLORS["border"])
        hint = w.label(top, "", size="small", fg="muted")

        w.label(top, "日期", size="small", fg="muted").place(x=20, y=18)
        w.entry(top, d_var, 12).place(x=70, y=14)
        w.label(top, "餐次", size="small", fg="muted").place(x=230, y=18)
        ttk.Combobox(top, textvariable=m_var, values=["早餐", "午餐", "晚餐"],
                     state="readonly", width=8).place(x=275, y=14)
        text_box.place(x=20, y=50, width=480, height=170)
        hint.place(x=20, y=232)

        def fill_from_chat():
            hint.configure(text="正在读微信当前会话…")
            def run():
                txt, err = self.app.reader.test_read(self.app.cfg.get("target_remark", ""))
                def done():
                    if txt:
                        text_box.delete("1.0", "end")
                        text_box.insert("1.0", txt)
                        hint.configure(text="已填入她最近一条：" + txt[:24])
                    else:
                        hint.configure(text="没读到：" + (err or "未知"))
                self.after(0, done)
            threading.Thread(target=run, daemon=True).start()

        def save():
            txt = text_box.get("1.0", "end").strip()
            if not txt:
                hint.configure(text="内容不能为空")
                return
            try:
                when = date.fromisoformat(d_var.get().strip())
            except Exception:
                hint.configure(text="日期格式应为 2026-11-03")
                return
            res = service.record_manual(self.app.cfg, self.app.plan, when, m_var.get(), txt)
            self.refresh()
            top.destroy()
            self.detail.configure(state="normal")
            self.detail.delete("1.0", "end")
            self.detail.insert("1.0", f"补录成功：{when} {m_var.get()} 判定={res['status']}\n原文：{txt}")

        w.ghost(top, "读取当前会话最后一条", fill_from_chat).place(x=20, y=285)
        w.primary(top, "保存", save).place(x=430, y=285)

    def show_weekly(self):
        from .. import report
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", report.weekly_text())
        self.detail.configure(state="disabled")

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows = {}
        for r in db.recent(100):
            iid = str(r["id"])
            self.rows[iid] = r
            self.tree.insert("", "end", iid=iid, values=(
                r["date"], r["meal"], status_text(r["status"]), (r["raw_text"] or "")[:24]))

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        r = self.rows.get(sel[0])
        if not r:
            return
        lines = [
            f"{r['date']}  {r['meal']}  DAY{r.get('plan_day')}",
            f"判定：{status_text(r['status'])}   {r.get('verdict_reason') or ''}",
            f"来源：{r.get('source')}   时间：{r.get('msg_time') or '—'}",
            "",
            "她说的：",
            r.get("raw_text") or "（空）",
            "",
            f"我的回复：{r.get('reply_text') or '（没回）'}",
        ]
        if r.get("image_path"):
            lines += ["", f"照片：{r['image_path']}"]
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", "\n".join(lines))
        self.detail.configure(state="disabled")