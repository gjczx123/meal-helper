"""记录：左列表 + 右详情。"""
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