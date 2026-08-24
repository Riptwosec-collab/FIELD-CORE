# FIELD CORE Advanced Pro Integration

This branch extends Fusion 2.0 non-destructively. The original 28 feature IDs (0..27), command names, storage keys, API gates and existing navigation remain intact.

## Advanced intelligence

- Field Context Engine 2.0 with multi-source supporting evidence
- Telemetry Confidence / freshness
- Lost Mode Pro
- Emergency Escalation levels and impact review integration
- Mission Pack Offline with checklist/contact/QR/text/trusted-network metadata
- Smart Geo Anchor integration and non-automatic parking suggestion API
- Environmental Risk Index
- Power Commander AUTO integration / power-cost declarations / recon scan coupling
- Sensor Self-Test
- Mission Timeline Pro / unified Field Event Bus
- Voice Macro Engine
- Field Notification Filter and priority-aware haptics
- Nearby Device Recon + local device history
- Running Zone HUD
- Sky Scanner Pro
- Night / Stealth HUD state and watch controls
- Return Decision HUD using route/battery inputs when available
- Field Quick Profiles with watch profile controls
- Impact Review snapshot
- Command Center
- FIELD CORE Settings for privacy, haptics, recon cadence and reduced motion state

## Outdoor Wi-Fi Scout

Phone-side only Wi-Fi discovery using Android `WifiManager`. The watch receives compact results over the existing Wear Engine bridge.

Implemented services include:

- Wi-Fi scan status and Quick Scan
- nearby list with RSSI sorting/filtering
- SSID/BSSID search API
- OPEN detection (never presented as proof of free Internet)
- WPA3/WPA2/WPA/WEP/OPEN/UNKNOWN classification
- 2.4/5/6 GHz band and channel classification
- Best Network score plus Signal/Security/Stability/Band component scores
- RSSI Signal Hunt / proximity buckets (no meter-distance claims and no physical-direction claim)
- hidden-network handling plus local user hide/show state
- user pin/unpin state
- new-network and security-change events
- trusted network local database
- duplicate SSID heuristic
- risk reasons / LOW-MEDIUM-HIGH heuristic labels without malicious claims
- channel load summary
- local history (SQLite)
- differential scan summary: ADDED / UPDATED / REMOVED counts
- Outdoor Scan foreground service with ACTIVE/BALANCED/BATTERY_SAVER cadence
- cached/throttled scan fallback
- Cyber Sweep integration with BLE discovery

## Nearby Device Recon

Phone-side BLE discovery using `BluetoothLeScanner`, local trusted/history state, RSSI proximity buckets and broad device-type hints. It does not claim physical distance or malicious intent. Device history stores last known name/type/RSSI locally.

## Privacy / real-data policy

- Wi-Fi and Bluetooth history are local by default.
- Location attachment/history remain OFF unless explicitly enabled.
- Cloud sync remains OFF.
- No random/fake telemetry is used in production paths.
- Missing providers/sensors return `UNAVAILABLE`, `NO DATA`, `PERMISSION REQUIRED`, `CACHED`, or `API GATED` as appropriate.
- Depth and ambient-light access remain API GATED.

## Watch integration

Original Masterpiece HUD remains the presentation system. New extension views are:

- FIELD CORE PRO / Advanced Hub
- Command Center
- Wi-Fi Scout radar/menu
- Wi-Fi Signal Hunt and Duplicate SSID actions
- Nearby Device scan/history actions
- Stealth enable/disable controls
- Daily/Outdoor/Running/Night profile controls
- Mission Start/Stop and Lost Mode Start/Stop controls
- Notification mode controls
- Emergency Escalation L0-L3 controls
- generic advanced result view for Context, Telemetry Confidence, Mission, Lost Mode, Environment Risk, Diagnostics, Timeline Pro, Voice Macros, Notifications, Running Zone, Sky Pro, Stealth, Return Decision, Profiles, Impact Review, Settings and Emergency Escalation

The Home dock adds `CMD` and `REC` entries without removing the original Home/BIO/RUN/NAV/ENV/TACT/SYS entries. Home also exposes current Wi-Fi count when real scan data exists.

## Release blockers still intentionally explicit

- official Lite Wearable `wearengine.js` must replace the repository stub
- Huawei App ID and signing fingerprints must be configured
- Huawei Health Service Kit scopes/approval are required for advanced health metrics
- Android Studio / DevEco Studio build and signing
- physical HUAWEI WATCH FIT 4 Pro permission, sensor, reconnect, power and P2P validation
