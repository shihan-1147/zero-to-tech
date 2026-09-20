"""
【API 路由层】routes.py
职责：HTTP 边界 —— 解析请求、校验输入、编排各层调用、统一响应格式。
设计要点（教学重点）：
  - 路由里不写业务逻辑，只「编排」：db → ai → db
  - 所有输入在边界处校验（Pydantic 模型 + 业务校验）
  - 统一错误响应结构 {"error": {"code", "message"}}，前端可稳定解析
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

import ai_service
import config
import db

router = APIRouter()


class ApiError(Exception):
    """业务错误：由 main.py 的异常处理器统一转为 {"error": {...}} 响应"""

    def __init__(self, status: int, code: str, message: str):
        self.status = status
        self.code = code
        self.message = message


class ChatIn(BaseModel):
    """请求体模型：类型和长度校验由 Pydantic 自动完成"""

    message: str = Field(..., max_length=2000)


# GET /api/health —— 健康检查 + 当前 AI 模式（前端顶栏用它展示状态）
@router.get("/health")
def health():
    return {
        "status": "ok",
        "aiMode": "mock（本地模拟）" if config.MOCK_MODE else f"live（{config.AI_MODEL}）",
        "time": datetime.now(timezone.utc).isoformat(),
    }


# GET /api/messages —— 拉取全部对话历史
@router.get("/messages")
def list_all():
    return {"messages": db.list_messages()}


# POST /api/chat —— 核心链路：收消息 → AI 生成 → 双双落库 → 返回
@router.post("/chat")
def chat(body: ChatIn):
    # ① 业务校验（格式校验已被 Pydantic 处理）
    content = body.message.strip()
    if not content:
        raise ApiError(400, "INVALID_INPUT", "message 必须是非空字符串")

    # ② 持久化：先存用户消息（刷新页面也不丢）
    db.save_message("user", content)

    # ③ AI 能力层生成回复
    result = ai_service.chat(content)

    # ④ 持久化：再存 AI 回复
    record = db.save_message("assistant", result["reply"])

    # ⑤ 统一响应
    return {"reply": result["reply"], "mode": result["mode"], "record": record}


# DELETE /api/messages —— 清空历史
@router.delete("/messages")
def clear_all():
    db.clear_messages()
    return {"ok": True}
