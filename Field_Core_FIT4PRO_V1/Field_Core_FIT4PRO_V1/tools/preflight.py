#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WATCH_BUNDLE = "com.riptwosec.fieldcore.watch"
PHONE_PACKAGE = "com.riptwosec.fieldcore"

parser = argparse.ArgumentParser(description="FIELD CORE Fusion 2.0 repository preflight")
parser.add_argument("--release", action="store_true", help="Treat release identity/SDK blockers as errors.")
args = parser.parse_args()
errors, warnings = [], []

required = [
    "watch-lite/entry/src/main/config.json",
    "watch-lite/entry/src/main/js/MainAbility/pages/index/index.js",
    "watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml",
    "watch-lite/entry/src/main/js/MainAbility/pages/index/index.css",
    "watch-lite/entry/src/main/js/MainAbility/common/constants.js",
    "watch-lite/entry/src/main/js/MainAbility/common/featureCatalog.js",
    "watch-lite/entry/src/main/js/MainAbility/common/fieldEngine.js",
    "watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js",
    "android-companion/app/build.gradle",
    "android-companion/app/src/main/AndroidManifest.xml",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/MainActivity.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldCommandRouter.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WearBridge.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/PhoneLocationProvider.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/ProviderRegistry.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WeatherProvider.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/HealthProvider.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutStore.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutManager.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/BluetoothReconManager.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldEventBus.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldUpgradeManager.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/ReconScanService.java",
]
for rel in required:
    if not (ROOT / rel).exists(): errors.append("missing " + rel)

def read(rel): return (ROOT / rel).read_text(encoding="utf-8", errors="replace")
def release_blocker(message): (errors if args.release else warnings).append(message)

def syntax_check_js(rel):
    if not shutil.which("node"):
        warnings.append("node not installed; skipped JS syntax check")
        return
    try:
        text = read(rel)
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", encoding="utf-8", delete=False) as tmp:
            tmp.write(text); name = tmp.name
        proc = subprocess.run(["node", "--check", name], capture_output=True, text=True)
        pathlib.Path(name).unlink(missing_ok=True)
        if proc.returncode: errors.append(rel + " syntax: " + proc.stderr.strip())
    except Exception as exc: errors.append(rel + " syntax check: " + str(exc))

# Packages, versions and peer identity.
try:
    cfg = json.loads(read("watch-lite/entry/src/main/config.json"))
    if cfg["app"]["bundleName"] != WATCH_BUNDLE: errors.append("watch bundleName mismatch")
    if cfg["module"]["package"] != WATCH_BUNDLE: errors.append("watch module package mismatch")
    if int(cfg["app"]["version"]["code"]) < 2000000: errors.append("watch version must be Fusion 2.0+")
    support = cfg["module"]["metaData"]["customizeData"][0]["value"]
    if not support.startswith(PHONE_PACKAGE + ":"): errors.append("watch supportLists peer package mismatch")
except Exception as exc: errors.append("watch config json: " + str(exc))

try:
    gradle = read("android-companion/app/build.gradle")
    app_id = re.search(r"applicationId\s+['\"]([^'\"]+)['\"]", gradle)
    if not app_id or app_id.group(1) != PHONE_PACKAGE: errors.append("android applicationId mismatch")
    if "versionCode 2" not in gradle or "2.0-fieldcore-fusion" not in gradle: errors.append("android Fusion 2.0 version mismatch")
    watch_pkg = re.search(r"WATCH_PACKAGE['\"]\s*,\s*['\"]\"([^\"]+)\"['\"]", gradle)
    if not watch_pkg or watch_pkg.group(1) != WATCH_BUNDLE: errors.append("android WATCH_PACKAGE mismatch")
except Exception as exc: errors.append("android gradle check: " + str(exc))

try:
    constants = read("watch-lite/entry/src/main/js/MainAbility/common/constants.js")
    if PHONE_PACKAGE not in constants: errors.append("watch PHONE_PACKAGE mismatch")
except Exception as exc: errors.append("watch constants check: " + str(exc))

identity_files = [
    "watch-lite/entry/src/main/config.json",
    "watch-lite/entry/src/main/js/MainAbility/common/constants.js",
    "android-companion/app/build.gradle",
    "android-companion/app/src/main/AndroidManifest.xml",
]
for rel in identity_files:
    try:
        if "REPLACE_WITH_" in read(rel): release_blocker("placeholder " + rel)
    except Exception: pass

