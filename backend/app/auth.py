"""
JWT + bcrypt 认证模块。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Request, HTTPException
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            return None
        return {"user_id": int(user_id), "email": email}
    except JWTError:
        return None


def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def get_current_user(request: Request) -> Optional[dict]:
    """从请求中解析当前用户，未登录返回 None（不抛异常）。"""
    token = _extract_token(request)
    if not token:
        return None
    return decode_access_token(token)


def require_user(request: Request) -> dict:
    """要求用户已登录，未登录抛 401。"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user
