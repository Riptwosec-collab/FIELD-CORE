#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Field_Core_FIT4PRO_V1'/'Field_Core_FIT4PRO_V1'
WATCH=BASE/'watch-lite'/'entry'/'src'/'main'/'js'/'MainAbility'/'pages'/'index'
JAVA=BASE/'android-companion'/'app'/'src'/'main'/'java'/'com'/'riptwosec'/'fieldcore'

def replace_once(path,old,new,label):
    text=path.read_text(encoding='utf-8')
    if new in text:
        print('already',label);return
    if old not in text: raise SystemExit('PATCH ANCHOR MISSING: '+label)
    path.write_text(text.replace(old,new,1),encoding='utf-8');print('patched',label)

def append_once(path,marker,block,label):
    text=path.read_text(encoding='utf-8')
    if block.strip() in text:
        print('already',label);return
    if marker not in text: raise SystemExit('APPEND MARKER MISSING: '+label)
    path.write_text(text.replace(marker,block+'\n'+marker,1),encoding='utf-8');print('appended',label)

# ------------------------------------------------------------------
# Android upgrade manager lifecycle + foreground Outdoor Scan service
# ------------------------------------------------------------------
manager=JAVA/'FieldUpgradeManager.java'
replace_once(manager,'import android.content.Context;\nimport android.content.SharedPreferences;',
'''import android.content.Context;\nimport android.content.Intent;\nimport android.content.SharedPreferences;''','manager Intent import')
replace_once(manager,
'    public void close(){events.unsubscribe(this);wifi.close();bluetooth.scan((ok,msg,data)->{});}',
'    public void close(){events.unsubscribe(this);stopOutdoorService();wifi.close();bluetooth.close();}',
'manager close')
replace_once(manager,
'''            case "OUTDOOR_SCAN_START": cb.done(true,"OUTDOOR SCAN ACTIVE",wifi.startOutdoor());return;\n            case "OUTDOOR_SCAN_STOP": cb.done(true,"SCAN SUMMARY",wifi.stopOutdoor());return;''',
'''            case "OUTDOOR_SCAN_START": wifi.setMode(p.optString("mode",wifi.getMode()));startOutdoorService(wifi.getMode());cb.done(true,"OUTDOOR SCAN ACTIVE",wifi.startOutdoor());return;\n            case "OUTDOOR_SCAN_STOP": stopOutdoorService();cb.done(true,"SCAN SUMMARY",wifi.stopOutdoor());return;''',
'outdoor foreground service wiring')
replace_once(manager,
'''    private void cyberSweep(Callback cb){''',
'''    private void startOutdoorService(String mode){\n        try{Intent i=new Intent(context,ReconScanService.class);i.setAction(ReconScanService.ACTION_START);i.putExtra(ReconScanService.EXTRA_MODE,mode);if(Build.VERSION.SDK_INT>=26)context.startForegroundService(i);else context.startService(i);}catch(Exception e){events.emit("OUTDOOR_SCAN_SERVICE","SYSTEM","P2","BACKGROUND SCAN RESTRICTED",null);}\n    }\n    private void stopOutdoorService(){try{Intent i=new Intent(context,ReconScanService.class);i.setAction(ReconScanService.ACTION_STOP);context.stopService(i);}catch(Exception ignored){}}\n\n    private void cyberSweep(Callback cb){''',
'outdoor service helpers')

wifi=JAVA/'WifiScoutManager.java'
replace_once(wifi,
'    public void close(){try{if(registered)context.unregisterReceiver(receiver);}catch(Exception ignored){}registered=false;store.close();}',
'    public void close(){main.removeCallbacksAndMessages(null);scanPending=false;pending=null;try{if(registered)context.unregisterReceiver(receiver);}catch(Exception ignored){}registered=false;store.close();}',
'wifi close')

bt=JAVA/'BluetoothReconManager.java'
replace_once(bt,
'    public boolean hasPermission(){return Build.VERSION.SDK_INT<31||context.checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED;}',
'    public boolean hasPermission(){return Build.VERSION.SDK_INT<31||(context.checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED&&context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)==PackageManager.PERMISSION_GRANTED);}',
'bluetooth permission gate')

