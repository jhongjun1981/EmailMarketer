"""MCP tools — workflow automation."""

from __future__ import annotations

import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def manage_workflows(
    action: str,
    workflow_id: int | None = None,
    name: str | None = None,
    description: str | None = None,
    trigger_type: str | None = None,
    trigger_config: dict | None = None,
    steps: list[dict] | None = None,
    page: int = 1,
    page_size: int = 50,
) -> str:
    """自动化工作流管理。

    触发器类型 (trigger_type):
    - "contact_added": 新联系人加入分段时触发
    - "email_opened": 邮件被打开时触发
    - "link_clicked": 链接被点击时触发
    - "date_field": 基于日期字段触发（如注册后N天）
    - "manual": 手动触发

    步骤动作类型 (action_type in steps):
    - "send_email": 发送邮件 (config: {"template_id": 2, "sender_email": "..."})
    - "wait": 等待 (config: {"duration": 72, "unit": "hours"})
    - "condition": 条件分支 (config: {"field": "company", "op": "eq", "value": "X", "true_step": 3, "false_step": 4})
    - "add_to_segment": 加入分段 (config: {"segment_id": 5})
    - "remove_from_segment": 从分段移除
    - "update_contact": 更新联系人字段 (config: {"fields": {"company": "新公司"}})

    action 可选值:
    - "create": 创建工作流（需 name + trigger_type，可选 steps）
    - "list": 列出所有工作流
    - "get": 获取工作流详情（需 workflow_id）
    - "activate": 激活工作流（需 workflow_id）
    - "pause": 暂停工作流（需 workflow_id）
    - "delete": 删除工作流（需 workflow_id）
    - "executions": 查看执行日志（需 workflow_id）

    示例 — 新客户3天后自动发欢迎邮件:
      action="create"
      name="新客户欢迎"
      trigger_type="contact_added"
      trigger_config={"segment_id": 1}
      steps=[
        {"action_type": "wait", "config": {"duration": 72, "unit": "hours"}},
        {"action_type": "send_email", "config": {"template_id": 2, "sender_email": "hello@example.com"}}
      ]
    """
    try:
        if action == "create":
            if not name or not trigger_type:
                return _error_text("创建工作流需要 name 和 trigger_type")
            data = {
                "name": name,
                "trigger_type": trigger_type,
            }
            if description: data["description"] = description
            if trigger_config: data["trigger_config"] = trigger_config
            if steps: data["steps"] = steps
            result = await api.post("/api/v1/workflows", data)
            return _json_text(result)

        elif action == "list":
            result = await api.get("/api/v1/workflows")
            return _json_text(result)

        elif action == "get":
            if not workflow_id:
                return _error_text("需要 workflow_id")
            result = await api.get(f"/api/v1/workflows/{workflow_id}")
            return _json_text(result)

        elif action == "activate":
            if not workflow_id:
                return _error_text("需要 workflow_id")
            result = await api.post(f"/api/v1/workflows/{workflow_id}/activate")
            return _json_text(result)

        elif action == "pause":
            if not workflow_id:
                return _error_text("需要 workflow_id")
            result = await api.post(f"/api/v1/workflows/{workflow_id}/pause")
            return _json_text(result)

        elif action == "delete":
            if not workflow_id:
                return _error_text("需要 workflow_id")
            result = await api.delete(f"/api/v1/workflows/{workflow_id}")
            return _json_text(result)

        elif action == "executions":
            if not workflow_id:
                return _error_text("需要 workflow_id")
            result = await api.get(
                f"/api/v1/workflows/{workflow_id}/executions",
                {"page": page, "page_size": page_size},
            )
            return _json_text(result)

        else:
            return _error_text(f"未知 action: {action}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
