"""SQLAlchemy ORM models — 12 tables for EmailMarketer."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, Enum as SAEnum, Index, Table, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────

class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class EmailStatus(str, enum.Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


class BounceType(str, enum.Enum):
    HARD = "hard"
    SOFT = "soft"


class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"


class TriggerType(str, enum.Enum):
    CONTACT_ADDED = "contact_added"
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    DATE_FIELD = "date_field"
    MANUAL = "manual"


class ActionType(str, enum.Enum):
    SEND_EMAIL = "send_email"
    WAIT = "wait"
    CONDITION = "condition"
    ADD_TO_SEGMENT = "add_to_segment"
    REMOVE_FROM_SEGMENT = "remove_from_segment"
    UPDATE_CONTACT = "update_contact"


# ── Association table ──────────────────────────────

contact_segment = Table(
    "contact_segment",
    Base.metadata,
    Column("contact_id", Integer, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True),
    Column("segment_id", Integer, ForeignKey("segments.id", ondelete="CASCADE"), primary_key=True),
)


# ── Contact ────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), default="")
    company = Column(String(255), default="")
    phone = Column(String(50), default="")
    status = Column(SAEnum(ContactStatus), default=ContactStatus.ACTIVE, index=True)
    custom_fields = Column(JSON, default=dict)
    source = Column(String(100), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)

    segments = relationship("Segment", secondary=contact_segment, back_populates="contacts")
    emails = relationship("EmailLog", back_populates="contact")


# ── Segment ────────────────────────────────────────

class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, default="")
    is_dynamic = Column(Boolean, default=False)
    rules = Column(JSON, nullable=True)
    contact_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("Contact", secondary=contact_segment, back_populates="segments")


# ── EmailTemplate ──────────────────────────────────

class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, default="")
    variables = Column(JSON, default=list)
    category = Column(String(100), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── SMTP Account ───────────────────────────────────

class SmtpAccount(Base):
    __tablename__ = "smtp_accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(500), nullable=False)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=465)
    use_ssl = Column(Boolean, default=True)
    daily_limit = Column(Integer, default=500)
    sent_today = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Campaign ───────────────────────────────────────

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=True)
    sender_email = Column(String(255), nullable=False)
    sender_name = Column(String(255), default="")
    reply_to = Column(String(255), default="")
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT, index=True)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    bounce_count = Column(Integer, default=0)
    unsubscribe_count = Column(Integer, default=0)
    rate_limit = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("EmailTemplate")
    segment = relationship("Segment")
    email_logs = relationship("EmailLog", back_populates="campaign")


# ── EmailLog ───────────────────────────────────────

class EmailLog(Base):
    __tablename__ = "email_logs"
    __table_args__ = (
        Index("ix_email_logs_campaign_status", "campaign_id", "status"),
    )

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    tracking_id = Column(String(36), unique=True, nullable=False, index=True)
    email_address = Column(String(255), nullable=False)
    status = Column(SAEnum(EmailStatus), default=EmailStatus.QUEUED, index=True)
    link_urls = Column(JSON, default=list)
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    clicked_at = Column(DateTime, nullable=True)
    click_count = Column(Integer, default=0)
    bounced_at = Column(DateTime, nullable=True)
    bounce_type = Column(SAEnum(BounceType), nullable=True)
    error_message = Column(Text, nullable=True)

    campaign = relationship("Campaign", back_populates="email_logs")
    contact = relationship("Contact", back_populates="emails")
    click_events = relationship("ClickEvent", back_populates="email_log")


# ── ClickEvent ─────────────────────────────────────

class ClickEvent(Base):
    __tablename__ = "click_events"

    id = Column(Integer, primary_key=True)
    email_log_id = Column(Integer, ForeignKey("email_logs.id", ondelete="CASCADE"), nullable=False)
    original_url = Column(Text, nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(500), default="")
    ip_address = Column(String(45), default="")

    email_log = relationship("EmailLog", back_populates="click_events")


# ── Workflow ───────────────────────────────────────

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(SAEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    trigger_type = Column(SAEnum(TriggerType), nullable=False)
    trigger_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship("WorkflowStep", back_populates="workflow", order_by="WorkflowStep.order")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, nullable=False)
    action_type = Column(SAEnum(ActionType), nullable=False)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="steps")


# ── WorkflowExecution ──────────────────────────────

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    current_step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=True)
    status = Column(String(20), default="running")
    next_execute_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    log = Column(JSON, default=list)