try:
    wear_js = read("watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js")
    if "OFFLINE STUB ONLY" in wear_js: release_blocker("official Lite Wearable wearengine.js not installed")
except Exception: pass

# Preserve the original 28-module contract.
try:
    catalog = read("watch-lite/entry/src/main/js/MainAbility/common/featureCatalog.js")
    ids = sorted({int(v) for v in re.findall(r"\bid\s*:\s*(\d+)\b", catalog)})
    if ids != list(range(28)): errors.append("feature catalog ids must be exactly 0..27")
    for title in ["DEPTH HUD", "LIGHT GUARDIAN", "POWER COMMANDER", "VOICE COMMAND", "DEVICE ACCESS"]:
        if ('title:"' + title + '"') not in catalog: errors.append("missing module " + title)
    if catalog.count('source:"API GATED"') < 2: errors.append("depth/light modules must stay API GATED")
except Exception as exc: errors.append("feature catalog check: " + str(exc))

# Fusion 2.0 watch runtime/UI contract.
try:
    runtime = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
    engine = read("watch-lite/entry/src/main/js/MainAbility/common/fieldEngine.js")
    hml = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml")
    required_runtime = [
        "adaptiveProfile", "pressureTrend", "fusionState", "routeStats", "impactUpdate",
        "fieldcore_anchors", "fieldcore_timeline", "fieldcore_offline_cache", "fieldcore_breadcrumb_route",
        "returnBreadcrumb", "toggleImpactAssist", "openCapabilities", "openTimeline", "saveAnchor",
    ]
    for token in required_runtime:
        if token not in runtime and token not in engine: errors.append("Fusion runtime missing " + token)
    for token in ["FUSION OS", "GEO ANCHORS", "MISSION TIMELINE", "DEVICE ACCESS", "emergencyConfirm", "COMMAND CENTER", "WI-FI SCOUT", "CYBER SWEEP"]:
        if token not in hml: errors.append("Fusion UI missing " + token)
    if len(re.findall(r"MAX_P2P_BYTES\s*=\s*1024", runtime)) < 1: errors.append("watch P2P 1KB guard missing")
except Exception as exc: errors.append("Fusion watch check: " + str(exc))

# Phone provider contract: live weather, fresh location, real-data-only health gate.
try:
    location = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/PhoneLocationProvider.java")
    weather = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WeatherProvider.java")
    health = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/HealthProvider.java")
    registry = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/ProviderRegistry.java")
    if "getCurrentLocation" not in location or "CURRENT_TIMEOUT_MS" not in location: errors.append("fresh phone location path missing")
    if "api.open-meteo.com/v1/forecast" not in weather or "OPEN_METEO" not in weather: errors.append("live weather provider missing")
    if "REAL_DATA_ONLY" not in health or "HUAWEI HEALTH SCOPE REQUIRED" not in health: errors.append("health fail-closed gate missing")
    if "READY_KEYLESS" not in registry: errors.append("weather provider not registered")
    if "API GATED" not in registry: errors.append("capability API gates missing")
except Exception as exc: errors.append("phone provider check: " + str(exc))


# FIELD CORE Advanced / Outdoor Wi-Fi Scout integration contract.
try:
    manifest = read("android-companion/app/src/main/AndroidManifest.xml")
    router = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldCommandRouter.java")
    upgrades = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldUpgradeManager.java")
    wifi = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutManager.java")
    bt = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/BluetoothReconManager.java")
    runtime = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
    for token in ["ACCESS_WIFI_STATE", "CHANGE_WIFI_STATE", "BLUETOOTH_SCAN", "FOREGROUND_SERVICE"]:
        if token not in manifest: errors.append("advanced manifest missing " + token)
    if "FieldUpgradeManager" not in router: errors.append("advanced command router missing")
    for token in ["WIFI_SCAN", "CYBER_SWEEP", "FIELD_CONTEXT_STATUS", "COMMAND_CENTER", "MISSION_PACK_STATUS", "SENSOR_SELF_TEST", "RETURN_DECISION", "IMPACT_REVIEW_STATUS"]:
        if token not in upgrades: errors.append("advanced manager missing " + token)
    for token in ["SCAN_RESULTS_AVAILABLE_ACTION", "VERY NEAR", "DUPLICATE", "BATTERY_SAVER"]:
        if token not in wifi: errors.append("Wi-Fi Scout missing " + token)
    for token in ["BluetoothLeScanner", "BLUETOOTH_SCAN", "UNKNOWN"]:
        if token not in bt: errors.append("Bluetooth Recon missing " + token)
    for token in ["openCommandCenter", "openWifiScout", "advCyberSweep", "TELEMETRY_CONFIDENCE"]:
        if token not in runtime: errors.append("watch advanced runtime missing " + token)
