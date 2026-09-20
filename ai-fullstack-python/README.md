# AI 全栈开发教学示例（Python 版）

与 `ai-fullstack-demo`（Node.js 版）**功能完全等价**的 Python 实现：
FastAPI 后端 + SQLite 持久化 + AI 能力集成 + 原生前端。
两个版本 API 契约完全一致，**前端代码一字未改直接复用** ——
这就是「前后端分离」的核心价值：后端换语言，前端零感知。

## 快速开始

```bash
pip install -r requirements.txt
python -m uvicorn main:app --port 8000     # 打开 http://localhost:8000
```

无需任何 API 密钥即可运行（自动进入「本地模拟模式」）。
要接入真实大模型：复制 `.env.example` 为 `.env`，填入 `AI_API_KEY` 即可，代码零改动。

## 与 Node 版的逐层对照（学习重点）

| 层 | Node 版 | Python 版 | 变化点 |
|----|---------|-----------|--------|
| 入口 | `server.js` | `main.py` | Express `app.use` → FastAPI 路由挂载 + 异常处理器 |
| 路由层 | `src/routes.js` | `routes.py` | 手写校验 → Pydantic 模型自动校验；装饰器注册路由 |
| AI 能力层 | `src/ai.js` | `ai_service.py` | 全局 `fetch` → 标准库 `urllib.request` |
| 持久化层 | `src/db.js` | `db.py` | `node:sqlite` → 标准库 `sqlite3`（需处理跨线程） |
| 配置层 | `src/config.js` | `config.py` | `process.loadEnvFile` → 手写 .env 解析 |
| 前端 | `public/` | `public/` | **完全相同，零改动** |

## 架构总览

```
浏览器                Python 进程（全栈单体）
┌──────────────┐    ┌──────────────────────────────────────────────┐
│  public/     │    │  main.py         应用入口：异常处理+挂载      │
│  index.html  │──▶ │  routes.py       路由层：Pydantic 校验、编排  │
│  app.js      │◀── │  ai_service.py   AI 能力层：上下文+调模型     │
│  style.css   │JSON│  db.py           持久化层：SQLite 读写        │
└──────────────┘    │  config.py       配置层：集中管理环境变量     │
                    └──────────────┬───────────────────────────────┘
                                   ▼
                    data.sqlite（对话记录，重启不丢）
```

## 一次对话的完整链路

以用户发送「你好」为例，对应 `POST /api/chat`：

| 步骤 | 发生位置 | 做了什么 |
|------|----------|----------|
| 1 | `public/app.js` | `fetch` 发 JSON，进入 loading 态 |
| 2 | `routes.py` | Pydantic 校验格式 + 业务校验非空 |
| 3 | `db.py` | 用户消息先落库 |
| 4 | `ai_service.py` | 取最近 10 条历史拼上下文 → 调模型/模拟器 |
| 5 | `db.py` | AI 回复落库 |
| 6 | `main.py` | 异常统一映射为 `{"error": {"code", "message"}}` |
| 7 | `public/app.js` | 渲染回复（`textContent` 防 XSS） |

## API 一览（与 Node 版完全一致）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 + 当前 AI 模式 |
| GET | `/api/messages` | 拉取全部对话历史 |
| POST | `/api/chat` | 发送消息，Body: `{ "message": "..." }` |
| DELETE | `/api/messages` | 清空历史 |

FastAPI 附带免费福利：访问 `http://localhost:8000/docs` 可看自动生成的交互式 API 文档。

## 验证

```bash
python smoke.py   # 端到端冒烟：健康/聊天/持久化/校验/清空 五项检查
```

## Python 版特有的实现细节

- **sqlite3 跨线程**：FastAPI 同步端点运行在线程池，`check_same_thread=False` + 锁串行化写入
- **异步选择**：本 demo 端点为同步 `def`（DB/HTTP 均为阻塞调用）；引入 `httpx.AsyncClient` 后可平滑改为 `async def`
- **类型即文档**：`ChatIn(BaseModel)` 既是校验器，也是 `/docs` 里的请求 schema
