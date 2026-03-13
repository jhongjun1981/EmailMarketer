"""MCP tools — email template management."""

from __future__ import annotations

import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def manage_templates(
    action: str,
    template_id: int | None = None,
    name: str | None = None,
    subject: str | None = None,
    html_body: str | None = None,
    text_body: str | None = None,
    variables: list[str] | None = None,
    category: str | None = None,
    preview_data: dict | None = None,
    test_email: str | None = None,
) -> str:
    """邮件模板管理。

    模板支持 Jinja2 变量: {{name}}, {{company}}, {{email}}, {{unsubscribe_url}} 等。

    action 可选值:
    - "create": 创建模板（需 name + subject + html_body）
    - "list": 列出所有模板（可选 category 筛选）
    - "get": 获取模板详情（需 template_id）
    - "update": 更新模板（需 template_id + 要更新的字段）
    - "delete": 删除模板（需 template_id）
    - "preview": 用示例数据渲染预览（需 template_id + preview_data）
    - "test_send": 发送测试邮件（需 template_id + test_email，可选 preview_data）
    """
    try:
        if action == "create":
            if not name or not subject or not html_body:
                return _error_text("创建模板需要 name, subject, html_body")
            data = {"name": name, "subject": subject, "html_body": html_body}
            if text_body: data["text_body"] = text_body
            if variables: data["variables"] = variables
            if category: data["category"] = category
            result = await api.post("/api/v1/templates", data)
            return _json_text(result)

        elif action == "list":
            params = {}
            if category: params["category"] = category
            result = await api.get("/api/v1/templates", params)
            return _json_text(result)

        elif action == "get":
            if not template_id:
                return _error_text("需要 template_id")
            result = await api.get(f"/api/v1/templates/{template_id}")
            return _json_text(result)

        elif action == "update":
            if not template_id:
                return _error_text("需要 template_id")
            data = {}
            if name is not None: data["name"] = name
            if subject is not None: data["subject"] = subject
            if html_body is not None: data["html_body"] = html_body
            if text_body is not None: data["text_body"] = text_body
            if variables is not None: data["variables"] = variables
            if category is not None: data["category"] = category
            result = await api.put(f"/api/v1/templates/{template_id}", data)
            return _json_text(result)

        elif action == "delete":
            if not template_id:
                return _error_text("需要 template_id")
            result = await api.delete(f"/api/v1/templates/{template_id}")
            return _json_text(result)

        elif action == "preview":
            if not template_id:
                return _error_text("需要 template_id")
            result = await api.post(
                f"/api/v1/templates/{template_id}/preview",
                {"data": preview_data or {}},
            )
            return _json_text(result)

        elif action == "test_send":
            if not template_id or not test_email:
                return _error_text("需要 template_id 和 test_email")
            result = await api.post(
                f"/api/v1/templates/{template_id}/test-send",
                {"to_email": test_email, "data": preview_data or {}},
            )
            return _json_text(result)

        else:
            return _error_text(f"未知 action: {action}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
