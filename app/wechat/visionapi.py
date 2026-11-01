"""视觉模型：把消息截图交给多模态模型，直接读出文字 / 说出吃了什么。

兼容 OpenAI 格式（火山方舟 / 豆包等），只用标准库，不额外依赖。
"""
import base64
import io
import json
import urllib.request

PROMPT = (
    "这是微信聊天窗口里的一条消息截图，请只做一件事：\n"
    "1) 如果里面是文字消息，原样输出文字内容，不要解释、不要加引号、不要换行；\n"
    "2) 如果是一张食物照片，用一句话说出吃了什么、大概多少（例如：一碗米饭、一份红烧肉）；\n"
    "3) 如果什么都认不出，输出空。"
)


LOCAL_HOSTS = ("127.0.0.1", "localhost", "0.0.0.0")


def is_local(cfg: dict) -> bool:
    v = (cfg or {}).get("vision", {})
    base = str(v.get("base_url", ""))
    return any(h in base for h in LOCAL_HOSTS)


def enabled(cfg: dict) -> bool:
    v = (cfg or {}).get("vision", {})
    if not v.get("enabled"):
        return False
    # 本地部署（Ollama / LM Studio / vLLM）不需要 Key
    return bool(v.get("api_key")) or is_local(cfg)


def _post(cfg: dict, payload: dict, timeout: int = 120) -> str:
    v = cfg.get("vision", {})
    url = v.get("base_url", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if v.get("api_key"):
        headers["Authorization"] = "Bearer " + v["api_key"]
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def read_image(cfg: dict, img) -> str:
    """img: PIL.Image。返回模型读出来的文字；失败返回空串。"""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    payload = {
        "model": cfg.get("vision", {}).get("model", "doubao-1.5-vision-pro-32k-250115"),
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
            ],
        }],
        "temperature": 0,
    }
    try:
        out = _post(cfg, payload)
    except Exception:
        return ""
    return out.strip().strip("「」\"'")