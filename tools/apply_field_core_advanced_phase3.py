#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Field_Core_FIT4PRO_V1'/'Field_Core_FIT4PRO_V1'
WATCH=BASE/'watch-lite'/'entry'/'src'/'main'/'js'/'MainAbility'/'pages'/'index'
JAVA=BASE/'android-companion'/'app'/'src'/'main'/'java'/'com'/'riptwosec'/'fieldcore'

def rep(path,old,new,label):
    t=path.read_text(encoding='utf-8')
    if new in t: print('already',label);return
    if old not in t: raise SystemExit('PHASE3 ANCHOR MISSING: '+label)
    path.write_text(t.replace(old,new,1),encoding='utf-8');print('patched',label)

def ins(path,marker,block,label):
    t=path.read_text(encoding='utf-8')
    if block.strip() in t: print('already',label);return
    if marker not in t: raise SystemExit('PHASE3 MARKER MISSING: '+label)
    path.write_text(t.replace(marker,block+'\n'+marker,1),encoding='utf-8');print('inserted',label)

# -------------------------------------------------
# Android: find-phone, context suggestions, session privacy
# -------------------------------------------------
mgr=JAVA/'FieldUpgradeManager.java'
rep(mgr,'import android.os.Build;\nimport org.json.JSONArray;',
'''import android.os.Build;\nimport android.os.VibrationEffect;\nimport android.os.Vibrator;\nimport org.json.JSONArray;''','manager vibrator imports')
rep(mgr,
'''return action.startsWith("WIFI_")||action.startsWith("BT_RECON_")||action.startsWith("FIELD_SETTINGS")''',
'''return action.startsWith("WIFI_")||action.startsWith("BT_RECON_")||action.startsWith("PHONE_FIND")||action.startsWith("FIELD_SETTINGS")''','manager phone find prefix')
rep(mgr,
'''            case "BT_RECON_UNTRUST": cb.done(true,"TRUSTED DEVICE UPDATED",bluetooth.setTrusted(p.optString("address",""),false));return;\n\n            case "CYBER_SWEEP":''',
'''            case "BT_RECON_UNTRUST": cb.done(true,"TRUSTED DEVICE UPDATED",bluetooth.setTrusted(p.optString("address",""),false));return;\n            case "PHONE_FIND": cb.done(findPhone(),"FIND PHONE ALERT",simple("status","PHONE VIBRATION REQUESTED"));return;\n\n            case "CYBER_SWEEP":''','find phone command')
rep(mgr,
'''            case "OUTDOOR_SCAN_START": wifi.setMode(p.optString("mode",wifi.getMode()));startOutdoorService(wifi.getMode());cb.done(true,"OUTDOOR SCAN ACTIVE",wifi.startOutdoor());return;\n            case "OUTDOOR_SCAN_STOP": stopOutdoorService();cb.done(true,"SCAN SUMMARY",wifi.stopOutdoor());return;''',
'''            case "OUTDOOR_SCAN_START": wifi.setMode(p.optString("mode",wifi.getMode()));startOutdoorService(wifi.getMode());captureOutdoorLocationIfEnabled();cb.done(true,"OUTDOOR SCAN ACTIVE",wifi.startOutdoor());return;\n            case "OUTDOOR_SCAN_STOP": stopOutdoorService();JSONObject sum=wifi.stopOutdoor();try{String loc=prefs.getString("outdoor_session_location","");sum.put("locationAttached",loc!=null&&!loc.isEmpty());if(loc!=null&&!loc.isEmpty())sum.put("location",new JSONObject(loc));}catch(Exception ignored){}cb.done(true,"SCAN SUMMARY",sum);return;''','outdoor location opt-in')
rep(mgr,
'''o.put("note","WI-FI / BLUETOOTH ARE SUPPORTING EVIDENCE ONLY");o.put("updatedAt",System.currentTimeMillis());''',
'''JSONArray suggestions=new JSONArray();if("NIGHT".equals(mode))suggestions.put("ENABLE NIGHT / STEALTH PROFILE?");if(battery>=0&&battery<30)suggestions.put("SWITCH TO ENDURANCE?");if("RUNNING".equals(mode))suggestions.put("START RUNNING HUD?");o.put("suggestions",suggestions);o.put("note","WI-FI / BLUETOOTH ARE SUPPORTING EVIDENCE ONLY");o.put("updatedAt",System.currentTimeMillis());''','context automation suggestions')
rep(mgr,
'''o.put("notification",prefs.getString("notification_mode","FIELD"));o.put("profile",prefs.getString("quick_profile","DAILY"));o.put("updatedAt",System.currentTimeMillis());''',
'''o.put("notification",prefs.getString("notification_mode","FIELD"));o.put("profile",prefs.getString("quick_profile","DAILY"));JSONArray priority=new JSONArray();String cm=o.optJSONObject("context").optString("mode","OUTDOOR");if("EMERGENCY".equals(cm)){priority.put("SOS").put("LOCATION").put("BATTERY");}else if("RUNNING".equals(cm)){priority.put("RUN").put("HEART RATE").put("NAVIGATION");}else if(prefs.getBoolean("lost_mode",false)){priority.put("RETURN").put("ANCHOR").put("BATTERY").put("GPS");}else{priority.put("MISSION").put("CONTEXT").put("ENVIRONMENT").put("BATTERY");}o.put("priority",priority);o.put("updatedAt",System.currentTimeMillis());''','command center priority')
manager_helpers=r'''    private boolean findPhone(){try{Vibrator v=(Vibrator)context.getSystemService(Context.VIBRATOR_SERVICE);if(v==null)return false;if(Build.VERSION.SDK_INT>=26)v.vibrate(VibrationEffect.createWaveform(new long[]{0,500,220,500,220,900},-1));else v.vibrate(1200);events.emit("FIND_PHONE","SYSTEM","P2","PHONE VIBRATION ALERT",null);return true;}catch(Exception e){return false;}}
    private void captureOutdoorLocationIfEnabled(){if(!prefs.getBoolean("wifi_attach_location",false)){prefs.edit().remove("outdoor_session_location").apply();return;}location.current((ok,msg,data)->{if(ok&&data!=null)prefs.edit().putString("outdoor_session_location",data.toString()).apply();});}
'''
ins(mgr,'    private JSONObject settingsStatus(){',manager_helpers,'manager find/location helpers')

