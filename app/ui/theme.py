"""配色与字体。"""

COLORS = {
    "bg": "#F2F4F8",
    "sidebar": "#1E2432",
    "sidebar_hover": "#2A3244",
    "sidebar_active": "#2F6BFF",
    "card": "#FFFFFF",
    "border": "#E4E8F0",
    "text": "#1B1F27",
    "muted": "#7A8496",
    "green": "#1FA971",
    "amber": "#E0990B",
    "red": "#E5484D",
    "blue": "#2F6BFF",
    "grey": "#9AA4B2",
}

FONTS = {
    "logo": ("Microsoft YaHei UI", 16, "bold"),
    "h1": ("Microsoft YaHei UI", 17, "bold"),
    "h2": ("Microsoft YaHei UI", 12, "bold"),
    "body": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "tiny": ("Microsoft YaHei UI", 8),
    "num": ("Microsoft YaHei UI", 20, "bold"),
}

STATUS_TEXT = {
    "normal": "正常",
    "over": "超标",
    "fasting": "未进食",
    "unparsed": "未识别",
    "missed": "未报备",
    "waiting": "等待中",
    "pending": "未到",
    "sent": "已提醒",
}

STATUS_COLOR = {
    "normal": COLORS["green"],
    "over": COLORS["red"],
    "fasting": COLORS["muted"],
    "unparsed": COLORS["amber"],
    "missed": COLORS["grey"],
    "waiting": COLORS["blue"],
    "pending": COLORS["grey"],
    "sent": COLORS["blue"],
}


def status_text(s: str) -> str:
    return STATUS_TEXT.get(s, s or "—")


def status_color(s: str) -> str:
    return STATUS_COLOR.get(s, COLORS["grey"])
