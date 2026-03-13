"""Tracking system — pixel injection, link rewriting, unsubscribe URL."""

from __future__ import annotations

import re
from urllib.parse import quote


class TrackingManager:
    """Inject tracking pixel, rewrite links, add unsubscribe URL."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def inject_tracking_pixel(self, html: str, tracking_id: str) -> str:
        """Insert a 1x1 transparent GIF before </body>."""
        pixel_url = f"{self.base_url}/t/o/{tracking_id}.gif"
        pixel_tag = (
            f'<img src="{pixel_url}" width="1" height="1" '
            f'style="display:none" alt="" />'
        )
        if "</body>" in html.lower():
            # Insert before </body>
            idx = html.lower().rfind("</body>")
            return html[:idx] + pixel_tag + html[idx:]
        else:
            return html + pixel_tag

    def rewrite_links(self, html: str, tracking_id: str) -> tuple[str, list[str]]:
        """Rewrite all <a href="..."> links to tracking URLs.

        Returns (new_html, original_url_list).
        Link index corresponds to position in the url list.
        """
        link_urls: list[str] = []
        link_pattern = re.compile(
            r'(<a\s[^>]*href=["\'])([^"\']+)(["\'][^>]*>)',
            re.IGNORECASE,
        )

        def _replace(m):
            prefix = m.group(1)
            url = m.group(2)
            suffix = m.group(3)

            # Skip mailto:, tel:, and anchor links
            if url.startswith(("mailto:", "tel:", "#", "{{", "{%")):
                return m.group(0)
            # Skip unsubscribe URL placeholder (handled separately)
            if "unsubscribe" in url.lower():
                return m.group(0)

            idx = len(link_urls)
            link_urls.append(url)
            tracking_url = f"{self.base_url}/t/c/{tracking_id}/{idx}"
            return f"{prefix}{tracking_url}{suffix}"

        new_html = link_pattern.sub(_replace, html)
        return new_html, link_urls

    def inject_unsubscribe(self, html: str, tracking_id: str) -> str:
        """Replace {{unsubscribe_url}} or append unsubscribe link at bottom."""
        unsub_url = f"{self.base_url}/t/u/{tracking_id}"

        if "{{unsubscribe_url}}" in html:
            return html.replace("{{unsubscribe_url}}", unsub_url)

        # Append default unsubscribe footer if no placeholder
        footer = (
            '<div style="text-align:center;font-size:12px;color:#999;'
            'margin-top:20px;padding:10px;">'
            f'<a href="{unsub_url}" style="color:#999;">退订 / Unsubscribe</a>'
            '</div>'
        )
        if "</body>" in html.lower():
            idx = html.lower().rfind("</body>")
            return html[:idx] + footer + html[idx:]
        return html + footer

    def get_unsubscribe_url(self, tracking_id: str) -> str:
        return f"{self.base_url}/t/u/{tracking_id}"
