"""MCP Server configuration."""

import os


class MCPConfig:
    API_BASE_URL = os.environ.get("EM_API_URL", "http://localhost:8100")
    API_KEY = os.environ.get("EM_API_KEY", "changeme-your-secret-key")
    HTTP_TIMEOUT: float = float(os.environ.get("EM_HTTP_TIMEOUT", "30"))
    TASK_POLL_TIMEOUT: int = int(os.environ.get("EM_TASK_TIMEOUT", "600"))
    TASK_POLL_INTERVAL: float = float(os.environ.get("EM_POLL_INTERVAL", "3"))
    SSE_HOST: str = os.environ.get("EM_SSE_HOST", "0.0.0.0")
    SSE_PORT: int = int(os.environ.get("EM_SSE_PORT", "8101"))
    SSE_AUTH_ENABLED: bool = os.environ.get("EM_SSE_AUTH", "true").lower() == "true"


config = MCPConfig()
