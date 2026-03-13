"""HTTP client for calling the FastAPI backend."""

from __future__ import annotations

import asyncio
import json
import httpx


class EmailAPIClient:
    """Async HTTP client wrapping FastAPI endpoints."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict:
        return {"X-API-Key": self.api_key}

    async def get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, data: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    async def put(self, path: str, data: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.put(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=data,
            )
            resp.raise_for_status()
            return resp.json()

    async def delete(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(
                f"{self.base_url}{path}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def post_form(
        self,
        path: str,
        data: dict | None = None,
        files: list[tuple[str, tuple[str, bytes]]] | None = None,
    ) -> dict:
        """POST with multipart/form-data (for file uploads)."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                data=data,
                files=files,
            )
            resp.raise_for_status()
            return resp.json()
