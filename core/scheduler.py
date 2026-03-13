"""APScheduler setup for periodic tasks."""

from __future__ import annotations

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger(__name__)


def setup_scheduler(
    workflow_engine,
    bounce_monitor,
    bounce_config: dict,
    db_session_factory,
    workflow_tick_seconds: int = 60,
    campaign_check_seconds: int = 60,
) -> AsyncIOScheduler:
    """Create and configure the scheduler with periodic jobs."""
    scheduler = AsyncIOScheduler()

    # Workflow engine tick
    def _workflow_tick():
        try:
            workflow_engine.tick()
        except Exception as e:
            log.error(f"Workflow tick error: {e}")

    scheduler.add_job(
        _workflow_tick,
        "interval",
        seconds=workflow_tick_seconds,
        id="workflow_tick",
        name="Workflow Engine Tick",
    )

    # Bounce detection (if configured)
    if bounce_config.get("enabled"):
        def _bounce_check():
            try:
                bounce_monitor.check_bounces(
                    imap_host=bounce_config["imap_host"],
                    imap_user=bounce_config["imap_user"],
                    imap_pass=bounce_config["imap_pass"],
                    db_session_factory=db_session_factory,
                )
            except Exception as e:
                log.error(f"Bounce check error: {e}")

        scheduler.add_job(
            _bounce_check,
            "interval",
            minutes=bounce_config.get("check_interval_minutes", 5),
            id="bounce_check",
            name="Bounce Detection",
        )

    log.info("Scheduler configured")
    return scheduler
