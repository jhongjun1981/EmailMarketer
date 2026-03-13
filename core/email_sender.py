"""Async email sending engine — rate-limited, personalized, tracked."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Campaign, CampaignStatus, Contact, ContactStatus,
    EmailLog, EmailStatus, EmailTemplate, Segment, SmtpAccount,
    contact_segment,
)
from core.smtp_pool import SmtpPool, smtp_pool, get_smtp_config
from core.template_engine import TemplateEngine, template_engine
from core.tracking import TrackingManager

log = logging.getLogger(__name__)


class EmailSender:
    """Send campaign emails asynchronously with rate limiting."""

    def __init__(
        self,
        pool: SmtpPool,
        tpl: TemplateEngine,
        tracker: TrackingManager,
    ):
        self.pool = pool
        self.tpl = tpl
        self.tracker = tracker

    async def send_campaign(self, campaign_id: int, db: AsyncSession) -> dict:
        """Send all emails for a campaign. Returns summary dict."""
        # Load campaign
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            return {"error": f"Campaign {campaign_id} not found"}

        template = await db.get(EmailTemplate, campaign.template_id)
        if not template:
            return {"error": f"Template {campaign.template_id} not found"}

        # Get SMTP credentials
        smtp_account = await self._get_smtp_account(campaign.sender_email, db)
        if not smtp_account:
            return {"error": f"No SMTP account for {campaign.sender_email}"}

        # Load segment contacts (active only)
        contacts = await self._get_contacts(campaign.segment_id, db)
        if not contacts:
            return {"error": "No active contacts in segment"}

        # Update campaign status
        campaign.status = CampaignStatus.SENDING
        campaign.total_recipients = len(contacts)
        campaign.started_at = datetime.utcnow()
        await db.commit()

        semaphore = asyncio.Semaphore(campaign.rate_limit)
        sent = 0
        failed = 0

        async def send_one(contact: Contact):
            nonlocal sent, failed
            async with semaphore:
                try:
                    tracking_id = uuid.uuid4().hex[:24]

                    # Render template
                    variables = {
                        "name": contact.name or contact.email,
                        "email": contact.email,
                        "company": contact.company,
                        "phone": contact.phone,
                        **(contact.custom_fields or {}),
                        "unsubscribe_url": self.tracker.get_unsubscribe_url(tracking_id),
                    }
                    subject = self.tpl.render(template.subject, variables)
                    html = self.tpl.render(template.html_body, variables)

                    # Inject tracking
                    html = self.tracker.inject_tracking_pixel(html, tracking_id)
                    html, link_urls = self.tracker.rewrite_links(html, tracking_id)
                    html = self.tracker.inject_unsubscribe(html, tracking_id)

                    # Create log entry
                    email_log = EmailLog(
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        tracking_id=tracking_id,
                        email_address=contact.email,
                        link_urls=link_urls,
                    )
                    db.add(email_log)

                    # Send via SMTP
                    await self.pool.send(
                        sender=campaign.sender_email,
                        password=smtp_account.password,
                        to=contact.email,
                        subject=subject,
                        html=html,
                        text=template.text_body or "",
                        sender_name=campaign.sender_name,
                        reply_to=campaign.reply_to,
                        smtp_host=smtp_account.smtp_host,
                        smtp_port=smtp_account.smtp_port,
                        use_ssl=smtp_account.use_ssl,
                        headers={
                            "List-Unsubscribe": f"<{self.tracker.get_unsubscribe_url(tracking_id)}>",
                        },
                    )

                    email_log.status = EmailStatus.SENT
                    email_log.sent_at = datetime.utcnow()
                    sent += 1

                    # Rate limit delay
                    await asyncio.sleep(1.0 / max(campaign.rate_limit, 1))

                except Exception as e:
                    log.error(f"Failed to send to {contact.email}: {e}")
                    failed += 1
                    # Still create log with error
                    error_log = EmailLog(
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        tracking_id=uuid.uuid4().hex[:24],
                        email_address=contact.email,
                        status=EmailStatus.FAILED,
                        error_message=str(e),
                    )
                    db.add(error_log)

        # Send concurrently
        tasks = [send_one(c) for c in contacts]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Update campaign
        campaign.sent_count = sent
        campaign.status = CampaignStatus.SENT
        campaign.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "campaign_id": campaign_id,
            "total": len(contacts),
            "sent": sent,
            "failed": failed,
            "status": "sent",
        }

    async def send_test(
        self,
        template: EmailTemplate,
        to_email: str,
        sender_email: str,
        password: str,
        data: dict,
    ) -> str:
        """Send a test email. Returns 'ok' or error message."""
        try:
            subject = self.tpl.render(template.subject, data)
            html = self.tpl.render(template.html_body, data)

            await self.pool.send(
                sender=sender_email,
                password=password,
                to=to_email,
                subject=f"[TEST] {subject}",
                html=html,
                text=template.text_body or "",
            )
            return "ok"
        except Exception as e:
            return str(e)

    async def _get_smtp_account(self, email: str, db: AsyncSession) -> SmtpAccount | None:
        result = await db.execute(
            select(SmtpAccount).where(
                SmtpAccount.email == email,
                SmtpAccount.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _get_contacts(self, segment_id: int | None, db: AsyncSession) -> list[Contact]:
        if segment_id:
            result = await db.execute(
                select(Contact)
                .join(contact_segment)
                .where(
                    contact_segment.c.segment_id == segment_id,
                    Contact.status == ContactStatus.ACTIVE,
                )
            )
        else:
            result = await db.execute(
                select(Contact).where(Contact.status == ContactStatus.ACTIVE)
            )
        return list(result.scalars().all())
