"""Coordinator entity helpers."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class BalenaDeviceEntity(CoordinatorEntity):
    """Common entity for one locally connected balenaSound device."""

    def __init__(self, coordinator, device_uuid: str) -> None:
        super().__init__(coordinator)
        self.device_uuid = device_uuid

    @property
    def device(self) -> dict:
        """Return the latest local device status."""
        return self.coordinator.data

    @property
    def device_name(self) -> str:
        """Human-readable device name."""
        return self.device.get("device_name", f"balenaSound {self.device_uuid[:8]}")

    @property
    def device_info(self):
        """Group entities under the physical balenaSound device."""
        return {
            "identifiers": {(DOMAIN, self.device_uuid)},
            "name": self.device_name,
            "manufacturer": "balena",
            "model": "balenaSound",
        }
