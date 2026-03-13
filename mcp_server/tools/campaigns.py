"""MCP tools — campaign management."""

from __future__ import annotations

import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def manage_campaigns(
    action: str,
    campaign_id: int | None = None,
    name: str | None = None,
    template_id: int | None = None,
    segment_id: int | None = None,
    sender_email: str | None = None,
    sender_name: str | None = None,
    reply_to: str | None = None,
    rate_limit: int = 10,
    scheduled_at: str | None = None,
    page: int = 1,
    page_size: int = 50,
    log_status: str | None = None,
) -> str:
    """群发活动管理。

    action 可选值:
    - "create": 创建活动草稿（需 name + template_id + sender_email，可选 segment_id/rate_limit）
    - "list": 列出所有活动
    - "get": 获取活动详情（需 campaign_id）
    - "send": 立即发送（需 campaign_id）
    - "schedule": 定时发送（需 campaign_id + scheduled_at，ISO格式如 "2026-03-15T09:00:00"）
    - "pause": 暂停发送中的活动（需 campaign_id）
    - "cancel": 取消活动（需 campaign_id）
    - "stats": 获取活动实时统计（需 campaign_id）— 返回打开率/点击率/弹回率
    - "logs": 获取发送日志（需 campaign_id，可选 log_status 筛选）
    """
    try:
        if action == "create":
            if not name or not template_id or not sender_email:
                return _error_text("创建活动需要 name, template_id, sender_email")
            data = {
                "name": name,
                "template_id": template_id,
                "sender_email": sender_email,
                "rate_limit": rate_limit,
            }
            if segment_id: data["segment_id"] = segment_id
            if sender_name: data["sender_name"] = sender_name
            if reply_to: data["reply_to"] = reply_to
            result = await api.post("/api/v1/campaigns", data)
            return _json_text(result)

        elif action == "list":
            result = await api.get("/api/v1/campaigns")
            return _json_text(result)

        elif action == "get":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.get(f"/api/v1/campaigns/{campaign_id}")
            return _json_text(result)

        elif action == "send":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.post(f"/api/v1/campaigns/{campaign_id}/send")
            return _json_text(result)

        elif action == "schedule":
            if not campaign_id or not scheduled_at:
                return _error_text("需要 campaign_id 和 scheduled_at")
            result = await api.post(
                f"/api/v1/campaigns/{campaign_id}/schedule",
                {"scheduled_at": scheduled_at},
            )
            return _json_text(result)

        elif action == "pause":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.post(f"/api/v1/campaigns/{campaign_id}/pause")
            return _json_text(result)

        elif action == "cancel":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.post(f"/api/v1/campaigns/{campaign_id}/cancel")
            return _json_text(result)

        elif action == "stats":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.get(f"/api/v1/campaigns/{campaign_id}/stats")
            return _json_text(result)

        elif action == "logs":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            params = {"page": page, "page_size": page_size}
            if log_status: params["status"] = log_status
            result = await api.get(f"/api/v1/campaigns/{campaign_id}/logs", params)
            return _json_text(result)

        else:
            return _error_text(f"未知 action: {action}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
