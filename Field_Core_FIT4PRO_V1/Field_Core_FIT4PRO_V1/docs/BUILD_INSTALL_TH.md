# Build / Install Field Core — FIT 4 Pro

## 1. เตรียม
- HUAWEI WATCH FIT 4 Pro จับคู่กับ HUAWEI Health
- Huawei Developer account / Wear Engine access
- DevEco Studio
- Android Studio + Android SDK
- Signing certificate ทั้ง Phone และ Watch

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
ดาวน์โหลด Huawei Lite Wearable Wear Engine SDK แล้วแทน stub:

```powershell
python tools/install_wearengine_sdk.py C:\path\wearengine.js
```

## 4. Android Companion
เปิด `android-companion/` ใน Android Studio → Sync Gradle → Sign → Install บน Android phone ที่จับคู่กับ Watch

กดในแอป:
1. AUTHORIZE WEAR ENGINE
2. FIND / REGISTER WATCH
3. GRANT LOCATION
4. SEND FIELD STATUS

## 5. Watch
เปิด `watch-lite/` ใน DevEco Studio → ตั้ง signing → เลือก FIT 4 Pro real device target → Run/Install

## 6. ทดสอบ local-first ก่อน
- BIO TELEMETRY → START HR
- TACTICAL NAV → COMPASS
- ATMOSPHERIC → PRESSURE
- GEO ANCHOR → SAVE / RETURN
- BREADCRUMB → START / RETURN
- TACTICAL LIGHT → RED

## 7. Provider-backed
Weather / UV / Transit / Sleep / Running Advanced Metrics / Golf / Sky ยังถูกแยกผ่าน `ProviderRegistry.java`
ต้องต่อ provider จริงก่อนจึงจะแสดง live data; ค่า default จะตอบ `PROVIDER NOT CONFIGURED` แทนการปลอมข้อมูล
