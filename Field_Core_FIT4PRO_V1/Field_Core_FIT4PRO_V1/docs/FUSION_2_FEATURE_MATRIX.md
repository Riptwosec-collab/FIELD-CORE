# FIELD CORE FUSION 2.0 — Feature Matrix

สถานะในเอกสารนี้แยก **implemented**, **provider-backed**, และ **API/approval gated** เพื่อไม่ให้ UI หรือเอกสารอ้างว่ามี live data ทั้งที่ source ยังไม่ได้รับสิทธิ์

| Upgrade | Watch | Phone | Offline | Status |
|---|---|---|---|---|
| Field Fusion Engine | HR/GPS/Compass/Barometer/Motion state | provider snapshot | yes | IMPLEMENTED |
| Geo Anchor Pro | named anchors, return bearing/distance, max 20 | voice slots | yes | IMPLEMENTED |
| Breadcrumb 2.0 | adaptive points, resume, return, off-route haptic | optional route provider | yes | IMPLEMENTED LOCAL |
| Emergency Core Pro | impact/stillness assist, countdown, light, return | fresh location packet | partial | IMPLEMENTED; DELIVERY CHANNEL NOT CONFIGURED |
| Health Provider Engine | local HR/session context | local session/hydration/golf + Health scope gate | yes for local state | LIVE HUAWEI HEALTH METRICS GATED |
| Atmospheric Intelligence | barometer trend | live weather/UV/sun/sky | weather cache | IMPLEMENTED |
| Power Commander 2.0 | AUTO/manual sampling policy | n/a | yes | IMPLEMENTED |
| Device Capability Scanner | local capability state | provider/API status | yes | IMPLEMENTED |
| Offline Field Cache | route/anchors/location/power/state | cached weather source | yes | IMPLEMENTED |
| Voice Command 2.0 | executes whitelist | Thai/English recognizer + slots | no | IMPLEMENTED PHONE-ASSISTED |
| Mission Timeline | 80-event local log | n/a | yes | IMPLEMENTED |
| Field HUD UI 2.0 | Fusion HUD + dedicated pages | n/a | yes | IMPLEMENTED |

## 28-module preservation

Fusion 2.0 keeps feature IDs `0..27` and upgrades behavior behind the existing catalog. Depth HUD and Light Guardian remain `API GATED` instead of presenting hardware presence as third-party API availability.

## Live provider behavior

### Weather

`WeatherProvider.java` requests current weather and daily UV/sun/sky timing using the phone's freshest available location. Network/provider failure returns an error; the watch may display its previously stored cache and labels it as cached.

### Health

`HealthProvider.java` deliberately separates:

- user-driven local state that can exist now: field session, hydration entries, manual golf score
- Huawei Health metrics that require SDK integration, platform approval where applicable, and user authorization

Sleep Readiness therefore does **not** fabricate a readiness score while those health scopes are absent.

### Emergency

Emergency Core can build a location packet after the countdown or a manual send. A packet is not the same as contacting emergency services. Delivery to SMS/contact/backend is intentionally not claimed until a user-configured channel is implemented.

## Release blockers

- official Huawei Lite Wearable `wearengine.js`
- Huawei App ID
- Android/watch signing fingerprints
- signed builds from Android Studio + DevEco Studio
- physical HUAWEI WATCH FIT 4 Pro verification
- Huawei Health Service Kit approval/scopes for live health metrics
- route/transit/acoustic providers where those modules are required

Run:

```bash
python tools/preflight.py
python tools/preflight.py --release
```
