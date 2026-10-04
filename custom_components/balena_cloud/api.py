"""Small asynchronous client for balenaCloud's API and Supervisor proxy."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote, urlsplit

from aiohttp import ClientError, ClientSession

from .const import API_BASE


_LOGGER = logging.getLogger(__name__)


class BalenaCloudApiError(Exception):
    """Raised for balenaCloud API errors."""


class BalenaCloudApi:
    """Access one balenaCloud application/fleet."""

    def __init__(
        self, session: ClientSession, token: str, app_id: str, local_device_urls: str = ""
    ) -> None:
        self._session = session
        self._token = token
        self.app_id = app_id
        self._manual_device_urls = self._parse_local_device_urls(local_device_urls)
        self._discovered_device_urls: dict[str, str] = {}

    def set_discovered_device_url(self, uuid: str, url: str) -> None:
        """Set a LAN URL learned from a balenaSound mDNS advertisement."""
        self._discovered_device_urls[uuid] = url.rstrip("/")

    def remove_discovered_device_url(self, uuid: str, url: str) -> None:
        """Remove a discovered URL only if it still matches the advertisement."""
        if self._discovered_device_urls.get(uuid) == url.rstrip("/"):
            self._discovered_device_urls.pop(uuid, None)

    def _local_device_url(self, uuid: str) -> str | None:
        """Prefer user-configured URLs over addresses learned with mDNS."""
        return self._manual_device_urls.get(uuid) or self._discovered_device_urls.get(uuid)

    @staticmethod
    def _parse_local_device_urls(value: str) -> dict[str, str]:
        """Parse UUID=URL lines for devices reachable on the local network."""
        urls = {}
        for line_number, line in enumerate(value.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            uuid, separator, url = line.partition("=")
            parsed = urlsplit(url.strip())
            if (
                not separator
                or not uuid.strip()
                or parsed.scheme not in ("http", "https")
                or not parsed.netloc
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(f"Invalid local device URL mapping on line {line_number}")
            urls[uuid.strip()] = url.strip().rstrip("/")
        return urls

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with self._session.request(
                method, f"{API_BASE}{path}", headers=self._headers, **kwargs
            ) as response:
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except (ClientError, TimeoutError, ValueError) as err:
            raise BalenaCloudApiError(str(err)) from err

    async def async_get_devices(self) -> dict[str, dict[str, Any]]:
        """Fetch devices and return them indexed by UUID."""
        # The application ID is numeric and accepted directly in OData's eq filter.
        query = (
            "?$filter=belongs_to__application%20eq%20%27"
            f"{quote(str(self.app_id), safe='')}%27&$select="
            "id,device_name,uuid,is_online,status,overall_status,is_running__release"
        )
        payload = await self._request("GET", f"/v7/device{query}")
        devices = (
            payload.get("d", payload.get("results", []))
            if isinstance(payload, dict)
            else payload
        )
        if not isinstance(devices, list):
            raise BalenaCloudApiError("Unexpected response when listing fleet devices")

        devices_by_uuid = {
            str(device["uuid"]): device for device in devices if device.get("uuid")
        }
        await self._update_local_playback(devices_by_uuid)
        return devices_by_uuid

    async def _update_local_playback(self, devices: dict[str, dict[str, Any]]) -> None:
        """Read playback state directly from configured devices on the LAN."""
        async def read_playback(uuid: str, device: dict[str, Any]) -> None:
            url = self._local_device_url(uuid)
            if not url:
                return
            try:
                async with self._session.get(f"{url}/audio/playback") as response:
                    response.raise_for_status()
                    payload = await response.json()
                playing = payload.get("playing") if isinstance(payload, dict) else None
                if playing is None or isinstance(playing, bool):
                    device["balena_sound_playing"] = playing
            except (ClientError, TimeoutError, ValueError) as err:
                # A failed LAN request leaves playback unknown without failing fleet refresh.
                _LOGGER.warning(
                    "Could not read playback for balenaSound device %s from %s: %s",
                    uuid,
                    url,
                    err,
                )
                return

        await asyncio.gather(
            *(read_playback(uuid, device) for uuid, device in devices.items())
        )

    async def _local_post(self, uuid: str, path: str) -> bool:
        """Post an action to a device's local supervisor, if configured."""
        url = self._local_device_url(uuid)
        if not url:
            return False
        try:
            async with self._session.post(f"{url}{path}") as response:
                response.raise_for_status()
        except (ClientError, TimeoutError, ValueError) as err:
            raise BalenaCloudApiError(f"Local device action failed: {err}") from err
        return True

    async def async_reboot(self, uuid: str) -> None:
        """Reboot locally when reachable, otherwise use balenaCloud's proxy."""
        if not await self._local_post(uuid, "/device/reboot"):
            await self._request("POST", "/supervisor/v1/reboot", json={"uuid": uuid})

    async def async_restart_app(self, uuid: str) -> None:
        """Restart locally when reachable, otherwise use balenaCloud's proxy."""
        if not await self._local_post(uuid, "/device/restart"):
            await self._request(
                "POST",
                "/supervisor/v1/restart",
                json={"uuid": uuid, "data": {"appId": int(self.app_id)}},
            )
