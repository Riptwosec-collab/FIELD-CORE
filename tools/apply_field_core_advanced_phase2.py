#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Field_Core_FIT4PRO_V1'/'Field_Core_FIT4PRO_V1'
WATCH=BASE/'watch-lite'/'entry'/'src'/'main'/'js'/'MainAbility'/'pages'/'index'
JAVA=BASE/'android-companion'/'app'/'src'/'main'/'java'/'com'/'riptwosec'/'fieldcore'

def rep(path,old,new,label):
    t=path.read_text(encoding='utf-8')
    if new in t: print('already',label);return
    if old not in t: raise SystemExit('PHASE2 ANCHOR MISSING: '+label)
    path.write_text(t.replace(old,new,1),encoding='utf-8');print('patched',label)

def ins(path,marker,block,label):
    t=path.read_text(encoding='utf-8')
    if block.strip() in t: print('already',label);return
    if marker not in t: raise SystemExit('PHASE2 MARKER MISSING: '+label)
    path.write_text(t.replace(marker,block+'\n'+marker,1),encoding='utf-8');print('inserted',label)

# --------------------------------------------------------------
# Wi-Fi Scout Pro: search, pin/hide, diff updates, score/risk detail
# --------------------------------------------------------------
wifi=JAVA/'WifiScoutManager.java'
rep(wifi,'import android.content.Context;\nimport android.content.Intent;',
'''import android.content.Context;\nimport android.content.Intent;\nimport android.content.SharedPreferences;''','wifi preferences import')
rep(wifi,
'''    private final WifiScoutStore store;\n    private final Handler main=new Handler(Looper.getMainLooper());''',
'''    private final WifiScoutStore store;\n    private final SharedPreferences prefs;\n    private final Handler main=new Handler(Looper.getMainLooper());''','wifi prefs field')
rep(wifi,
'''        context=c.getApplicationContext();events=sink;wifi=(WifiManager)context.getSystemService(Context.WIFI_SERVICE);store=new WifiScoutStore(context);register();''',
'''        context=c.getApplicationContext();events=sink;wifi=(WifiManager)context.getSystemService(Context.WIFI_SERVICE);store=new WifiScoutStore(context);prefs=context.getSharedPreferences("fieldcore_wifi_scout_prefs",Context.MODE_PRIVATE);register();''','wifi prefs init')

rep(wifi,
'''        long now=System.currentTimeMillis();List<Network> next=new ArrayList<>();Map<String,Integer> ssidCounts=new HashMap<>();''',
'''        long now=System.currentTimeMillis();List<Network> before=snapshot();Map<String,Integer> beforeRssi=new HashMap<>();for(Network old:before)beforeRssi.put(old.bssid,old.rssi);Set<String> seenBssid=new HashSet<>();\n        List<Network> next=new ArrayList<>();Map<String,Integer> ssidCounts=new HashMap<>();''','wifi diff baseline')
rep(wifi,
'''        next.sort((a,b)->Integer.compare(b.rssi,a.rssi));int newCount=0,open=0,hidden=0,secured=0;''',
'''        next.sort((a,b)->Integer.compare(b.rssi,a.rssi));int newCount=0,open=0,hidden=0,secured=0,added=0,updated=0;''','wifi diff counters')
rep(wifi,
'''        for(Network n:next){n.duplicate=n.ssid.length()>0&&ssidCounts.getOrDefault(n.ssid,0)>1;JSONObject change=store.upsert(n.ssid,n.bssid,n.rssi,n.security,n.band,n.channel,n.hidden,now);''',
'''        for(Network n:next){seenBssid.add(n.bssid);Integer oldR=beforeRssi.get(n.bssid);if(oldR==null)added++;else if(Math.abs(oldR-n.rssi)>=5)updated++;n.duplicate=n.ssid.length()>0&&ssidCounts.getOrDefault(n.ssid,0)>1;JSONObject change=store.upsert(n.ssid,n.bssid,n.rssi,n.security,n.band,n.channel,n.hidden,now);''','wifi diff classify')
rep(wifi,
'''sessionSeen.add(n.bssid);previousRssi.put(n.bssid,n.rssi);}''',
'''sessionSeen.add(n.bssid);}''','signal hunt independent history')
rep(wifi,
'''        JSONObject out=summary();try{out.put("source",source);out.put("new",newCount);out.put("secured",secured);out.put("hidden",hidden);}catch(Exception ignored){}''',
'''        int removed=0;for(String oldBssid:beforeRssi.keySet())if(!seenBssid.contains(oldBssid))removed++;JSONObject out=summary();try{out.put("source",source);out.put("new",newCount);out.put("secured",secured);out.put("hidden",hidden);JSONObject diff=new JSONObject();diff.put("added",added);diff.put("updated",updated);diff.put("removed",removed);out.put("diff",diff);}catch(Exception ignored){}''','wifi differential summary')

