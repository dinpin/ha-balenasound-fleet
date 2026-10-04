"""Sensors for balenaSound devices."""

from homeassistant.components.sensor import SensorEntity

from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the local device status sensor."""
    coordinator = hass.data["balena_cloud"][entry.entry_id]["coordinator"]
    async_add_entities([BalenaDeviceStatusSensor(coordinator, entry.data["device_uuid"])])


class BalenaDeviceStatusSensor(BalenaDeviceEntity, SensorEntity):
    """Expose local Supervisor connectivity status."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:raspberry-pi"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_status"

    @property
    def native_value(self):
        return "online" if self.device.get("online") else "offline"

    @property
    def extra_state_attributes(self):
        return {"uuid": self.device_uuid}
