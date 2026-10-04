"""Set up locally discovered balenaSound devices."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_DEVICE_URL, CONF_DEVICE_UUID, DOMAIN, PLATFORMS, SCAN_INTERVAL
from .device_api import BalenaSoundDeviceApi


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a coordinator for one local balenaSound device."""
    api = BalenaSoundDeviceApi(
        async_get_clientsession(hass),
        entry.data[CONF_DEVICE_URL],
        entry.data[CONF_DEVICE_UUID],
    )

    async def async_update_device():
        return await api.async_get_status()

    coordinator = DataUpdateCoordinator(
        hass,
        logger=_LOGGER,
        name=f"balenaSound {entry.data[CONF_DEVICE_UUID][:8]}",
        update_method=async_update_device,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a local device entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