# Android manifest vibrator permission
manifest=BASE/'android-companion'/'app'/'src'/'main'/'AndroidManifest.xml'
rep(manifest,'    <uses-permission android:name="android.permission.INTERNET"/>',
'''    <uses-permission android:name="android.permission.INTERNET"/>\n    <uses-permission android:name="android.permission.VIBRATE"/>''','vibrate permission')

# -------------------------------------------------
# Wi-Fi channel analyzer: account for 2.4 GHz neighbors
# -------------------------------------------------
wifi=JAVA/'WifiScoutManager.java'
rep(wifi,
'''    public JSONObject channels(){Map<String,Integer> counts=new HashMap<>();for(Network n:snapshot()){String k=n.band+"/"+n.channel;counts.put(k,counts.getOrDefault(k,0)+1);}JSONArray a=new JSONArray();for(Map.Entry<String,Integer> e:counts.entrySet()){String[] p=e.getKey().split("/");JSONObject c=new JSONObject();try{int count=e.getValue();c.put("band",p[0]);c.put("channel",Integer.parseInt(p[1]));c.put("aps",count);c.put("load",count>=5?"BUSY":(count>=3?"MEDIUM":"CLEAR"));a.put(c);}catch(Exception ignored){}}JSONObject o=new JSONObject();try{o.put("channels",a);o.put("updatedAt",lastScanAt);}catch(Exception ignored){}return o;}''',
'''    public JSONObject channels(){List<Network> list=snapshot();Map<String,Integer> counts=new HashMap<>();for(Network n:list){String k=n.band+"/"+n.channel;counts.put(k,counts.getOrDefault(k,0)+1);}JSONArray a=new JSONArray();for(Map.Entry<String,Integer> e:counts.entrySet()){String[] p=e.getKey().split("/");JSONObject c=new JSONObject();try{String bandName=p[0];int ch=Integer.parseInt(p[1]),same=e.getValue(),weighted=same;if("2.4GHz".equals(bandName)){for(Network n:list)if("2.4GHz".equals(n.band)&&n.channel!=ch){int d=Math.abs(n.channel-ch);if(d<=2)weighted+=2;else if(d<=4)weighted+=1;}}c.put("band",bandName);c.put("channel",ch);c.put("aps",same);c.put("weightedLoad",weighted);c.put("load",weighted>=7?"BUSY":(weighted>=4?"MEDIUM":"CLEAR"));a.put(c);}catch(Exception ignored){}}JSONObject o=new JSONObject();try{o.put("channels",a);o.put("updatedAt",lastScanAt);o.put("note","2.4 GHZ INCLUDES NEARBY-CHANNEL WEIGHTING");}catch(Exception ignored){}return o;}''','channel neighbor weighting')

