"""Report routes."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from api.models import OverviewReport, TrendDataPoint
from db.models import (
    Contact, ContactStatus, Campaign, CampaignStatus,
    EmailLog, EmailStatus,
)

router = APIRouter(prefix="/api/v1/reports", tags=["报表"])


@router.get("/overview", response_model=OverviewReport)
async def overview(db: AsyncSession = Depends(get_db)):
    """全局概览。"""
    total_contacts = (await db.execute(select(func.count(Contact.id)))).scalar() or 0
    active_contacts = (await db.execute(
        select(func.count(Contact.id)).where(Contact.status == ContactStatus.ACTIVE)
    )).scalar() or 0

    total_campaigns = (await db.execute(select(func.count(Campaign.id)))).scalar() or 0

    total_sent = (await db.execute(
        select(func.count(EmailLog.id)).where(EmailLog.status != EmailStatus.QUEUED)
    )).scalar() or 0

    total_opened = (await db.execute(
        select(func.count(EmailLog.id)).where(EmailLog.opened_at.isnot(None))
    )).scalar() or 0

    total_clicked = (await db.execute(
        select(func.count(EmailLog.id)).where(EmailLog.clicked_at.isnot(None))
    )).scalar() or 0

    avg_open = round(total_opened / max(total_sent, 1) * 100, 2)
    avg_click = round(total_clicked / max(total_sent, 1) * 100, 2)

    return OverviewReport(
        total_contacts=total_contacts,
        active_contacts=active_contacts,
        total_campaigns=total_campaigns,
        total_sent=total_sent,
        total_opened=total_opened,
        total_clicked=total_clicked,
        avg_open_rate=avg_open,
        avg_click_rate=avg_click,
    )


@router.get("/trends")
async def trends(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """按天聚合的发送/打开/点击趋势。"""
    since = datetime.utcnow() - timedelta(days=days)

    # Get all logs in range
    result = await db.execute(
        select(EmailLog).where(EmailLog.sent_at >= since)
    )
    logs = result.scalars().all()

    # Aggregate by date
    data: dict[str, dict] = {}
    for log in logs:
        if not log.sent_at:
            continue
        date_str = log.sent_at.strftime("%Y-%m-%d")
        if date_str not in data:
            data[date_str] = {"sent": 0, "opened": 0, "clicked": 0}
        data[date_str]["sent"] += 1
        if log.opened_at:
            data[date_str]["opened"] += 1
        if log.clicked_at:
            data[date_str]["clicked"] += 1

    points = sorted(
        [TrendDataPoint(date=d, **v) for d, v in data.items()],
        key=lambda p: p.date,
    )
    return points


@router.get("/campaigns/{campaign_id}")
async def campaign_report(campaign_id: int, db: AsyncSession = Depends(get_db)):
    """单活动详细报告。"""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return {"error": "活动不存在"}

    total = campaign.total_recipients or 1

    # Status distribution
    result = await db.execute(
        select(EmailLog.status, func.count(EmailLog.id))
        .where(EmailLog.campaign_id == campaign_id)
        .group_by(EmailLog.status)
    )
    status_dist = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in result}

    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "status": campaign.status.value if hasattr(campaign.status, 'value') else campaign.status,
        "total_recipients": campaign.total_recipients,
        "sent": campaign.sent_count,
        "opened": campaign.open_count,
        "clicked": campaign.click_count,
        "bounced": campaign.bounce_count,
        "unsubscribed": campaign.unsubscribe_count,
        "open_rate": round(campaign.open_count / total * 100, 2),
        "click_rate": round(campaign.click_count / total * 100, 2),
        "bounce_rate": round(campaign.bounce_count / total * 100, 2),
        "status_distribution": status_dist,
        "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
        "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
    }


@router.get("/contacts/engagement")
async def contact_engagement(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """联系人活跃度排名。"""
    result = await db.execute(
        select(
            Contact.id,
            Contact.email,
            Contact.name,
            func.count(EmailLog.id).label("total_emails"),
            func.sum(EmailLog.open_count).label("total_opens"),
            func.sum(EmailLog.click_count).label("total_clicks"),
        )
        .join(EmailLog, EmailLog.contact_id == Contact.id)
        .group_by(Contact.id)
        .order_by(func.sum(EmailLog.open_count).desc())
        .limit(limit)
    )

    return [
        {
            "contact_id": row[0],
            "email": row[1],
            "name": row[2],
            "total_emails": row[3],
            "total_opens": row[4] or 0,
            "total_clicks": row[5] or 0,
        }
        for row in result
    ]