rep(wifi,
'''    public JSONObject detail(String bssid){Network n=find(bssid);if(n==null){JSONObject cached=store.get(bssid);return cached==null?new JSONObject():cached;}return n.detail();}''',
'''    public JSONObject detail(String bssid){Network n=find(bssid);if((bssid==null||bssid.length()==0)&&!snapshot().isEmpty())n=snapshot().get(0);if(n==null){JSONObject cached=store.get(bssid);return cached==null?new JSONObject():cached;}JSONObject o=n.detail();try{o.put("pinned",prefs.getBoolean("pin_"+n.bssid,false));o.put("userHidden",prefs.getBoolean("hide_"+n.bssid,false));o.put("riskLevel",n.risk>=70?"HIGH":(n.risk>=35?"MEDIUM":"LOW"));o.put("riskReasons",riskReasons(n));}catch(Exception ignored){}return o;}''','wifi detail risk')
rep(wifi,
'''    public JSONObject best(){Network n=bestNetwork(snapshot());JSONObject o=new JSONObject();try{if(n==null)o.put("status","NO NETWORKS");else{o.put("network",n.detail());o.put("score",score(n));}}catch(Exception ignored){}return o;}''',
'''    public JSONObject best(){Network n=bestNetwork(snapshot());JSONObject o=new JSONObject();try{if(n==null)o.put("status","NO NETWORKS");else{o.put("network",detail(n.bssid));JSONObject parts=scoreParts(n);o.put("score",parts.optInt("total"));o.put("signal",parts.optInt("signal"));o.put("security",parts.optInt("security"));o.put("stability",parts.optInt("stability"));o.put("bandScore",parts.optInt("band"));}}catch(Exception ignored){}return o;}''','wifi best breakdown')
rep(wifi,
'''    public JSONObject signalHunt(String bssid){Network n=find(bssid);JSONObject o=new JSONObject();try{if(n==null){o.put("status","TARGET NOT VISIBLE");return o;}''',
'''    public JSONObject signalHunt(String bssid){Network n=find(bssid);if(n==null&&(bssid==null||bssid.length()==0))n=bestNetwork(snapshot());JSONObject o=new JSONObject();try{if(n==null){o.put("status","TARGET NOT VISIBLE");return o;}''','wifi signal hunt default target')

wifi_extra=r'''    public JSONObject search(String query,int limit){String q=query==null?"":query.trim().toLowerCase(Locale.ROOT);JSONArray a=new JSONArray();for(Network n:snapshot()){if(prefs.getBoolean("hide_"+n.bssid,false))continue;if(q.length()==0||n.ssid.toLowerCase(Locale.ROOT).contains(q)||n.bssid.toLowerCase(Locale.ROOT).contains(q)){a.put(n.compact());if(a.length()>=Math.max(1,Math.min(8,limit)))break;}}JSONObject o=new JSONObject();try{o.put("query",query==null?"":query);o.put("count",a.length());o.put("items",a);}catch(Exception ignored){}return o;}
    public JSONObject setPinned(String bssid,boolean value){prefs.edit().putBoolean("pin_"+bssid,value).apply();JSONObject o=new JSONObject();try{o.put("bssid",bssid);o.put("pinned",value);}catch(Exception ignored){}return o;}
    public JSONObject setUserHidden(String bssid,boolean value){prefs.edit().putBoolean("hide_"+bssid,value).apply();JSONObject o=new JSONObject();try{o.put("bssid",bssid);o.put("hidden",value);}catch(Exception ignored){}return o;}
    private JSONArray riskReasons(Network n){JSONArray a=new JSONArray();if("OPEN".equals(n.security))a.put("OPEN NETWORK");if("WEP".equals(n.security))a.put("WEAK LEGACY SECURITY");if(n.isNew)a.put("NEW BSSID");if(n.duplicate)a.put("DUPLICATE SSID");if(n.securityChanged)a.put("SECURITY CHANGED");if(n.rssi>-45&&!n.trusted)a.put("VERY STRONG UNKNOWN AP");return a;}
    private JSONObject scoreParts(Network n){int signal=Math.max(0,Math.min(100,2*(n.rssi+100)));int sec=securityScore(n.security);int bandScore="5GHz".equals(n.band)?90:("6GHz".equals(n.band)?95:70);int stability=Math.max(40,100-Math.min(60,Math.abs(n.strongestRssi-n.rssi)*2));int total=Math.max(0,Math.min(100,(signal*40+sec*30+stability*20+bandScore*10)/100-("OPEN".equals(n.security)?15:0)));JSONObject o=new JSONObject();try{o.put("signal",signal);o.put("security",sec);o.put("stability",stability);o.put("band",bandScore);o.put("total",total);}catch(Exception ignored){}return o;}
'''
ins(wifi,'    public JSONObject duplicateSummary(){',wifi_extra,'wifi pro APIs')
rep(wifi,
'''    private int score(Network n){int signal=Math.max(0,Math.min(100,2*(n.rssi+100)));int sec=securityScore(n.security);int band="5GHz".equals(n.band)?90:("6GHz".equals(n.band)?95:70);int stability=Math.max(40,100-Math.min(60,Math.abs(n.strongestRssi-n.rssi)*2));return Math.max(0,Math.min(100,(signal*40+sec*30+stability*20+band*10)/100));}''',
'''    private int score(Network n){return scoreParts(n).optInt("total",0);}''','wifi score reuse')

