"""设置：时间、备注、开关。"""
import threading
import tkinter as tk
from tkinter import messagebox

from .. import config as cfgmod
from . import widgets as w
from .theme import COLORS, FONTS

MEALS = ["早餐", "午餐", "晚餐"]


class SettingsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=COLORS["bg"])
        self.app = app
        self.vars = {}

        head = tk.Frame(self, bg=COLORS["bg"])
        head.pack(fill="x", padx=28, pady=(22, 6))
        w.label(head, "设置", size="h1", bg="bg").pack(side="left")
        w.ghost(head, "测试视觉", self.test_vision).pack(side="right", padx=(8, 0))
        w.ghost(head, "测试发送", self.test_send).pack(side="right")
        w.primary(head, "保存", self.save).pack(side="right", padx=8)

        card = w.Card(self, pad=22)
        card.pack(fill="both", expand=True, padx=24, pady=10)
        body = card.body
        body.columnconfigure(1, weight=1)

        r = 0
        r = self._row(body, r, "她的微信备注")
        self.vars["remark"] = tk.StringVar()
        e = w.entry(body, self.vars["remark"], 30)
        e.grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "记住多久（天）")
        self.vars["keep_days"] = tk.StringVar()
        w.entry(body, self.vars["keep_days"], 8).grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "等待回复（分钟）")
        self.vars["wait"] = tk.StringVar()
        w.entry(body, self.vars["wait"], 8).grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "开关")
        box = tk.Frame(body, bg=COLORS["card"])
        box.grid(row=r, column=1, sticky="w")
        self.vars["dry_run"] = tk.BooleanVar()
        self.vars["warn"] = tk.BooleanVar()
        tk.Checkbutton(box, text="演练模式（只记录不真发）", variable=self.vars["dry_run"],
                       bg=COLORS["card"], activebackground=COLORS["card"],
                       font=FONTS["small"]).pack(side="left")
        tk.Checkbutton(box, text="超标时提醒她", variable=self.vars["warn"],
                       bg=COLORS["card"], activebackground=COLORS["card"],
                       font=FONTS["small"]).pack(side="left", padx=14)

        r += 1
        r = self._row(body, r, "读消息校准")
        cal = tk.Frame(body, bg=COLORS["card"])
        cal.grid(row=r, column=1, sticky="w")
        self.vars["calibrated"] = tk.BooleanVar()
        tk.Checkbutton(cal, text="已校准", variable=self.vars["calibrated"],
                       bg=COLORS["card"], activebackground=COLORS["card"],
                       font=FONTS["small"]).pack(side="left")
        self.vars["menu_dx"] = tk.StringVar()
        self.vars["menu_dy"] = tk.StringVar()
        w.label(cal, "菜单偏移", size="tiny", fg="muted").pack(side="left", padx=8)
        w.entry(cal, self.vars["menu_dx"], 4).pack(side="left")
        w.entry(cal, self.vars["menu_dy"], 4).pack(side="left", padx=4)

        r += 1
        r = self._row(body, r, "开机自启")
        self.vars["autostart"] = tk.BooleanVar()
        tk.Checkbutton(body, text="开机自动启动", variable=self.vars["autostart"],
                       bg=COLORS["card"], activebackground=COLORS["card"],
                       font=FONTS["small"]).grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "视觉识别")
        vbox = tk.Frame(body, bg=COLORS["card"])
        vbox.grid(row=r, column=1, sticky="w")
        self.vars["vision_on"] = tk.BooleanVar()
        tk.Checkbutton(vbox, text="用视觉模型读消息（能识别照片）", variable=self.vars["vision_on"],
                       bg=COLORS["card"], activebackground=COLORS["card"],
                       font=FONTS["small"]).pack(side="left")

        r += 1
        r = self._row(body, r, "API Key")
        self.vars["api_key"] = tk.StringVar()
        w.entry(body, self.vars["api_key"], 46).grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "模型")
        self.vars["vmodel"] = tk.StringVar()
        w.entry(body, self.vars["vmodel"], 34).grid(row=r, column=1, sticky="w")

        r += 1
        r = self._row(body, r, "接口地址")
        self.vars["vbase"] = tk.StringVar()
        w.entry(body, self.vars["vbase"], 40).grid(row=r, column=1, sticky="w")

        r += 1
        tk.Frame(body, bg=COLORS["border"], height=1).grid(row=r, column=0, columnspan=2,
                                                           sticky="ew", pady=14)

        for meal in MEALS:
            r += 1
            w.label(body, meal, size="h2").grid(row=r, column=0, sticky="w", pady=(8, 0))
            line = tk.Frame(body, bg=COLORS["card"])
            line.grid(row=r, column=1, sticky="ew", pady=(8, 0))
            self.vars[meal + "_time"] = tk.StringVar()
            w.entry(line, self.vars[meal + "_time"], 8).pack(side="left")
            self.vars[meal + "_ask"] = tk.StringVar()
            e = w.entry(line, self.vars[meal + "_ask"], 40)
            e.pack(side="left", fill="x", expand=True, padx=10)

        self.hint = w.label(body, "", size="small", fg="red")
        self.hint.grid(row=r + 1, column=0, columnspan=2, sticky="w", pady=12)

    def _row(self, body, r, text):
        w.label(body, text, size="small", fg="muted").grid(row=r, column=0, sticky="w", pady=7)
        return r

    def refresh(self):
        cfg = self.app.cfg
        self.vars["remark"].set(cfg.get("target_remark", ""))
        self.vars["dry_run"].set(bool(cfg.get("dry_run", True)))
        self.vars["warn"].set(bool(cfg.get("warn_on_over", True)))
        self.vars["keep_days"].set(str(cfg.get("keep_days", 60)))
        from .. import autostart
        self.vars["autostart"].set(autostart.is_enabled())
        vis = cfg.get("vision", {})
        self.vars["vision_on"].set(bool(vis.get("enabled")))
        self.vars["api_key"].set(vis.get("api_key", ""))
        self.vars["vmodel"].set(vis.get("model", "doubao-1.5-vision-pro-32k-250115"))
        self.vars["vbase"].set(vis.get("base_url", "https://ark.cn-beijing.volces.com/api/v3"))
        rd = cfg.get("reader", {})
        self.vars["calibrated"].set(bool(rd.get("calibrated")))
        self.vars["menu_dx"].set(str((rd.get("menu_offset") or [70, 0])[0]))
        self.vars["menu_dy"].set(str((rd.get("menu_offset") or [70, 0])[1]))
        self.vars["wait"].set(str(cfg.get("wait_minutes", 30)))
        for meal in MEALS:
            self.vars[meal + "_time"].set(cfg["meals"][meal]["time"])
            self.vars[meal + "_ask"].set(cfg["meals"][meal]["ask_text"])
        self.hint.configure(text="")

    def save(self):
        cfg = self.app.cfg
        cfg["target_remark"] = self.vars["remark"].get().strip()
        cfg["dry_run"] = bool(self.vars["dry_run"].get())
        cfg["warn_on_over"] = bool(self.vars["warn"].get())
        try:
            cfg["keep_days"] = int(self.vars["keep_days"].get() or 60)
            cfg["wait_minutes"] = int(self.vars["wait"].get() or 30)
        except ValueError:
            self.hint.configure(text="天数和等待时间必须是数字")
            return
        for meal in MEALS:
            cfg["meals"][meal]["time"] = self.vars[meal + "_time"].get().strip()
            cfg["meals"][meal]["ask_text"] = self.vars[meal + "_ask"].get().strip()

        errs = cfgmod.validate_settings(cfg)
        if errs:
            self.hint.configure(text="；".join(errs))
            return
        try:
            dx = int(self.vars["menu_dx"].get() or 70)
            dy = int(self.vars["menu_dy"].get() or 0)
        except ValueError:
            self.hint.configure(text="菜单偏移必须是数字")
            return
        cfg["reader"] = {"calibrated": bool(self.vars["calibrated"].get()),
                         "menu_offset": [dx, dy]}
        cfg["vision"] = {
            "enabled": bool(self.vars["vision_on"].get()),
            "api_key": self.vars["api_key"].get().strip(),
            "model": self.vars["vmodel"].get().strip() or "doubao-1.5-vision-pro-32k-250115",
            "base_url": self.vars["vbase"].get().strip() or "https://ark.cn-beijing.volces.com/api/v3",
        }
        from .. import autostart
        if self.vars["autostart"].get():
            autostart.enable()
        else:
            autostart.disable()
        cfgmod.save_config(cfg)
        self.app.reader.cfg = cfg
        self.app.reader.menu_offset = (dx, dy)
        self.hint.configure(text="已保存", fg=COLORS["green"])
        self.app.reload()

    def test_vision(self):
        from PIL import Image, ImageDraw, ImageFont
        from ..wechat import visionapi
        cfg = dict(self.app.cfg)
        cfg["vision"] = {
            "enabled": True,
            "api_key": self.vars["api_key"].get().strip(),
            "model": self.vars["vmodel"].get().strip() or "doubao-1.5-vision-pro-32k-250115",
            "base_url": self.vars["vbase"].get().strip() or "https://ark.cn-beijing.volces.com/api/v3",
        }
        if not cfg["vision"]["api_key"]:
            self.hint.configure(text="先填 API Key", fg=COLORS["red"])
            return

        img = Image.new("RGB", (420, 60), (255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)
        except Exception:
            font = ImageFont.load_default()
        d.text((12, 14), "中午吃了一碗米饭和一份红烧肉", font=font, fill=(20, 20, 20))

        def run():
            out = visionapi.read_image(cfg, img)
            self.after(0, lambda: self.hint.configure(
                text=("视觉模型返回：" + out) if out else "没返回内容，检查 Key / 模型名 / 网络",
                fg=COLORS["green"] if out else COLORS["red"]))
        threading.Thread(target=run, daemon=True).start()

    def test_send(self):
        def run():
            ok = self.app.sender.send("三餐助手测试消息", self.app.cfg.get("target_remark", ""))
            self.after(0, lambda: self.hint.configure(
                text="测试发送成功" if ok else "测试发送失败：" + (self.app.sender.last_error or ""),
                fg=COLORS["green"] if ok else COLORS["red"]))
        threading.Thread(target=run, daemon=True).start()