#!/usr/bin/env python3
import pathlib,json,re,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
errors=[];warnings=[]
required=['watch-lite/entry/src/main/config.json','watch-lite/entry/src/main/js/MainAbility/pages/index/index.js','watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml','android-companion/app/src/main/AndroidManifest.xml']
for f in required:
    if not (R/f).exists(): errors.append('missing '+f)
try:
    cfg=json.loads((R/'watch-lite/entry/src/main/config.json').read_text());
    if cfg['app']['bundleName']!='com.riptwosec.fieldcore.watch': errors.append('watch bundle mismatch')
except Exception as e: errors.append('config json '+str(e))
for path in R.rglob('*'):
    if path.is_file() and path.suffix in {'.js','.json','.xml','.gradle'}:
        try:t=path.read_text(errors='ignore')
        except:continue
        if 'REPLACE_WITH_' in t: warnings.append('placeholder '+str(path.relative_to(R)))
js=R/'watch-lite/entry/src/main/js/MainAbility/pages/index/index.js'
if shutil:=__import__('shutil'):
    if shutil.which('node'):
        p=subprocess.run(['node','--check',str(js)],capture_output=True,text=True)
        if p.returncode: errors.append('watch JS syntax: '+p.stderr.strip())
print('FIELD CORE PREFLIGHT')
print('Errors:',len(errors));[print(' ERROR',x) for x in errors]
print('Warnings:',len(warnings));[print(' WARN ',x) for x in warnings]
print('Result:','PASS' if not errors else 'FAIL')
sys.exit(1 if errors else 0)