# -----------------------------------
# Bluetooth local device history API
# -----------------------------------
bt=JAVA/'BluetoothReconManager.java'
rep(bt,
'''x.lastSeen=now;current.put(address,x);history.put(address,now);''',
'''x.lastSeen=now;current.put(address,x);history.put(address,now);prefs.edit().putString("name_"+address,x.name).putString("type_"+address,x.type).putInt("rssi_"+address,x.rssi).apply();''','bt persist detail')
bt_history=r'''    public JSONObject historyPage(int limit){List<Map.Entry<String,Long>> rows=new ArrayList<>(history.entrySet());rows.sort((a,b)->Long.compare(b.getValue(),a.getValue()));JSONArray a=new JSONArray();int max=Math.max(1,Math.min(8,limit));for(int i=0;i<Math.min(max,rows.size());i++){Map.Entry<String,Long> e=rows.get(i);JSONObject d=new JSONObject();try{d.put("a",e.getKey());d.put("n",prefs.getString("name_"+e.getKey(),"UNKNOWN DEVICE"));d.put("type",prefs.getString("type_"+e.getKey(),"UNKNOWN"));d.put("r",prefs.getInt("rssi_"+e.getKey(),-127));d.put("ts",e.getValue());d.put("t",prefs.getBoolean("trusted_"+e.getKey(),false));a.put(d);}catch(Exception ignored){}}JSONObject o=new JSONObject();try{o.put("count",a.length());o.put("items",a);}catch(Exception ignored){}return o;}
'''
ins(bt,'    public JSONObject setTrusted(String address,boolean trusted){',bt_history,'bt history API')

# ------------------------------------------------------------
# Advanced manager: settings, search, pin/hide, anchor suggestion
# ------------------------------------------------------------
mgr=JAVA/'FieldUpgradeManager.java'
rep(mgr,
'''return action.startsWith("WIFI_")||action.startsWith("BT_RECON_")||action.startsWith("FIELD_CONTEXT")''',
'''return action.startsWith("WIFI_")||action.startsWith("BT_RECON_")||action.startsWith("FIELD_SETTINGS")||action.startsWith("ANCHOR_SUGGESTION")||action.startsWith("FIELD_CONTEXT")''','manager new prefixes')
rep(mgr,
'''            case "WIFI_SIGNAL_HUNT": cb.done(true,"SIGNAL DIRECTION ESTIMATE",wifi.signalHunt(p.optString("bssid","")));return;\n            case "WIFI_SCAN_MODE":''',
'''            case "WIFI_SIGNAL_HUNT": cb.done(true,"SIGNAL DIRECTION ESTIMATE",wifi.signalHunt(p.optString("bssid","")));return;\n            case "WIFI_SEARCH": cb.done(true,"WI-FI SEARCH",wifi.search(p.optString("query",""),p.optInt("limit",6)));return;\n            case "WIFI_PIN": cb.done(true,"NETWORK PIN UPDATED",wifi.setPinned(p.optString("bssid",""),true));return;\n            case "WIFI_UNPIN": cb.done(true,"NETWORK PIN UPDATED",wifi.setPinned(p.optString("bssid",""),false));return;\n            case "WIFI_HIDE": cb.done(true,"NETWORK VISIBILITY UPDATED",wifi.setUserHidden(p.optString("bssid",""),true));return;\n            case "WIFI_SHOW": cb.done(true,"NETWORK VISIBILITY UPDATED",wifi.setUserHidden(p.optString("bssid",""),false));return;\n            case "WIFI_SCAN_MODE":''','manager wifi pro commands')
rep(mgr,
'''            case "BT_RECON_LIST": cb.done(true,"NEARBY DEVICES",bluetooth.page(p.optInt("page",0),4,p.optString("filter","ALL")));return;''',
'''            case "BT_RECON_LIST": cb.done(true,"NEARBY DEVICES",bluetooth.page(p.optInt("page",0),4,p.optString("filter","ALL")));return;\n            case "BT_RECON_HISTORY": cb.done(true,"DEVICE HISTORY",bluetooth.historyPage(p.optInt("limit",6)));return;''','manager bt history command')
rep(mgr,
'''            case "VOICE_MACRO_STATUS": cb.done(true,"VOICE MACRO ENGINE",voiceMacroStatus());return;''',
'''            case "VOICE_MACRO_STATUS": cb.done(true,"VOICE MACRO ENGINE",voiceMacroStatus());return;\n            case "FIELD_SETTINGS_STATUS": cb.done(true,"FIELD CORE SETTINGS",settingsStatus());return;\n            case "FIELD_SETTINGS_SET": cb.done(true,"FIELD CORE SETTINGS UPDATED",setSettings(p));return;\n            case "ANCHOR_SUGGESTION": cb.done(true,"ANCHOR SUGGESTION",anchorSuggestion(p));return;''','manager settings commands')
rep(mgr,
'''            case "EMERGENCY_ESCALATION_SET": cb.done(true,"ESCALATION LEVEL UPDATED",setEmergencyLevel(p.optInt("level",0),p.optString("reason","USER")));return;''',
'''            case "EMERGENCY_ESCALATION_SET": cb.done(true,"ESCALATION LEVEL UPDATED",setEmergencyLevel(p.optInt("level",0),p.optString("reason","USER")));return;\n            case "EMERGENCY_ESCALATION_EVENT": cb.done(true,"EMERGENCY EVENT REVIEWED",reviewEmergencyEvent(p));return;''','manager escalation event')

