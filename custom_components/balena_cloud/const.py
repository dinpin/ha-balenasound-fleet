"""Constants for the balenaSound local integration."""

from datetime import timedelta

DOMAIN = "balena_cloud"
CONF_DEVICE_UUID = "device_uuid"
CONF_DEVICE_URL = "device_url"
PLATFORMS = ["sensor", "binary_sensor", "button"]
SCAN_INTERVAL = timedelta(seconds=60)
