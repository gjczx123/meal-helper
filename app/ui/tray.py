"""托盘图标：关窗口后还能叫她出来。"""
import threading
import time

from PIL import Image

from .. import paths

try:
    import pystray
    from pystray import Menu, MenuItem
except Exception:  # pragma: no cover
    pystray = None


def start(app):
    if pystray is None:
        return None
    try:
        image = Image.open(paths.resource("icon.png"))
    except Exception:
        image = Image.new("RGB", (64, 64), "#1E2432")

    def open_window(icon, item):
        app.after(0, app.deiconify)

    def ask_now(icon, item):
        app.after(0, app.remind_now)

    def toggle_run(icon, item):
        app.after(0, app.toggle_running)

    def quit_app(icon, item):
        icon.stop()
        app.after(0, app.destroy)

    menu = Menu(
        MenuItem("打开", open_window, default=True),
        MenuItem("立即提醒", ask_now),
        MenuItem(lambda item: "暂停自动提醒" if app.cfg.get("running") else "恢复自动提醒",
                 toggle_run),
        Menu.SEPARATOR,
        MenuItem("退出", quit_app),
    )
    icon = pystray.Icon("meal_helper", image, "三餐助手", menu)
    threading.Thread(target=icon.run, daemon=True).start()

    def watchdog():
        # 托盘没起来就别把窗口藏了，否则叫不回来
        time.sleep(2.5)
        if not getattr(icon, "visible", False):
            app.tray = None

    threading.Thread(target=watchdog, daemon=True).start()
    return icon