rep(mgr,
'''        int hour=java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);double speed=p.optDouble("speedKmh",-1);int battery=p.optInt("battery",-1);boolean emergency=p.optBoolean("emergency",false);boolean mission=prefs.getBoolean("mission_active",false);JSONObject ws=wifi.summary();int trusted=ws.optInt("trusted",0);String mode="OUTDOOR";String movement="UNKNOWN";int evidence=1;''',
'''        int hour=java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);double speed=p.optDouble("speedKmh",-1);int battery=p.optInt("battery",-1);boolean emergency=p.optBoolean("emergency",false);boolean mission=prefs.getBoolean("mission_active",false);JSONObject ws=wifi.summary(),bs=bluetooth.summary();int trusted=ws.optInt("trusted",0),knownDevices=bs.optInt("trusted",0);String mode="OUTDOOR";String movement="UNKNOWN";int evidence=1;if(p.optBoolean("gpsAvailable",false))evidence++;if(p.has("heartRate")&&!"--".equals(p.optString("heartRate")))evidence++;if(!"NO DATA".equalsIgnoreCase(p.optString("weatherState","NO DATA")))evidence++;if(knownDevices>0)evidence++;''','context more evidence')
rep(mgr,
'''o.put("wifiEvidence",trusted>0?"TRUSTED NETWORK SEEN":"NO TRUST SIGNAL");o.put("note","WI-FI IS SUPPORTING EVIDENCE ONLY");''',
'''o.put("wifiEvidence",trusted>0?"TRUSTED NETWORK SEEN":"NO TRUST SIGNAL");o.put("deviceEvidence",knownDevices>0?"TRUSTED DEVICE SEEN":"NO TRUSTED DEVICE");o.put("note","WI-FI / BLUETOOTH ARE SUPPORTING EVIDENCE ONLY");''','context evidence note')

rep(mgr,
'''o.put("map",p.optString("map","NOT CACHED"));prefs.edit().putString("mission_pack",o.toString()).apply();''',
'''o.put("map",p.optString("map","NOT CACHED"));o.put("checklist",p.optJSONArray("checklist")!=null?p.optJSONArray("checklist"):new JSONArray());o.put("emergencyContact",trim(p.optString("emergencyContact",""),80));o.put("phoneNumbers",p.optJSONArray("phoneNumbers")!=null?p.optJSONArray("phoneNumbers"):new JSONArray());o.put("compassBearing",p.has("compassBearing")?p.opt("compassBearing"):"UNAVAILABLE");o.put("qrText",trim(p.optString("qrText",""),160));o.put("trustedNetworks",p.optJSONArray("trustedNetworks")!=null?p.optJSONArray("trustedNetworks"):new JSONArray());prefs.edit().putString("mission_pack",o.toString()).apply();''','mission pack extended fields')

