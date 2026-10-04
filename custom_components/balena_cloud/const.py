"""Constants for the balenaCloud integration."""

from datetime import timedelta

DOMAIN = "balena_cloud"
CONF_API_TOKEN = "api_token"
CONF_APP_ID = "app_id"
CONF_LOCAL_DEVICE_URLS = "local_device_urls"
PLATFORMS = ["sensor", "binary_sensor", "button"]
SCAN_INTERVAL = timedelta(seconds=60)
API_BASE = "https://api.balena-cloud.com"
ZEROCONF_SERVICE_TYPE = "_balenasound._tcp.local."
