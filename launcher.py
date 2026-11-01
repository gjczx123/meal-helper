"""程序入口：双击运行。可带 --page 参数直接打开某一页（调试用）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.app import main  # noqa: E402

if __name__ == "__main__":
    page = "today"
    if "--page" in sys.argv:
        page = sys.argv[sys.argv.index("--page") + 1]
    main(page)
