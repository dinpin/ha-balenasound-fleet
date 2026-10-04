"""Tests for local balenaSound API access and mDNS address selection."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

package_name = "custom_components.balena_cloud"
if package_name not in sys.modules:
    package = types.ModuleType(package_name)
    package.__path__ = [str(Path(__file__).parents[1] / "custom_components" / "balena_cloud")]
    sys.modules[package_name] = package
if "aiohttp" not in sys.modules:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = type("ClientSession", (), {})
    sys.modules["aiohttp"] = aiohttp

BalenaSoundDeviceApi = importlib.import_module(
    f"{package_name}.device_api"
).BalenaSoundDeviceApi
select_service_address = importlib.import_module(
    f"{package_name}.discovery"
).select_service_address


def response_context(payload=None, content_type="application/json"):
    """Make a mocked asynchronous HTTP response context."""
    response = MagicMock()
    response.content_type = content_type
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value=payload)
    response.text = AsyncMock(return_value="OK")
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


class BalenaSoundDiscoveryTests(unittest.TestCase):
    """Verify mDNS address selection."""

    def test_prefers_advertised_device_interface_address(self):
        self.assertEqual(
            select_service_address(
                {"ip_address": "192.168.1.25"}, ["172.18.0.1", "192.168.1.25"]
            ),
            "192.168.1.25",
        )

    def test_falls_back_to_ipv4_for_older_advertisements(self):
        self.assertEqual(
            select_service_address({}, ["fe80::1", "172.18.0.1"]), "172.18.0.1"
        )

    def test_returns_none_when_no_addresses_are_available(self):
        self.assertIsNone(select_service_address({}, []))


class BalenaSoundDeviceApiTests(unittest.IsolatedAsyncioTestCase):
    """Verify local playback polling and Supervisor actions."""

    async def test_reads_ping_then_playback(self):
        session = MagicMock()
        session.request.side_effect = [
            response_context(content_type="text/plain"),
            response_context({"playing": True}),
        ]
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2:80/", "device-a")

        status = await api.async_get_status()

        self.assertEqual(status, {"uuid": "device-a", "online": True, "playing": True})
        self.assertEqual(
            [call.args[:2] for call in session.request.call_args_list],
            [
                ("GET", "http://192.168.1.2:80/ping"),
                ("GET", "http://192.168.1.2:80/audio/playback"),
            ],
        )

    async def test_unknown_playback_is_preserved(self):
        session = MagicMock()
        session.request.side_effect = [
            response_context(content_type="text/plain"),
            response_context({"playing": None}),
        ]
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        self.assertIsNone((await api.async_get_status())["playing"])

    async def test_ignores_invalid_playback_value(self):
        session = MagicMock()
        session.request.side_effect = [
            response_context(content_type="text/plain"),
            response_context({"playing": "yes"}),
        ]
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        self.assertIsNone((await api.async_get_status())["playing"])

    async def test_unreachable_device_reports_offline(self):
        session = MagicMock()
        session.request.side_effect = sys.modules["aiohttp"].ClientError("offline")
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        self.assertEqual(
            await api.async_get_status(),
            {"uuid": "device-a", "online": False, "playing": None},
        )

    async def test_playback_failure_keeps_device_online(self):
        session = MagicMock()
        session.request.side_effect = [
            response_context(content_type="text/plain"),
            sys.modules["aiohttp"].ClientError("playback unavailable"),
        ]
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        self.assertEqual(
            await api.async_get_status(),
            {"uuid": "device-a", "online": True, "playing": None},
        )

    async def test_reboot_posts_to_local_supervisor(self):
        session = MagicMock()
        session.request.return_value = response_context(content_type="text/plain")
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        await api.async_reboot()

        session.request.assert_called_once_with(
            "POST", "http://192.168.1.2/device/reboot"
        )

    async def test_restart_posts_to_local_supervisor(self):
        session = MagicMock()
        session.request.return_value = response_context(content_type="text/plain")
        api = BalenaSoundDeviceApi(session, "http://192.168.1.2", "device-a")

        await api.async_restart_app()

        session.request.assert_called_once_with(
            "POST", "http://192.168.1.2/device/restart"
        )


if __name__ == "__main__":
    unittest.main()
