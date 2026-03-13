"""Application settings — loaded from config.yaml + environment variables."""

from __future__ import annotations

import os
import yaml

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CFG_PATH = os.path.join(_BASE_DIR, "config.yaml")


def _load_yaml() -> dict:
    if os.path.exists(_CFG_PATH):
        with open(_CFG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_cfg = _load_yaml()


class Settings:
    # API
    HOST: str = os.environ.get("EM_HOST", _cfg.get("api", {}).get("host", "0.0.0.0"))
    PORT: int = int(os.environ.get("EM_PORT", _cfg.get("api", {}).get("port", 8100)))
    API_KEY: str = os.environ.get("EM_API_KEY", _cfg.get("api", {}).get("api_key", "changeme-your-secret-key"))

    # Database
    DATABASE_URL: str = os.environ.get(
        "EM_DATABASE_URL",
        _cfg.get("database", {}).get("url", f"sqlite+aiosqlite:///{os.path.join(_BASE_DIR, 'data', 'emailmarketer.db')}"),
    )

    # Tracking
    TRACKING_BASE_URL: str = os.environ.get(
        "EM_TRACKING_URL",
        _cfg.get("tracking", {}).get("base_url", "http://localhost:8100"),
    )

    # SMTP defaults
    DEFAULT_SENDER_EMAIL: str = _cfg.get("smtp", {}).get("default_sender_email", "")
    DEFAULT_SENDER_NAME: str = _cfg.get("smtp", {}).get("default_sender_name", "")
    DEFAULT_PASSWORD: str = _cfg.get("smtp", {}).get("default_password", "")

    # Bounce IMAP
    BOUNCE_ENABLED: bool = _cfg.get("bounce", {}).get("enabled", False)
    IMAP_HOST: str = _cfg.get("bounce", {}).get("imap_host", "")
    IMAP_USER: str = _cfg.get("bounce", {}).get("imap_user", "")
    IMAP_PASS: str = _cfg.get("bounce", {}).get("imap_pass", "")

    # Scheduler
    WORKFLOW_TICK_SECONDS: int = _cfg.get("scheduler", {}).get("workflow_tick_seconds", 60)
    CAMPAIGN_CHECK_SECONDS: int = _cfg.get("scheduler", {}).get("campaign_check_seconds", 60)


settings = Settings()