main=JAVA/'MainActivity.java'
replace_once(main,
'''        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.NEARBY_WIFI_DEVICES)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.NEARBY_WIFI_DEVICES);\n        if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.ACCESS_FINE_LOCATION);''',
'''        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.NEARBY_WIFI_DEVICES)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.NEARBY_WIFI_DEVICES);\n        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.POST_NOTIFICATIONS);\n        if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.ACCESS_FINE_LOCATION);''',
'notification permission request')

# ------------------------------------------------------------------
# Watch runtime: presentation/navigation state + real command bridge
# ------------------------------------------------------------------
js=WATCH/'index.js'
replace_once(js,
'''    hrSubscribed:false,motionArmed:false,motionCalibrating:false,compassActive:false,barometerActive:false,breadcrumbActive:false,breadcrumbPoints:0,returning:false,sosConfirmUntil:0\n''',
'''    hrSubscribed:false,motionArmed:false,motionCalibrating:false,compassActive:false,barometerActive:false,breadcrumbActive:false,breadcrumbPoints:0,returning:false,sosConfirmUntil:0,\n    advancedTitle:'COMMAND CENTER',advancedSubtitle:'FIELD INTELLIGENCE',advancedState:'NO DATA',advancedData:'NO DATA',advancedAction:'',\n    wifiCount:'--',wifiOpen:'--',wifiSecured:'--',wifiBest:'NO DATA',wifiAge:'--',btCount:'--',btTrusted:'--',btUnknown:'--',\n    contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD'\n''','watch advanced state')

replace_once(js,
'''  handleResult(obj){var action=String(obj.action||'');this.featureState=obj.ok?'READY':'ERROR';this.message=(obj.ok?'OK: ':'ERROR: ')+(obj.message||action||'');\n    if(action==='DEVICE_STATUS'||action==='FIELD_SYNC'){''',
'''  handleResult(obj){var action=String(obj.action||'');this.featureState=obj.ok?'READY':'ERROR';this.message=(obj.ok?'OK: ':'ERROR: ')+(obj.message||action||'');\n    if(this.isAdvancedAction(action)){this.applyAdvancedResult(action,obj);return;}\n    if(action==='DEVICE_STATUS'||action==='FIELD_SYNC'){''','watch advanced result hook')

