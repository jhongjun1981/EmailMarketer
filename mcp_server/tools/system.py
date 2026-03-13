"""MCP tools — system management, SMTP accounts, quick send."""

from __future__ import annotations

import os
import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def manage_smtp(
    action: str,
    account_id: int | None = None,
    name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    use_ssl: bool | None = None,
    daily_limit: int | None = None,
    is_active: bool | None = None,
    to_email: str | None = None,
) -> str:
    """SMTP 账户管理。

    action 可选值:
    - "list": 列出所有 SMTP 账户
    - "add": 添加账户（需 name + email + password，可选 smtp_host/smtp_port/use_ssl/daily_limit）
    - "update": 修改账户（需 account_id + 要更新的字段）
    - "delete": 删除账户（需 account_id）
    - "test": 测试 SMTP 连接（需 email + password + to_email）
    - "health": 检查 API 健康状态
    """
    try:
        if action == "list":
            result = await api.get("/api/v1/system/smtp/accounts")
            return _json_text(result)

        elif action == "add":
            if not name or not email or not password:
                return _error_text("添加账户需要 name, email, password")
            data = {"name": name, "email": email, "password": password}
            if smtp_host: data["smtp_host"] = smtp_host
            if smtp_port: data["smtp_port"] = smtp_port
            if use_ssl is not None: data["use_ssl"] = use_ssl
            if daily_limit: data["daily_limit"] = daily_limit
            result = await api.post("/api/v1/system/smtp/accounts", data)
            return _json_text(result)

        elif action == "update":
            if not account_id:
                return _error_text("需要 account_id")
            data = {}
            if name is not None: data["name"] = name
            if email is not None: data["email"] = email
            if password is not None: data["password"] = password
            if smtp_host is not None: data["smtp_host"] = smtp_host
            if smtp_port is not None: data["smtp_port"] = smtp_port
            if use_ssl is not None: data["use_ssl"] = use_ssl
            if daily_limit is not None: data["daily_limit"] = daily_limit
            if is_active is not None: data["is_active"] = is_active
            result = await api.put(f"/api/v1/system/smtp/accounts/{account_id}", data)
            return _json_text(result)

        elif action == "delete":
            if not account_id:
                return _error_text("需要 account_id")
            result = await api.delete(f"/api/v1/system/smtp/accounts/{account_id}")
            return _json_text(result)

        elif action == "test":
            if not email or not password or not to_email:
                return _error_text("测试连接需要 email, password, to_email")
            result = await api.post("/api/v1/system/smtp/test", {
                "email": email,
                "password": password,
                "to_email": to_email,
            })
            return _json_text(result)

        elif action == "health":
            result = await api.get("/api/v1/system/health")
            return _json_text(result)

        else:
            return _error_text(f"未知 action: {action}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)


@server.tool()
async def send_email(
    to_email: str,
    subject: str,
    content: str = "",
    smtp_account_id: int = 0,
    attachment_path: str | None = None,
) -> str:
    """快速发送邮件（支持附件）。

    参数:
    - to_email: 收件人邮箱
    - subject: 邮件标题
    - content: 邮件正文
    - smtp_account_id: SMTP 账户 ID（用 manage_smtp action=list 查看可用账户，0 表示使用第一个可用账户）
    - attachment_path: 附件文件路径（可选，本地绝对路径）
    """
    try:
        # 自动选择第一个可用账户
        if smtp_account_id == 0:
            accounts = await api.get("/api/v1/system/smtp/accounts")
            active = [a for a in accounts if a.get("is_active")]
            if not active:
                return _error_text("没有可用的 SMTP 账户", "请先用 manage_smtp action=add 添加账户")
            smtp_account_id = active[0]["id"]

        form_data = {
            "to_email": to_email,
            "subject": subject,
            "content": content,
            "smtp_account_id": str(smtp_account_id),
        }

        files = None
        if attachment_path:
            if not os.path.isfile(attachment_path):
                return _error_text(f"附件文件不存在: {attachment_path}")
            filename = os.path.basename(attachment_path)
            with open(attachment_path, "rb") as f:
                file_bytes = f.read()
            files = [("attachments", (filename, file_bytes))]

        result = await api.post_form(
            "/api/v1/system/quick-send",
            data=form_data,
            files=files,
        )
        return _json_text(result)

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
