"""今日：三张餐次卡片 + 今天记了什么 + 今天该吃什么。"""
import threading
import tkinter as tk
from datetime import date

from .. import db, plan as planmod, service
from . import widgets as w
from .theme import COLORS, FONTS, status_color, status_text

ORDER = ["早餐", "午餐", "晚餐"]


class TodayPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app
        self._sig = None

        head = tk.Frame(self, bg=COLORS["bg"])
        head.pack(fill="x", padx=28, pady=(22, 6))
        self.title = w.label(head, "今天", size="h1", bg="bg")
        self.title.pack(side="left")
        self.sub = w.label(head, "", size="small", fg="muted", bg="bg")
        self.sub.pack(side="left", padx=12, pady=(6, 0))

        self.toggle = w.ghost(head, "开启自动提醒", self.toggle_run)
        self.toggle.pack(side="right")
        self.run_hint = w.label(head, "", size="tiny", fg="muted", bg="bg")
        self.run_hint.pack(side="right", padx=10)

        self.cards = tk.Frame(self, bg=COLORS["bg"])
        self.cards.pack(fill="x", padx=22, pady=4)

        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=22, pady=(8, 18))

        left = w.Card(body, pad=16)
        left.pack(side="left", fill="both", expand=True)
        w.label(left.body, "今天记了什么", size="h2").pack(anchor="w")
        self.summary = w.label(left.body, "", size="tiny", fg="muted")
        self.summary.pack(anchor="w", pady=(2, 0))
        self.listbox = tk.Frame(left.body, bg=COLORS["card"])
        self.listbox.pack(fill="both", expand=True, pady=(10, 0))

        right = w.Card(body, pad=16)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        w.label(right.body, "今天该吃什么", size="h2").pack(anchor="w")
        self.planbox = tk.Frame(right.body, bg=COLORS["card"])
        self.planbox.pack(fill="both", expand=True, pady=(10, 0))

    # ----------
    def toggle_run(self):
        from .. import config as cfgmod
        self.app.cfg["running"] = not self.app.cfg.get("running")
        cfgmod.save_config(self.app.cfg)
        self.refresh()

    def refresh(self):
        try:
            day = planmod.day_plan(self.app.plan, date.today())
        except Exception:
            day = {"day": "?", "type": "normal", "meals": {}}
        today = date.today().isoformat()
        recs = db.today_map(today)
        times = tuple(self.app.cfg["meals"][m]["time"] for m in ORDER)
        sig = (today, day.get("day"), times,
               tuple(sorted((k, v["status"]) for k, v in recs.items())),
               bool(self.app.cfg.get("running")))
        if sig == self._sig:
            return
        self._sig = sig

        kind = "轻断日" if day.get("type") == "light" else "正常日"
        self.title.configure(text=f"今天是 DAY{day.get('day')}")
        self.sub.configure(text=f"{today} · {kind} · {day.get('kcal', '')} kcal")

        running = bool(self.app.cfg.get("running"))
        self.toggle.configure(text="暂停自动提醒" if running else "开启自动提醒",
                              bg=COLORS["blue"] if running else COLORS["card"],
                              fg="white" if running else COLORS["text"])
        self.run_hint.configure(text="演练模式：只记录不真发" if self.app.cfg.get("dry_run") else "")

        for c in self.cards.winfo_children():
            c.destroy()
        for name in ORDER:
            self._make_card(name, recs.get(name), w.MEALS_PLAN(day, name))

        normal = sum(1 for r in recs.values() if r["status"] == "normal")
        over = sum(1 for r in recs.values() if r["status"] == "over")
        self.summary.configure(text=f"已记 {len(recs)} 顿 · 正常 {normal} · 超标 {over}")

        for c in self.listbox.winfo_children():
            c.destroy()
        if not recs:
            w.label(self.listbox, "还没有记录。到她回复后会自动出现在这里。",
                    size="small", fg="muted").pack(anchor="w")
        for name in ORDER:
            r = recs.get(name)
            if not r:
                continue
            row = tk.Frame(self.listbox, bg=COLORS["card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=status_text(r["status"]), bg=status_color(r["status"]),
                     fg="white", font=FONTS["tiny"], padx=8, pady=1).pack(side="left")
            w.label(row, name, size="small", fg="muted", width=4, anchor="w").pack(side="left", padx=8)
            w.label(row, (r.get("raw_text") or "")[:34], size="small", fg="text").pack(side="left")

        for c in self.planbox.winfo_children():
            c.destroy()
        for name in ORDER:
            items = (day.get("meals") or {}).get(name) or []
            row = tk.Frame(self.planbox, bg=COLORS["card"])
            row.pack(fill="x", pady=4)
            w.label(row, name, size="small", fg="muted", width=4, anchor="w").pack(side="left")
            w.label(row, " · ".join(i["name"] for i in items) or "—", size="small", fg="text").pack(side="left")

    def _make_card(self, name, rec, plan_items):
        status = rec["status"] if rec else "pending"
        card = tk.Frame(self.cards, bg=COLORS["card"], highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=5, pady=4)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        top = tk.Frame(inner, bg=COLORS["card"])
        top.pack(fill="x")
        w.label(top, name, size="h2").pack(side="left")
        tk.Label(top, text=status_text(status), bg=status_color(status), fg="white",
                 font=FONTS["tiny"], padx=8, pady=1).pack(side="right")

        t = self.app.cfg["meals"][name]["time"]
        w.label(inner, t, size="num", fg="text").pack(anchor="w", pady=(6, 0))
        plan_txt = " + ".join(i["name"] for i in plan_items[:2]) or ""
        w.label(inner, "计划：" + plan_txt, size="tiny", fg="muted",
                wraplength=230, justify="left").pack(anchor="w", pady=(2, 0))
        txt = (rec.get("raw_text") or "") if rec else ""
        if txt:
            w.label(inner, "她：" + txt[:20], size="small", fg="text",
                    wraplength=230, justify="left").pack(anchor="w", pady=(4, 0))

        tk.Button(inner, text="立即提醒", relief="flat", bd=0, bg="#EEF3FF",
                  fg=COLORS["blue"], font=FONTS["small"], cursor="hand2",
                  command=lambda n=name: self._ask_now(n)).pack(anchor="w", pady=(8, 0))

    def _ask_now(self, meal):
        def run():
            service.run_meal(self.app.cfg, self.app.plan, meal, self.app.sender, self.app.reader)
            self.app.after(0, self.refresh)
        threading.Thread(target=run, daemon=True).start()