advanced_methods=r'''  isAdvancedAction(action){return action.indexOf('WIFI_')===0||action.indexOf('BT_RECON_')===0||action.indexOf('FIELD_CONTEXT')===0||action.indexOf('TELEMETRY_CONFIDENCE')===0||action.indexOf('LOST_MODE')===0||action.indexOf('MISSION_')===0||action.indexOf('ENV_RISK')===0||action.indexOf('SENSOR_SELF_TEST')===0||action.indexOf('TIMELINE_PRO')===0||action.indexOf('VOICE_MACRO')===0||action.indexOf('NOTIFICATION_FILTER')===0||action.indexOf('RUN_ZONE')===0||action.indexOf('SKY_PRO')===0||action.indexOf('STEALTH')===0||action.indexOf('RETURN_DECISION')===0||action.indexOf('QUICK_PROFILE')===0||action.indexOf('IMPACT_REVIEW')===0||action.indexOf('COMMAND_CENTER')===0||action.indexOf('CYBER_SWEEP')===0||action.indexOf('OUTDOOR_SCAN')===0||action.indexOf('EMERGENCY_ESCALATION')===0||action.indexOf('ALERT_')===0;},
  pick(o,k,fallback){return o&&typeof o[k]!=='undefined'?o[k]:fallback;},
  compactAdvanced(v){if(!v)return 'NO DATA';if(typeof v!=='object')return String(v);var keys=['status','mode','decision','profile','recommended','level','score','confidence','count','networks','open','secured','trusted','new','unknown','durationSec','ageSec','active'],out=[],i,k;for(i=0;i<keys.length;i++){k=keys[i];if(typeof v[k]!=='undefined'&&v[k]!==null)out.push(k.toUpperCase()+': '+String(v[k]));}if(out.length)return out.join(' • ');try{var s=JSON.stringify(v);return s.length>230?s.substring(0,227)+'...':s;}catch(e){return 'DATA READY';}},
  applyAdvancedResult(action,obj){var d=obj&&obj.data?obj.data:{};this.advancedState=obj&&obj.ok?'READY':'ERROR';this.advancedData=this.compactAdvanced(d);this.featureData=this.advancedData;this.message=(obj&&obj.ok?'OK: ':'ERROR: ')+(obj&&obj.message?obj.message:action);this.lastSync=timeText(Date.now());
    if(action.indexOf('WIFI_')===0||action.indexOf('OUTDOOR_SCAN')===0){this.wifiCount=this.pick(d,'count',this.pick(d,'total',this.pick(d,'networks',this.wifiCount)));this.wifiOpen=this.pick(d,'open',this.wifiOpen);this.wifiSecured=this.pick(d,'secured',this.wifiSecured);this.wifiAge=this.pick(d,'ageSec',this.wifiAge);var b=d.best&&d.best.network?d.best.network:(d.best||d.strongest||null);if(b)this.wifiBest=String(this.pick(b,'s',this.pick(b,'ssid','AVAILABLE')));}
    if(action.indexOf('BT_RECON_')===0){this.btCount=this.pick(d,'count',this.pick(d,'total',this.btCount));this.btTrusted=this.pick(d,'trusted',this.btTrusted);this.btUnknown=this.pick(d,'unknown',this.btUnknown);}
    if(action==='CYBER_SWEEP'){var w=d.wifi||{},b2=d.bluetooth||{};this.wifiCount=this.pick(w,'count',this.wifiCount);this.wifiOpen=this.pick(w,'open',this.wifiOpen);this.btCount=this.pick(b2,'count',this.btCount);this.btTrusted=this.pick(b2,'trusted',this.btTrusted);this.btUnknown=this.pick(b2,'unknown',this.btUnknown);}
    if(action==='FIELD_CONTEXT_STATUS'){this.contextMode=String(this.pick(d,'mode','UNKNOWN'));this.contextConfidence=String(this.pick(d,'confidence','--'));}
    if(action==='ENV_RISK_STATUS'){this.envRisk=String(this.pick(d,'level','--'));}
    if(action==='MISSION_STATUS'||action==='MISSION_START'||action==='MISSION_STOP'){this.missionLabel=this.pick(d,'active',false)?'ACTIVE':'INACTIVE';}
    if(action==='QUICK_PROFILE_STATUS'||action==='QUICK_PROFILE_SET'){this.quickProfile=String(this.pick(d,'profile',this.quickProfile));}
    if(action==='NOTIFICATION_FILTER_STATUS'||action==='NOTIFICATION_FILTER_SET'){this.notificationMode=String(this.pick(d,'mode',this.notificationMode));}
    if(action==='COMMAND_CENTER'){var c=d.context||{},w2=d.wifi||{},bt=d.devices||{},env=d.environment||{},ms=d.mission||{};this.contextMode=String(this.pick(c,'mode',this.contextMode));this.contextConfidence=String(this.pick(c,'confidence',this.contextConfidence));this.wifiCount=this.pick(w2,'count',this.wifiCount);this.wifiOpen=this.pick(w2,'open',this.wifiOpen);this.btCount=this.pick(bt,'count',this.btCount);this.btTrusted=this.pick(bt,'trusted',this.btTrusted);this.envRisk=String(this.pick(env,'level',this.envRisk));this.missionLabel=this.pick(ms,'active',false)?'ACTIVE':'INACTIVE';this.quickProfile=String(this.pick(d,'profile',this.quickProfile));this.notificationMode=String(this.pick(d,'notification',this.notificationMode));}
    this.logEvent('ADV',action+' '+(obj&&obj.ok?'OK':'ERROR'));
  },
  advancedPayload(extra){var p={battery:this.watchBattery,heartRate:this.heartRate,speedKmh:this.speedKmh,altitude:this.altitude,gpsState:this.gpsState,gpsAvailable:!!this.lastLocation,gpsAccuracyM:this.lastLocation&&this.lastLocation.accuracy?Number(this.lastLocation.accuracy):null,gpsAgeMs:this.lastLocation?Date.now()-Number(this.lastLocation.ts||0):null,hrAvailable:this.hrSubscribed,compassAvailable:this.compassActive,barometerAvailable:this.barometerActive,motionAvailable:this.motionArmed,emergency:this.emergencyCountdown>0||this.impactPending,returnAvailable:this.breadcrumbRoute.length>0,missionMinutes:0};var k;if(extra)for(k in extra)if(extra.hasOwnProperty(k))p[k]=extra[k];return p;},
  openAdvanced(title,subtitle,action,extra){this.advancedTitle=title;this.advancedSubtitle=subtitle||'FIELD INTELLIGENCE';this.advancedAction=action||'';this.advancedState='LOADING';this.advancedData='WAITING FOR PHONE';this.view='advanced';if(action)this.sendCommand(action,this.advancedPayload(extra));this.haptic('short');},
  openAdvancedHub(){this.view='advancedHub';this.haptic('short');},
  openCommandCenter(){this.openAdvanced('COMMAND CENTER','UNIFIED FIELD CORE','COMMAND_CENTER');},
  openWifiScout(){this.view='wifiScout';this.advancedTitle='WI-FI SCOUT';this.advancedSubtitle='PHONE SCAN • LOCAL DATA';this.sendCommand('WIFI_STATUS',this.advancedPayload());this.haptic('short');},
  openReconHub(){this.openWifiScout();},
  advancedRefresh(){if(this.advancedAction)this.sendCommand(this.advancedAction,this.advancedPayload());},
  advancedBack(){if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';else this.goHome();},
  advContext(){this.openAdvanced('FIELD CONTEXT','CONTEXT AWARENESS','FIELD_CONTEXT_STATUS');},
  advTelemetry(){this.openAdvanced('TELEMETRY CONFIDENCE','DATA QUALITY','TELEMETRY_CONFIDENCE');},
  advLostMode(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STATUS');},
  advMissionPack(){this.openAdvanced('MISSION PACK','OFFLINE MISSION DATA','MISSION_PACK_STATUS');},
  advEnvRisk(){var temp=finite(this.weatherTemp),uv=String(this.weatherUV||'').replace(/[^0-9.]/g,'');this.openAdvanced('ENVIRONMENT RISK','DECISION SUPPORT','ENV_RISK_STATUS',{temperatureC:temp,uv:finite(uv),altitudeM:this.lastLocation&&finite(this.lastLocation.altitude)!==null?Number(this.lastLocation.altitude):null});},
  advSensorTest(){this.openAdvanced('SENSOR SELF-TEST','DIAGNOSTICS','SENSOR_SELF_TEST');},
  advTimeline(){this.openAdvanced('MISSION TIMELINE PRO','UNIFIED EVENT LOG','TIMELINE_PRO',{filter:'ALL',limit:6});},
  advVoiceMacro(){this.openAdvanced('VOICE MACRO ENGINE','WHITELISTED COMMANDS','VOICE_MACRO_STATUS');},
  advNotification(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_STATUS');},
  advBtRecon(){this.openAdvanced('NEARBY DEVICE RECON','PHONE BLE SCAN','BT_RECON_STATUS');},
  advBtScan(){this.openAdvanced('NEARBY DEVICE RECON','PHONE BLE SCAN','BT_RECON_SCAN');},
  advRunZone(){this.openAdvanced('RUNNING ZONE HUD','REAL RUN TELEMETRY','RUN_ZONE_STATUS');},
  advSkyPro(){this.openAdvanced('SKY SCANNER PRO','OUTDOOR / PHOTO','SKY_PRO_STATUS');},
  advStealth(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_STATUS');},
  advReturnDecision(){this.openAdvanced('RETURN DECISION HUD','DECISION SUPPORT','RETURN_DECISION',{battery:this.watchBattery,returnDistanceM:-1,returnEtaMin:-1,sunsetInMin:-1});},
  advProfiles(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_STATUS');},
  advImpactReview(){this.openAdvanced('IMPACT REVIEW','EVENT SNAPSHOT','IMPACT_REVIEW_STATUS');},
  advEmergencyEscalation(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_STATUS');},
  advPowerAuto(){this.openFeature('24');},
  advSmartAnchor(){this.openFeature('11');},
  advWifiScan(){this.view='wifiScout';this.advancedState='SCANNING';this.advancedData='WAITING FOR PHONE SCAN';this.sendCommand('WIFI_SCAN',this.advancedPayload());},
  advWifiNetworks(){this.openAdvanced('NEARBY NETWORKS','RSSI STRONGEST FIRST','WIFI_NETWORKS',{page:0,size:4,filter:'ALL',sort:'SIGNAL'});},
  advWifiOpen(){this.openAdvanced('OPEN WI-FI','OPEN DOES NOT MEAN FREE','WIFI_OPEN',{page:0});},
  advWifiBest(){this.openAdvanced('BEST WI-FI','QUALITY RECOMMENDATION','WIFI_BEST');},
  advWifiChannels(){this.openAdvanced('CHANNELS','CHANNEL LOAD','WIFI_CHANNELS');},
  advWifiHistory(){this.openAdvanced('WI-FI HISTORY','LOCAL ONLY','WIFI_HISTORY');},
  advWifiTrusted(){this.openAdvanced('TRUSTED WI-FI','USER TRUST LIST','WIFI_TRUSTED');},
  advWifiOutdoor(){this.openAdvanced('OUTDOOR SCAN','BALANCED BACKGROUND SCAN','OUTDOOR_SCAN_START',{mode:'BALANCED'});},
  advCyberSweep(){this.openAdvanced('CYBER SWEEP','WI-FI + BLUETOOTH','CYBER_SWEEP');},
'''
replace_once(js,
'''  applyVoiceIntent(intent,data){var slot=data&&data.slot?String(data.slot):null;''',
advanced_methods+'''  applyVoiceIntent(intent,data){var slot=data&&data.slot?String(data.slot):null;''','watch advanced methods')

