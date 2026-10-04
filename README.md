# balenaSound Fleet Monitor for Home Assistant

A Home Assistant integration for monitoring **balenaSound playback and device health** across a balenaCloud fleet. It uses balenaCloud to find fleet devices and read their status, and mDNS to discover balenaSound devices on the local network. Manual per-device LAN URLs remain available as overrides. This is not a general-purpose balenaCloud fleet-management integration.

- Connectivity and playback binary sensors, plus a status sensor, for each device.
- Reboot and application-restart buttons. When a local URL is configured, these use the device's local supervisor API; otherwise, they use the balenaCloud Supervisor proxy.

It does **not** identify the audio source or track, change volume or mode, deploy releases, or monitor service-level health. Keep Home Assistant private and use a dedicated balenaCloud API key.

## Install with HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu in the upper-right and choose **Custom repositories**.
3. Add `https://github.com/dinpin/ha-balenasound-fleet` and select **Integration** as the category.
4. Find **balenaSound Fleet Monitor** in HACS, download it, and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**, then search for **balenaSound Fleet Monitor**.

HACS can install updates for this repository after it is added as a custom repository. Alternatively, install manually by copying `custom_components/balena_cloud` into `<config>/custom_components/` and restarting Home Assistant.

Enter a balenaCloud API key and the numeric application/fleet ID. balenaSound devices advertise their supervisor API address over mDNS, which enables LAN playback monitoring and local actions automatically when Home Assistant and the devices share an mDNS-reachable network. Manual URLs are optional overrides; provide one mapping per device using its exact balena UUID and the base URL for its supervisor HTTP API (usually port `80`):

```text
<device-uuid>=http://192.168.1.42:80
<another-device-uuid>=http://192.168.1.43:80
```

The URL must be reachable from Home Assistant. Leave it blank to rely on mDNS discovery or for cloud-only operation. mDNS generally does not cross VLANs or routers; add a manual URL if multicast discovery is unavailable. balenaCloud credentials are sent only to `api.balena-cloud.com`; local requests use discovered addresses or configured overrides.

## Entities and actions

For each device in the configured fleet, the integration creates:

- `binary_sensor.*_online`
- `binary_sensor.*_playing_audio` (on when at least one PulseAudio sink is active)
- `sensor.*_status` (status attributes include UUID, connectivity, release ID, and raw balena status)
- `button.*_reboot_device`
- `button.*_restart_application`

The buttons take effect immediately. Restart/reboot may make the device temporarily unavailable. Keep these actions out of unattended automations unless that is intentional.

## Limitations

- Entities are initially created for devices present during setup. Reload the config entry or restart Home Assistant to add devices provisioned later.
- API response field availability and release metadata depend on the balenaCloud API response and user permissions.
- Release deployment is deliberately omitted; the prototype does not change a device's desired release.
- Playback is read from each discovered or manually configured device's local `/audio/playback` endpoint. Devices must run a release that advertises `_balenasound._tcp.local.` and exposes that endpoint. Playback remains unknown until the supervisor observes a `play` or `stop` event, and reflects active PulseAudio sinks rather than the selected source or track metadata.
- Local reboot/restart requests require a configured, reachable URL. A local request failure is reported to Home Assistant; it does not silently fall back to cloud control. Devices without a URL use the cloud proxy.
- Home Assistant's built-in Snapcast integration remains useful for multiroom player/group control, but is independent of this fleet integration.

## Development validation

The integration requires Home Assistant at runtime. From the repository root, Python syntax and JSON metadata can be checked with:

```sh
python3 -m compileall -q custom_components/balena_cloud
python3 -c 'import json, pathlib; [json.loads(p.read_text()) for p in pathlib.Path("custom_components/balena_cloud").glob("*.json")]'
```
