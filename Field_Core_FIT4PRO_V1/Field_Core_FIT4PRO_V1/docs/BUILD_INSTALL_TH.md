# Build / Install Field Core — FIT 4 Pro

## 1. เตรียม

- HUAWEI WATCH FIT 4 Pro จับคู่กับ HUAWEI Health
- Huawei Developer account / Wear Engine access
- DevEco Studio
- Android Studio + Android SDK
- Signing certificate ทั้ง Phone และ Watch
- Huawei official Lite Wearable `wearengine.js`

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

ดาวน์โหลด Huawei Lite Wearable Wear Engine SDK แล้วแทน offline stub:

```powershell
python tools/install_wearengine_sdk.py C:\path\wearengine.js
```

> อย่า release แอปโดยใช้ `wearengine.js` stub ที่อยู่ใน repository เพราะ stub ถูกสร้างไว้เพื่อให้ source tree เปิดอ่านได้แบบ offline เท่านั้น และจะไม่สร้าง P2P link จริง

## 4. Preflight

ตรวจ source ก่อนเปิด IDE:

```powershell
python tools/preflight.py
```

ก่อนทำ build สำหรับติดตั้งจริง ให้ใช้ release gate:

```powershell
python tools/preflight.py --release
```

Release gate จะตรวจอย่างน้อย:

- Phone/Watch package identity ตรงกัน
- Feature catalog ครบ 28 modules
- UI แสดง Depth/Light เป็น `API GATED`
- Watch/Phone มี P2P message guard 1 KB
- ไม่มี App ID / signing fingerprint placeholder
- ไม่ได้ใช้ offline Wear Engine stub
- Syntax ของ watch JavaScript เมื่อเครื่องมี Node.js

## 5. Android Companion

เปิด `android-companion/` ใน Android Studio → Sync Gradle → Sign → Install บน Android phone ที่จับคู่กับ Watch

กดในแอปตามลำดับ:

1. `AUTHORIZE WEAR ENGINE`
2. `FIND / REGISTER WATCH`
3. `GRANT LOCATION`
4. `SEND FIELD STATUS`

ตรวจว่า log แสดง watch connected/receiver ready ก่อนทดสอบ command จากนาฬิกา

## 6. Watch

เปิด `watch-lite/` ใน DevEco Studio → ตั้ง signing → เลือก FIT 4 Pro real device target → Run/Install

หน้าหลักควรแสดง:

- PHONE: `CONNECTED` เมื่อ P2P พร้อม
- Battery จาก watch
- HR เฉพาะเมื่อ subscription สำเร็จ
- FIELD status จาก local state หรือ phone snapshot

## 7. ทดสอบ local-first ก่อน

ทดสอบทีละ module และตรวจทั้ง success/failure state:

- BIO TELEMETRY → `START HR` / `STOP HR`
- TACTICAL NAV → `COMPASS` / `STOP`
- ATMOSPHERIC → `PRESSURE` / `STOP`
- GEO ANCHOR → `SAVE` / `LAST` / `RETURN`
- BREADCRUMB → `START` / `MARK` / `RETURN` / `STOP`
- POWER COMMANDER → เปลี่ยน profile แล้วปิด/เปิดแอปเพื่อตรวจ restore
- TACTICAL LIGHT → RED / WHITE / SOS และ Stop
- MOTION COMMAND → ARM / CALIBRATE / DISARM

สิ่งที่ต้องตรวจเป็นพิเศษใน V1.1:

- เมื่อ sensor permission/API fail ต้องไม่ค้างสถานะ ACTIVE
- `BREADCRUMB MARK` ต้องไม่เขียนทับ GEO Anchor
- เปลี่ยน POWER profile ขณะ Breadcrumb ทำงานแล้ว sampling interval ต้องถูก reschedule

## 8. ทดสอบ Phone-assisted

- DEVICE ACCESS → STATUS / SYNC
- PHONE location: ทดสอบทั้ง permission granted และ denied
- VOICE COMMAND → ทดสอบ Anchor / Compass / Weather / Emergency / Breadcrumb Return
- EMERGENCY CORE → SEND LOC ต้องรายงานชัดเจนหากยังไม่ได้ตั้ง contact channel
- ปิด Bluetooth/Watch link แล้วทดสอบ reconnect + `FIND / REGISTER WATCH`

## 9. Provider-backed

Weather / UV / Transit / Sleep / Running Advanced Metrics / Golf / Sky ยังถูกแยกผ่าน `ProviderRegistry.java`
ต้องต่อ provider จริงก่อนจึงจะแสดง live data; ค่า default จะตอบ `PROVIDER NOT CONFIGURED` แทนการปลอมข้อมูล

Depth HUD และ Light Guardian ต้องคงสถานะ `API GATED` จนกว่าจะยืนยัน third-party API ที่อนุญาตสำหรับ FIT 4 Pro ได้จริง

## 10. Release checklist

ก่อนส่งไฟล์ให้ติดตั้งจริง:

1. `python tools/preflight.py --release` ต้อง PASS
2. Android Companion build/sign สำเร็จ
3. Watch app build/sign สำเร็จ
4. P2P ส่ง/รับ command ได้สองทางบนอุปกรณ์จริง
5. ทดสอบ sensor permission denial อย่างน้อย 1 รอบ
6. ทดสอบ disconnect/reconnect อย่างน้อย 1 รอบ
7. ยืนยันว่าไม่มี DEMO/provider-missing data ถูกแสดงเป็น live data
