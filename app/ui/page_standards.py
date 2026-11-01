"""餐标：7 天菜单编辑。"""
import tkinter as tk
from tkinter import messagebox, ttk

from .. import config as cfgmod
from . import widgets as w
from .theme import COLORS, FONTS

MEALS = ["早餐", "午餐", "晚餐"]


class StandardsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app
        self.plan = app.plan
        self.day = 1

        head = tk.Frame(self, bg=COLORS["bg"])
        head.pack(fill="x", padx=28, pady=(24, 8))
        w.label(head, "餐标", size="h1", bg="bg").pack(side="left")
        self.info = w.label(head, "", size="small", fg="muted", bg="bg")
        self.info.pack(side="left", padx=12, pady=(6, 0))

        bar = tk.Frame(self, bg=COLORS["bg"])
        bar.pack(fill="x", padx=28, pady=4)
        w.label(bar, "DAY1 起始日", size="small", fg="muted", bg="bg").pack(side="left")
        self.start_var = tk.StringVar(value=self.plan.get("cycle_start", ""))
        e = w.entry(bar, self.start_var, width=12)
        e.pack(side="left", padx=8)
        w.ghost(bar, "保存起始日", self.save_start).pack(side="left")
        w.label(bar, "  （格式 2026-11-01）", size="tiny", fg="muted", bg="bg").pack(side="left")

        body = w.Card(self, pad=12)
        body.pack(fill="both", expand=True, padx=24, pady=12)

        top = tk.Frame(body.body, bg=COLORS["card"])
        top.pack(fill="x")
        self.day_var = tk.StringVar(value="DAY1")
        cb = ttk.Combobox(top, textvariable=self.day_var, state="readonly", width=9,
                          values=[f"DAY{i}" for i in range(1, 8)])
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", self._on_day)
        self.type_lbl = w.label(top, "", size="small", fg="muted")
        self.type_lbl.pack(side="left", padx=12)
        w.primary(top, "添加食物", self.add_item).pack(side="right", padx=6)
        w.ghost(top, "删除选中", self.del_item).pack(side="right", padx=6)
        w.ghost(top, "编辑选中", self.edit_item).pack(side="right", padx=6)

        self.tree = ttk.Treeview(body.body, columns=("meal", "name", "qty", "alias"),
                                 show="headings", height=14)
        for col, txt, width in (("meal", "餐次", 70), ("name", "食物", 220),
                                ("qty", "份量", 60), ("alias", "别名（逗号分隔）", 380)):
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=10)
        self.tree.bind("<Double-1>", lambda e: self.edit_item())

        foot = tk.Frame(body.body, bg=COLORS["card"])
        foot.pack(fill="x")
        w.label(foot, "改完记得保存，保存后下一次判定就用新菜单。", size="tiny", fg="muted").pack(side="left")
        w.primary(foot, "保存菜单", self.save_plan).pack(side="right")

    # ----------
    def _day_obj(self):
        for d in self.plan["days"]:
            if int(d["day"]) == self.day:
                return d
        return None

    def refresh(self):
        self.plan = self.app.plan
        self.start_var.set(self.plan.get("cycle_start", ""))
        self._render()

    def _on_day(self, _=None):
        self.day = int(self.day_var.get().replace("DAY", ""))
        self._render()

    def _render(self):
        d = self._day_obj()
        for i in self.tree.get_children():
            self.tree.delete(i)
        if not d:
            return
        kind = "轻断日" if d.get("type") == "light" else "正常日"
        self.type_lbl.configure(text=f"{kind} · {d.get('kcal', '')} kcal")
        for meal in MEALS:
            for it in (d.get("meals") or {}).get(meal, []):
                self.tree.insert("", "end", values=(meal, it["name"], it.get("qty", 1),
                                                    "，".join(it.get("aliases") or [])))

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        return vals

    def add_item(self):
        self._dialog()

    def edit_item(self):
        vals = self._selected()
        if not vals:
            messagebox.showinfo("提示", "先选中一行")
            return
        self._dialog(vals)

    def del_item(self):
        vals = self._selected()
        if not vals:
            return
        d = self._day_obj()
        meal, name = vals[0], vals[1]
        d["meals"][meal] = [i for i in d["meals"][meal] if i["name"] != name]
        self._render()

    def _dialog(self, vals=None):
        d = self._day_obj()
        top = tk.Toplevel(self)
        top.title("编辑食物")
        top.configure(bg=COLORS["card"])
        top.geometry("420x260")
        top.transient(self)

        meal_var = tk.StringVar(value=vals[0] if vals else "早餐")
        name_var = tk.StringVar(value=vals[1] if vals else "")
        qty_var = tk.StringVar(value=vals[2] if vals else "1")
        alias_var = tk.StringVar(value=vals[3] if vals else "")

        rows = [("餐次", ttk.Combobox(top, textvariable=meal_var, values=MEALS, state="readonly")),
                ("食物", w.entry(top, name_var, 30)),
                ("份量", w.entry(top, qty_var, 8)),
                ("别名", w.entry(top, alias_var, 40))]
        for i, (txt, widget) in enumerate(rows):
            w.label(top, txt, size="small", fg="muted").grid(row=i, column=0, padx=16, pady=10, sticky="w")
            widget.grid(row=i, column=1, padx=10, pady=10, sticky="w")

        def ok():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "食物名不能为空")
                return
            meal = meal_var.get()
            if vals:
                d["meals"][meal_var.get()] = [i for i in d["meals"].get(meal, [])
                                              if i["name"] != vals[1]]
            item = {"name": name, "qty": float(qty_var.get() or 1),
                    "aliases": [a.strip() for a in alias_var.get().replace("，", ",").split(",") if a.strip()] or [name]}
            d["meals"].setdefault(meal, []).append(item)
            top.destroy()
            self._render()

        w.primary(top, "确定", ok).grid(row=4, column=1, padx=10, pady=14, sticky="e")

    def save_start(self):
        s = self.start_var.get().strip()
        try:
            from datetime import date
            date.fromisoformat(s)
        except Exception:
            messagebox.showwarning("提示", "日期格式应为 2026-11-01")
            return
        self.plan["cycle_start"] = s
        cfgmod.save_plan(self.plan)
        self.app.plan = self.plan
        messagebox.showinfo("已保存", "起始日已更新")

    def save_plan(self):
        cfgmod.save_plan(self.plan)
        self.app.plan = self.plan
        messagebox.showinfo("已保存", "菜单已保存，下一次判定立即生效")