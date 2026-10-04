"""Config flow for locally connected balenaSound devices."""

from urllib.parse import urlsplit

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_DEVICE_URL, CONF_DEVICE_UUID, DOMAIN
from .discovery import select_service_address


class BalenaSoundConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up one balenaSound device discovered on the local network."""

    VERSION = 1

    async def async_step_zeroconf(self, discovery_info):
        """Create an entry for a balenaSound mDNS advertisement."""
        properties = {
            key.decode() if isinstance(key, bytes) else key:
            value.decode() if isinstance(value, bytes) else value
            for key, value in discovery_info.properties.items()
        }
        uuid = properties.get("uuid")
        addresses = getattr(discovery_info, "ip_addresses", None)
        if not addresses:
            address = getattr(discovery_info, "ip_address", None)
            addresses = [address] if address else []
        address = select_service_address(properties, addresses)
        if not isinstance(uuid, str) or not uuid.strip() or not address:
            return self.async_abort(reason="not_balena_sound")
        uuid = uuid.strip()

        await self.async_set_unique_id(uuid)
        self._abort_if_unique_id_configured()
        if ":" in address:
            address = f"[{address}]"
        url = f"http://{address}:{discovery_info.port}"
        return self.async_create_entry(
            title=f"balenaSound {uuid[:8]}",
            data={CONF_DEVICE_UUID: uuid, CONF_DEVICE_URL: url},
        )

    async def async_step_user(self, user_input=None):
        """Allow a device to be added with its local Supervisor URL."""
        errors = {}
        if user_input is not None:
            uuid = user_input[CONF_DEVICE_UUID].strip()
            url = user_input[CONF_DEVICE_URL].strip().rstrip("/")
            parsed = urlsplit(url)
            if (
                not uuid
                or parsed.scheme not in ("http", "https")
                or not parsed.netloc
                or parsed.query
                or parsed.fragment
            ):
                errors["base"] = "invalid_device"
            else:
                await self.async_set_unique_id(uuid)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"balenaSound {uuid[:8]}",
                    data={CONF_DEVICE_UUID: uuid, CONF_DEVICE_URL: url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_UUID): str,
                    vol.Required(CONF_DEVICE_URL): str,
                }
            ),
            errors=errors,
        )
