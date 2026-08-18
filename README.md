# FIELD CORE — HUAWEI WATCH FIT 4 Pro

Repository สำหรับ FIELD CORE บน HUAWEI WATCH FIT 4 Pro + Android Companion

## Project entrypoint

Source หลักอยู่ที่:

```text
Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1/
├── watch-lite/          # Lite Wearable watch app
├── android-companion/   # Android + Huawei Wear Engine companion
├── tools/               # identity / SDK install / preflight
├── docs/                # build, install, module map
├── README_TH.md
└── SOURCE_MANIFEST.json
```

> Repository มี directory wrapper ซ้อน 2 ชั้นจากไฟล์ต้นฉบับเดิม ดังนั้นให้เปิด IDE จาก path ด้านบน ไม่ใช่จาก repository root

## V1.1 status

V1.1 เน้น reliability โดยไม่ลบ 28 modules เดิม:

- sensor failure state recovery
- Geo Anchor / Breadcrumb state separation
- breadcrumb + power-profile persistence
- watch execution of whitelisted Voice intents
- Voice/Emergency request correlation IDs
- Wear Engine P2P 1 KB payload guards
- phone location permission + stale-location visibility
- reduced Android permissions
- explicit `API GATED` state for depth / ambient-light capabilities
- stronger development/release preflight

## Start here

```bash
cd Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1
python3 tools/preflight.py
```

ก่อน build สำหรับติดตั้งจริง:

```bash
python3 tools/preflight.py --release
```

จากนั้นอ่าน:

- `README_TH.md`
- `docs/BUILD_INSTALL_TH.md`
- `docs/MODULE_MAP.md`

## Current release blockers

ก่อนทำไฟล์ติดตั้งจริง ต้องมีอย่างน้อย:

1. Huawei official Lite Wearable `wearengine.js` แทน offline stub
2. Huawei App ID
3. Android signing SHA-256 fingerprint
4. Watch signing SHA-256 fingerprint
5. DevEco/Android signing configuration
6. Real-device validation บน HUAWEI WATCH FIT 4 Pro

Provider-backed modules เช่น Weather / UV / Transit / Sleep / advanced sports ยังคงตอบ `PROVIDER NOT CONFIGURED` จนกว่าจะต่อ provider จริง เพื่อไม่ให้สร้างข้อมูลปลอม

## Principle

**LOCAL FIRST • REAL DATA ONLY • FAIL CLOSED**

ถ้า API, permission, provider หรือ sensor ใช้งานไม่ได้ FIELD CORE ต้องรายงาน `UNAVAILABLE`, `NO PERMISSION`, `API GATED` หรือ `PROVIDER NOT CONFIGURED` แทนการสร้างค่าจำลอง