# -------------------------------------------------
# Watch runtime: Wi-Fi list/detail + Cyber Sweep page + controls
# -------------------------------------------------
js=WATCH/'index.js'
rep(js,
'''contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD',stealthMode:false,fieldSettings:'--'\n''',
'''contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD',stealthMode:false,fieldSettings:'--',wifiScanMode:'BALANCED',\n    wifiListTitle:'NEARBY NETWORKS',wifi1:'-',wifi2:'-',wifi3:'-',wifi4:'-',wifi1Meta:'',wifi2Meta:'',wifi3Meta:'',wifi4Meta:'',wifi1Bssid:'',wifi2Bssid:'',wifi3Bssid:'',wifi4Bssid:'',\n    wifiSelectedSsid:'-',wifiSelectedBssid:'',wifiSelectedRssi:'--',wifiSelectedSecurity:'--',wifiSelectedBand:'--',wifiSelectedChannel:'--',wifiSelectedRisk:'--',lastSignalHaptic:0\n''','watch wifi detail state')

rep(js,
'''if(action.indexOf('WIFI_')===0||action.indexOf('OUTDOOR_SCAN')===0){this.wifiCount=this.pick(d,'count',this.pick(d,'total',this.pick(d,'networks',this.wifiCount)));this.wifiOpen=this.pick(d,'open',this.wifiOpen);this.wifiSecured=this.pick(d,'secured',this.wifiSecured);this.wifiAge=this.pick(d,'ageSec',this.wifiAge);var b=d.best&&d.best.network?d.best.network:(d.best||d.strongest||null);if(b)this.wifiBest=String(this.pick(b,'s',this.pick(b,'ssid','AVAILABLE')));}''',
'''if(action.indexOf('WIFI_')===0||action.indexOf('OUTDOOR_SCAN')===0){this.wifiCount=this.pick(d,'count',this.pick(d,'total',this.pick(d,'networks',this.wifiCount)));this.wifiOpen=this.pick(d,'open',this.wifiOpen);this.wifiSecured=this.pick(d,'secured',this.wifiSecured);this.wifiAge=this.pick(d,'ageSec',this.wifiAge);this.wifiScanMode=String(this.pick(d,'mode',this.pick(d,'scanMode',this.wifiScanMode)));var b=d.best&&d.best.network?d.best.network:(d.best||d.strongest||null);if(b)this.wifiBest=String(this.pick(b,'s',this.pick(b,'ssid','AVAILABLE')));if(action==='WIFI_NETWORKS'||action==='WIFI_OPEN'||action==='WIFI_HISTORY'||action==='WIFI_TRUSTED'||action==='WIFI_SEARCH'){this.applyWifiList(d,action);}if(action==='WIFI_DETAIL'){this.applyWifiDetail(d);}if(action==='WIFI_SIGNAL_HUNT'){this.signalHuntFeedback(d);}}''','watch wifi result parsing')
rep(js,
'''if(action==='CYBER_SWEEP'){var w=d.wifi||{},b2=d.bluetooth||{};this.wifiCount=this.pick(w,'count',this.wifiCount);this.wifiOpen=this.pick(w,'open',this.wifiOpen);this.btCount=this.pick(b2,'count',this.btCount);this.btTrusted=this.pick(b2,'trusted',this.btTrusted);this.btUnknown=this.pick(b2,'unknown',this.btUnknown);}''',
'''if(action==='CYBER_SWEEP'){var w=d.wifi||{},b2=d.bluetooth||{};this.wifiCount=this.pick(w,'count',this.wifiCount);this.wifiOpen=this.pick(w,'open',this.wifiOpen);this.btCount=this.pick(b2,'count',this.btCount);this.btTrusted=this.pick(b2,'trusted',this.btTrusted);this.btUnknown=this.pick(b2,'unknown',this.btUnknown);this.view='cyberSweep';}''','cyber sweep dedicated view')

