"""Local balenaSound device action buttons."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .device_api import BalenaSoundDeviceApiError
from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up restart and reboot buttons for one device."""
    data = hass.data["balena_cloud"][entry.entry_id]
    coordinator = data["coordinator"]
    device_uuid = entry.data["device_uuid"]
    async_add_entities(
        [
            BalenaRebootButton(coordinator, data["api"], device_uuid),
            BalenaRestartAppButton(coordinator, data["api"], device_uuid),
        ]
    )


class BalenaActionButton(BalenaDeviceEntity, ButtonEntity):
    """Base for a local Supervisor action."""

    def __init__(self, coordinator, api, device_uuid: str) -> None:
        super().__init__(coordinator, device_uuid)
        self.api = api

    async def press(self) -> None:
        """Perform the action and report request errors in Home Assistant."""
        try:
            await self._press()
        except BalenaSoundDeviceApiError as err:
            raise HomeAssistantError(f"balenaSound local action failed: {err}") from err

    async def _press(self) -> None:
        raise NotImplementedError


class BalenaRebootButton(BalenaActionButton):
    """Reboot one device through its local Supervisor API."""

    _attr_has_entity_name = True
    _attr_name = "Reboot device"
    _attr_icon = "mdi:restart-alert"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_reboot"

    async def _press(self) -> None:
        await self.api.async_reboot()


class BalenaRestartAppButton(BalenaActionButton):
    """Restart the balena application on one device."""

    _attr_has_entity_name = True
    _attr_name = "Restart application"
    _attr_icon = "mdi:restart"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_restart_app"

    async def _press(self) -> None:
        await self.api.async_restart_app()
