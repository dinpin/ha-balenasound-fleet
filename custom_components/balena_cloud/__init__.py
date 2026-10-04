"""balenaCloud fleet integration."""

import logging

from homeassistant.components import zeroconf
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
    ZEROCONF_SERVICE_TYPE,
)
from .discovery import select_service_address


_LOGGER = logging.getLogger(__name__)


class BalenaSoundServiceListener:
    """Resolve balenaSound mDNS announcements for devices in this fleet."""

    def __init__(self, hass, aiozc, api, coordinator) -> None:
        self.hass = hass
        self.aiozc = aiozc
        self.api = api
        self.coordinator = coordinator
        self.services = {}

    def add_service(self, _zc, service_type, name) -> None:
        """Resolve a newly advertised service."""
        self.hass.async_create_task(self._async_resolve(service_type, name))

    def update_service(self, zc, service_type, name) -> None:
        """Refresh the address when an advertisement changes."""
        self.add_service(zc, service_type, name)

    def remove_service(self, _zc, _service_type, name) -> None:
        """Drop an address after its mDNS service disappears."""
        discovered = self.services.pop(name, None)
        if discovered:
            uuid, url = discovered
            self.api.remove_discovered_device_url(uuid, url)
            self.hass.async_create_task(self.coordinator.async_request_refresh())

    async def _async_resolve(self, service_type, name) -> None:
        """Resolve a service and register its address if it belongs to the fleet."""
        try:
            info = await self.aiozc.async_get_service_info(service_type, name)
        except Exception:  # mDNS lookups can fail while services are changing.
            _LOGGER.debug("Could not resolve balenaSound mDNS service %s", name, exc_info=True)
            return
        if info is None:
            return

        properties = {
            key.decode() if isinstance(key, bytes) else key:
            value.decode() if isinstance(value, bytes) else value
            for key, value in info.properties.items()
        }
        uuid = properties.get("uuid")
        if not uuid or uuid not in self.coordinator.data:
            return

        addresses = info.parsed_addresses()
        address = select_service_address(properties, addresses)
        if not address:
            _LOGGER.debug("balenaSound service %s has no usable addresses", name)
            return
        if ":" in address:
            address = f"[{address}]"
        url = f"http://{address}:{info.port}"
        previous = self.services.get(name)
        if previous and previous != (uuid, url):
            self.api.remove_discovered_device_url(*previous)
        self.services[name] = (uuid, url)
        self.api.set_discovered_device_url(uuid, url)
        _LOGGER.info("Discovered balenaSound device %s at %s", uuid, url)
        self.hass.async_create_task(self.coordinator.async_request_refresh())


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

    aiozc = await zeroconf.async_get_async_instance(hass)
    listener = BalenaSoundServiceListener(hass, aiozc, api, coordinator)
    await aiozc.async_add_service_listener(ZEROCONF_SERVICE_TYPE, listener)
    entry.async_on_unload(lambda: aiozc.async_remove_service_listener(listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a fleet config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