wifi_methods=r'''  wifiItemName(x){return x?String(this.pick(x,'s',this.pick(x,'ssid','HIDDEN NETWORK'))):'-';},
  wifiItemMeta(x){if(!x)return '';var r=this.pick(x,'r',this.pick(x,'rssi','--')),sec=this.pick(x,'sec',this.pick(x,'security','UNKNOWN')),band=this.pick(x,'band','');return String(r)+' dBm • '+String(sec)+' • '+String(band);},
  setWifiSlot(i,x){this['wifi'+i]=this.wifiItemName(x);this['wifi'+i+'Meta']=this.wifiItemMeta(x);this['wifi'+i+'Bssid']=x?String(this.pick(x,'b',this.pick(x,'bssid',''))):'';},
  applyWifiList(d,action){var arr=d&&d.items?d.items:[];this.wifiListTitle=action==='WIFI_OPEN'?'OPEN WI-FI':(action==='WIFI_HISTORY'?'WI-FI HISTORY':(action==='WIFI_TRUSTED'?'TRUSTED WI-FI':(action==='WIFI_SEARCH'?'SEARCH RESULTS':'NEARBY NETWORKS')));var i;for(i=1;i<=4;i++)this.setWifiSlot(i,arr&&arr.length>=i?arr[i-1]:null);this.view='wifiList';},
  applyWifiDetail(d){this.wifiSelectedSsid=String(this.pick(d,'s',this.pick(d,'ssid','HIDDEN NETWORK')));this.wifiSelectedBssid=String(this.pick(d,'b',this.pick(d,'bssid','')));this.wifiSelectedRssi=String(this.pick(d,'r',this.pick(d,'rssi','--')));this.wifiSelectedSecurity=String(this.pick(d,'sec',this.pick(d,'security','UNKNOWN')));this.wifiSelectedBand=String(this.pick(d,'band','UNKNOWN'));this.wifiSelectedChannel=String(this.pick(d,'ch',this.pick(d,'channel','--')));this.wifiSelectedRisk=String(this.pick(d,'riskLevel',this.pick(d,'risk','--')));this.view='wifiDetail';},
  signalHuntFeedback(d){var now=Date.now();if(now-this.lastSignalHaptic<2500)return;var trend=String(this.pick(d,'trend','STABLE')),prox=String(this.pick(d,'proximity',''));if(trend==='STRONGER'||prox==='VERY NEAR'){this.haptic('short');if(prox==='VERY NEAR'){var self=this;setTimeout(function(){self.haptic('short');},220);}this.lastSignalHaptic=now;}},
  wifiOpenSlot(i){var b=this['wifi'+i+'Bssid'];if(!b){this.message='NO NETWORK';return;}this.openAdvanced('WI-FI DETAIL','SECURITY / SIGNAL','WIFI_DETAIL',{bssid:b});},
  wifi1Detail(){this.wifiOpenSlot(1);},wifi2Detail(){this.wifiOpenSlot(2);},wifi3Detail(){this.wifiOpenSlot(3);},wifi4Detail(){this.wifiOpenSlot(4);},
  wifiTrustSelected(){if(this.wifiSelectedBssid)this.sendCommand('WIFI_TRUST',{bssid:this.wifiSelectedBssid});},wifiPinSelected(){if(this.wifiSelectedBssid)this.sendCommand('WIFI_PIN',{bssid:this.wifiSelectedBssid});},wifiHideSelected(){if(this.wifiSelectedBssid){this.sendCommand('WIFI_HIDE',{bssid:this.wifiSelectedBssid});this.view='wifiScout';}},wifiSignalSelected(){if(this.wifiSelectedBssid)this.openAdvanced('SIGNAL HUNT','RSSI TREND • NOT DIRECTION','WIFI_SIGNAL_HUNT',{bssid:this.wifiSelectedBssid});},
  wifiListBack(){this.view='wifiScout';},
'''
ins(js,'  advSettings(){',wifi_methods,'watch wifi list helpers')

