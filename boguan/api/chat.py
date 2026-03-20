"""
对话 SSE API
=============
Agent 对话接口，使用 Server-Sent Events 流式推送。
"""

import asyncio
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from sse_starlette.sse import EventSourceResponse

from ..core.runtime import (
    active_threads,
    agent_thread_map,
    build_runtime,
    new_thread_id,
    restore_messages_from_history,
    thread_turns,
)
from .agents import find_agent
from .auth import require_auth
from .history import load_history

router = APIRouter(tags=["chat"])


def _sse(evt: str, data: dict) -> dict:
    return {"event": evt, "data": json.dumps(data, ensure_ascii=False)}


def _fmt(args, mx: int = 300) -> str:
    try:
        s = json.dumps(args, ensure_ascii=False)
    except Exception:
        s = str(args)
    return s[:mx] + "..." if len(s) > mx else s


def _extract_todos(payload: Any) -> list[dict]:
    """
    从 write_todos 的参数或返回值中提取标准 todo 列表。
    """
    data = payload
    if hasattr(data, "content"):
        data = getattr(data, "content")
    if isinstance(data, str):
        s = data.strip()
        try:
            data = json.loads(s)
        except Exception:
            return []

    if isinstance(data, dict):
        if isinstance(data.get("todos"), list):
            data = data["todos"]
        elif isinstance(data.get("items"), list):
            data = data["items"]
        else:
            return []

    if not isinstance(data, list):
        return []

    out: list[dict] = []
    for i, it in enumerate(data):
        if not isinstance(it, dict):
            continue
        out.append(
            {
                "id": str(it.get("id") or f"todo_{i+1}"),
                "content": str(it.get("content") or it.get("title") or ""),
                "status": str(it.get("status") or "pending"),
            }
        )
    return out


