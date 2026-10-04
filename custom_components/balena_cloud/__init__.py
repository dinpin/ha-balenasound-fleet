"""balenaCloud fleet integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import BalenaCloudApi
from .const import (
    CONF_API_TOKEN,
    CONF_APP_ID,
    CONF_LOCAL_DEVICE_URLS,
    DOMAIN,
    PLATFORMS,
    SCAN_INTERVAL,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a fleet coordinator from a config entry."""
    api = BalenaCloudApi(
        async_get_clientsession(hass),
        entry.data[CONF_API_TOKEN],
        entry.data[CONF_APP_ID],
        entry.data.get(CONF_LOCAL_DEVICE_URLS, ""),
    )
    coordinator = DataUpdateCoordinator(
        hass,
        logger=logging.getLogger(__name__),
        name=f"balenaCloud fleet {entry.data[CONF_APP_ID]}",
        update_method=api.async_get_devices,
        update_interval=SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"api": api, "coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a fleet config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
