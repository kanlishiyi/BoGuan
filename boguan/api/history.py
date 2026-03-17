"""
对话历史 API
=============
对话历史的持久化存储与加载。
"""

import json
import os

from fastapi import APIRouter, Depends, HTTPException

from ..config import settings
from .agents import find_agent
from .auth import require_auth
from ..core.runtime import cleanup_thread

router = APIRouter(prefix="/api/agents", tags=["history"])


# ============================================================
# 存储
# ============================================================

def _history_path(aid: str) -> str:
    d = settings.HISTORY_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{aid}.json")


def load_history(aid: str) -> dict:
    """加载指定 Agent 的对话历史。"""
    fp = _history_path(aid)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"thread_id": "", "messages": []}


def save_history(aid: str, data: dict):
    """保存对话历史。"""
    fp = _history_path(aid)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 路由
# ============================================================

@router.get("/{aid}/history")
async def get_history(aid: str, user: dict = Depends(require_auth)):
    """获取对话历史。"""
    if not find_agent(aid):
        raise HTTPException(404)
    return load_history(aid)


@router.post("/{aid}/history")
async def post_history(aid: str, body: dict, user: dict = Depends(require_auth)):
    """保存对话历史。"""
    if not find_agent(aid):
        raise HTTPException(404)
    save_history(aid, body)
    return {"ok": True}


@router.delete("/{aid}/history")
async def clear_history(aid: str, user: dict = Depends(require_auth)):
    """清除对话历史。"""
    fp = _history_path(aid)
    if os.path.exists(fp):
        os.remove(fp)
    cleanup_thread(aid)
    return {"ok": True}
