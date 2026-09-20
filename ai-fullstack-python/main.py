"""
【应用入口】main.py
职责：把各层组装起来 —— 应用实例、异常处理、API 路由、静态前端托管。
     这是典型的「全栈单体」形态：一个 Python 进程同时服务前端页面和后端接口。

请求链路总览：
  浏览器(public/) ──HTTP──> FastAPI 路由(routes.py)
                               ├─> AI 能力层(ai_service.py) ──> 大模型 API / 本地模拟
                               └─> 持久化层(db.py)         ──> SQLite 文件(data.sqlite)

启动方式：python -m uvicorn main:app --port 8000
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import ai_service
import config
import routes

app = FastAPI(title="AI 全栈教学示例（Python 版）")


def _error(status: int, code: str, message: str) -> JSONResponse:
    """统一错误响应结构，与 Node 版完全一致（前端零改动的原因就在这）"""
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


# 业务错误（路由层主动抛出）
@app.exception_handler(routes.ApiError)
async def api_error_handler(_req: Request, exc: routes.ApiError):
    return _error(exc.status, exc.code, exc.message)


# 请求格式错误（Pydantic 校验失败，如 message 超长/缺失）
@app.exception_handler(RequestValidationError)
async def validation_error_handler(_req: Request, _exc: RequestValidationError):
    return _error(400, "INVALID_INPUT", "请求格式不正确：message 需为不超过 2000 字的字符串")


# AI 上游错误（类型化错误 → 502）
@app.exception_handler(ai_service.AIServiceError)
async def ai_error_handler(_req: Request, _exc: ai_service.AIServiceError):
    return _error(502, "AI_UPSTREAM_ERROR", "AI 服务暂时不可用，请稍后重试")


# 兜底错误 → 500
@app.exception_handler(Exception)
async def fallback_error_handler(_req: Request, exc: Exception):
    print(f"[ERROR] {type(exc).__name__}: {exc}")
    return _error(500, "INTERNAL_ERROR", "服务器内部错误")


# 挂载 API 路由
app.include_router(routes.router, prefix="/api")

# 托管前端静态资源（注意：必须放在 API 路由之后挂载到根路径）
app.mount("/", StaticFiles(directory=config.BASE_DIR / "public", html=True), name="static")
