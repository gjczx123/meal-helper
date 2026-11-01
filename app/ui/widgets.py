"""小部件：卡片、标签、按钮。"""
import tkinter as tk

from .theme import COLORS, FONTS


class Card(tk.Frame):
    def __init__(self, master, pad=16, **kw):
        super().__init__(master, bg=COLORS["card"], highlightbackground=COLORS["border"],
                         highlightthickness=1, **kw)
        self.body = tk.Frame(self, bg=COLORS["card"])
        self.body.pack(fill="both", expand=True, padx=pad, pady=pad)


class Pill(tk.Label):
    def __init__(self, master, text="", color=None, bg=None):
        super().__init__(master, text=text, fg="#FFFFFF",
                         bg=color or COLORS["grey"], font=FONTS["small"],
                         padx=10, pady=2)
        self._bg = bg

    def set(self, text, color):
        self.configure(text=text, bg=color)


def primary(master, text, command=None, width=None):
    return tk.Button(master, text=text, command=command, bg=COLORS["blue"], fg="white",
                     activebackground="#2557D6", activeforeground="white",
                     relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                     font=FONTS["body"], width=width)


def ghost(master, text, command=None):
    return tk.Button(master, text=text, command=command, bg=COLORS["card"], fg=COLORS["text"],
                     activebackground="#F0F3F9", relief="flat", bd=0, padx=12, pady=7,
                     cursor="hand2", font=FONTS["body"],
                     highlightbackground=COLORS["border"], highlightthickness=1)


def label(master, text, size="body", fg="text", bg="card", **kw):
    return tk.Label(master, text=text, font=FONTS[size], fg=COLORS[fg],
                    bg=COLORS[bg], **kw)


def entry(master, textvariable=None, width=24):
    e = tk.Entry(master, textvariable=textvariable, width=width, font=FONTS["body"],
                 relief="flat", bg="#F7F9FC", fg=COLORS["text"],
                 highlightbackground=COLORS["border"], highlightthickness=1,
                 insertbackground=COLORS["text"])
    return e

def MEALS_PLAN(day: dict, meal: str) -> list:
    return (day.get("meals") or {}).get(meal) or []