except Exception as exc: errors.append("advanced integration check: " + str(exc))


# Advanced phase 2 functional surface.
try:
    upgrades = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldUpgradeManager.java")
    wifi = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutManager.java")
    runtime = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
    hml = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml")
    for token in ["WIFI_SEARCH", "WIFI_PIN", "WIFI_HIDE", "FIELD_SETTINGS_STATUS", "ANCHOR_SUGGESTION", "EMERGENCY_ESCALATION_EVENT", "BT_RECON_HISTORY"]:
        if token not in upgrades: errors.append("advanced phase2 manager missing " + token)
    for token in ["scoreParts", "riskReasons", "setPinned", "setUserHidden", "diff"]:
        if token not in wifi: errors.append("Wi-Fi Scout phase2 missing " + token)
    for token in ["advWifiSignal", "advSettings", "advStealthOn", "advEmergencyLevel3"]:
        if token not in runtime: errors.append("watch phase2 runtime missing " + token)
    for token in ["FIELD CORE SETTINGS", "SIGNAL HUNT", "WIFI {{wifiCount}}"]:
        if token not in hml: errors.append("watch phase2 UI missing " + token)
except Exception as exc: errors.append("advanced phase2 check: " + str(exc))


# Advanced phase 3 interaction surface.
try:
    upgrades = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldUpgradeManager.java")
    wifi = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutManager.java")
    runtime = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
    hml = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml")
    for token in ["PHONE_FIND", "captureOutdoorLocationIfEnabled", "priority"]:
        if token not in upgrades: errors.append("advanced phase3 manager missing " + token)
    for token in ["weightedLoad", "2.4 GHZ INCLUDES NEARBY-CHANNEL WEIGHTING"]:
        if token not in wifi: errors.append("Wi-Fi Scout phase3 missing " + token)
    for token in ["wifi1Detail", "wifiTrustSelected", "advMissionPrepare", "advFindPhone", "cyberSweep"]:
        if token not in runtime: errors.append("watch phase3 runtime missing " + token)
    for token in ["NETWORK DETAIL", "SIGNAL HUNT USES RSSI TREND", "NEW / UNKNOWN ≠ MALICIOUS", "PREPARE PACK"]:
        if token not in hml: errors.append("watch phase3 UI missing " + token)
except Exception as exc: errors.append("advanced phase3 check: " + str(exc))

# Both transport directions must enforce <=1 KB P2P messages.
try:
    bridge = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WearBridge.java")
    if not re.search(r"MAX_P2P_BYTES\s*=\s*1024", bridge): errors.append("phone P2P 1KB guard missing")
except Exception as exc: errors.append("phone P2P guard check: " + str(exc))

syntax_check_js("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
syntax_check_js("watch-lite/entry/src/main/js/MainAbility/common/fieldEngine.js")

# Health live metrics are intentionally not a release-blocker for local/core use, but stay explicit.
try:
    health = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/HealthProvider.java")
    if "healthSdkPresent" in health: warnings.append("Huawei Health live metrics remain scope/approval gated until SDK + authorization are configured")
except Exception: pass

errors = sorted(set(errors)); warnings = sorted(set(warnings))
print("FIELD CORE FUSION 2.0 PREFLIGHT")
print("Mode:", "RELEASE" if args.release else "DEVELOPMENT")
print("Errors:", len(errors))
for item in errors: print(" ERROR", item)
print("Warnings:", len(warnings))
for item in warnings: print(" WARN ", item)
print("Result:", "PASS" if not errors else "FAIL")
sys.exit(1 if errors else 0)
