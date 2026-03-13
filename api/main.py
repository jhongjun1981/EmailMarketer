"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.auth import verify_api_key
from db.engine import init_db, SyncSessionLocal

# Import routers
from api.routers import contacts, segments, templates, campaigns, tracking, workflows, reports, system

# Core modules
from core.smtp_pool import smtp_pool
from core.template_engine import template_engine
from core.tracking import TrackingManager
from core.email_sender import EmailSender
from core.workflow_engine import WorkflowEngine
from core.bounce_monitor import bounce_monitor
from core.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Init database
    await init_db()
    log.info("Database initialized")

    # Init tracking manager
    tracker = TrackingManager(settings.TRACKING_BASE_URL)

    # Init email sender
    sender = EmailSender(smtp_pool, template_engine, tracker)
    campaigns.set_email_sender(sender)
    log.info("Email sender ready")

    # Init workflow engine
    wf_engine = WorkflowEngine(SyncSessionLocal, email_sender=sender)

    # Setup scheduler
    scheduler = setup_scheduler(
        workflow_engine=wf_engine,
        bounce_monitor=bounce_monitor,
        bounce_config={
            "enabled": settings.BOUNCE_ENABLED,
            "imap_host": settings.IMAP_HOST,
            "imap_user": settings.IMAP_USER,
            "imap_pass": settings.IMAP_PASS,
        },
        db_session_factory=SyncSessionLocal,
        workflow_tick_seconds=settings.WORKFLOW_TICK_SECONDS,
        campaign_check_seconds=settings.CAMPAIGN_CHECK_SECONDS,
    )
    scheduler.start()
    log.info("Scheduler started")

    # Store in app state for access from routes
    app.state.tracker = tracker
    app.state.sender = sender
    app.state.wf_engine = wf_engine

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")


# Create app — tracking routes are PUBLIC (no auth)
app = FastAPI(
    title="EmailMarketer API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authenticated routes
auth_dep = [Depends(verify_api_key)]

app.include_router(contacts.router, dependencies=auth_dep)
app.include_router(segments.router, dependencies=auth_dep)
app.include_router(templates.router, dependencies=auth_dep)
app.include_router(campaigns.router, dependencies=auth_dep)
app.include_router(workflows.router, dependencies=auth_dep)
app.include_router(reports.router, dependencies=auth_dep)
app.include_router(system.router, dependencies=auth_dep)

# Public routes (tracking pixels, link redirects, unsubscribe)
app.include_router(tracking.router)
