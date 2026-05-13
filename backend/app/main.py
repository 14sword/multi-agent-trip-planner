from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.config import settings
import time
import logging
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="智能旅行助手 API",
    description="基于多智能体的旅行规划系统",
    version="1.0.0"
)

# CORS: 开发环境允许 localhost，生产环境从环境变量读取
ALLOWED_ORIGINS = settings.CORS_ORIGINS or [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# 简易内存限流器
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = 10  # 窗口内最大请求数
RATE_LIMIT_WINDOW = 60    # 窗口秒数
_last_cleanup = time.time()
CLEANUP_INTERVAL = 300    # 每5分钟清理一次过期key

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        global _last_cleanup
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # 定期清理过期key，防止内存无限增长
        if now - _last_cleanup > CLEANUP_INTERVAL:
            _last_cleanup = now
            empty_keys = [k for k, v in _rate_limit_store.items() if not v or now - v[-1] > RATE_LIMIT_WINDOW * 2]
            for k in empty_keys:
                del _rate_limit_store[k]

        key = f"{client_ip}:{request.url.path}"
        _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]
        if len(_rate_limit_store[key]) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"error": "请求过于频繁，请稍后再试"}
            )
        _rate_limit_store[key].append(now)
    response = await call_next(request)
    return response

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "智能旅行助手 API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