@router.get("/api/agents/{aid}/chat")
async def chat(aid: str, message: str, thread_id: str = "", user: dict = Depends(require_auth)):
    """Agent 对话（SSE 流式响应）。"""
    cfg = find_agent(aid)
    if not cfg:
        raise HTTPException(404)

    async def gen():
        nonlocal thread_id

        # ---- 多轮对话：thread_id 管理与上下文恢复 ----
        need_restore = False
        restored_msgs = []

        if thread_id and thread_id not in active_threads:
            # 可能是服务重启后的续接
            old_tid = thread_id
            thread_id = new_thread_id()
            history = load_history(aid)
            msgs = history.get("messages", [])
            restored_msgs = restore_messages_from_history(msgs, max_pairs=10)
            if restored_msgs:
                need_restore = True
                user_count = sum(1 for m in restored_msgs if isinstance(m, HumanMessage))
                thread_turns[thread_id] = user_count
                print(
                    f"  [多轮恢复] Agent {aid}: 从历史恢复 {len(restored_msgs)} 条消息 "
                    f"(原 thread={old_tid} → 新 thread={thread_id})"
                )
        elif not thread_id:
            thread_id = new_thread_id()

        # 更新轮次
        turn = thread_turns.get(thread_id, 0) + 1
        thread_turns[thread_id] = turn

        yield _sse("start", {"thread_id": thread_id, "turn": turn})

        if need_restore:
            yield _sse("status", {"text": f"正在恢复对话上下文（{len(restored_msgs)} 条历史消息）..."})

        # ---- 构建运行时 ----
        sq = asyncio.Queue()

        async def scb(m):
            await sq.put(m)

        try:
            task = asyncio.create_task(build_runtime(cfg, status_cb=scb))
            while not task.done():
                try:
                    m = await asyncio.wait_for(sq.get(), timeout=0.3)
                    yield _sse("status", {"text": m})
                except asyncio.TimeoutError:
                    pass
            while not sq.empty():
                yield _sse("status", {"text": await sq.get()})
            rt = await task
        except Exception as e:
            yield _sse("error", {"message": f"初始化失败: {e}"})
            yield _sse("done", {"thread_id": thread_id, "turn": turn, "steps": 0})
            return

        rcfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 60}
        step = 0

        # ---- 构建输入消息 ----
        if need_restore and restored_msgs:
            input_messages = restored_msgs + [HumanMessage(content=message)]
        else:
            input_messages = [{"role": "user", "content": message}]

        if turn > 1 and not need_restore:
            yield _sse("status", {"text": f"多轮对话 · 第 {turn} 轮"})

        # ---- 流式处理 ----
        print(f"  [chat] 开始流式处理: agent={aid}, thread={thread_id}, turn={turn}")
        print(f"  [chat] 输入消息数: {len(input_messages)}, 工具数: {rt['n']}")
        event_count = 0
        try:
            async for ev in rt["agent"].astream_events(
                {"messages": input_messages},
                config=rcfg,
                version="v2",
            ):
                kind = ev.get("event", "")
                name = ev.get("name", "")
                data = ev.get("data", {})
                event_count += 1

                if kind == "on_chat_model_start":
                    step += 1
                    print(f"  [chat] LLM 开始 step={step}")
                    yield _sse("llm_start", {"step": step})

                elif kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if not chunk:
                        continue
                    content = getattr(chunk, "content", "")
                    if isinstance(content, str) and content:
                        yield _sse("token", {"text": content})
                    elif isinstance(content, list):
                        for b in content:
                            if isinstance(b, dict):
                                if b.get("type") == "text" and b.get("text"):
                                    yield _sse("token", {"text": b["text"]})
                                elif b.get("type") == "thinking" and b.get("thinking"):
                                    yield _sse("thinking", {"text": b["thinking"]})

                elif kind == "on_chat_model_end":
                    output = data.get("output")
                    if output:
                        tool_calls = getattr(output, "tool_calls", [])
                        if tool_calls:
                            print(f"  [chat] LLM 输出 tool_calls: {[tc['name'] for tc in tool_calls]}")
                        for tc in tool_calls:
                            if tc["name"] == "write_todos":
                                todos = _extract_todos(tc.get("args", {}))
                                if todos:
                                    yield _sse("plan_update", {
                                        "source": "write_todos_call",
                                        "todos": todos,
                                    })
                                continue
                            else:
                                yield _sse("tool_call", {
                                    "name": tc["name"],
                                    "args": _fmt(tc.get("args", {})),
                                })

                elif kind == "on_tool_start":
                    if name == "write_todos":
                        # 更可靠：直接从工具启动事件中提取本次 write_todos 入参
                        todos = _extract_todos(
                            data.get("input")
                            or data.get("args")
                            or data.get("kwargs")
                            or {}
                        )
                        if todos:
                            yield _sse("plan_update", {
                                "source": "write_todos_start",
                                "todos": todos,
                            })
                    else:
                        print(f"  [chat] 工具开始: {name}")

                elif kind == "on_tool_end":
                    if name == "write_todos":
                        todos = _extract_todos(data.get("output"))
                        if todos:
                            yield _sse("plan_update", {
                                "source": "write_todos_result",
                                "todos": todos,
                            })
                        continue
                    print(f"  [chat] 工具完成: {name}")
                    output = data.get("output")
                    if output:
                        r = str(getattr(output, "content", str(output)))
                        if len(r) > 1500:
                            r = r[:1500] + "\n...(截断)"
                        yield _sse("tool_end", {"name": name, "result": r})

        except Exception as e:
            print(f"  [chat] 流式处理异常: {e}")
            import traceback
            traceback.print_exc()
            yield _sse("error", {"message": str(e)})

        print(f"  [chat] 流式处理结束: events={event_count}, steps={step}")

        # 标记 thread 激活
        active_threads.add(thread_id)
        agent_thread_map[aid] = thread_id
        yield _sse("done", {"thread_id": thread_id, "turn": turn, "steps": step})

    return EventSourceResponse(gen())
