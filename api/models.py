"""Pydantic request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Contact ────────────────────────────────────────

class ContactCreate(BaseModel):
    email: str
    name: str = ""
    company: str = ""
    phone: str = ""
    custom_fields: dict = Field(default_factory=dict)
    source: str = "manual"


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    custom_fields: Optional[dict] = None


class ContactBatchImport(BaseModel):
    contacts: list[ContactCreate]
    segment_id: Optional[int] = None


class ContactResponse(BaseModel):
    id: int
    email: str
    name: str
    company: str
    phone: str
    status: str
    custom_fields: dict
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Segment ────────────────────────────────────────

class SegmentCreate(BaseModel):
    name: str
    description: str = ""
    is_dynamic: bool = False
    rules: Optional[dict] = None


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[dict] = None


class SegmentResponse(BaseModel):
    id: int
    name: str
    description: str
    is_dynamic: bool
    rules: Optional[dict]
    contact_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Template ───────────────────────────────────────

class TemplateCreate(BaseModel):
    name: str
    subject: str
    html_body: str
    text_body: str = ""
    variables: list[str] = Field(default_factory=list)
    category: str = "general"


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    variables: Optional[list[str]] = None
    category: Optional[str] = None


class TemplatePreviewRequest(BaseModel):
    data: dict = Field(default_factory=dict)


class TemplateTestSendRequest(BaseModel):
    to_email: str
    data: dict = Field(default_factory=dict)


class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    html_body: str
    text_body: str
    variables: list
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Campaign ───────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    template_id: int
    segment_id: Optional[int] = None
    sender_email: str
    sender_name: str = ""
    reply_to: str = ""
    rate_limit: int = 10


class CampaignScheduleRequest(BaseModel):
    scheduled_at: datetime


class CampaignResponse(BaseModel):
    id: int
    name: str
    template_id: int
    segment_id: Optional[int]
    sender_email: str
    sender_name: str
    status: str
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_recipients: int
    sent_count: int
    open_count: int
    click_count: int
    bounce_count: int
    unsubscribe_count: int
    rate_limit: int
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignStatsResponse(BaseModel):
    campaign_id: int
    name: str
    status: str
    total: int
    sent: int
    opened: int
    clicked: int
    bounced: int
    unsubscribed: int
    open_rate: float
    click_rate: float
    bounce_rate: float


# ── Workflow ───────────────────────────────────────

class WorkflowStepData(BaseModel):
    action_type: str
    config: dict = Field(default_factory=dict)


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    trigger_type: str
    trigger_config: dict = Field(default_factory=dict)
    steps: list[WorkflowStepData] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    trigger_type: str
    trigger_config: dict
    steps: list[dict] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


# ── SMTP ───────────────────────────────────────────

class SmtpAccountCreate(BaseModel):
    name: str
    email: str
    password: str
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    use_ssl: Optional[bool] = None
    daily_limit: int = 500


class SmtpAccountUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    use_ssl: Optional[bool] = None
    daily_limit: Optional[int] = None
    is_active: Optional[bool] = None


class SmtpTestRequest(BaseModel):
    email: str
    password: str
    to_email: str


# ── Reports ────────────────────────────────────────

class OverviewReport(BaseModel):
    total_contacts: int
    active_contacts: int
    total_campaigns: int
    total_sent: int
    total_opened: int
    total_clicked: int
    avg_open_rate: float
    avg_click_rate: float


class TrendDataPoint(BaseModel):
    date: str
    sent: int
    opened: int
    clicked: int