rep(js,
'''  advWifiNetworks(){this.openAdvanced('NEARBY NETWORKS','RSSI STRONGEST FIRST','WIFI_NETWORKS',{page:0,size:4,filter:'ALL',sort:'SIGNAL'});},''',
'''  advWifiNetworks(){this.wifiListTitle='NEARBY NETWORKS';this.view='wifiList';this.sendCommand('WIFI_NETWORKS',{page:0,size:4,filter:'ALL',sort:'SIGNAL'});},''','wifi network list direct')
rep(js,
'''  advWifiOpen(){this.openAdvanced('OPEN WI-FI','OPEN DOES NOT MEAN FREE','WIFI_OPEN',{page:0});},''',
'''  advWifiOpen(){this.wifiListTitle='OPEN WI-FI';this.view='wifiList';this.sendCommand('WIFI_OPEN',{page:0});},''','wifi open list direct')
rep(js,
'''  advWifiHistory(){this.openAdvanced('WI-FI HISTORY','LOCAL ONLY','WIFI_HISTORY');},''',
'''  advWifiHistory(){this.wifiListTitle='WI-FI HISTORY';this.view='wifiList';this.sendCommand('WIFI_HISTORY');},''','wifi history list direct')
rep(js,
'''  advWifiTrusted(){this.openAdvanced('TRUSTED WI-FI','USER TRUST LIST','WIFI_TRUSTED');},''',
'''  advWifiTrusted(){this.wifiListTitle='TRUSTED WI-FI';this.view='wifiList';this.sendCommand('WIFI_TRUSTED');},''','wifi trusted list direct')
rep(js,
'''  advCyberSweep(){this.openAdvanced('CYBER SWEEP','WI-FI + BLUETOOTH','CYBER_SWEEP');},''',
'''  advCyberSweep(){this.advancedState='SCANNING';this.advancedData='WI-FI + BLUETOOTH';this.view='cyberSweep';this.sendCommand('CYBER_SWEEP',this.advancedPayload());},''','cyber sweep dedicated launch')
rep(js,
'''  advMissionStart(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_START');},advMissionStop(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_STOP');},''',
'''  advMissionPrepare(){this.openAdvanced('MISSION PACK','OFFLINE MISSION DATA','MISSION_PACK_SAVE',{name:'FIELD MISSION',waypoints:this.breadcrumbPoints,weatherSnapshot:this.weatherState,compassBearing:this.headingNameText,safePoints:this.anchorsCount,map:'NOT CACHED'});},advMissionStart(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_START');},advMissionStop(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_STOP');},''','mission prepare watch')
rep(js,
'''  advLostStart(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');},advLostStop(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STOP');},''',
'''  advFindPhone(){this.openAdvanced('FIND PHONE','PHONE HAPTIC ALERT','PHONE_FIND');},advLostReturn(){if(this.breadcrumbRoute.length)this.returnBreadcrumb();else this.message='NO RETURN ROUTE';},advLostSos(){this.quickEmergency();},advLostStart(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');},advLostStop(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STOP');},''','lost mode actions')
rep(js,
'''  advStealthOn(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:true});},''',
'''  advStealthOn(){this.applyPowerProfileInternal('ENDURANCE',false);this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:true});},''','stealth reduced motion')
rep(js,
'''  advStealthOff(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:false});},''',
'''  advStealthOff(){this.enableAutoPower();this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:false});},''','stealth restore auto')
settings_methods=r'''  advWifiModeActive(){this.openAdvanced('FIELD CORE SETTINGS','WI-FI SCAN MODE','WIFI_SCAN_MODE',{mode:'ACTIVE'});},advWifiModeBalanced(){this.openAdvanced('FIELD CORE SETTINGS','WI-FI SCAN MODE','WIFI_SCAN_MODE',{mode:'BALANCED'});},advWifiModeSaver(){this.openAdvanced('FIELD CORE SETTINGS','WI-FI SCAN MODE','WIFI_SCAN_MODE',{mode:'BATTERY_SAVER'});},
  advLocationAttachOn(){this.openAdvanced('FIELD CORE SETTINGS','PRIVACY','FIELD_SETTINGS_SET',{attachLocation:true});},advLocationAttachOff(){this.openAdvanced('FIELD CORE SETTINGS','PRIVACY','FIELD_SETTINGS_SET',{attachLocation:false});},advHapticsOn(){this.openAdvanced('FIELD CORE SETTINGS','HAPTICS','FIELD_SETTINGS_SET',{haptics:true});},advHapticsOff(){this.openAdvanced('FIELD CORE SETTINGS','HAPTICS','FIELD_SETTINGS_SET',{haptics:false});},
'''
ins(js,'  advStealthOn(){',settings_methods,'watch settings controls')

