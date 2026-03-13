"""MCP tools — email reports."""

from __future__ import annotations

import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def get_email_reports(
    report_type: str,
    campaign_id: int | None = None,
    days: int = 30,
    limit: int = 20,
) -> str:
    """获取邮件营销报表。

    report_type 可选值:
    - "overview": 全局概览（联系人总数、发送总量、平均打开率/点击率）
    - "campaign": 单活动详细报告（需 campaign_id）
    - "trends": 近 N 天趋势（发送量/打开量/点击量按天聚合，可选 days 参数）
    - "engagement": 联系人活跃度排名（可选 limit 参数）
    """
    try:
        if report_type == "overview":
            result = await api.get("/api/v1/reports/overview")
            return _json_text(result)

        elif report_type == "campaign":
            if not campaign_id:
                return _error_text("需要 campaign_id")
            result = await api.get(f"/api/v1/reports/campaigns/{campaign_id}")
            return _json_text(result)

        elif report_type == "trends":
            result = await api.get("/api/v1/reports/trends", {"days": days})
            return _json_text(result)

        elif report_type == "engagement":
            result = await api.get("/api/v1/reports/contacts/engagement", {"limit": limit})
            return _json_text(result)

        else:
            return _error_text(f"未知 report_type: {report_type}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
