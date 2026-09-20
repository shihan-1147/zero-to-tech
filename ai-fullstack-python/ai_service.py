"""
【AI 能力层】ai_service.py
职责：与「智能」相关的全部逻辑都收敛在这一层。
  1. 拼上下文：从持久化层取最近对话，组装成模型消息列表（多轮对话的关键）
  2. 调模型：调用 OpenAI 兼容的 /chat/completions 接口（标准库 urllib，零额外依赖）
  3. 可降级：未配置 AI_API_KEY 时自动切换本地模拟回复，保证 demo 开箱即跑
路由层只调 chat() 这一个函数，不关心背后是真实模型还是模拟器。
"""
import json
import time
import urllib.error
import urllib.request

import config
import db


class AIServiceError(Exception):
    """类型化错误：AI 服务异常，应用层据此映射为 502"""


SYSTEM_PROMPT = "你是一个 AI 全栈开发教学助手，回答简洁清晰，多用分点说明。"


def _mock_reply(user_message: str) -> str:
    """模拟模式：让用户在没有密钥时也能看到完整的 请求→AI→落库→响应 链路"""
    return "\n".join(
        [
            f"【本地模拟模式】我收到了你的消息：「{user_message}」",
            "",
            "这条回复没有经过真实大模型，但它完整走过了全栈链路：",
            "1. 前端 fetch POST /api/chat",
            "2. FastAPI 路由层用 Pydantic 做参数校验",
            "3. AI 能力层读取历史并生成回复（当前为模拟器）",
            "4. SQLite 持久化层保存了本轮问答",
            "",
            "在 .env 中配置 AI_API_KEY 后，同样的链路将返回真实模型的回答。",
        ]
    )


def _call_llm(messages: list[dict]) -> str:
    """调用 OpenAI 兼容接口"""
    payload = json.dumps({"model": config.AI_MODEL, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(
        f"{config.AI_BASE_URL}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.AI_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise AIServiceError(f"AI 接口返回 {e.code}") from e
    except urllib.error.URLError as e:
        raise AIServiceError("无法连接 AI 服务") from e

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise AIServiceError("AI 接口返回结构异常") from e


def chat(user_message: str) -> dict:
    """
    对外唯一入口：输入用户消息，输出 AI 回复（不碰数据库写操作——
    落库由路由层编排，演示「层与层之间职责分明」的分工方式）。
    """
    # 取最近 10 条历史作为上下文 —— 多轮对话能力的核心
    history = db.recent_messages(10)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history,
                {"role": "user", "content": user_message}]

    if config.MOCK_MODE:
        time.sleep(0.4)  # 模拟网络延迟，前端 loading 态可见
        return {"reply": _mock_reply(user_message), "mode": "mock"}

    return {"reply": _call_llm(messages), "mode": "live"}