manager_extra=r'''    private JSONObject settingsStatus(){JSONObject o=new JSONObject();try{o.put("autoContext",prefs.getBoolean("auto_context",true));o.put("haptics",prefs.getBoolean("haptic_alerts",true));o.put("voiceMacros",prefs.getBoolean("voice_macros",true));o.put("notificationFilter",prefs.getString("notification_mode","FIELD"));o.put("wifiScan",wifi.getMode());o.put("deviceRecon",prefs.getString("device_recon_mode","BALANCED"));o.put("attachLocation",prefs.getBoolean("wifi_attach_location",false));o.put("locationHistory",prefs.getBoolean("location_history",false));o.put("reduceMotion",prefs.getBoolean("reduce_motion",false));o.put("cloudSync","OFF");}catch(Exception ignored){}return o;}
    private JSONObject setSettings(JSONObject p){SharedPreferences.Editor e=prefs.edit();if(p.has("autoContext"))e.putBoolean("auto_context",p.optBoolean("autoContext",true));if(p.has("haptics"))e.putBoolean("haptic_alerts",p.optBoolean("haptics",true));if(p.has("voiceMacros"))e.putBoolean("voice_macros",p.optBoolean("voiceMacros",true));if(p.has("attachLocation"))e.putBoolean("wifi_attach_location",p.optBoolean("attachLocation",false));if(p.has("locationHistory"))e.putBoolean("location_history",p.optBoolean("locationHistory",false));if(p.has("reduceMotion"))e.putBoolean("reduce_motion",p.optBoolean("reduceMotion",false));if(p.has("deviceRecon"))e.putString("device_recon_mode",p.optString("deviceRecon","BALANCED"));e.apply();if(p.has("wifiScan"))wifi.setMode(p.optString("wifiScan",WifiScoutManager.MODE_BALANCED));if(p.has("notificationFilter"))setNotificationMode(p.optString("notificationFilter","FIELD"));events.emit("SETTINGS_CHANGED","SYSTEM","P3","FIELD SETTINGS UPDATED",null);return settingsStatus();}
    private JSONObject anchorSuggestion(JSONObject p){double before=p.optDouble("previousSpeedKmh",-1),now=p.optDouble("speedKmh",-1);JSONObject o=new JSONObject();try{boolean candidate=before>=15&&now>=0&&now<2;o.put("suggest",candidate);o.put("type",candidate?"CAR":"NONE");o.put("message",candidate?"POSSIBLE PARKING LOCATION • ASK USER":"NO ANCHOR SUGGESTION");o.put("autoSaved",false);}catch(Exception ignored){}return o;}
    private JSONObject reviewEmergencyEvent(JSONObject p){double confidence=p.optDouble("confidence",0);boolean auto=prefs.getBoolean("emergency_auto",false);int level=confidence>=.90&&auto?2:1;String reason=p.optString("type","EVENT");JSONObject o=setEmergencyLevel(level,reason);try{o.put("confirmationRequired",true);o.put("autoSos",false);o.put("confidence",confidence);o.put("note","SOS REQUIRES USER CONFIRMATION UNLESS EXPLICIT AUTO POLICY IS ENABLED");}catch(Exception ignored){}return o;}
    public boolean hapticAlertsEnabled(){return prefs.getBoolean("haptic_alerts",true);}
'''
ins(mgr,'    private JSONObject timeline(String filter,int limit){',manager_extra,'manager settings/helpers')

# --------------------------------------
# Alert haptics: P2 gets two short pulses
# --------------------------------------
main=JAVA/'MainActivity.java'
rep(main,'import android.os.Build;\nimport android.os.Bundle;',
'''import android.os.Build;\nimport android.os.Bundle;\nimport android.os.Handler;\nimport android.os.Looper;''','main handler imports')
rep(main,
'''    private String pendingVoiceRequestId="";''',
'''    private String pendingVoiceRequestId="";\n    private final Handler alertHandler=new Handler(Looper.getMainLooper());''','main alert handler')
rep(main,
'''        if(upgrades==null||event==null||!upgrades.shouldSurface(event))return;\n        try{\n            String priority=event.optString("priority","P3");String pattern="P1".equals(priority)?"long":("P2".equals(priority)?"short":"short");\n            JSONObject h=new JSONObject();h.put("v",1);h.put("type","haptic");h.put("pattern",pattern);h.put("message",event.optString("message",event.optString("type","FIELD EVENT")));wear.sendJson(h.toString());\n        }catch(Exception ignored){}''',
'''        if(upgrades==null||event==null||!upgrades.shouldSurface(event)||!upgrades.hapticAlertsEnabled())return;\n        try{\n            String priority=event.optString("priority","P3");String pattern="P1".equals(priority)?"long":"short";\n            JSONObject h=new JSONObject();h.put("v",1);h.put("type","haptic");h.put("pattern",pattern);h.put("message",event.optString("message",event.optString("type","FIELD EVENT")));final String wire=h.toString();wear.sendJson(wire);if("P2".equals(priority))alertHandler.postDelayed(()->wear.sendJson(wire),260L);\n        }catch(Exception ignored){}''','alert haptic patterns')

