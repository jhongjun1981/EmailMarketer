"""Bounce detection via IMAP monitoring."""

from __future__ import annotations

import imaplib
import email
import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Contact, ContactStatus, EmailLog, EmailStatus, BounceType, Campaign

log = logging.getLogger(__name__)

# DSN status code patterns
HARD_BOUNCE_CODES = re.compile(r"5\.\d+\.\d+")
SOFT_BOUNCE_CODES = re.compile(r"4\.\d+\.\d+")


class BounceMonitor:
    """Monitor IMAP mailbox for bounce notifications."""

    def check_bounces(
        self,
        imap_host: str,
        imap_user: str,
        imap_pass: str,
        db_session_factory,
    ):
        """Scan IMAP inbox for delivery failure notifications."""
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(imap_user, imap_pass)
            mail.select("INBOX")

            # Search for bounce-related emails
            search_terms = [
                '(SUBJECT "Delivery Status Notification")',
                '(SUBJECT "Undelivered")',
                '(SUBJECT "Mail delivery failed")',
                '(SUBJECT "Returned mail")',
            ]

            all_ids = set()
            for term in search_terms:
                _, data = mail.search(None, term)
                if data[0]:
                    all_ids.update(data[0].split())

            if not all_ids:
                mail.logout()
                return

            log.info(f"Found {len(all_ids)} potential bounce messages")

            with db_session_factory() as db:
                for msg_id in all_ids:
                    try:
                        self._process_bounce_message(mail, msg_id, db)
                    except Exception as e:
                        log.error(f"Error processing bounce message {msg_id}: {e}")

                db.commit()

            mail.logout()

        except Exception as e:
            log.error(f"Bounce check failed: {e}")

    def _process_bounce_message(self, mail, msg_id: bytes, db: Session):
        """Parse a single bounce message and update contact status."""
        _, data = mail.fetch(msg_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract failed email address from DSN
        failed_email = self._extract_failed_address(msg)
        if not failed_email:
            return

        # Determine bounce type from DSN status
        bounce_type = self._classify_bounce(msg)

        # Find contact
        contact = db.execute(
            select(Contact).where(Contact.email == failed_email)
        ).scalar_one_or_none()

        if not contact:
            return

        if bounce_type == BounceType.HARD:
            contact.status = ContactStatus.BOUNCED
            log.info(f"Hard bounce: {failed_email} marked as BOUNCED")
        else:
            # Soft bounce — log but don't disable
            log.info(f"Soft bounce: {failed_email}")

        # Update related email_logs
        logs = db.execute(
            select(EmailLog).where(
                EmailLog.contact_id == contact.id,
                EmailLog.status == EmailStatus.SENT,
            )
        ).scalars().all()

        for el in logs:
            el.status = EmailStatus.BOUNCED
            el.bounce_type = bounce_type
            el.bounced_at = datetime.utcnow()

        # Move bounce email to processed folder (optional)
        try:
            mail.store(msg_id, "+FLAGS", "\\Seen")
        except Exception:
            pass

    def _extract_failed_address(self, msg) -> str | None:
        """Extract the failed recipient email from DSN body."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct in ("text/plain", "message/delivery-status"):
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                pass

        # Look for "Final-Recipient:" header in DSN
        match = re.search(r"Final-Recipient:\s*rfc822;\s*(\S+@\S+)", body, re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()

        # Fallback: look for email pattern
        match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", body)
        if match:
            return match.group(0).strip().lower()

        return None

    def _classify_bounce(self, msg) -> BounceType:
        """Classify bounce as hard or soft based on DSN status codes."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                try:
                    body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                pass

        if HARD_BOUNCE_CODES.search(body):
            return BounceType.HARD
        return BounceType.SOFT


bounce_monitor = BounceMonitor()
