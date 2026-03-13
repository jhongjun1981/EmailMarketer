"""SMTP connection pool — multi-account rotation, daily limits, auto-reconnect."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr

import aiosmtplib

log = logging.getLogger(__name__)

# Well-known SMTP servers (reused from TaobaoScraper)
SMTP_SERVERS: dict[str, tuple[str, int, bool]] = {
    "qq.com":       ("smtp.qq.com", 465, True),
    "foxmail.com":  ("smtp.qq.com", 465, True),
    "163.com":      ("smtp.163.com", 465, True),
    "126.com":      ("smtp.126.com", 465, True),
    "yeah.net":     ("smtp.yeah.net", 465, True),
    "gmail.com":    ("smtp.gmail.com", 465, True),
    "outlook.com":  ("smtp-mail.outlook.com", 587, False),
    "hotmail.com":  ("smtp-mail.outlook.com", 587, False),
    "sina.com":     ("smtp.sina.com", 465, True),
    "sohu.com":     ("smtp.sohu.com", 465, True),
}


def get_smtp_config(email_addr: str) -> tuple[str, int, bool]:
    """Auto-detect SMTP server settings from email domain."""
    domain = email_addr.strip().split("@")[-1].lower()
    if domain in SMTP_SERVERS:
        return SMTP_SERVERS[domain]
    return (f"smtp.{domain}", 465, True)


class SmtpPool:
    """Async SMTP connection manager."""

    async def send(
        self,
        sender: str,
        password: str,
        to: str,
        subject: str,
        html: str,
        text: str = "",
        sender_name: str = "",
        reply_to: str = "",
        headers: dict | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        use_ssl: bool | None = None,
        attachments: list[tuple[str, bytes]] | None = None,
    ) -> None:
        """Send a single email via SMTP.

        attachments: list of (filename, file_bytes) tuples.
        """
        # Build MIME message — use "mixed" when attachments present
        msg = MIMEMultipart("mixed" if attachments else "alternative")
        msg["From"] = formataddr((sender_name, sender), charset="utf-8") if sender_name else sender
        msg["To"] = to
        msg["Subject"] = Header(subject, "utf-8")
        if reply_to:
            msg["Reply-To"] = reply_to

        # Extra headers (e.g. List-Unsubscribe)
        if headers:
            for k, v in headers.items():
                msg[k] = v

        # Body part (wrap in alternative sub-part when attachments exist)
        if attachments:
            body_part = MIMEMultipart("alternative")
            if text:
                body_part.attach(MIMEText(text, "plain", "utf-8"))
            body_part.attach(MIMEText(html, "html", "utf-8"))
            msg.attach(body_part)
        else:
            if text:
                msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))

        # Attachments
        if attachments:
            for filename, file_bytes in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                encoded_name = Header(filename, "utf-8").encode()
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=encoded_name,
                )
                msg.attach(part)

        # Resolve SMTP config
        if not smtp_host:
            smtp_host, auto_port, auto_ssl = get_smtp_config(sender)
            smtp_port = smtp_port or auto_port
            use_ssl = use_ssl if use_ssl is not None else auto_ssl
        smtp_port = smtp_port or 465
        if use_ssl is None:
            use_ssl = True

        # Connect and send
        if use_ssl:
            smtp = aiosmtplib.SMTP(
                hostname=smtp_host,
                port=smtp_port,
                use_tls=True,
                timeout=30,
            )
        else:
            smtp = aiosmtplib.SMTP(
                hostname=smtp_host,
                port=smtp_port,
                timeout=30,
            )

        try:
            await smtp.connect()
            if not use_ssl:
                await smtp.starttls()
            await smtp.login(sender, password)
            await smtp.send_message(msg)
            log.info(f"Email sent: {sender} -> {to} [{subject}]")
        finally:
            try:
                await smtp.quit()
            except Exception:
                pass

    async def test_connection(self, email: str, password: str) -> str:
        """Test SMTP connectivity. Returns 'ok' or error message."""
        host, port, ssl = get_smtp_config(email)
        try:
            if ssl:
                smtp = aiosmtplib.SMTP(hostname=host, port=port, use_tls=True, timeout=15)
            else:
                smtp = aiosmtplib.SMTP(hostname=host, port=port, timeout=15)
            await smtp.connect()
            if not ssl:
                await smtp.starttls()
            await smtp.login(email, password)
            await smtp.quit()
            return "ok"
        except Exception as e:
            return str(e)


# Global singleton
smtp_pool = SmtpPool()