# --------------------------------------------------
# Watch runtime: richer real snapshot + controls
# --------------------------------------------------
js=WATCH/'index.js'
rep(js,
'''contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD'\n''',
'''contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD',stealthMode:false,fieldSettings:'--'\n''','watch phase2 state')
rep(js,
'''if(action==='QUICK_PROFILE_STATUS'||action==='QUICK_PROFILE_SET'){this.quickProfile=String(this.pick(d,'profile',this.quickProfile));}\n    if(action==='NOTIFICATION_FILTER_STATUS'||action==='NOTIFICATION_FILTER_SET'){this.notificationMode=String(this.pick(d,'mode',this.notificationMode));}''',
'''if(action==='QUICK_PROFILE_STATUS'||action==='QUICK_PROFILE_SET'){this.quickProfile=String(this.pick(d,'profile',this.quickProfile));var pp=String(this.pick(d,'power','AUTO'));if(pp==='ENDURANCE')this.applyPowerProfileInternal('ENDURANCE',false);else if(pp==='AUTO')this.enableAutoPower();}\n    if(action==='STEALTH_STATUS'||action==='STEALTH_SET'){this.stealthMode=!!this.pick(d,'enabled',this.stealthMode);}\n    if(action==='FIELD_SETTINGS_STATUS'||action==='FIELD_SETTINGS_SET'){this.fieldSettings=this.compactAdvanced(d);this.notificationMode=String(this.pick(d,'notificationFilter',this.notificationMode));}\n    if(action==='NOTIFICATION_FILTER_STATUS'||action==='NOTIFICATION_FILTER_SET'){this.notificationMode=String(this.pick(d,'mode',this.notificationMode));}''','watch phase2 result state')
rep(js,
'''advancedPayload(extra){var p={battery:this.watchBattery,heartRate:this.heartRate,speedKmh:this.speedKmh,altitude:this.altitude,gpsState:this.gpsState,gpsAvailable:!!this.lastLocation,gpsAccuracyM:this.lastLocation&&this.lastLocation.accuracy?Number(this.lastLocation.accuracy):null,gpsAgeMs:this.lastLocation?Date.now()-Number(this.lastLocation.ts||0):null,hrAvailable:this.hrSubscribed,compassAvailable:this.compassActive,barometerAvailable:this.barometerActive,motionAvailable:this.motionArmed,emergency:this.emergencyCountdown>0||this.impactPending,returnAvailable:this.breadcrumbRoute.length>0,missionMinutes:0};var k;if(extra)for(k in extra)if(extra.hasOwnProperty(k))p[k]=extra[k];return p;},''',
'''advancedPayload(extra){var p={battery:this.watchBattery,heartRate:this.heartRate,speedKmh:this.speedKmh,altitude:this.altitude,gpsState:this.gpsState,gpsAvailable:!!this.lastLocation,gpsAccuracyM:this.lastLocation&&this.lastLocation.accuracy?Number(this.lastLocation.accuracy):null,gpsAgeMs:this.lastLocation?Date.now()-Number(this.lastLocation.ts||0):null,hrAvailable:this.hrSubscribed,compassAvailable:this.compassActive,barometerAvailable:this.barometerActive,motionAvailable:this.motionArmed,emergency:this.emergencyCountdown>0||this.impactPending,returnAvailable:this.breadcrumbRoute.length>0,missionMinutes:0,weatherState:this.weatherState};if(this.lastLocation&&this.breadcrumbRoute.length){var rs=routeStats(this.lastLocation,this.breadcrumbRoute,(function(self){return function(a,b){return self.distanceM(a,b);};})(this),(function(self){return function(a,b){return self.bearingDeg(a,b);};})(this));if(rs){p.returnDistanceM=rs.distanceToBaseM;p.returnEtaMin=rs.etaMin;}}var k;if(extra)for(k in extra)if(extra.hasOwnProperty(k))p[k]=extra[k];return p;},''','watch route decision payload')
rep(js,
'''advEnvRisk(){var temp=finite(this.weatherTemp),uv=String(this.weatherUV||'').replace(/[^0-9.]/g,'');this.openAdvanced('ENVIRONMENT RISK','DECISION SUPPORT','ENV_RISK_STATUS',{temperatureC:temp,uv:finite(uv),altitudeM:this.lastLocation&&finite(this.lastLocation.altitude)!==null?Number(this.lastLocation.altitude):null});},''',
'''advEnvRisk(){var temp=String(this.weatherTemp||'').replace(/[^0-9.-]/g,''),uv=String(this.weatherUV||'').replace(/[^0-9.]/g,'');this.openAdvanced('ENVIRONMENT RISK','DECISION SUPPORT','ENV_RISK_STATUS',{temperatureC:finite(temp),uv:finite(uv),altitudeM:this.lastLocation&&finite(this.lastLocation.altitude)!==null?Number(this.lastLocation.altitude):null});},''','watch env numeric parsing')