replace_once(js,
'''    if(intent==='OPEN_TIMELINE'){this.openTimeline();return;}\n    this.message='VOICE INTENT UNSUPPORTED';''',
'''    if(intent==='OPEN_TIMELINE'){this.openTimeline();return;}\n    if(intent==='CYBER_SWEEP'){this.advCyberSweep();return;}\n    if(intent==='WIFI_SCAN'){this.openWifiScout();this.advWifiScan();return;}\n    if(intent==='OUTDOOR_SCAN_START'){this.advWifiOutdoor();return;}\n    if(intent==='MISSION_START'){this.openAdvanced('MISSION','MISSION CONTROL','MISSION_START');return;}\n    if(intent==='COMMAND_CENTER'){this.openCommandCenter();return;}\n    if(intent==='LOST_MODE_START'){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');return;}\n    this.message='VOICE INTENT UNSUPPORTED';''','watch advanced voice intents')

replace_once(js,
'''  swipeEvent(e){if(e.direction==='right'){if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack'){this.stopLight();return;}if(this.view==='home')app.terminate();else if(this.view==='detail')this.goList();else if(this.view==='anchors'||this.view==='timeline'||this.view==='capabilities'||this.view==='emergencyConfirm')this.goHome();else this.goHome();}},''',
'''  swipeEvent(e){if(e.direction==='right'){if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack'){this.stopLight();return;}if(this.view==='home')app.terminate();else if(this.view==='detail')this.goList();else if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';else if(this.view==='advancedHub'||this.view==='anchors'||this.view==='timeline'||this.view==='capabilities'||this.view==='emergencyConfirm')this.goHome();else this.goHome();}},''','watch advanced swipe')

