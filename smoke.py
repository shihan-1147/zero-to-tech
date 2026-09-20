"""端到端冒烟测试：依次打 5 个检查点，结果写入 smoke-result.json"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api"
results = {}


def req(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


try:
    # 1. 健康检查
    _, results["health"] = req("GET", "/health")

    # 2. 发送消息（核心链路：路由 → AI → 落库）
    _, chat = req("POST", "/chat", {"message": "你好，请用一句话介绍什么是全栈开发"})
    results["chat"] = {"mode": chat.get("mode"), "replyPreview": (chat.get("reply") or "")[:60]}

    # 3. 拉取历史（验证持久化：应包含刚才两条）
    _, msgs = req("GET", "/messages")
    results["historyCount"] = len(msgs["messages"])
    results["historyRoles"] = [m["role"] for m in msgs["messages"]]

    # 4. 输入校验（空消息应返回 400，且为统一错误结构）
    status, bad = req("POST", "/chat", {"message": "  "})
    results["invalidInputStatus"] = status
    results["invalidInputShape"] = bad

    # 5. 清空历史（应归零）
    req("DELETE", "/messages")
    _, after = req("GET", "/messages")
    results["afterClear"] = len(after["messages"])
except Exception as e:  # noqa: BLE001
    results["fatal"] = repr(e)

with open("smoke-result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("smoke done")
