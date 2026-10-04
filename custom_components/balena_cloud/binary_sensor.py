"""Online sensors for balenaCloud devices."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .coordinator import BalenaDeviceEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up device online sensors."""
    coordinator = hass.data["balena_cloud"][entry.entry_id]["coordinator"]
    async_add_entities(
        entity_type(coordinator, uuid)
        for uuid in coordinator.data
        for entity_type in (BalenaDeviceOnlineSensor, BalenaDevicePlayingSensor)
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
        value = self.device.get("is_online")
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
        return self.device.get("balena_sound_playing")

