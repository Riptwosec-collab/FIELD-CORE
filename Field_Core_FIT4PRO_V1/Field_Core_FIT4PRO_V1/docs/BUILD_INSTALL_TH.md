# Build / Install FIELD CORE Fusion 2.0 — HUAWEI WATCH FIT 4 Pro

## 1. เตรียม

- HUAWEI WATCH FIT 4 Pro จับคู่กับ HUAWEI Health
- Huawei Developer account / Wear Engine access
- DevEco Studio
- Android Studio + Android SDK
- JDK 17
- Signing certificate ทั้ง Phone และ Watch
- Huawei official Lite Wearable `wearengine.js`
- Internet บนโทรศัพท์สำหรับ live Weather/UV/Sun/Sky

หากต้องการ Sleep Readiness หรือ health metrics จาก HUAWEI Health จริง ต้องเตรียม Health Service Kit SDK + scopes ที่ได้รับอนุมัติ + user authorization เพิ่มเติม

## 2. Identity

```powershell
python tools/configure_identity.py ^
  --huawei-app-id YOUR_APP_ID ^
  --android-fingerprint "AA:BB:..." ^
  --watch-fingerprint "11:22:..."
```

Packages:

- Phone: `com.riptwosec.fieldcore`
- Watch: `com.riptwosec.fieldcore.watch`

## 3. Wear Engine SDK

แทน offline stub ด้วย official Lite Wearable SDK file:

```powershell
python tools/install_wearengine_sdk.py C:\path\wearengine.js
```

> Offline stub ใน repository ใช้สำหรับ source development เท่านั้น ไม่สร้าง P2P link จริง

## 4. Preflight

Development:

```powershell
python tools/preflight.py
```

Release gate:

```powershell
python tools/preflight.py --release
```

Fusion 2.0 preflight ตรวจ:

- Phone/Watch package identity + version
- Feature catalog IDs `0..27`
- Field Fusion runtime
- Geo Anchor / Breadcrumb / Timeline / Cache / Impact Assist hooks
- Field HUD dedicated views
- live Weather adapter
- Health `REAL_DATA_ONLY` + scope gate
- Depth/Ambient Light `API GATED`
- P2P <= 1 KB guards ทั้งสองฝั่ง
- App ID / fingerprint placeholders
- offline Wear Engine stub
- Watch JS syntax เมื่อมี Node.js

GitHub Actions จะเรียก development preflight อัตโนมัติบน push/PR

## 5. Android Companion

เปิด `android-companion/` ใน Android Studio → Sync Gradle → Sign → Install บนโทรศัพท์ Android ที่จับคู่กับ Watch

กดตามลำดับ:

1. `AUTHORIZE WEAR ENGINE`
2. `FIND / REGISTER WATCH`
3. `GRANT LOCATION`
4. `SEND FIELD STATUS`
5. `TEST PHONE LOCATION`
6. `TEST LIVE WEATHER`
7. `PROVIDER STATUS`

Location จะพยายามขอ fresh fix ก่อน และ fallback เป็น last-known พร้อม `ageMs/stale` เมื่อจำเป็น

## 6. Watch

เปิด `watch-lite/` ใน DevEco Studio → ตั้ง signing → เลือก FIT 4 Pro real device target → Run/Install

Fusion HUD ควรแสดงอย่างน้อย:

- Field state / reason
- PHONE link
- GPS state
- Battery
- HR เมื่อ subscription สำเร็จ
- Altitude เมื่อ location API ให้ค่า
- Weather/UV เมื่อ phone provider พร้อม
- Pressure เมื่อ Barometer ทำงาน
- Heading เมื่อ Compass ทำงาน
- Power profile
- Route/cache status

## 7. Local-first test matrix

### Field Fusion
- เปิด HR + Compass + Barometer
- ตรวจว่าค่าใน Fusion HUD เปลี่ยนตาม source จริง
- ปิด sensor ทีละตัวและตรวจว่า state ไม่ค้าง ACTIVE

### Geo Anchor Pro
- Save anchor หลายจุด
- ทดสอบ named anchors: `CAR`, `CAMP`, `HOTEL`, `HOME` ผ่าน Voice
- ตรวจ distance / bearing return
- ปิด/เปิด app แล้ว anchor ต้อง restore