# ------------------------------------------------------------------
# Watch HML: add Command/Recon dock, extensions and advanced pages
# ------------------------------------------------------------------
hml=WATCH/'index.hml'
replace_once(hml,
'''        <input type="button" class="dock-item" value="SYS" onclick="catSystem"/>\n''',
'''        <input type="button" class="dock-item" value="SYS" onclick="catSystem"/>\n        <input type="button" class="dock-item" value="CMD" onclick="openCommandCenter"/>\n        <input type="button" class="dock-item" value="REC" onclick="openReconHub"/>\n''','home advanced dock')
replace_once(hml,
'''    <input if="{{selectedId == '27'}}" type="button" class="wide-extra" value="CAPABILITY MATRIX" onclick="openCapabilities"/>\n  </div>''',
'''    <input if="{{selectedId == '27'}}" type="button" class="wide-extra" value="CAPABILITY MATRIX" onclick="openCapabilities"/>\n    <input if="{{selectedId == '0'}}" type="button" class="wide-extra advanced-wide" value="COMMAND CENTER" onclick="openCommandCenter"/>\n    <input if="{{selectedId == '27'}}" type="button" class="wide-extra advanced-wide" value="RECON / WI-FI SCOUT" onclick="openReconHub"/>\n  </div>''','detail advanced extensions')

