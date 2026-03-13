"""Tracking endpoints — NO authentication required.

These are called by email clients when recipients open/click emails.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from db.models import (
    EmailLog, EmailStatus, ClickEvent, Contact, ContactStatus, Campaign,
)

router = APIRouter(prefix="/t", tags=["追踪"])

# 1x1 transparent GIF
PIXEL_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B,
])


@router.get("/o/{tracking_id}.gif")
async def track_open(tracking_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """追踪像素 — 记录邮件打开。"""
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()

    if email_log:
        email_log.open_count = (email_log.open_count or 0) + 1
        if not email_log.opened_at:
            email_log.opened_at = datetime.utcnow()
            email_log.status = EmailStatus.OPENED
            # Update campaign aggregate
            campaign = await db.get(Campaign, email_log.campaign_id)
            if campaign:
                campaign.open_count = (campaign.open_count or 0) + 1
        await db.commit()

    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/c/{tracking_id}/{link_index}")
async def track_click(
    tracking_id: str,
    link_index: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """链接点击追踪 — 302 重定向到原始 URL。"""
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()

    if not email_log:
        return RedirectResponse("/")

    # Get original URL
    link_urls = email_log.link_urls or []
    if 0 <= link_index < len(link_urls):
        target_url = link_urls[link_index]
    else:
        target_url = "/"

    # Record click
    email_log.click_count = (email_log.click_count or 0) + 1
    if not email_log.clicked_at:
        email_log.clicked_at = datetime.utcnow()
        if email_log.status != EmailStatus.CLICKED:
            email_log.status = EmailStatus.CLICKED
        campaign = await db.get(Campaign, email_log.campaign_id)
        if campaign:
            campaign.click_count = (campaign.click_count or 0) + 1

    click_event = ClickEvent(
        email_log_id=email_log.id,
        original_url=target_url,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else "",
    )
    db.add(click_event)
    await db.commit()

    return RedirectResponse(target_url, status_code=302)


@router.get("/u/{tracking_id}")
async def unsubscribe_page(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """退订确认页面。"""
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()
    email_addr = email_log.email_address if email_log else "unknown"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>退订确认</title>
<style>
body {{ font-family: sans-serif; max-width: 500px; margin: 80px auto; text-align: center; }}
button {{ padding: 12px 32px; font-size: 16px; background: #e74c3c; color: white;
    border: none; border-radius: 6px; cursor: pointer; }}
button:hover {{ background: #c0392b; }}
.email {{ color: #666; margin: 20px 0; }}
</style></head>
<body>
<h2>确认退订</h2>
<p class="email">{email_addr}</p>
<p>确定要退订后续邮件吗？</p>
<form method="POST">
    <button type="submit">确认退订</button>
</form>
</body></html>"""
    return HTMLResponse(html)


@router.post("/u/{tracking_id}")
async def confirm_unsubscribe(tracking_id: str, db: AsyncSession = Depends(get_db)):
    """确认退订。"""
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()

    if email_log:
        contact = await db.get(Contact, email_log.contact_id)
        if contact:
            contact.status = ContactStatus.UNSUBSCRIBED
            contact.unsubscribed_at = datetime.utcnow()

        # Update campaign unsubscribe count
        campaign = await db.get(Campaign, email_log.campaign_id)
        if campaign:
            campaign.unsubscribe_count = (campaign.unsubscribe_count or 0) + 1

        await db.commit()

    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>已退订</title>
<style>
body { font-family: sans-serif; max-width: 500px; margin: 80px auto; text-align: center; }
</style></head>
<body>
<h2>✅ 已退订成功</h2>
<p>您将不再收到我们的邮件。</p>
</body></html>"""
    return HTMLResponse(html)