rep(js,
'''else if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';''',
'''else if(this.view==='wifiDetail')this.view='wifiList';else if(this.view==='wifiList'||this.view==='cyberSweep')this.view='wifiScout';else if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';''','watch wifi swipe navigation')

# -------------------------------------
# Watch HML dedicated Wi-Fi/Cyber views
# -------------------------------------
hml=WATCH/'index.hml'
wifi_pages=r'''
  <div if="{{view == 'wifiList'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">CORE</text></div><text class="status-label">LOCAL / PHONE</text><text class="status-label">AGE {{wifiAge}}s</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="wifiListBack"/><div class="status-area"><text class="status-title">SORT</text><text class="status-secure">SIGNAL</text></div></div>
    <div class="page-header compact-header"><text class="page-title advanced-title">{{wifiListTitle}}</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">RSSI • SECURITY • BAND</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="wifi-network-list">
      <div class="wifi-network-row"><input type="button" class="wifi-network-btn" value="{{wifi1}}" onclick="wifi1Detail"/><text class="wifi-network-meta">{{wifi1Meta}}</text></div>
      <div class="wifi-network-row"><input type="button" class="wifi-network-btn" value="{{wifi2}}" onclick="wifi2Detail"/><text class="wifi-network-meta">{{wifi2Meta}}</text></div>
      <div class="wifi-network-row"><input type="button" class="wifi-network-btn" value="{{wifi3}}" onclick="wifi3Detail"/><text class="wifi-network-meta">{{wifi3Meta}}</text></div>
      <div class="wifi-network-row"><input type="button" class="wifi-network-btn" value="{{wifi4}}" onclick="wifi4Detail"/><text class="wifi-network-meta">{{wifi4Meta}}</text></div>
    </div>
    <text class="wifi-note">OPEN ≠ FREE INTERNET • HIDDEN ≠ THREAT</text>
  </div>

  <div if="{{view == 'wifiDetail'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">WI-FI</text></div><text class="status-label">DETAIL</text><text class="status-label">LOCAL</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="advWifiNetworks"/><div class="status-area"><text class="status-title">RISK</text><text class="status-secure">{{wifiSelectedRisk}}</text></div></div>
    <div class="page-header compact-header"><text class="page-title advanced-title">{{wifiSelectedSsid}}</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">NETWORK DETAIL</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="wifi-detail-card"><div class="wifi-detail-row"><text class="module-k">SIGNAL</text><text class="module-v">{{wifiSelectedRssi}} dBm</text></div><div class="wifi-detail-row"><text class="module-k">SECURITY</text><text class="module-v">{{wifiSelectedSecurity}}</text></div><div class="wifi-detail-row"><text class="module-k">BAND / CH</text><text class="module-v">{{wifiSelectedBand}} / {{wifiSelectedChannel}}</text></div><div class="wifi-detail-row"><text class="module-k">BSSID</text><text class="wifi-bssid">{{wifiSelectedBssid}}</text></div></div>
    <div class="wifi-detail-actions"><input type="button" class="wifi-detail-btn" value="TRUST" onclick="wifiTrustSelected"/><input type="button" class="wifi-detail-btn" value="PIN" onclick="wifiPinSelected"/><input type="button" class="wifi-detail-btn active-state" value="SIGNAL HUNT" onclick="wifiSignalSelected"/><input type="button" class="wifi-detail-btn warning-btn" value="HIDE" onclick="wifiHideSelected"/></div>
    <text class="wifi-note">SIGNAL HUNT USES RSSI TREND • NOT PHYSICAL DIRECTION</text>
  </div>

  <div if="{{view == 'cyberSweep'}}" class="page masterpiece-page utility-page page-enter">
    <div class="system-status-strip"><div class="status-cell"><text class="status-dot online">●</text><text class="status-label">CORE</text></div><text class="status-label">CYBER SWEEP</text><text class="status-label">LOCAL</text><text class="battery-mini">{{watchBattery}}%</text></div>
    <div class="header"><input type="button" class="back-cyber" value="‹" onclick="openWifiScout"/><div class="status-area"><text class="status-title">STATE</text><text class="status-secure">{{advancedState}}</text></div></div>
    <div class="page-header compact-header"><text class="page-title">CYBER SWEEP</text><div class="subtitle-row"><div class="subtitle-line pulse-line"></div><text class="page-subtitle">WI-FI + BLUETOOTH</text><div class="subtitle-line pulse-line"></div></div></div>
    <div class="cyber-sweep-stage"><div class="network-radar sweep-radar"><div class="radar-ring r1"></div><div class="radar-ring r2"></div><div class="radar-ring r3"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="radar-sweep"></div><div class="radar-core"><text class="radar-value">{{wifiCount}}</text><text class="radar-label">WIFI</text></div></div><div class="sweep-side"><div class="module-stat"><text class="module-k">BLUETOOTH</text><text class="module-v">{{btCount}}</text></div><div class="module-stat"><text class="module-k">TRUSTED</text><text class="module-v">{{btTrusted}}</text></div><div class="module-stat"><text class="module-k">UNKNOWN</text><text class="module-v">{{btUnknown}}</text></div><div class="module-stat"><text class="module-k">OPEN WIFI</text><text class="module-v warning-text">{{wifiOpen}}</text></div></div></div>
    <div class="detail-extra"><input type="button" class="mini-extra active-state" value="SCAN AGAIN" onclick="advCyberSweep"/><input type="button" class="mini-extra" value="DEVICE HISTORY" onclick="advBtHistory"/></div>
    <text class="wifi-note">NEW / UNKNOWN ≠ MALICIOUS</text>
  </div>
'''
ins(hml,'  <div if="{{view == \'advanced\'}}" class="page masterpiece-page utility-page page-enter">',wifi_pages,'wifi list/detail/cyber pages')

