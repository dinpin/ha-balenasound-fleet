"""Asynchronous client for a local balenaSound Supervisor API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession


class BalenaSoundDeviceApiError(Exception):
    """Raised when a local balenaSound device request fails."""


class BalenaSoundDeviceApi:
    """Read status and perform actions through one device's local API."""

    def __init__(self, session: ClientSession, base_url: str, device_uuid: str) -> None:
        self._session = session
        self.base_url = base_url.rstrip("/")
        self.device_uuid = device_uuid

    async def _request(self, method: str, path: str) -> Any:
        try:
            async with self._session.request(method, f"{self.base_url}{path}") as response:
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except (ClientError, TimeoutError, ValueError) as err:
            raise BalenaSoundDeviceApiError(str(err)) from err

    async def async_get_status(self) -> dict[str, Any]:
        """Return connectivity and playback state from the local supervisor."""
        try:
            await self._request("GET", "/ping")
        except BalenaSoundDeviceApiError:
            return {"uuid": self.device_uuid, "online": False, "playing": None}

        try:
            payload = await self._request("GET", "/audio/playback")
        except BalenaSoundDeviceApiError:
            return {"uuid": self.device_uuid, "online": True, "playing": None}

        playing = payload.get("playing") if isinstance(payload, dict) else None
        if playing is not None and not isinstance(playing, bool):
            playing = None
        return {"uuid": self.device_uuid, "online": True, "playing": playing}

    async def async_reboot(self) -> None:
        """Request a local device reboot."""
        await self._request("POST", "/device/reboot")

    async def async_restart_app(self) -> None:
        """Request a local application restart."""
        await self._request("POST", "/device/restart")
