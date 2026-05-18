from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router, auth_router
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
    title="Voyager API",
    description="Voyager — AI 智能旅行助手",
    version="2.0.0"
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
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# 内存限流器
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = settings.RATE_LIMIT_REQUESTS
RATE_LIMIT_WINDOW = 60
_last_cleanup = time.time()
CLEANUP_INTERVAL = 300

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 认证端点豁免限流（有自己的保护机制）
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/auth/"):
        global _last_cleanup
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

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

@app.on_event("startup")
def startup():
    from app.database import init_db
    init_db()
    logging.info("数据库初始化完成")

app.include_router(router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Voyager API", "status": "running", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