rep(hml,
'''    <div if="{{advancedTitle == 'MISSION PACK'}}" class="detail-extra"><input type="button" class="mini-extra" value="MISSION START" onclick="advMissionStart"/><input type="button" class="mini-extra" value="MISSION STOP" onclick="advMissionStop"/></div>''',
'''    <div if="{{advancedTitle == 'MISSION PACK'}}" class="detail-extra"><input type="button" class="mini-extra active-state" value="PREPARE PACK" onclick="advMissionPrepare"/><input type="button" class="mini-extra" value="MISSION START" onclick="advMissionStart"/></div><input if="{{advancedTitle == 'MISSION PACK'}}" type="button" class="wide-extra" value="MISSION STOP" onclick="advMissionStop"/>''','mission pack watch controls')
rep(hml,
'''    <div if="{{advancedTitle == 'LOST MODE PRO'}}" class="detail-extra"><input type="button" class="mini-extra" value="START LOST" onclick="advLostStart"/><input type="button" class="mini-extra" value="STOP LOST" onclick="advLostStop"/></div>''',
'''    <div if="{{advancedTitle == 'LOST MODE PRO'}}" class="profile-row"><input type="button" class="profile-btn" value="FIND PHONE" onclick="advFindPhone"/><input type="button" class="profile-btn" value="RETURN" onclick="advLostReturn"/><input type="button" class="profile-btn danger-btn" value="SOS" onclick="advLostSos"/></div><div if="{{advancedTitle == 'LOST MODE PRO'}}" class="detail-extra"><input type="button" class="mini-extra" value="START LOST" onclick="advLostStart"/><input type="button" class="mini-extra" value="STOP LOST" onclick="advLostStop"/></div>''','lost mode action controls')
rep(hml,
'''    <div if="{{advancedTitle == 'EMERGENCY ESCALATION'}}" class="profile-row"><input type="button" class="profile-btn" value="L0" onclick="advEmergencyLevel0"/><input type="button" class="profile-btn" value="L1" onclick="advEmergencyLevel1"/><input type="button" class="profile-btn" value="L2" onclick="advEmergencyLevel2"/><input type="button" class="profile-btn danger-btn" value="L3" onclick="advEmergencyLevel3"/></div>''',
'''    <div if="{{advancedTitle == 'EMERGENCY ESCALATION'}}" class="profile-row"><input type="button" class="profile-btn" value="L0" onclick="advEmergencyLevel0"/><input type="button" class="profile-btn" value="L1" onclick="advEmergencyLevel1"/><input type="button" class="profile-btn" value="L2" onclick="advEmergencyLevel2"/><input type="button" class="profile-btn danger-btn" value="L3" onclick="advEmergencyLevel3"/></div>\n    <div if="{{advancedTitle == 'FIELD CORE SETTINGS'}}" class="profile-row"><input type="button" class="profile-btn" value="WIFI ACTIVE" onclick="advWifiModeActive"/><input type="button" class="profile-btn" value="BALANCED" onclick="advWifiModeBalanced"/><input type="button" class="profile-btn" value="SAVER" onclick="advWifiModeSaver"/></div>\n    <div if="{{advancedTitle == 'FIELD CORE SETTINGS'}}" class="detail-extra"><input type="button" class="mini-extra" value="LOCATION ATTACH ON" onclick="advLocationAttachOn"/><input type="button" class="mini-extra" value="LOCATION ATTACH OFF" onclick="advLocationAttachOff"/></div>\n    <div if="{{advancedTitle == 'FIELD CORE SETTINGS'}}" class="detail-extra"><input type="button" class="mini-extra" value="HAPTICS ON" onclick="advHapticsOn"/><input type="button" class="mini-extra" value="HAPTICS OFF" onclick="advHapticsOff"/></div>''','settings watch controls')

