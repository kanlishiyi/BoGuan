"""
工具包装器
==========
- 自动重试：MCP 工具调用失败时自动重试，全部失败后返回错误信息让 Agent 跳过
- 中文显示名：将工具函数名映射为用户友好的中文名称
"""

import asyncio
from typing import Callable, Optional

from langchain_core.tools import StructuredTool

from ..config import settings

# ============================================================
# 工具中文显示名
# ============================================================

#: 预定义的工具中文名称映射
KNOWN_TOOL_NAMES: dict[str, str] = {
    # 告警类
    "get_alert_by_id": "获取告警详情",
    "search_alerts": "搜索告警列表",
    "get_vertical_influence": "获取纵向影响范围",
    "get_horizontal_influence": "获取横向影响范围",
    # 实体信息类
    "get_target_info_by_target_id": "获取实体信息",
    "get_owner_host": "获取所属主机",
    "get_host_id_by_ip": "通过IP查询主机",
    "get_target_id_by_name": "通过名称查询实体",
    # 关联分析类
    "one_query_relationship": "一键关联查询",
    "query_entity_relationship_path": "查询实体关系路径",
    "get_service_by_interface": "通过接口获取服务",
    # 资源监控类
    "list_cpu_top_processes": "查看CPU高消耗进程",
    "list_memory_top_processes": "查看内存高消耗进程",
    "check_process": "检查进程状态",
    "check_port": "检查端口状态",
    "list_disk_usage": "查看磁盘使用",
    "list_network_connections": "查看网络连接",
    # 日志/事件类
    "list_logs": "查询日志",
    "query_rizhiy_logs": "查询日志平台日志",
    "list_events": "查询事件列表",
    "search_log_patterns": "搜索日志模式",
    # APM 链路类
    "list_apm_traces": "查询APM链路追踪",
    "get_trace_detail_by_id": "获取链路详情",
    "list_apm_services": "查询APM服务列表",
    "list_apm_interfaces": "查询APM接口列表",
    "list_apm_exceptions": "查询APM异常列表",
    # 指标类
    "query_metric_by_target_id": "查询指标数据",
    "list_metrics": "列出可用指标",
    "query_metric_top": "查询指标TopN",
    # 变更类
    "query_change_order_by_service": "查询服务变更工单",
    "cms_get_change_order": "获取变更工单详情",
    # 知识库
    "search_knowledge_chunks": "搜索知识库",
    # 内建
    "write_todos": "更新执行计划",
}

_display_map: dict[str, str] = {}


def build_tool_display_map(tools: list) -> None:
    """从工具描述中构建显示名映射，优先使用预定义名称。"""
    _display_map.clear()
    _display_map.update(KNOWN_TOOL_NAMES)
    for t in tools:
        if t.name not in _display_map:
            desc = (t.description or "").strip()
            if desc:
                first_line = desc.split("\n")[0].strip()
                for sep in ["。", ".", "，"]:
                    if sep in first_line:
                        first_line = first_line.split(sep)[0]
                        break
                if len(first_line) > 25:
                    first_line = first_line[:22] + "..."
                _display_map[t.name] = first_line
            else:
                _display_map[t.name] = t.name


def get_tool_display_name(name: str) -> str:
    """获取工具的中文显示名称。"""
    return _display_map.get(name, name)


# ============================================================
# 工具重试包装器
# ============================================================


def wrap_tools_with_retry(
    tools: list,
    max_retries: int = 0,
    retry_delay: float = 0.0,
    retry_queue: Optional[asyncio.Queue] = None,
    display_name_fn: Optional[Callable] = None,
) -> list:
    """
    为工具列表添加自动重试机制。

    参数:
        tools: 原始工具列表
        max_retries: 最大重试次数（默认从配置读取）
        retry_delay: 重试间隔秒数（默认从配置读取）
        retry_queue: 可选队列，推送重试事件到 SSE 流
        display_name_fn: 可选函数，获取工具中文名用于事件推送

    返回:
        包装后的工具列表（重试失败返回错误信息而非抛异常）
    """
    if max_retries <= 0:
        max_retries = settings.TOOL_MAX_RETRIES
    if retry_delay <= 0:
        retry_delay = settings.TOOL_RETRY_DELAY

    def _make_retry_coro(orig_tool):
        _raw_coro = getattr(orig_tool, "coroutine", None)
        _raw_func = getattr(orig_tool, "func", None)

        async def _invoke_with_retry(**kwargs):
            last_error = None
            for attempt in range(1, max_retries + 1):
                try:
                    if _raw_coro:
                        return await _raw_coro(**kwargs)
                    elif _raw_func:
                        return _raw_func(**kwargs)
                    else:
                        return await orig_tool.ainvoke(kwargs)
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if len(err_str) > 200:
                        err_str = err_str[:200] + "..."
                    print(
                        f"  [重试 {attempt}/{max_retries}] "
                        f"工具 '{orig_tool.name}' 调用失败: {err_str}"
                    )
                    if retry_queue:
                        dn = (
                            display_name_fn(orig_tool.name)
                            if display_name_fn
                            else orig_tool.name
                        )
                        await retry_queue.put({
                            "name": orig_tool.name,
                            "display_name": dn,
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "error": err_str,
                        })
                    if attempt < max_retries:
                        print(f"    {retry_delay} 秒后重试...")
                        await asyncio.sleep(retry_delay)

            error_msg = (
                f"[工具调用失败] '{orig_tool.name}' 已重试{max_retries}次仍然失败，"
                f"最后错误: {last_error}。请跳过此工具，继续执行后续步骤。"
            )
            print(f"  [跳过] {error_msg}")
            return error_msg

        return _invoke_with_retry

    return [
        StructuredTool(
            name=t.name,
            description=t.description,
            args_schema=t.args_schema,
            coroutine=_make_retry_coro(t),
        )
        for t in tools
    ]