### Breadcrumb 2.0
- START → เดินจริง → ตรวจ point count
- เปลี่ยน Power profile ระหว่าง route และตรวจ sampling policy
- ปิด/เปิด app แล้ว START ต้อง resume route
- RETURN ต้องอัปเดต distance/bearing/ETA
- เดินออกจาก route มากพอและตรวจ off-route haptic
- NEW ROUTE ต้องเริ่ม route ใหม่โดยไม่แตะ Geo Anchors

### Power Commander 2.0
- AUTO: ตรวจการเปลี่ยน BALANCED → ENDURANCE → GRID ตาม battery thresholds
- Manual: PERFORMANCE / BALANCED / ENDURANCE / GRID
- ปิด/เปิด app และตรวจ persistence

### Offline Field Cache
- Sync Weather แล้วตัด phone link
- ตรวจว่า cached data ถูกแสดงด้วย label `CACHED`
- ตรวจ route/anchor/power state หลัง restart

### Mission Timeline
- ทำ Anchor / Route / Power / Sensor / SOS action
- ตรวจ timeline และ paging
- ตรวจ cap ไม่เกิน 80 events

## 8. Emergency Core Pro

Impact Assist เป็น **opt-in assistance heuristic** ไม่ใช่ certified fall-detection หรือ medical system

ทดสอบ:

1. เปิด `IMPACT ON`
2. ตรวจว่า Motion monitoring ถูก arm
3. ทดสอบ workflow ด้วย simulator/dev instrumentation ก่อน ไม่ควรสร้างการกระแทกอุปกรณ์จริงเพื่อทดสอบ
4. เมื่อเกิด candidate state ต้องขึ้น countdown
5. `I'M OK / CANCEL` ต้องยกเลิกได้
6. `SEND NOW` หรือ countdown หมด → ขอ fresh phone location packet
7. ตรวจ packet มี timestamp/location/accuracy เมื่อ source มีข้อมูล

> Repository ปัจจุบัน **ยังไม่ส่ง SMS/โทร/ติดต่อ emergency service อัตโนมัติ** จนกว่าจะเพิ่ม delivery channel ที่ผู้ใช้ตั้งค่าเอง

## 9. Phone-assisted providers

### Implemented
- fresh phone location
- live Weather
- UV
- sunrise/sunset
- moonrise/moonset/moon phase
- thermal load derived from live weather fields
- Voice Command TH/EN
- local field sessions / hydration / manual golf score

### Still gated
- HUAWEI Health live Sleep Readiness / advanced health metrics: Health Service Kit + scopes + authorization required
- Transit / route-backed Silent Nav: provider not configured
- Acoustic exposure: provider/API not configured
- Raw Depth / Ambient Light: `API GATED`

Provider failure must return an explicit error; cached data must remain labeled cached.

## 10. Voice Command 2.0 test

ตัวอย่าง:

- `บันทึกตำแหน่งรถ` → save `CAR`
- `กลับไปที่รถ` → return `CAR`
- `เปิดเข็มทิศ`
- `เช็กอากาศ`
- `โหมดประหยัด`
- `โหมด performance`
- `ประวัติภาคสนาม`
- `สถานะอุปกรณ์`

คำสั่งนอก whitelist ต้องตอบ unknown และไม่ execute

## 11. Release checklist

ก่อนส่งไฟล์ติดตั้งจริง:

1. `python tools/preflight.py --release` ต้อง PASS
2. official Watch Wear Engine SDK ถูกใส่จริง
3. App ID/fingerprints ถูกต้อง
4. Android Companion build/sign สำเร็จ
5. Watch build/sign สำเร็จ
6. P2P รับ/ส่งได้สองทางบน FIT 4 Pro จริง
7. sensor permission denial/retry ผ่าน
8. Bluetooth disconnect/reconnect ผ่าน
9. Weather live → cached fallback ผ่าน
10. Geo Anchor/Breadcrumb persistence ผ่าน
11. Emergency cancel path ผ่าน
12. ไม่มี demo/provider-missing data ถูกแสดงเป็น live data

ดู status matrix ที่ `docs/FUSION_2_FEATURE_MATRIX.md`
