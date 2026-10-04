"""Device management buttons for balenaCloud."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .api import BalenaCloudApiError
from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up restart and reboot buttons for each fleet device."""
    data = hass.data["balena_cloud"][entry.entry_id]
    coordinator = data["coordinator"]
    async_add_entities(
        button_type(coordinator, data["api"], uuid)
        for uuid in coordinator.data
        for button_type in (BalenaRebootButton, BalenaRestartAppButton)
    )


class BalenaActionButton(BalenaDeviceEntity, ButtonEntity):
    """Base for an explicit balenaCloud device action."""

    def __init__(self, coordinator, api, device_uuid: str) -> None:
        super().__init__(coordinator, device_uuid)
        self.api = api

    async def press(self) -> None:
        """Perform its action and report API errors in Home Assistant."""
        try:
            await self._press()
        except BalenaCloudApiError as err:
            raise HomeAssistantError(f"balenaCloud action failed: {err}") from err

    async def _press(self) -> None:
        raise NotImplementedError


class BalenaRebootButton(BalenaActionButton):
    """Reboot one device through the Supervisor proxy."""

    _attr_has_entity_name = True
    _attr_name = "Reboot device"
    _attr_icon = "mdi:restart-alert"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_reboot"

    async def _press(self) -> None:
        await self.api.async_reboot(self.device_uuid)


class BalenaRestartAppButton(BalenaActionButton):
    """Restart the balena application on one device."""

    _attr_has_entity_name = True
    _attr_name = "Restart application"
    _attr_icon = "mdi:restart"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_restart_app"

    async def _press(self) -> None:
        await self.api.async_restart_app(self.device_uuid)