watch_controls=r'''  advSettings(){this.openAdvanced('FIELD CORE SETTINGS','PRIVACY / POWER / ALERTS','FIELD_SETTINGS_STATUS');},
  advStealthOn(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:true});},
  advStealthOff(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:false});},
  advProfileDaily(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'DAILY'});},
  advProfileOutdoor(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'OUTDOOR'});},
  advProfileRunning(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'RUNNING'});},
  advProfileNight(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'NIGHT'});},
  advMissionStart(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_START');},advMissionStop(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_STOP');},
  advLostStart(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');},advLostStop(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STOP');},
  advNotifyField(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'FIELD'});},advNotifyMission(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'MISSION'});},advNotifyStealth(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'STEALTH'});},
  advEmergencyLevel0(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:0,reason:'USER'});},advEmergencyLevel1(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:1,reason:'USER CHECK'});},advEmergencyLevel2(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:2,reason:'USER WARNING'});},advEmergencyLevel3(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:3,reason:'USER SOS'});},
  advBtHistory(){this.openAdvanced('DEVICE HISTORY','LOCAL BLE HISTORY','BT_RECON_HISTORY',{limit:6});},
  advWifiSignal(){this.openAdvanced('SIGNAL HUNT','RSSI TREND • NOT DIRECTION','WIFI_SIGNAL_HUNT');},
  advWifiDuplicates(){this.openAdvanced('DUPLICATE SSID','CHECK BEFORE CONNECTING','WIFI_DUPLICATES');},
'''
ins(js,'  advWifiScan(){',watch_controls,'watch advanced controls')

rep(js,
'''  onImpactPending(){this.impactPending=true;this.logEvent('SOS','HIGH IMPACT / STILLNESS');this.startEmergencyCountdown('IMPACT');},''',
'''  onImpactPending(){this.impactPending=true;this.logEvent('SOS','HIGH IMPACT / STILLNESS');this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:'HIGH',movementAfter:'LOW',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'PENDING'});this.sendCommand('EMERGENCY_ESCALATION_EVENT',{type:'IMPACT',confidence:0.90});this.startEmergencyCountdown('IMPACT');},''','impact snapshot integration')
rep(js,
'''this.view='detail';this.message='EMERGENCY CANCELED';this.logEvent('SOS','CANCELED');},''',
'''this.view='detail';this.message='EMERGENCY CANCELED';this.logEvent('SOS','CANCELED');this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:'EVENT',movementAfter:'AVAILABLE',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'I AM OK'});this.sendCommand('EMERGENCY_ESCALATION_SET',{level:0,reason:'USER OK'});},''','impact cancel integration')
rep(js,
'''this.message='SOS LOCATION SENDING';this.logEvent('SOS',reason+' TRIGGER');this.sendCommand('EMERGENCY_SEND',{reason:reason,battery:this.watchBattery});this.haptic('long');},''',
'''this.message='SOS LOCATION SENDING';this.logEvent('SOS',reason+' TRIGGER');this.sendCommand('EMERGENCY_ESCALATION_SET',{level:3,reason:reason});this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:reason,movementAfter:'UNAVAILABLE',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'SOS'});this.sendCommand('EMERGENCY_SEND',{reason:reason,battery:this.watchBattery});this.haptic('long');},''','impact sos integration')
rep(js,
'''if(changed||user){this.message='POWER '+p;this.logEvent('POWER',(this.powerAuto?'AUTO ':'')+p);if(user)this.haptic('short');}},''',
'''if(changed||user){this.message='POWER '+p;this.logEvent('POWER',(this.powerAuto?'AUTO ':'')+p);var sm=p==='PERFORMANCE'?'ACTIVE':((p==='ENDURANCE'||p==='GRID')?'BATTERY_SAVER':'BALANCED');if(this.connectionState==='CONNECTED')this.sendCommand('WIFI_SCAN_MODE',{mode:sm});if(user)this.haptic('short');}},''','power commander recon coupling')