advanced_hml=r'''
  <div if="{{view == 'advancedHub'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">CORE</text></div><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">ADVANCED</text></div><text class="status-label">{{quickProfile}}</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="goHome"/><div class="status-area"><text class="status-title">CONTEXT</text><text class="status-secure">{{contextMode}}</text></div></div>
    <div class="page-header compact-header"><text class="page-title">FIELD CORE PRO</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">CONTEXT • MISSION • RECON</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="advanced-summary"><div class="adv-stat"><text class="adv-k">WIFI</text><text class="adv-v">{{wifiCount}}</text></div><div class="adv-stat"><text class="adv-k">BT</text><text class="adv-v">{{btCount}}</text></div><div class="adv-stat"><text class="adv-k">MISSION</text><text class="adv-v">{{missionLabel}}</text></div><div class="adv-stat"><text class="adv-k">RISK</text><text class="adv-v">{{envRisk}}</text></div></div>
    <list class="advanced-list">
      <list-item class="advanced-row"><input type="button" class="advanced-btn active-state" value="COMMAND CENTER" onclick="openCommandCenter"/><text class="advanced-source">CORE</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="FIELD CONTEXT ENGINE 2.0" onclick="advContext"/><text class="advanced-source">FUSION</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="TELEMETRY CONFIDENCE" onclick="advTelemetry"/><text class="advanced-source">QUALITY</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="LOST MODE PRO" onclick="advLostMode"/><text class="advanced-source">NAV</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="MISSION PACK OFFLINE" onclick="advMissionPack"/><text class="advanced-source">OFFLINE</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="SMART GEO ANCHOR" onclick="advSmartAnchor"/><text class="advanced-source">WATCH</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="ENVIRONMENT RISK INDEX" onclick="advEnvRisk"/><text class="advanced-source">ENV</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="POWER COMMANDER AUTO 2.0" onclick="advPowerAuto"/><text class="advanced-source">WATCH</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="SENSOR SELF-TEST" onclick="advSensorTest"/><text class="advanced-source">SYSTEM</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="MISSION TIMELINE PRO" onclick="advTimeline"/><text class="advanced-source">EVENTS</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="VOICE MACRO ENGINE" onclick="advVoiceMacro"/><text class="advanced-source">PHONE</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="FIELD NOTIFICATION FILTER" onclick="advNotification"/><text class="advanced-source">ALERT</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="NEARBY DEVICE RECON" onclick="advBtRecon"/><text class="advanced-source">PHONE BLE</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="RUNNING ZONE HUD" onclick="advRunZone"/><text class="advanced-source">SPORT</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="SKY SCANNER PRO" onclick="advSkyPro"/><text class="advanced-source">PHONE</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="NIGHT / STEALTH HUD" onclick="advStealth"/><text class="advanced-source">POWER</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="RETURN DECISION HUD" onclick="advReturnDecision"/><text class="advanced-source">NAV</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="FIELD QUICK PROFILES" onclick="advProfiles"/><text class="advanced-source">SYSTEM</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="IMPACT REVIEW SCREEN" onclick="advImpactReview"/><text class="advanced-source">SAFETY</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn danger-feature" value="EMERGENCY ESCALATION" onclick="advEmergencyEscalation"/><text class="advanced-source danger-text">P1–P4</text></list-item>
      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="WI-FI SCOUT / CYBER SWEEP" onclick="openWifiScout"/><text class="advanced-source">RECON</text></list-item>
    </list>
  </div>

  <div if="{{view == 'wifiScout'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">CORE</text></div><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">PHONE SCAN</text></div><text class="status-label">AGE {{wifiAge}}s</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="advancedBack"/><div class="status-area"><text class="status-title">PHONE LINK</text><text class="status-secure">{{connectionState}}</text></div></div>
    <div class="page-header compact-header"><text class="page-title">WI-FI SCOUT</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">RADAR • LOCAL HISTORY</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="wifi-stage"><div class="network-radar wifi-radar"><div class="radar-ring r1"></div><div class="radar-ring r2"></div><div class="radar-ring r3"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="radar-sweep"></div><div class="radar-core"><text class="radar-value">{{wifiCount}}</text><text class="radar-label">NETWORKS</text></div></div><div class="wifi-side"><div class="module-stat"><text class="module-k">OPEN</text><text class="module-v warning-text">{{wifiOpen}}</text></div><div class="module-stat"><text class="module-k">SECURED</text><text class="module-v">{{wifiSecured}}</text></div><div class="module-stat"><text class="module-k">BEST</text><text class="module-v wifi-best">{{wifiBest}}</text></div></div></div>
    <div class="wifi-menu">
      <div class="wifi-row"><input type="button" class="wifi-btn active-state" value="SCAN" onclick="advWifiScan"/><input type="button" class="wifi-btn" value="NETWORKS" onclick="advWifiNetworks"/><input type="button" class="wifi-btn warning-btn" value="OPEN" onclick="advWifiOpen"/></div>
      <div class="wifi-row"><input type="button" class="wifi-btn" value="BEST" onclick="advWifiBest"/><input type="button" class="wifi-btn" value="CHANNELS" onclick="advWifiChannels"/><input type="button" class="wifi-btn" value="HISTORY" onclick="advWifiHistory"/></div>
      <div class="wifi-row"><input type="button" class="wifi-btn" value="TRUSTED" onclick="advWifiTrusted"/><input type="button" class="wifi-btn" value="OUTDOOR" onclick="advWifiOutdoor"/><input type="button" class="wifi-btn" value="CYBER SWEEP" onclick="advCyberSweep"/></div>
      <div class="wifi-row"><input type="button" class="wifi-btn" value="BT RECON" onclick="advBtScan"/><input type="button" class="wifi-btn" value="DUPLICATE" onclick="advWifiNetworks"/><input type="button" class="wifi-btn" value="STATUS" onclick="openWifiScout"/></div>
    </div>
    <text class="wifi-note">RSSI = SIGNAL PROXIMITY • NOT PHYSICAL DISTANCE</text>
  </div>

  <div if="{{view == 'advanced'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">CORE</text></div><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">ADV</text></div><text class="status-label">{{advancedState}}</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="advancedBack"/><div class="status-area"><text class="status-title">STATE</text><text class="status-secure">{{advancedState}}</text></div></div>
    <div class="page-header compact-header"><text class="page-title advanced-title">{{advancedTitle}}</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">{{advancedSubtitle}}</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="advanced-core"><div class="command-core"><div if="{{powerProfile != 'ENDURANCE'}}" class="command-pulse"></div><text class="command-state">{{advancedState}}</text><text class="command-app">{{contextMode}}</text></div><div class="advanced-side"><div class="module-stat"><text class="module-k">CONTEXT</text><text class="module-v">{{contextMode}}</text></div><div class="module-stat"><text class="module-k">CONF</text><text class="module-v">{{contextConfidence}}</text></div><div class="module-stat"><text class="module-k">WIFI / BT</text><text class="module-v">{{wifiCount}} / {{btCount}}</text></div><div class="module-stat"><text class="module-k">RISK</text><text class="module-v">{{envRisk}}</text></div></div></div>
    <div class="advanced-data-card"><text class="section-label">REAL / CACHED RESULT</text><text class="advanced-data">{{advancedData}}</text><text class="module-note">{{message}}</text></div>
    <div class="detail-extra"><input type="button" class="mini-extra active-state" value="REFRESH" onclick="advancedRefresh"/><input type="button" class="mini-extra" value="ADVANCED HUB" onclick="openAdvancedHub"/></div>
  </div>
'''
append_once(hml,
'''  <div if="{{view == 'emergencyConfirm'}}" class="emergency-screen page-enter">''',
advanced_hml,'advanced watch views')

