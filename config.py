"""
【配置层】config.py
职责：集中管理所有环境变量，其他模块一律从这里取配置，
     不允许在代码各处散落 os.environ（便于维护、避免隐式依赖）。
为保持依赖精简，这里用十几行代码手写 .env 解析（等价于 python-dotenv）。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env() -> None:
    """读取 .env 文件注入环境变量（已存在的变量不覆盖）"""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

PORT = int(os.environ.get("PORT", "8000"))
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-4o-mini")
DB_FILE = str(BASE_DIR / "data.sqlite")

# 未配置密钥 → 本地模拟模式（demo 开箱即跑的关键设计）
MOCK_MODE = not AI_API_KEY
