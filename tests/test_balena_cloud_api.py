"""Tests for balenaCloud fleet lookup and local device requests."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Load the API module without importing Home Assistant or requiring aiohttp.
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
BalenaCloudApi = importlib.import_module(f"{package_name}.api").BalenaCloudApi


def response_context(payload=None):
    """Create an async response context manager for the local HTTP session."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(return_value=payload or {})
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


class BalenaCloudApiLocalTests(unittest.IsolatedAsyncioTestCase):
    """Verify local playback polling and local-first device actions."""

    async def test_poll_playback_for_configured_device(self):
        session = MagicMock()
        session.get.return_value = response_context({"playing": True})
        api = BalenaCloudApi(session, "token", "42", "device-a=http://192.168.1.2:80/")
        api._request = AsyncMock(return_value={"d": [{"uuid": "device-a"}]})

        devices = await api.async_get_devices()

        self.assertTrue(devices["device-a"]["balena_sound_playing"])
        session.get.assert_called_once_with("http://192.168.1.2:80/audio/playback")

    async def test_unknown_playback_is_preserved(self):
        session = MagicMock()
        session.get.return_value = response_context({"playing": None})
        api = BalenaCloudApi(session, "token", "42", "device-a=http://192.168.1.2")
        api._request = AsyncMock(return_value={"d": [{"uuid": "device-a"}]})

        devices = await api.async_get_devices()

        self.assertIsNone(devices["device-a"]["balena_sound_playing"])

    async def test_reboot_posts_to_local_supervisor(self):
        session = MagicMock()
        session.post.return_value = response_context()
        api = BalenaCloudApi(session, "token", "42", "device-a=http://192.168.1.2")
        api._request = AsyncMock()

        await api.async_reboot("device-a")

        session.post.assert_called_once_with("http://192.168.1.2/device/reboot")
        api._request.assert_not_awaited()

    async def test_restart_posts_to_local_supervisor(self):
        session = MagicMock()
        session.post.return_value = response_context()
        api = BalenaCloudApi(session, "token", "42", "device-a=http://192.168.1.2")
        api._request = AsyncMock()

        await api.async_restart_app("device-a")

        session.post.assert_called_once_with("http://192.168.1.2/device/restart")
        api._request.assert_not_awaited()

    async def test_reboot_uses_cloud_proxy_without_local_url(self):
        api = BalenaCloudApi(None, "token", "42")
        api._request = AsyncMock()

        await api.async_reboot("device-a")

        api._request.assert_awaited_once_with(
            "POST", "/supervisor/v1/reboot", json={"uuid": "device-a"}
        )

    def test_discovered_url_used_when_no_manual_url_exists(self):
        api = BalenaCloudApi(None, "token", "42")
        api.set_discovered_device_url("device-a", "http://192.168.1.2:80/")

        self.assertEqual(api._local_device_url("device-a"), "http://192.168.1.2:80")

    def test_manual_url_overrides_discovered_url(self):
        api = BalenaCloudApi(
            None, "token", "42", "device-a=http://192.168.1.3:80"
        )
        api.set_discovered_device_url("device-a", "http://192.168.1.2:80")

        self.assertEqual(api._local_device_url("device-a"), "http://192.168.1.3:80")

    def test_removing_stale_discovery_does_not_remove_new_url(self):
        api = BalenaCloudApi(None, "token", "42")
        api.set_discovered_device_url("device-a", "http://192.168.1.2:80")
        api.set_discovered_device_url("device-a", "http://192.168.1.3:80")

        api.remove_discovered_device_url("device-a", "http://192.168.1.2:80")

        self.assertEqual(api._local_device_url("device-a"), "http://192.168.1.3:80")

    def test_rejects_invalid_local_mapping(self):
        with self.assertRaises(ValueError):
            BalenaCloudApi(None, "token", "42", "device-a=192.168.1.2")


if __name__ == "__main__":
    unittest.main()
