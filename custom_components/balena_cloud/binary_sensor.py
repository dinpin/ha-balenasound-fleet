"""Connectivity and playback binary sensors."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary sensors for one local device."""
    coordinator = hass.data["balena_cloud"][entry.entry_id]["coordinator"]
    device_uuid = entry.data["device_uuid"]
    async_add_entities(
        [
            BalenaDeviceOnlineSensor(coordinator, device_uuid),
            BalenaDevicePlayingSensor(coordinator, device_uuid),
        ]
    )


class BalenaDeviceOnlineSensor(BalenaDeviceEntity, BinarySensorEntity):
    """Indicate whether a balena device is online."""

    _attr_has_entity_name = True
    _attr_name = "Online"
    _attr_device_class = "connectivity"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_online"

    @property
    def is_on(self):
        value = self.device.get("online")
        if value is None:
            return None
        return str(value).lower() == "true" if isinstance(value, str) else bool(value)


class BalenaDevicePlayingSensor(BalenaDeviceEntity, BinarySensorEntity):
    """Indicate whether any PulseAudio sink on a device is active."""

    _attr_has_entity_name = True
    _attr_name = "Playing audio"
    _attr_icon = "mdi:music-note"

    @property
    def unique_id(self) -> str:
        return f"{self.device_uuid}_playing_audio"

    @property
    def is_on(self):
        """Return playback state, or unknown until the device reports it."""
        return self.device.get("playing")

