# FIELD CORE — FUSION 2.0

FIELD CORE สำหรับ HUAWEI WATCH FIT 4 Pro + Android Companion โดยยึดหลัก **LOCAL FIRST • REAL DATA ONLY • FAIL CLOSED**

## Project entrypoint

```text
Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1/
├── watch-lite/          # Lite Wearable watch app / Field Fusion runtime
├── android-companion/   # Android + Wear Engine + phone providers
├── tools/               # identity / SDK install / preflight
├── docs/                # build, install, module map, Fusion matrix
├── README_TH.md
└── SOURCE_MANIFEST.json
```

> Repository มี directory wrapper ซ้อน 2 ชั้นจาก source เดิม ให้เปิด IDE จาก path ด้านบน

## Fusion 2.0 — 28 modules เดิมยังอยู่ครบ

อัปเกรดรอบนี้ไม่ได้เพิ่มเมนูเพื่อเพิ่มจำนวน แต่ทำให้โมดูลเดิมทำงานร่วมกันเป็น Field OS:

1. **Field Fusion Engine** — รวม HR / GPS / motion / altitude / pressure / navigation state
2. **Geo Anchor Pro** — named anchors สูงสุด 20 จุด + distance/bearing return
3. **Breadcrumb 2.0** — adaptive sampling, resume, return loop, off-route warning, ETA/elevation statistics
4. **Emergency Core Pro** — Impact Assist + stillness check + cancellable SOS countdown + location packet
5. **Health Provider Engine** — local field sessions/hydration/golf + strict Huawei Health authorization gate
6. **Atmospheric Intelligence** — live weather/UV/sun/sky + barometer pressure trend + offline cache
7. **Power Commander 2.0** — AUTO + PERFORMANCE/BALANCED/ENDURANCE/GRID
8. **Device Capability Scanner** — local sensor / phone / provider / API-gated matrix
9. **Offline Field Cache** — last location, weather, route, anchors, power and field state
10. **Voice Command 2.0** — Thai/English intents, named CAR/CAMP/HOTEL/HOME anchors and power commands
11. **Mission Timeline** — local event timeline capped at 80 important events
12. **Field HUD UI 2.0** — Fusion HUD optimized for wrist use

## Provider status

### Implemented now
- Watch-local: HR, compass, barometer, accelerometer/gyroscope workflows, anchors, breadcrumb, power, cache, timeline, tactical light
- Phone-assisted: fresh location, live Weather / UV / sunrise-sunset / sky timing, voice recognition
- User-driven local state: field sessions, hydration log, manual golf scorecard

### Gated by external approval / SDK / provider
- Huawei Health live sleep/health metrics: requires Health Service Kit integration + approved/user-granted scopes
- Transit / route-backed Silent Nav: provider not configured
- Acoustic exposure: provider/API not configured
- Raw Depth and Ambient Light: remain **API GATED** until approved third-party access is verified

## Start here

```bash
cd Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1
python3 tools/preflight.py
```

Release gate:

```bash
python3 tools/preflight.py --release
```

CI also runs development preflight on pushes and pull requests via `.github/workflows/field-core-preflight.yml`.

## Current release blockers

A real signed Watch + Android release still requires:

1. Huawei official Lite Wearable `wearengine.js` replacing the offline stub
2. Huawei App ID
3. Android signing SHA-256 fingerprint
4. Watch signing SHA-256 fingerprint
5. DevEco Studio / Android Studio signing configuration
6. Real-device validation on HUAWEI WATCH FIT 4 Pro
7. Huawei Health Service Kit approval/scopes if live Sleep Readiness/advanced health data is required

Emergency Core currently creates a real location packet for the paired phone but **does not automatically contact emergency services or a person** until a user-configured delivery channel is added.

## Documents

- `README_TH.md`
- `docs/BUILD_INSTALL_TH.md`
- `docs/MODULE_MAP.md`
- `docs/FUSION_2_FEATURE_MATRIX.md`

## Principle

If an API, permission, provider, sensor or credential is unavailable, FIELD CORE must report the limitation instead of generating fake live data.
