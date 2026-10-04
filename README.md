# balenaSound LAN Monitor for Home Assistant

A Home Assistant integration that discovers balenaSound devices on the local network using mDNS. It talks directly to each device's local Supervisor API; it does not need balenaCloud credentials or internet access.

For each device, it provides connectivity and playback sensors, a status sensor, and local reboot/restart buttons. It does **not** identify audio sources or tracks, change volume or mode, deploy releases, or monitor service-level health.

## Install with HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu in the upper-right and choose **Custom repositories**.
3. Add `https://github.com/dinpin/ha-balenasound-fleet` as an **Integration**.
4. Install **balenaSound LAN Monitor** and restart Home Assistant.
5. Open **Settings → Devices & services**. Devices advertising balenaSound over mDNS are discovered automatically.

Alternatively, copy `custom_components/balena_cloud` into `<config>/custom_components/` and restart Home Assistant.

If mDNS does not cross your network/VLAN boundary, manually add the integration and enter the balena device UUID and its local Supervisor URL (usually port `80`), for example `http://192.168.1.42:80`. The address must be reachable from Home Assistant. The balenaSound release must advertise `_balenasound._tcp.local.` and expose `/ping`, `/audio/playback`, `/device/reboot`, and `/device/restart`.

## Entities

Each discovered device has:

- `binary_sensor.*_online`
- `binary_sensor.*_playing_audio` (on when at least one PulseAudio sink is active)
- `sensor.*_status`
- `button.*_reboot_device`
- `button.*_restart_application`

Reboot and restart act immediately and may make a device temporarily unavailable. Playback remains unknown until the Supervisor observes a `play` or `stop` event. The playback sensor reflects active sinks, not track/source metadata.

## Upgrade note

This release changes the integration from one cloud fleet entry to one local entry per device. Remove the old balenaCloud fleet config entry, install/update the integration, then allow mDNS discovery or add each device manually. Existing cloud fleet entities/status and cloud-proxy actions are no longer available.

## Development validation

From the repository root:

```sh
python3 -m compileall -q custom_components/balena_cloud
python3 -c 'import json, pathlib; [json.loads(p.read_text()) for p in pathlib.Path("custom_components/balena_cloud").glob("*.json")]'
python3 -m unittest discover -s tests
```
