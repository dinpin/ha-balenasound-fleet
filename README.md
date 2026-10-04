# balenaCloud Fleet for Home Assistant

A custom Home Assistant integration that creates entities for devices in a balenaCloud application. It polls balenaCloud for device inventory and status. Optionally configured local URLs let it poll playback and run device actions directly over the LAN.

- Connectivity and playback binary sensors, plus a status sensor, for each device.
- Reboot and application-restart buttons. When a local URL is configured, these use the device's local supervisor API; otherwise, they use the balenaCloud Supervisor proxy.

It does **not** identify the audio source or track, change volume or mode, deploy releases, or monitor service-level health. Keep Home Assistant private and use a dedicated balenaCloud API key.

## Install with HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu in the upper-right and choose **Custom repositories**.
3. Add `https://github.com/dinpin/ha-balena-cloud` and select **Integration** as the category.
4. Find **balenaCloud Fleet** in HACS, download it, and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**, then search for **balenaCloud Fleet**.

HACS can install updates for this repository after it is added as a custom repository. Alternatively, install manually by copying `custom_components/balena_cloud` into `<config>/custom_components/` and restarting Home Assistant.

Enter a balenaCloud API key and the numeric application/fleet ID. To enable LAN playback and local actions, also provide one mapping per device, using its exact balena UUID and the base URL for its supervisor HTTP API (usually port `80`):

```text
<device-uuid>=http://192.168.1.42:80
<another-device-uuid>=http://192.168.1.43:80
```

The URL must be reachable from Home Assistant. Leave it blank for cloud-only operation. balenaCloud credentials are sent only to `api.balena-cloud.com`; local requests use the configured device URLs.

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
- Playback is read from each configured device's local `/audio/playback` endpoint. Devices must run a release exposing that endpoint. Playback remains unknown until the supervisor observes a `play` or `stop` event, and reflects active PulseAudio sinks rather than the selected source or track metadata.
- Local reboot/restart requests require a configured, reachable URL. A local request failure is reported to Home Assistant; it does not silently fall back to cloud control. Devices without a URL use the cloud proxy.
- Home Assistant's built-in Snapcast integration remains useful for multiroom player/group control, but is independent of this fleet integration.

## Development validation

The integration requires Home Assistant at runtime. From the repository root, Python syntax and JSON metadata can be checked with:

```sh
python3 -m compileall -q custom_components/balena_cloud
python3 -c 'import json, pathlib; [json.loads(p.read_text()) for p in pathlib.Path("custom_components/balena_cloud").glob("*.json")]'
```
