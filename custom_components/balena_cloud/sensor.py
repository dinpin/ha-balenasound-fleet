"""Sensors for balenaCloud devices."""

from homeassistant.components.sensor import SensorEntity

from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up device status sensors."""
    coordinator = hass.data["balena_cloud"][entry.entry_id]["coordinator"]
    async_add_entities(
        BalenaDeviceStatusSensor(coordinator, uuid) for uuid in coordinator.data
    )


class BalenaDeviceStatusSensor(BalenaDeviceEntity, SensorEntity):
    """Expose balenaCloud's overall device status."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:raspberry-pi"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_status"

    @property
    def native_value(self):
        return self.device.get("overall_status") or self.device.get("status") or "unknown"

    @property
    def extra_state_attributes(self):
        device = self.device
        return {
            "uuid": self.device_uuid,
            "online": device.get("is_online"),
            "release_id": device.get("is_running__release"),
            "balena_status": device.get("status"),
        }
