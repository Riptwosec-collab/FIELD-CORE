# FIELD CORE — HUAWEI WATCH FIT 4 Pro

Standalone project ที่แยกจาก PC Remote Deck โดยเน้น:

- Bio / Wellness
- Sports
- Navigation
- Outdoor / Environment
- Tactical / Emergency
- Power / Motion / Voice

## Package

- Android Companion: `com.riptwosec.fieldcore`
- Watch Lite Wearable: `com.riptwosec.fieldcore.watch`

## Architecture

```text
HUAWEI WATCH FIT 4 PRO
        │
        │ Wear Engine P2P
        ▼
ANDROID FIELD CORE COMPANION
        │
        ├─ Weather / UV provider
        ├─ Transit provider
        ├─ Voice recognition
        ├─ Route provider
        └─ Health/Workout provider adapters
```

Watch-native/local-first:
- Heart rate subscription
- Accelerometer / Gyroscope
- Compass
- Barometer
- Haptic
- Battery
- Geo Anchor
- Breadcrumb route
- Tactical light
- Grid-down local state

Phone-assisted/provider-backed:
- Weather / UV
- Transit
- Silent navigation
- Voice recognition
- Sleep / workout / golf providers
- Emergency location sharing

API-gated/unavailable by default:
- Raw depth sensor access
- Ambient light raw access if Lite Wearable API does not expose it
- Any health metric that provider/API has not granted

> UI must never present DEMO/estimated/provider-missing data as live sensor data.

## Build

1. เปิด `watch-lite/` ใน DevEco Studio
2. เปิด `android-companion/` ใน Android Studio
3. ใส่ Huawei App ID + signing fingerprints ด้วย `tools/configure_identity.py`
4. ใส่ Huawei official Lite Wearable `wearengine.js`
5. Build/Sign Android Companion
6. Build/Sign Watch app

ดู `docs/BUILD_INSTALL_TH.md`
