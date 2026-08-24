# FIELD CORE — FUSION 2.0 for HUAWEI WATCH FIT 4 Pro

FIELD CORE เป็นโปรเจกต์แยกจาก PC Remote Deck สำหรับงานภาคสนามบน HUAWEI WATCH FIT 4 Pro โดยยึดหลัก **LOCAL FIRST • REAL DATA ONLY • FAIL CLOSED** และยังคง 28 modules เดิมไว้ครบ

## Fusion 2.0

รอบนี้เปลี่ยน FIELD CORE จากชุดฟังก์ชันแยกกันให้ทำงานร่วมกันเป็น Field OS:

- **Field Fusion Engine** — รวม HR / GPS / speed / altitude / pressure trend / motion / navigation state
- **Geo Anchor Pro** — เก็บ named anchor ได้สูงสุด 20 จุด, รองรับ CAR / CAMP / HOTEL / HOME ผ่าน Voice, return distance/bearing
- **Breadcrumb 2.0** — adaptive sampling ตาม power profile, resume route, return loop, off-route haptic, ETA และ elevation statistics
- **Emergency Core Pro** — Impact Assist แบบ opt-in, impact + stillness check, 15-second cancellable countdown, fresh phone location packet
- **Health Provider Engine** — local field sessions / hydration / manual golf score พร้อม strict Huawei Health authorization gate
- **Atmospheric Intelligence** — barometer trend + live Weather / UV / sunrise-sunset / moon timing + cache
- **Power Commander 2.0** — AUTO + PERFORMANCE / BALANCED / ENDURANCE / GRID
- **Device Capability Scanner** — แยก AVAILABLE / PERMISSION / NOT CONFIGURED / API GATED
- **Offline Field Cache** — location / weather / route / anchors / power / field state
- **Voice Command 2.0** — Thai + English whitelist, named anchors, power commands, capability/timeline commands
- **Mission Timeline** — event log สำคัญสูงสุด 80 รายการบน watch
- **Field HUD UI 2.0** — Fusion HUD สำหรับดู GPS / HR / ALT / BAT / Weather / Pressure / Heading แบบรวดเร็ว

## Packages

- Android Companion: `com.riptwosec.fieldcore`
- Watch Lite Wearable: `com.riptwosec.fieldcore.watch`
- Android version: `2.0-fieldcore-fusion`
- Watch version: `2.0.0`

## Architecture

```text
HUAWEI WATCH FIT 4 PRO
        │
        ├─ Local sensors / GPS / storage
        │      │
        │      └─ FIELD FUSION ENGINE
        │              ├─ Geo Anchors
        │              ├─ Breadcrumb / Return
        │              ├─ Pressure Trend
        │              ├─ Adaptive Power
        │              ├─ Offline Cache
        │              ├─ Timeline
        │              └─ Impact Assist
        │
        │ Wear Engine P2P (<= 1 KB/message)
        ▼
ANDROID FIELD CORE COMPANION
        ├─ Fresh Phone Location
        ├─ Live Weather / UV / Sun / Sky
        ├─ Voice Recognition TH/EN
        ├─ Field Session / Hydration / Golf local state
        ├─ Huawei Health authorization gate
        └─ Capability / Provider status
```

## Data source policy

### Watch-local / implemented

- Heart-rate subscription when the Lite Wearable API/permission is available
- Accelerometer / Gyroscope workflows
- Compass
- Barometer
- GPS location
- Named Geo Anchors
- Breadcrumb / Return
- Adaptive Power
- Mission Timeline
- Offline Field Cache
- Tactical Light
- Grid-down state

### Phone-assisted / implemented

- fresh phone location with last-known fallback + `ageMs/stale`
- live Weather
- UV
- sunrise / sunset
- moonrise / moonset / moon phase
- Thai/English voice recognition and intent slots
- local field session / hydration / manual golf state

### Provider / approval gated

- Huawei Health live sleep/readiness/advanced health metrics require Health Service Kit + approved/user-granted scopes
- Transit and route-backed Silent Nav are not configured
- Acoustic exposure provider is not configured
- Raw Depth / Ambient Light remain `API GATED` until approved third-party API access is verified

> Cached data must be labeled cached. Provider-missing or permission-missing data must never be shown as live sensor data.

## Emergency Core policy

Impact Assist is supplementary assistance only. It uses local motion heuristics to ask the user after a high-impact/stillness pattern and starts a cancellable countdown. It is **not** a medical or certified fall-detection system.

The Android Companion can prepare a fresh location packet, but the current repository does **not** automatically contact a person or emergency service. A user-configured delivery channel must be added before claiming external SOS delivery.

## Configure identity

```bash
python3 tools/configure_identity.py \
  --huawei-app-id YOUR_APP_ID \
  --android-fingerprint YOUR_ANDROID_SHA256 \
  --watch-fingerprint YOUR_WATCH_SHA256
```

## Preflight

```bash
python3 tools/preflight.py
```

Release gate:

```bash
python3 tools/preflight.py --release
```

Development preflight checks Fusion runtime/UI, 28-module preservation, live weather adapter, Health fail-closed policy, P2P guard and JS syntax. `--release` additionally fails while identity placeholders or the offline Lite Wearable Wear Engine stub remain.

GitHub Actions runs development preflight automatically on push / pull request.

## Current release blockers

1. Replace offline `wearengine.js` with Huawei official Lite Wearable SDK file
2. Configure Huawei App ID
3. Configure Android + Watch SHA-256 signing fingerprints
4. Configure signed Android Studio / DevEco Studio builds
5. Validate on a physical HUAWEI WATCH FIT 4 Pro
6. Obtain/configure Huawei Health scopes if live Sleep Readiness/advanced health metrics are required
7. Add real route/transit/acoustic providers if those provider-backed modules are required

## Build

1. เปิด `watch-lite/` ใน DevEco Studio
2. เปิด `android-companion/` ใน Android Studio
3. Configure identity
4. Install official Lite Wearable `wearengine.js`
5. Run `python tools/preflight.py --release`
6. Build/sign Android Companion
7. Build/sign Watch app
8. Real-device test P2P, permissions, sensors, GPS, cache, breadcrumb, anchors, impact-assist cancellation and provider failure states

อ่านต่อ:

- `docs/BUILD_INSTALL_TH.md`
- `docs/MODULE_MAP.md`
- `docs/FUSION_2_FEATURE_MATRIX.md`