css=WATCH/'index.css'
css3=r'''
.wifi-network-list{width:452px;height:244px;flex-direction:column;justify-content:space-between;margin-top:3px;}.wifi-network-row{width:452px;height:58px;border-radius:10px;border-width:1px;border-color:#12364a;background-color:#07111c;padding:4px 8px;flex-direction:column;justify-content:center;}.wifi-network-btn{width:430px;height:25px;background-color:#010507;border-width:0px;color:#ffffff;font-size:9px;text-align:left;}.wifi-network-meta{width:430px;height:18px;color:#00e5ff;font-size:7px;}.wifi-detail-card{width:452px;height:170px;border-radius:13px;border-width:1px;border-color:#12364a;background-color:#07111c;padding:10px 12px;margin-top:4px;}.wifi-detail-row{width:428px;height:36px;flex-direction:row;align-items:center;justify-content:space-between;border-bottom-width:1px;border-color:#0c252d;}.wifi-bssid{width:260px;color:#7d8dae;font-size:7px;text-align:right;}.wifi-detail-actions{width:452px;height:74px;flex-direction:row;flex-wrap:wrap;justify-content:space-between;margin-top:5px;}.wifi-detail-btn{width:223px;height:34px;border-radius:9px;border-width:1px;border-color:#12343d;background-color:#010507;color:#9aa4aa;font-size:7px;margin-bottom:4px;}.cyber-sweep-stage{width:452px;height:184px;border-radius:13px;border-width:1px;border-color:#12364a;background-color:#02080b;flex-direction:row;align-items:center;justify-content:space-around;margin-top:4px;}.sweep-radar{margin-right:24px;}.sweep-side{width:200px;height:150px;flex-direction:column;justify-content:space-between;}
'''
ins(css,'@keyframes scanMove',css3,'phase3 css')

pre=BASE/'tools'/'preflight.py'
pre3=r'''
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
'''
ins(pre,'# Both transport directions must enforce <=1 KB P2P messages.',pre3,'phase3 preflight')

print('FIELD CORE ADVANCED PHASE 3 PATCH COMPLETE')
