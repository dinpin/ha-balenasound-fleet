"""Config flow for balenaCloud."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BalenaCloudApi, BalenaCloudApiError
from .const import CONF_API_TOKEN, CONF_APP_ID, CONF_LOCAL_DEVICE_URLS, DOMAIN


class BalenaCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a balenaCloud fleet using an API key and application ID."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Validate credentials and create the fleet entry."""
        errors = {}
        if user_input is not None:
            token = user_input[CONF_API_TOKEN].strip()
            app_id = user_input[CONF_APP_ID].strip()
            local_device_urls = user_input.get(CONF_LOCAL_DEVICE_URLS, "").strip()
            await self.async_set_unique_id(app_id)
            self._abort_if_unique_id_configured()
            try:
                api = BalenaCloudApi(
                    async_get_clientsession(self.hass), token, app_id, local_device_urls
                )
                await api.async_get_devices()
            except (BalenaCloudApiError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"balenaCloud fleet {app_id}",
                    data={
                        CONF_API_TOKEN: token,
                        CONF_APP_ID: app_id,
                        CONF_LOCAL_DEVICE_URLS: local_device_urls,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_TOKEN): str,
                    vol.Required(CONF_APP_ID): str,
                    vol.Optional(CONF_LOCAL_DEVICE_URLS, default=""): str,
                }
            ),
            errors=errors,
        )
