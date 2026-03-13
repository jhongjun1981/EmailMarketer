"""MCP Server entry point — registers all tools."""

from __future__ import annotations

import json
from mcp.server.fastmcp import FastMCP

from mcp_server.config import config
from mcp_server.api_client import EmailAPIClient

# Create MCP server
server = FastMCP(
    "email-marketer",
    host=config.SSE_HOST,
    port=config.SSE_PORT,
)

# API client
api = EmailAPIClient(
    base_url=config.API_BASE_URL,
    api_key=config.API_KEY,
    timeout=config.HTTP_TIMEOUT,
)


def _json_text(data) -> str:
    """Format result as readable JSON."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _error_text(msg: str, hint: str = "") -> str:
    """Format error message."""
    result = f"❌ {msg}"
    if hint:
        result += f"\n💡 {hint}"
    return result


# Import all tool modules (they register via @server.tool())
from mcp_server.tools import contacts   # noqa
from mcp_server.tools import templates  # noqa
from mcp_server.tools import campaigns  # noqa
from mcp_server.tools import workflows  # noqa
from mcp_server.tools import reports    # noqa
from mcp_server.tools import system     # noqa
