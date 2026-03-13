"""MCP tools — contact and segment management."""

from __future__ import annotations

import httpx
from mcp_server.server import server, api, _json_text, _error_text


@server.tool()
async def manage_contacts(
    action: str,
    email: str | None = None,
    name: str | None = None,
    company: str | None = None,
    phone: str | None = None,
    custom_fields: dict | None = None,
    contact_id: int | None = None,
    segment_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    contacts_data: list[dict] | None = None,
    page: int = 1,
    page_size: int = 50,
) -> str:
    """联系人和分段管理。

    action 可选值:
    - "create": 创建联系人（需 email，可选 name/company/phone/custom_fields）
    - "list": 列出联系人（可选 segment_id/status/search 筛选，支持分页）
    - "get": 获取联系人详情（需 contact_id）
    - "update": 更新联系人（需 contact_id + 要更新的字段）
    - "delete": 删除联系人（需 contact_id）
    - "import": 批量导入（需 contacts_data=[{"email":"..","name":".."},...]，可选 segment_id）
    - "add_to_segment": 将联系人加入分段（需 contact_id + segment_id）
    - "remove_from_segment": 从分段移除（需 contact_id + segment_id）
    - "create_segment": 创建分段（需 name，可选 description/rules）
    - "list_segments": 列出所有分段
    - "get_segment": 获取分段详情（需 segment_id）
    - "refresh_segment": 刷新动态分段（需 segment_id）
    - "segment_contacts": 获取分段内联系人（需 segment_id）
    """
    try:
        if action == "create":
            if not email:
                return _error_text("创建联系人需要 email 参数")
            data = {"email": email}
            if name: data["name"] = name
            if company: data["company"] = company
            if phone: data["phone"] = phone
            if custom_fields: data["custom_fields"] = custom_fields
            result = await api.post("/api/v1/contacts", data)
            return _json_text(result)

        elif action == "list":
            params = {"page": page, "page_size": page_size}
            if status: params["status"] = status
            if segment_id: params["segment_id"] = segment_id
            if search: params["search"] = search
            result = await api.get("/api/v1/contacts", params)
            return _json_text(result)

        elif action == "get":
            if not contact_id:
                return _error_text("需要 contact_id")
            result = await api.get(f"/api/v1/contacts/{contact_id}")
            return _json_text(result)

        elif action == "update":
            if not contact_id:
                return _error_text("需要 contact_id")
            data = {}
            if name is not None: data["name"] = name
            if company is not None: data["company"] = company
            if phone is not None: data["phone"] = phone
            if status is not None: data["status"] = status
            if custom_fields is not None: data["custom_fields"] = custom_fields
            result = await api.put(f"/api/v1/contacts/{contact_id}", data)
            return _json_text(result)

        elif action == "delete":
            if not contact_id:
                return _error_text("需要 contact_id")
            result = await api.delete(f"/api/v1/contacts/{contact_id}")
            return _json_text(result)

        elif action == "import":
            if not contacts_data:
                return _error_text("需要 contacts_data")
            data = {"contacts": contacts_data}
            if segment_id: data["segment_id"] = segment_id
            result = await api.post("/api/v1/contacts/batch", data)
            return _json_text(result)

        elif action == "add_to_segment":
            if not contact_id or not segment_id:
                return _error_text("需要 contact_id 和 segment_id")
            result = await api.post(f"/api/v1/contacts/{contact_id}/segments/{segment_id}")
            return _json_text(result)

        elif action == "remove_from_segment":
            if not contact_id or not segment_id:
                return _error_text("需要 contact_id 和 segment_id")
            result = await api.delete(f"/api/v1/contacts/{contact_id}/segments/{segment_id}")
            return _json_text(result)

        # Segment operations
        elif action == "create_segment":
            if not name:
                return _error_text("创建分段需要 name")
            data = {"name": name}
            if custom_fields and "description" in custom_fields:
                data["description"] = custom_fields["description"]
            if custom_fields and "rules" in custom_fields:
                data["is_dynamic"] = True
                data["rules"] = custom_fields["rules"]
            result = await api.post("/api/v1/segments", data)
            return _json_text(result)

        elif action == "list_segments":
            result = await api.get("/api/v1/segments")
            return _json_text(result)

        elif action == "get_segment":
            if not segment_id:
                return _error_text("需要 segment_id")
            result = await api.get(f"/api/v1/segments/{segment_id}")
            return _json_text(result)

        elif action == "refresh_segment":
            if not segment_id:
                return _error_text("需要 segment_id")
            result = await api.post(f"/api/v1/segments/{segment_id}/refresh")
            return _json_text(result)

        elif action == "segment_contacts":
            if not segment_id:
                return _error_text("需要 segment_id")
            result = await api.get(f"/api/v1/segments/{segment_id}/contacts", {"page": page, "page_size": page_size})
            return _json_text(result)

        else:
            return _error_text(f"未知 action: {action}")

    except httpx.ConnectError:
        return _error_text("无法连接 EmailMarketer API", "请确认 run_api.py 已启动 (端口 8100)")
    except httpx.HTTPStatusError as e:
        return _error_text(f"API 错误 {e.response.status_code}", e.response.text)
