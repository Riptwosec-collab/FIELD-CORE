#!/usr/bin/env python3
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WATCH_BUNDLE = "com.riptwosec.fieldcore.watch"
PHONE_PACKAGE = "com.riptwosec.fieldcore"

parser = argparse.ArgumentParser(description="FIELD CORE repository preflight")
parser.add_argument(
    "--release",
    action="store_true",
    help="Treat signing/app identity placeholders and the offline Wear Engine stub as errors.",
)
args = parser.parse_args()

errors = []
warnings = []

required = [
    "watch-lite/entry/src/main/config.json",
    "watch-lite/entry/src/main/js/MainAbility/pages/index/index.js",
    "watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml",
    "watch-lite/entry/src/main/js/MainAbility/common/constants.js",
    "watch-lite/entry/src/main/js/MainAbility/common/featureCatalog.js",
    "watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js",
    "android-companion/app/build.gradle",
    "android-companion/app/src/main/AndroidManifest.xml",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/MainActivity.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldCommandRouter.java",
    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WearBridge.java",
]

for rel in required:
    if not (ROOT / rel).exists():
        errors.append("missing " + rel)

def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")

def add_placeholder(message):
    (errors if args.release else warnings).append(message)

# Identity and package consistency.
try:
    cfg = json.loads(read("watch-lite/entry/src/main/config.json"))
    if cfg["app"]["bundleName"] != WATCH_BUNDLE:
        errors.append("watch bundleName mismatch")
    if cfg["module"]["package"] != WATCH_BUNDLE:
        errors.append("watch module package mismatch")
    support = cfg["module"]["metaData"]["customizeData"][0]["value"]
    if not support.startswith(PHONE_PACKAGE + ":"):
        errors.append("watch supportLists peer package mismatch")
except Exception as exc:
    errors.append("watch config json: " + str(exc))

try:
    gradle = read("android-companion/app/build.gradle")
    app_id = re.search(r"applicationId\s+['\"]([^'\"]+)['\"]", gradle)
    if not app_id or app_id.group(1) != PHONE_PACKAGE:
        errors.append("android applicationId mismatch")
    watch_pkg = re.search(
        r"buildConfigField\s+['\"]String['\"]\s*,\s*['\"]WATCH_PACKAGE['\"]\s*,\s*['\"]\\\"([^\\\"]+)\\\"['\"]",
        gradle,
    )
    if not watch_pkg or watch_pkg.group(1) != WATCH_BUNDLE:
        errors.append("android WATCH_PACKAGE mismatch")
except Exception as exc:
    errors.append("android gradle check: " + str(exc))

try:
    constants = read("watch-lite/entry/src/main/js/MainAbility/common/constants.js")
    if "PHONE_PACKAGE='" + PHONE_PACKAGE + "'" not in constants and 'PHONE_PACKAGE="' + PHONE_PACKAGE + '"' not in constants:
        errors.append("watch PHONE_PACKAGE mismatch")
except Exception as exc:
    errors.append("watch constants check: " + str(exc))

# Only runtime/config identity files are checked for release placeholders.
identity_files = [
    "watch-lite/entry/src/main/config.json",
    "watch-lite/entry/src/main/js/MainAbility/common/constants.js",
    "android-companion/app/build.gradle",
    "android-companion/app/src/main/AndroidManifest.xml",
]
for rel in identity_files:
    try:
        if "REPLACE_WITH_" in read(rel):
            add_placeholder("placeholder " + rel)
    except Exception:
        pass

# Official Lite Wearable Wear Engine JS is mandatory for a release build.
try:
    wear_js = read("watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js")
    if "OFFLINE STUB ONLY" in wear_js:
        add_placeholder("official Lite Wearable wearengine.js not installed")
except Exception:
    pass

# Feature catalog must stay 0..27 and the watch UI must expose gated hardware honestly.
try:
    catalog = read("watch-lite/entry/src/main/js/MainAbility/common/featureCatalog.js")
    ids = sorted({int(v) for v in re.findall(r"\bid\s*:\s*(\d+)\b", catalog)})
    if ids != list(range(28)):
        errors.append("feature catalog ids must be exactly 0..27")
    if 'title:"DEPTH HUD"' not in catalog or 'source:"API GATED"' not in catalog:
        errors.append("DEPTH HUD must remain API GATED")
except Exception as exc:
    errors.append("feature catalog check: " + str(exc))

try:
    hml = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml")
    if hml.count("API GATED") < 2:
        errors.append("watch UI must label depth/light capabilities API GATED")
    if "V1.1" not in hml:
        warnings.append("watch UI does not show V1.1")
except Exception as exc:
    errors.append("watch HML check: " + str(exc))

# Transport guards: Huawei Wear Engine P2P messages are kept <= 1 KB.
try:
    watch_runtime = read("watch-lite/entry/src/main/js/MainAbility/pages/index/index.js")
    phone_bridge = read("android-companion/app/src/main/java/com/riptwosec/fieldcore/WearBridge.java")
    if "MAX_P2P_BYTES = 1024" not in watch_runtime:
        errors.append("watch P2P 1KB guard missing")
    if "MAX_P2P_BYTES = 1024" not in phone_bridge:
        errors.append("phone P2P 1KB guard missing")
except Exception as exc:
    errors.append("P2P guard check: " + str(exc))

# JavaScript syntax check when Node is available.
watch_index = ROOT / "watch-lite/entry/src/main/js/MainAbility/pages/index/index.js"
if watch_index.exists():
    if shutil.which("node"):
        proc = subprocess.run(
            ["node", "--check", str(watch_index)],
            capture_output=True,
            text=True,
        )
        if proc.returncode:
            errors.append("watch JS syntax: " + proc.stderr.strip())
    else:
        warnings.append("node not installed; skipped watch JS syntax check")

errors = sorted(set(errors))
warnings = sorted(set(warnings))

print("FIELD CORE PREFLIGHT")
print("Mode:", "RELEASE" if args.release else "DEVELOPMENT")
print("Errors:", len(errors))
for item in errors:
    print(" ERROR", item)
print("Warnings:", len(warnings))
for item in warnings:
    print(" WARN ", item)
print("Result:", "PASS" if not errors else "FAIL")
sys.exit(1 if errors else 0)
