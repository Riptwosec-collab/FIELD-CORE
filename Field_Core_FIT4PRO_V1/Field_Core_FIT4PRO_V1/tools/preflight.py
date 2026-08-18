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
    for token in ["FUSION OS", "GEO ANCHORS", "MISSION TIMELINE", "DEVICE ACCESS", "emergencyConfirm"]:
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