# ------------------------------------------------------------------
# CSS: extend existing Masterpiece skin, no replacement of legacy styles
# ------------------------------------------------------------------
css=WATCH/'index.css'
advanced_css=r'''
/* FIELD CORE Advanced / Pro extension — inherits Original Masterpiece tokens */
.advanced-wide{border-color:#00e5ff;color:#00e5ff;background-color:#00171d;}
.advanced-summary{width:452px;height:42px;flex-direction:row;justify-content:space-between;align-items:center;border-width:1px;border-color:#12364a;border-radius:11px;background-color:#07111c;padding:3px 6px;margin-top:2px;}
.adv-stat{width:106px;height:34px;flex-direction:column;align-items:center;justify-content:center;}
.adv-k{width:100px;color:#7d8dae;font-size:6px;text-align:center;}.adv-v{width:100px;color:#00e5ff;font-size:8px;font-weight:bold;text-align:center;margin-top:2px;}
.advanced-list{width:452px;height:270px;margin-top:4px;padding-bottom:5px;}
.advanced-row{width:452px;height:38px;flex-direction:row;align-items:center;justify-content:space-between;border-bottom-width:1px;border-color:#0c252d;}
.advanced-btn{width:348px;height:32px;border-radius:9px;border-width:1px;border-color:#27424d;border-left-width:2px;background-color:#010507;color:#ffffff;font-size:8px;text-align:left;padding-left:10px;}
.advanced-source{width:94px;color:#00e5ff;font-size:7px;text-align:right;}.advanced-title{font-size:13px;}
.wifi-stage{width:452px;height:146px;flex-direction:row;align-items:center;justify-content:center;border-width:1px;border-color:#12364a;border-radius:13px;background-color:#02080b;margin-top:2px;}
.wifi-radar{margin-right:28px;}.wifi-side{width:188px;height:124px;flex-direction:column;justify-content:space-between;}.wifi-best{font-size:7px;}
.wifi-menu{width:452px;height:142px;flex-direction:column;justify-content:space-between;margin-top:4px;}.wifi-row{width:452px;height:33px;flex-direction:row;justify-content:space-between;}
.wifi-btn{width:148px;height:31px;border-radius:8px;border-width:1px;border-color:#12343d;background-color:#010507;color:#9aa4aa;font-size:7px;}.wifi-note{width:452px;height:12px;color:#7d8dae;font-size:6px;text-align:center;margin-top:2px;}
.advanced-core{width:452px;height:126px;flex-direction:row;align-items:center;justify-content:space-around;border-width:1px;border-color:#12364a;border-radius:13px;background-color:#02080b;margin-top:3px;}
.advanced-side{width:210px;height:108px;flex-direction:column;justify-content:space-between;}.advanced-data-card{width:452px;height:102px;border-radius:12px;background-color:#07111c;border-width:1px;border-color:#12364a;padding:8px 10px;margin-top:5px;}.advanced-data{width:430px;height:54px;color:#a9f0ec;font-size:7px;margin-top:3px;}
'''
append_once(css,'@keyframes scanMove',advanced_css,'advanced css')