# --------------------------------------------------
# HML controls: settings, Wi-Fi signal/duplicate, mode actions
# --------------------------------------------------
hml=WATCH/'index.hml'
rep(hml,
'''      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="WI-FI SCOUT / CYBER SWEEP" onclick="openWifiScout"/><text class="advanced-source">RECON</text></list-item>''',
'''      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="WI-FI SCOUT / CYBER SWEEP" onclick="openWifiScout"/><text class="advanced-source">RECON</text></list-item>\n      <list-item class="advanced-row"><input type="button" class="advanced-btn" value="FIELD CORE SETTINGS" onclick="advSettings"/><text class="advanced-source">PRIVACY</text></list-item>''','advanced settings row')
rep(hml,
'''      <div class="wifi-row"><input type="button" class="wifi-btn" value="BT RECON" onclick="advBtScan"/><input type="button" class="wifi-btn" value="DUPLICATE" onclick="advWifiNetworks"/><input type="button" class="wifi-btn" value="STATUS" onclick="openWifiScout"/></div>''',
'''      <div class="wifi-row"><input type="button" class="wifi-btn" value="BT RECON" onclick="advBtScan"/><input type="button" class="wifi-btn" value="SIGNAL HUNT" onclick="advWifiSignal"/><input type="button" class="wifi-btn" value="DUPLICATE" onclick="advWifiDuplicates"/></div>''','wifi signal duplicate actions')
rep(hml,
'''    <div class="detail-extra"><input type="button" class="mini-extra active-state" value="REFRESH" onclick="advancedRefresh"/><input type="button" class="mini-extra" value="ADVANCED HUB" onclick="openAdvancedHub"/></div>\n  </div>''',
'''    <div class="detail-extra"><input type="button" class="mini-extra active-state" value="REFRESH" onclick="advancedRefresh"/><input type="button" class="mini-extra" value="ADVANCED HUB" onclick="openAdvancedHub"/></div>\n    <div if="{{advancedTitle == 'NIGHT / STEALTH HUD'}}" class="detail-extra"><input type="button" class="mini-extra" value="ENABLE" onclick="advStealthOn"/><input type="button" class="mini-extra" value="DISABLE" onclick="advStealthOff"/></div>\n    <div if="{{advancedTitle == 'FIELD QUICK PROFILES'}}" class="profile-row"><input type="button" class="profile-btn" value="DAILY" onclick="advProfileDaily"/><input type="button" class="profile-btn" value="OUTDOOR" onclick="advProfileOutdoor"/><input type="button" class="profile-btn" value="RUNNING" onclick="advProfileRunning"/><input type="button" class="profile-btn" value="NIGHT" onclick="advProfileNight"/></div>\n    <div if="{{advancedTitle == 'MISSION PACK'}}" class="detail-extra"><input type="button" class="mini-extra" value="MISSION START" onclick="advMissionStart"/><input type="button" class="mini-extra" value="MISSION STOP" onclick="advMissionStop"/></div>\n    <div if="{{advancedTitle == 'LOST MODE PRO'}}" class="detail-extra"><input type="button" class="mini-extra" value="START LOST" onclick="advLostStart"/><input type="button" class="mini-extra" value="STOP LOST" onclick="advLostStop"/></div>\n    <div if="{{advancedTitle == 'FIELD NOTIFICATION FILTER'}}" class="profile-row"><input type="button" class="profile-btn" value="FIELD" onclick="advNotifyField"/><input type="button" class="profile-btn" value="MISSION" onclick="advNotifyMission"/><input type="button" class="profile-btn" value="STEALTH" onclick="advNotifyStealth"/></div>\n    <div if="{{advancedTitle == 'NEARBY DEVICE RECON'}}" class="detail-extra"><input type="button" class="mini-extra" value="SCAN" onclick="advBtScan"/><input type="button" class="mini-extra" value="HISTORY" onclick="advBtHistory"/></div>\n    <div if="{{advancedTitle == 'EMERGENCY ESCALATION'}}" class="profile-row"><input type="button" class="profile-btn" value="L0" onclick="advEmergencyLevel0"/><input type="button" class="profile-btn" value="L1" onclick="advEmergencyLevel1"/><input type="button" class="profile-btn" value="L2" onclick="advEmergencyLevel2"/><input type="button" class="profile-btn danger-btn" value="L3" onclick="advEmergencyLevel3"/></div>\n  </div>''','advanced mode controls')
rep(hml,
'''<div class="favorite-label"><text class="section-lbl">● FIELD QUICK ACTIONS</text><text class="mini-state">{{powerLabel}}</text></div>''',
'''<div class="favorite-label"><text class="section-lbl">● FIELD QUICK ACTIONS</text><text class="mini-state">{{powerLabel}} • WIFI {{wifiCount}}</text></div>''','home wifi widget')

css=WATCH/'index.css'
phase2_css=r'''
.profile-row{width:452px;height:31px;flex-direction:row;justify-content:space-between;margin-top:3px;}.profile-btn{width:109px;height:29px;border-radius:8px;border-width:1px;border-color:#12343d;background-color:#010507;color:#9aa4aa;font-size:6px;}
'''
ins(css,'@keyframes scanMove',phase2_css,'phase2 css')

# Preflight phase 2 tokens
pre=BASE/'tools'/'preflight.py'
phase2_pre=r'''
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
'''
ins(pre,'# Both transport directions must enforce <=1 KB P2P messages.',phase2_pre,'phase2 preflight')

print('FIELD CORE ADVANCED PHASE 2 PATCH COMPLETE')
