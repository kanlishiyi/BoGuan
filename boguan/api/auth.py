"""
认证 API
========
登录 / 登出 / 当前用户信息。
使用简单的 Token 机制（内存存储，适合单实例部署）。
"""

import hashlib
import json
import os
import secrets
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from ..config import settings
from ..models import LoginBody

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============================================================
# 用户存储
# ============================================================
_active_tokens: Dict[str, dict] = {}  # token -> user info


def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def _load_users() -> List[dict]:
    fp = settings.USERS_DATA_FILE
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_users(users: List[dict]):
    fp = settings.USERS_DATA_FILE
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def ensure_default_user():
    """确保存在默认管理员账号（首次启动时调用）。"""
    users = _load_users()
    if not users:
        users = [{
            "username": "admin",
            "password": _hash_pwd(settings.DEFAULT_ADMIN_PASSWORD),
            "display_name": "管理员",
            "role": "admin",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }]
        _save_users(users)
        print(f"[启动] 已创建默认管理员账号: admin / {settings.DEFAULT_ADMIN_PASSWORD}")


# ============================================================
# Token 验证
# ============================================================

def verify_token(token: str) -> Optional[dict]:
    return _active_tokens.get(token)


async def require_auth(request: Request) -> dict:
    """FastAPI 依赖：从请求中提取并验证 token。"""
    # 优先从 Header 获取
    auth = request.headers.get("Authorization", "")
    token = ""
    if auth.startswith("Bearer "):
        token = auth[7:]
    # SSE 请求通过 query param 传递 token
    if not token:
        token = request.query_params.get("token", "")
    if not token:
        raise HTTPException(401, "未登录，请先登录")
    user = verify_token(token)
    if not user:
        raise HTTPException(401, "登录已过期，请重新登录")
    return user


# ============================================================
# 路由
# ============================================================

@router.post("/login")
async def login(body: LoginBody):
    """用户登录，返回 token。"""
    users = _load_users()
    pwd_hash = _hash_pwd(body.password)
    for u in users:
        if u["username"] == body.username and u["password"] == pwd_hash:
            token = secrets.token_hex(32)
            _active_tokens[token] = {
                "username": u["username"],
                "display_name": u.get("display_name", u["username"]),
                "role": u.get("role", "user"),
                "login_time": time.time(),
            }
            return {
                "ok": True,
                "token": token,
                "user": {
                    "username": u["username"],
                    "display_name": u.get("display_name", u["username"]),
                    "role": u.get("role", "user"),
                },
            }
    raise HTTPException(401, "用户名或密码错误")


@router.post("/logout")
async def logout(request: Request):
    """用户登出。"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        _active_tokens.pop(auth[7:], None)
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(require_auth)):
    """获取当前用户信息。"""
    return {"ok": True, "user": user}
