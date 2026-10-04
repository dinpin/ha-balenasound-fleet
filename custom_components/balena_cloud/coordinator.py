"""Coordinator entity helpers."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class BalenaDeviceEntity(CoordinatorEntity):
    """Common entity for a balena device."""

    def __init__(self, coordinator, device_uuid: str) -> None:
        super().__init__(coordinator)
        self.device_uuid = device_uuid

    @property
    def device(self) -> dict:
        """Current cloud record, or an empty record when no longer listed."""
        return self.coordinator.data.get(self.device_uuid, {})

    @property
    def device_name(self) -> str:
        """Human-readable balena device name."""
        return self.device.get("device_name") or self.device_uuid[:8]

    @property
    def device_info(self):
        """Group entities under the physical balena device."""
        return {
            "identifiers": {(DOMAIN, self.device_uuid)},
            "name": self.device_name,
            "manufacturer": "balena",
            "model": "balenaOS device",
            "configuration_url": "https://dashboard.balena-cloud.com/",
        }
