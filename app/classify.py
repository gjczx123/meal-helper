"""用本地小模型判断一句话是不是在报备吃喝。

只在规则词表完全没命中时才调用，省钱省显存。
"""
import json
import urllib.request

from . import logger

PROMPT = (
    "判断下面这句话是不是在说「吃了什么 / 喝了什么 / 吃没吃」。\n"
    "只回答一个字：是 或 否。\n"
    "句子："
)


def enabled(cfg: dict) -> bool:
    c = (cfg or {}).get("classify", {})
    return bool(c.get("enabled", True))


def is_meal_report(cfg: dict, text: str) -> bool:
    """True = 当成报备；False = 闲聊。调用失败时保守地返回 True（宁可多记）。"""
    c = cfg.get("classify", {})
    base = str(c.get("base_url", "http://127.0.0.1:11434")).rstrip("/").replace("/v1", "")
    payload = {
        "model": c.get("model", "qwen2.5vl:3b"),
        "messages": [{"role": "user", "content": PROMPT + text}],
        "stream": False,
        "keep_alive": c.get("keep_alive", "30s"),
        "options": {"temperature": 0, "num_ctx": 512},
    }
    try:
        req = urllib.request.Request(base + "/api/chat",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        ans = ((body.get("message") or {}).get("content") or "").strip()
    except Exception as e:
        logger.get().warning("分类失败，按报备处理：%s", e)
        return True

    head = ans[:4]
    if "否" in head or head.lower().startswith("no"):
        return False
    if "是" in head or head.lower().startswith("yes"):
        return True
    return True
