"""Campaign management routes."""

from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import (
    CampaignCreate, CampaignResponse, CampaignScheduleRequest, CampaignStatsResponse,
)
from db.models import Campaign, CampaignStatus, EmailTemplate, Segment, EmailLog

router = APIRouter(prefix="/api/v1/campaigns", tags=["群发活动"])

# Will be set from main.py
_email_sender = None


def set_email_sender(sender):
    global _email_sender
    _email_sender = sender


@router.post("", response_model=CampaignResponse)
async def create_campaign(req: CampaignCreate, db: AsyncSession = Depends(get_db)):
    tpl = await db.get(EmailTemplate, req.template_id)
    if not tpl:
        raise HTTPException(404, f"模板 {req.template_id} 不存在")

    if req.segment_id:
        seg = await db.get(Segment, req.segment_id)
        if not seg:
            raise HTTPException(404, f"分段 {req.segment_id} 不存在")

    campaign = Campaign(
        name=req.name,
        template_id=req.template_id,
        segment_id=req.segment_id,
        sender_email=req.sender_email,
        sender_name=req.sender_name,
        reply_to=req.reply_to,
        rate_limit=req.rate_limit,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).order_by(Campaign.id.desc()))
    campaigns = result.scalars().all()
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")
    return campaign


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """立即开始发送活动。"""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")
    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PAUSED):
        raise HTTPException(400, f"活动状态 {campaign.status} 不允许发送")

    if not _email_sender:
        raise HTTPException(500, "邮件发送引擎未初始化")

    # Launch send in background
    async def _do_send():
        from db.engine import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await _email_sender.send_campaign(campaign_id, session)

    background_tasks.add_task(_do_send)

    campaign.status = CampaignStatus.SENDING
    await db.commit()

    return {"message": "发送任务已启动", "campaign_id": campaign_id}


@router.post("/{campaign_id}/schedule")
async def schedule_campaign(
    campaign_id: int,
    req: CampaignScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")
    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(400, "只有草稿状态可以定时")

    campaign.status = CampaignStatus.SCHEDULED
    campaign.scheduled_at = req.scheduled_at
    await db.commit()

    return {"message": f"已设定 {req.scheduled_at} 发送", "campaign_id": campaign_id}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")
    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    return {"ok": True}


@router.post("/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")
    campaign.status = CampaignStatus.CANCELLED
    await db.commit()
    return {"ok": True}


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def campaign_stats(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "活动不存在")

    total = campaign.total_recipients or 1
    return CampaignStatsResponse(
        campaign_id=campaign.id,
        name=campaign.name,
        status=campaign.status.value if hasattr(campaign.status, 'value') else campaign.status,
        total=campaign.total_recipients,
        sent=campaign.sent_count,
        opened=campaign.open_count,
        clicked=campaign.click_count,
        bounced=campaign.bounce_count,
        unsubscribed=campaign.unsubscribe_count,
        open_rate=round(campaign.open_count / total * 100, 2) if total else 0,
        click_rate=round(campaign.click_count / total * 100, 2) if total else 0,
        bounce_rate=round(campaign.bounce_count / total * 100, 2) if total else 0,
    )


@router.get("/{campaign_id}/logs")
async def campaign_logs(
    campaign_id: int,
    page: int = 1,
    page_size: int = 50,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(EmailLog).where(EmailLog.campaign_id == campaign_id)
    if status:
        q = q.where(EmailLog.status == status)
    q = q.order_by(EmailLog.id.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "contact_id": log.contact_id,
            "email": log.email_address,
            "status": log.status.value if hasattr(log.status, 'value') else log.status,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "opened_at": log.opened_at.isoformat() if log.opened_at else None,
            "open_count": log.open_count,
            "click_count": log.click_count,
            "error": log.error_message,
        }
        for log in logs
    ]
