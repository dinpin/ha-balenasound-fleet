"""Asynchronous client for a local balenaSound Supervisor API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

from aiohttp import ClientError, ClientSession

_LOGGER = logging.getLogger(__name__)


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

    async def async_listen_playback_events(
        self, callback: Callable[[bool | None], None]
    ) -> None:
        """Listen for playback events, reconnecting if push is unavailable."""
        url = f"{self.base_url}/audio/playback/events"
        while True:
            try:
                async with self._session.get(url, timeout=None) as response:
                    response.raise_for_status()
                    async for line in response.content:
                        if not line.startswith(b"data:"):
                            continue
                        try:
                            payload = json.loads(line[5:].strip())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue
                        playing = payload.get("playing") if isinstance(payload, dict) else None
                        if playing is None or isinstance(playing, bool):
                            callback(playing)
            except asyncio.CancelledError:
                raise
            except (ClientError, TimeoutError, ValueError, OSError) as err:
                _LOGGER.debug("Playback event stream disconnected: %s", err)
            await asyncio.sleep(5)

    async def async_reboot(self) -> None:
        """Request a local device reboot."""
        await self._request("POST", "/device/reboot")

    async def async_restart_app(self) -> None:
        """Request a local application restart."""
        await self._request("POST", "/device/restart")
