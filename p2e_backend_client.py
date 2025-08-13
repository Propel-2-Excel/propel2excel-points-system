import os
import aiohttp
import asyncio
from typing import Any, Dict, Optional

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "").rstrip("/")
BOT_SHARED_SECRET = os.getenv("BOT_SHARED_SECRET", "")


class P2EClient:
    def __init__(self, base_url: Optional[str] = None, secret: Optional[str] = None):
        self.base_url = (base_url or BACKEND_API_URL).rstrip("/")
        self.secret = secret or BOT_SHARED_SECRET
        if not self.base_url or not self.secret:
            raise RuntimeError("BACKEND_API_URL and BOT_SHARED_SECRET must be set")

    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json", "X-Bot-Secret": self.secret}

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/bot/", json=payload, headers=self._headers()) as resp:
                text = await resp.text()
                if resp.status not in (200, 201):
                    raise RuntimeError(f"API {payload.get('action')} failed {resp.status}: {text[:400]}")
                if "application/json" in resp.headers.get("Content-Type", ""):
                    return await resp.json()
                return {}

    # Public API
    async def upsert_user(self, discord_id: str, display_name: str = "", username: str = ""):
        return await self._post({"action": "upsert-user", "discord_id": discord_id, "display_name": display_name, "username": username})

    async def add_activity(self, discord_id: str, activity_type: str, details: str = ""):
        return await self._post({"action": "add-activity", "discord_id": discord_id, "activity_type": activity_type, "details": details})

    async def summary(self, discord_id: str, limit: int = 10):
        return await self._post({"action": "summary", "discord_id": discord_id, "limit": int(limit)})

    async def leaderboard(self, page: int = 1, page_size: int = 10):
        return await self._post({"action": "leaderboard", "page": int(page), "page_size": int(page_size)})

    async def admin_adjust(self, discord_id: str, delta_points: int, reason: str = "Admin adjustment"):
        return await self._post({"action": "admin-adjust", "discord_id": discord_id, "delta_points": int(delta_points), "reason": reason})

    async def redeem(self, discord_id: str, incentive_id: int):
        return await self._post({"action": "redeem", "discord_id": discord_id, "incentive_id": int(incentive_id)})

    async def clear_warnings(self, discord_id: str):
        return await self._post({"action": "clear-warnings", "discord_id": discord_id})

    async def suspend_user(self, discord_id: str, minutes: int):
        return await self._post({"action": "suspend-user", "discord_id": discord_id, "duration_minutes": int(minutes)})

    async def unsuspend_user(self, discord_id: str):
        return await self._post({"action": "unsuspend-user", "discord_id": discord_id})

    async def activitylog(self, hours: int = 24, limit: int = 20):
        return await self._post({"action": "activitylog", "hours": int(hours), "limit": int(limit)})

    async def get_incentives(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/incentives/", headers=self._headers()) as resp:
                text = await resp.text()
                if resp.status != 200:
                    raise RuntimeError(f"GET incentives failed {resp.status}: {text[:400]}")
                if "application/json" in resp.headers.get("Content-Type", ""):
                    return await resp.json()
                return {}

    async def link(self, code: str, discord_id: str):
        return await self._post({"action": "link", "code": code, "discord_id": discord_id})


async def with_retries(coro_factory, retries: int = 2, delay: float = 0.5):
    last = None
    for i in range(retries + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last = e
            if i < retries:
                await asyncio.sleep(delay)
    raise last


