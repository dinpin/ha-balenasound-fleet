"""Helpers for resolving balenaSound mDNS advertisements."""


def select_device_name(properties: dict, device_uuid: str) -> str:
    """Use the advertised balena device name, or a stable UUID fallback."""
    name = properties.get("device_name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return f"balenaSound {device_uuid[:8]}"


def select_service_address(properties: dict, addresses: list[str]) -> str | None:
    """Prefer the device interface IP advertised by new supervisor versions."""
    advertised_address = properties.get("ip_address")
    if isinstance(advertised_address, str) and advertised_address:
        return advertised_address
    # Older supervisor versions do not include an interface address in TXT records.
    return next(
        (item for item in addresses if ":" not in item),
        addresses[0] if addresses else None,
    )
