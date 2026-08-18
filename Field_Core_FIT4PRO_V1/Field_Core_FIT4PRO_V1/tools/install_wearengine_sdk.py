#!/usr/bin/env python3
import pathlib,shutil,sys
if len(sys.argv)!=2: raise SystemExit('Usage: python tools/install_wearengine_sdk.py /path/to/wearengine.js')
root=pathlib.Path(__file__).resolve().parents[1]
src=pathlib.Path(sys.argv[1]);dst=root/'watch-lite/entry/src/main/js/MainAbility/wearengine/wearengine.js'
if not src.exists(): raise SystemExit('wearengine.js not found')
shutil.copy2(src,dst);print('Installed Huawei official wearengine.js ->',dst)
