# FIELD CORE — HUAWEI WATCH FIT 4 Pro

FIELD CORE เป็นโปรเจกต์แยกจาก PC Remote Deck สำหรับใช้งานภาคสนามบน HUAWEI WATCH FIT 4 Pro โดยยึดหลัก **local-first**, **real-data-only** และไม่แสดงข้อมูลจำลองเป็นข้อมูล sensor จริง

## V1.1 Reliability Upgrade

- แก้สถานะ Heart Rate / Compass / Barometer ไม่ให้ค้าง ACTIVE เมื่อ subscription ล้มเหลว
- แยก `BREADCRUMB MARK` ออกจาก `GEO ANCHOR` เพื่อไม่ให้ตำแหน่ง Anchor ถูกเขียนทับ
- Restore breadcrumb route และ power profile หลังเปิดแอปใหม่
- Voice Command จาก Android Companion สามารถส่ง intent ที่อนุญาตกลับมาสั่งงาน watch ได้จริง
- เพิ่ม request/response correlation ID สำหรับ Voice และ Emergency
- เพิ่ม P2P payload guard สูงสุด 1 KB ทั้ง watch และ Android Companion
- เพิ่มสถานะ Location permission และความเก่าของ last-known location ฝั่งโทรศัพท์
- ลด Android permission ที่ไม่จำเป็น โดยไม่ขอ `RECORD_AUDIO` จากตัวแอป
- แสดง Depth HUD / Light Guardian เป็น `API GATED` จนกว่าจะมี third-party API ที่อนุญาตจริง
- เพิ่ม `tools/preflight.py --release` สำหรับตรวจ blocker ก่อน build/release

## Modules

FIELD CORE มี 28 modules แบ่งเป็น:

- Bio / Wellness
- Sports
- Navigation
- Outdoor / Environment
- Tactical / Emergency
- Power / Motion / Voice / Device Access

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
        └─ Health / Workout provider adapters
```

### Watch-native / local-first

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

### Phone-assisted / provider-backed

- Weather / UV
- Transit
- Silent navigation
- Voice recognition
- Sleep / workout / golf providers
- Emergency location sharing

### API-gated

- Raw depth sensor access
- Raw ambient-light access when Lite Wearable API does not expose it
- Any health metric that provider/API has not granted

> UI must never present DEMO, estimated, cached-without-label, or provider-missing data as live sensor data.

## Important: current release blockers

Repository นี้ยังไม่ควรถูกมองว่าเป็นไฟล์ติดตั้งพร้อมใช้ทันทีจนกว่าจะทำครบรายการต่อไปนี้:

1. แทนที่ `watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js` ซึ่งปัจจุบันเป็น offline stub ด้วย Huawei official Lite Wearable `wearengine.js`
2. ใส่ Huawei App ID และ signing fingerprints ของ Android/Watch
3. ตั้งค่า Weather / Health / Transit / Route provider ที่ต้องการใช้งานจริง
4. Build และ sign ทั้ง Android Companion และ Watch app ด้วย toolchain ของ Huawei/Android
5. ทดสอบบน HUAWEI WATCH FIT 4 Pro จริง โดยเฉพาะ permission, sensor subscription และ P2P reconnect

## Configure identity

```bash
python3 tools/configure_identity.py \
  --huawei-app-id YOUR_APP_ID \
  --android-fingerprint YOUR_ANDROID_SHA256 \
  --watch-fingerprint YOUR_WATCH_SHA256
```

## Preflight

Development check:

```bash
python3 tools/preflight.py
```

Release gate:

```bash
python3 tools/preflight.py --release
```

`--release` จะ fail หากยังมี App ID/fingerprint placeholder หรือยังใช้ offline Wear Engine stub

## Build

1. เปิด `watch-lite/` ใน DevEco Studio
2. เปิด `android-companion/` ใน Android Studio
3. Configure identity
4. ใส่ Huawei official Lite Wearable `wearengine.js`
5. รัน release preflight
6. Build/Sign Android Companion
7. Build/Sign Watch app
8. ทดสอบ P2P และ module สำคัญบนอุปกรณ์จริง

ดูรายละเอียดเพิ่มที่ `docs/BUILD_INSTALL_TH.md`