# ------------------------------------------------------------------
# Preflight: additive checks; preserve exact 0..27 legacy contract
# ------------------------------------------------------------------
pre=BASE/'tools'/'preflight.py'
replace_once(pre,
'''    "android-companion/app/src/main/java/com/riptwosec/fieldcore/HealthProvider.java",\n]''',
'''    "android-companion/app/src/main/java/com/riptwosec/fieldcore/HealthProvider.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutStore.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/WifiScoutManager.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/BluetoothReconManager.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldEventBus.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/FieldUpgradeManager.java",\n    "android-companion/app/src/main/java/com/riptwosec/fieldcore/ReconScanService.java",\n]''','preflight advanced files')
replace_once(pre,
'''    for token in ["FUSION OS", "GEO ANCHORS", "MISSION TIMELINE", "DEVICE ACCESS", "emergencyConfirm"]:\n        if token not in hml: errors.append("Fusion UI missing " + token)''',
'''    for token in ["FUSION OS", "GEO ANCHORS", "MISSION TIMELINE", "DEVICE ACCESS", "emergencyConfirm", "COMMAND CENTER", "WI-FI SCOUT", "CYBER SWEEP"]:\n        if token not in hml: errors.append("Fusion UI missing " + token)''','preflight advanced ui tokens')
advanced_pre=r'''
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
'''
append_once(pre,'# Both transport directions must enforce <=1 KB P2P messages.',advanced_pre,'preflight advanced contract')

print('FIELD CORE ADVANCED PATCH COMPLETE')
