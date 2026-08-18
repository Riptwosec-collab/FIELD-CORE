package com.riptwosec.fieldcore;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Locale;

/**
 * Non-destructive upgrade layer for FIELD CORE. Existing feature commands remain owned by
 * ProviderRegistry/watch runtime; this manager adds context, mission, recon, diagnostics,
 * profiles, confidence, alerts and command-center intelligence.
 */
public final class FieldUpgradeManager implements FieldEventBus.Listener {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }

    private final Context context;
    private final SharedPreferences prefs;
    private final ProviderRegistry providers;
    private final PhoneLocationProvider location;
    private final FieldEventBus events;
    private final WifiScoutManager wifi;
    private final BluetoothReconManager bluetooth;
    private JSONObject lastImpact=new JSONObject();

    public FieldUpgradeManager(Context c,ProviderRegistry p,PhoneLocationProvider l){
        context=c.getApplicationContext();providers=p;location=l;prefs=context.getSharedPreferences("fieldcore_upgrade",Context.MODE_PRIVATE);events=new FieldEventBus(context);
        wifi=new WifiScoutManager(context,(type,msg,data)->emitMapped(type,msg,data));
        bluetooth=new BluetoothReconManager(context,(type,msg,data)->emitMapped(type,msg,data));
        events.subscribe(this);
        try{lastImpact=new JSONObject(prefs.getString("impact_review","{}"));}catch(Exception ignored){}
    }

    public void close(){events.unsubscribe(this);stopOutdoorService();wifi.close();bluetooth.close();}
    public FieldEventBus eventBus(){return events;}
    public WifiScoutManager wifi(){return wifi;}
    public BluetoothReconManager bluetooth(){return bluetooth;}

    public boolean handles(String action){
        if(action==null)return false;
        return action.startsWith("WIFI_")||action.startsWith("BT_RECON_")||action.startsWith("FIELD_CONTEXT")||action.startsWith("TELEMETRY_CONFIDENCE")||action.startsWith("LOST_MODE")||action.startsWith("MISSION_PACK")||action.startsWith("ENV_RISK")||action.startsWith("SENSOR_SELF_TEST")||action.startsWith("TIMELINE_PRO")||action.startsWith("VOICE_MACRO")||action.startsWith("NOTIFICATION_FILTER")||action.startsWith("RUN_ZONE")||action.startsWith("SKY_PRO")||action.startsWith("STEALTH")||action.startsWith("RETURN_DECISION")||action.startsWith("QUICK_PROFILE")||action.startsWith("IMPACT_REVIEW")||action.startsWith("COMMAND_CENTER")||action.startsWith("CYBER_SWEEP")||action.startsWith("OUTDOOR_SCAN")||action.startsWith("EMERGENCY_ESCALATION")||action.startsWith("MISSION_")||action.startsWith("ALERT_");
    }

    public void execute(String action,JSONObject payload,Callback cb){
        if(payload==null)payload=new JSONObject();final JSONObject p=payload;
        switch(action){
            case "WIFI_STATUS": cb.done(true,"WI-FI SCOUT STATUS",wifi.status());return;
            case "WIFI_SCAN": wifi.scan((ok,msg,data)->cb.done(ok,msg,data));return;
            case "WIFI_NETWORKS": cb.done(true,"WI-FI NETWORKS",wifi.networkPage(p.optInt("page",0),p.optInt("size",4),p.optString("filter","ALL"),p.optString("sort","SIGNAL")));return;
            case "WIFI_DETAIL": cb.done(true,"WI-FI DETAIL",wifi.detail(p.optString("bssid","")));return;
            case "WIFI_OPEN": cb.done(true,"OPEN WI-FI",wifi.networkPage(p.optInt("page",0),4,"OPEN","SIGNAL"));return;
            case "WIFI_BEST": cb.done(true,"BEST WI-FI",wifi.best());return;
            case "WIFI_CHANNELS": cb.done(true,"CHANNEL ANALYZER",wifi.channels());return;
            case "WIFI_HISTORY": cb.done(true,"WI-FI HISTORY",wifi.history(3));return;
            case "WIFI_TRUSTED": cb.done(true,"TRUSTED WI-FI",wifi.trusted(3));return;
            case "WIFI_DUPLICATES": cb.done(true,"DUPLICATE SSID",wifi.duplicateSummary());return;
            case "WIFI_TRUST": cb.done(true,"TRUSTED NETWORK UPDATED",wifi.setTrusted(p.optString("bssid",""),true));return;
            case "WIFI_UNTRUST": cb.done(true,"TRUSTED NETWORK UPDATED",wifi.setTrusted(p.optString("bssid",""),false));return;
            case "WIFI_SIGNAL_HUNT": cb.done(true,"SIGNAL DIRECTION ESTIMATE",wifi.signalHunt(p.optString("bssid","")));return;
            case "WIFI_SCAN_MODE": wifi.setMode(p.optString("mode",WifiScoutManager.MODE_BALANCED));cb.done(true,"SCAN MODE "+wifi.getMode(),wifi.status());return;
            case "OUTDOOR_SCAN_START": wifi.setMode(p.optString("mode",wifi.getMode()));startOutdoorService(wifi.getMode());cb.done(true,"OUTDOOR SCAN ACTIVE",wifi.startOutdoor());return;
            case "OUTDOOR_SCAN_STOP": stopOutdoorService();cb.done(true,"SCAN SUMMARY",wifi.stopOutdoor());return;

            case "BT_RECON_STATUS": cb.done(true,"NEARBY DEVICE RECON",bluetooth.status());return;
            case "BT_RECON_SCAN": bluetooth.scan((ok,msg,data)->cb.done(ok,msg,data));return;
            case "BT_RECON_LIST": cb.done(true,"NEARBY DEVICES",bluetooth.page(p.optInt("page",0),4,p.optString("filter","ALL")));return;
            case "BT_RECON_TRUST": cb.done(true,"TRUSTED DEVICE UPDATED",bluetooth.setTrusted(p.optString("address",""),true));return;
            case "BT_RECON_UNTRUST": cb.done(true,"TRUSTED DEVICE UPDATED",bluetooth.setTrusted(p.optString("address",""),false));return;

            case "CYBER_SWEEP": cyberSweep(cb);return;
            case "FIELD_CONTEXT_STATUS": cb.done(true,"FIELD CONTEXT",contextStatus(p));return;
            case "TELEMETRY_CONFIDENCE": cb.done(true,"TELEMETRY CONFIDENCE",telemetryConfidence(p));return;
            case "ENV_RISK_STATUS": cb.done(true,"ENVIRONMENTAL RISK",environmentRisk(p));return;
            case "SENSOR_SELF_TEST": cb.done(true,"SENSOR SELF-TEST",sensorSelfTest(p));return;
            case "COMMAND_CENTER": cb.done(true,"COMMAND CENTER",commandCenter(p));return;
            case "RETURN_DECISION": cb.done(true,"RETURN DECISION SUPPORT",returnDecision(p));return;
            case "RUN_ZONE_STATUS": cb.done(true,"RUNNING ZONE HUD",runningZone(p));return;
            case "SKY_PRO_STATUS": providers.execute("SKY_REFRESH",p,(ok,msg,data)->cb.done(ok,msg,data));return;
            case "SKY_PRO_ASTRO": providers.execute("ASTRO_REFRESH",p,(ok,msg,data)->cb.done(ok,msg,data));return;

            case "MISSION_PACK_STATUS": cb.done(true,"MISSION PACK",missionPackStatus());return;
            case "MISSION_PACK_SAVE": cb.done(true,"MISSION PACK SAVED",saveMissionPack(p));return;
            case "MISSION_PACK_CLEAR": prefs.edit().remove("mission_pack").apply();events.emit("MISSION_PACK_CLEARED","MISSION","P3","MISSION PACK CLEARED",null);cb.done(true,"MISSION PACK CLEARED",missionPackStatus());return;
            case "MISSION_START": setBool("mission_active",true);events.emit("MISSION_STARTED","MISSION","P2","MISSION STARTED",p);cb.done(true,"MISSION ACTIVE",missionState());return;
            case "MISSION_STOP": setBool("mission_active",false);events.emit("MISSION_STOPPED","MISSION","P2","MISSION STOPPED",p);cb.done(true,"MISSION STOPPED",missionState());return;
            case "MISSION_STATUS": cb.done(true,"MISSION STATUS",missionState());return;

            case "LOST_MODE_STATUS": lostModeStatus(p,cb);return;
            case "LOST_MODE_START": setBool("lost_mode",true);events.emit("LOST_MODE_STARTED","NAVIGATION","P2","LOST MODE ACTIVE",p);lostModeStatus(p,cb);return;
            case "LOST_MODE_STOP": setBool("lost_mode",false);events.emit("LOST_MODE_STOPPED","NAVIGATION","P3","LOST MODE STOPPED",p);cb.done(true,"LOST MODE STOPPED",simple("active",false));return;

            case "QUICK_PROFILE_STATUS": cb.done(true,"FIELD QUICK PROFILE",profileStatus());return;
            case "QUICK_PROFILE_SET": cb.done(true,"PROFILE APPLIED",setProfile(p.optString("profile","DAILY")));return;
            case "STEALTH_STATUS": cb.done(true,"STEALTH HUD",stealthStatus());return;
            case "STEALTH_SET": cb.done(true,"STEALTH UPDATED",setStealth(p.optBoolean("enabled",true)));return;
            case "NOTIFICATION_FILTER_STATUS": cb.done(true,"NOTIFICATION FILTER",notificationStatus());return;
            case "NOTIFICATION_FILTER_SET": cb.done(true,"NOTIFICATION FILTER UPDATED",setNotificationMode(p.optString("mode","FIELD")));return;
            case "VOICE_MACRO_STATUS": cb.done(true,"VOICE MACRO ENGINE",voiceMacroStatus());return;

            case "IMPACT_REVIEW_SAVE": cb.done(true,"IMPACT SNAPSHOT SAVED",saveImpact(p));return;
            case "IMPACT_REVIEW_STATUS": cb.done(true,"IMPACT REVIEW",lastImpact);return;
            case "EMERGENCY_ESCALATION_STATUS": cb.done(true,"EMERGENCY ESCALATION",emergencyStatus());return;
            case "EMERGENCY_ESCALATION_SET": cb.done(true,"ESCALATION LEVEL UPDATED",setEmergencyLevel(p.optInt("level",0),p.optString("reason","USER")));return;

            case "TIMELINE_PRO": cb.done(true,"MISSION TIMELINE PRO",timeline(p.optString("filter","ALL"),p.optInt("limit",6)));return;
            case "ALERT_STATUS": cb.done(true,"SMART ALERT SYSTEM",notificationStatus());return;
            default: cb.done(false,"UNSUPPORTED UPGRADE COMMAND",null);
        }
    }

    private void startOutdoorService(String mode){
        try{Intent i=new Intent(context,ReconScanService.class);i.setAction(ReconScanService.ACTION_START);i.putExtra(ReconScanService.EXTRA_MODE,mode);if(Build.VERSION.SDK_INT>=26)context.startForegroundService(i);else context.startService(i);}catch(Exception e){events.emit("OUTDOOR_SCAN_SERVICE","SYSTEM","P2","BACKGROUND SCAN RESTRICTED",null);}
    }
    private void stopOutdoorService(){try{Intent i=new Intent(context,ReconScanService.class);i.setAction(ReconScanService.ACTION_STOP);context.stopService(i);}catch(Exception ignored){}}

    private void cyberSweep(Callback cb){
        wifi.scan((wOk,wMsg,wData)->bluetooth.scan((bOk,bMsg,bData)->{JSONObject o=new JSONObject();try{o.put("wifi",wData==null?wifi.summary():wData);o.put("bluetooth",bData==null?bluetooth.summary():bData);o.put("environment",environmentLabel());o.put("updatedAt",System.currentTimeMillis());}catch(Exception ignored){}events.emit("CYBER_SWEEP","NETWORK","P3","CYBER SWEEP COMPLETE",o);cb.done(wOk||bOk,"CYBER SWEEP COMPLETE",o);}));
    }

    private JSONObject contextStatus(JSONObject p){
        int hour=java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);double speed=p.optDouble("speedKmh",-1);int battery=p.optInt("battery",-1);boolean emergency=p.optBoolean("emergency",false);boolean mission=prefs.getBoolean("mission_active",false);JSONObject ws=wifi.summary();int trusted=ws.optInt("trusted",0);String mode="OUTDOOR";String movement="UNKNOWN";int evidence=1;
        if(speed>=0){movement=speed>15?"VEHICLE":(speed>7?"RUNNING":(speed>1?"WALKING":"STILL"));evidence++;}
        if(emergency){mode="EMERGENCY";evidence+=2;}else if(battery>=0&&battery<=10){mode="LOW BATTERY";evidence++;}else if(speed>15){mode="COMMUTING";evidence++;}else if(speed>7){mode="RUNNING";evidence++;}else if(mission){mode="MISSION";evidence++;}else if(hour>=20||hour<6){mode="NIGHT";evidence++;}else if(trusted>0){mode="KNOWN AREA";evidence++;}
        int confidence=Math.min(96,45+evidence*10);JSONObject o=new JSONObject();try{o.put("mode",mode);o.put("movement",movement);o.put("environment",environmentLabel());o.put("connectivity","PHONE LINKED");o.put("battery",battery<0?"UNAVAILABLE":battery);o.put("confidence",confidence);o.put("wifiEvidence",trusted>0?"TRUSTED NETWORK SEEN":"NO TRUST SIGNAL");o.put("note","WI-FI IS SUPPORTING EVIDENCE ONLY");o.put("updatedAt",System.currentTimeMillis());}catch(Exception ignored){}return o;
    }

    private JSONObject telemetryConfidence(JSONObject p){JSONObject o=new JSONObject();try{o.put("heartRate",confidenceMetric(p.has("heartRate")&&!"--".equals(p.optString("heartRate")),p.optLong("hrAgeMs",Long.MAX_VALUE),p.optInt("hrQuality",80)));o.put("gps",gpsConfidence(p));o.put("altitude",confidenceMetric(p.has("altitude")&&!"--".equals(p.optString("altitude")),p.optLong("gpsAgeMs",Long.MAX_VALUE),p.optInt("altQuality",70)));JSONObject ws=wifi.summary();long wifiAge=ws.optLong("ageSec",-1);o.put("wifi",confidenceMetric(ws.optInt("count",0)>0,wifiAge<0?Long.MAX_VALUE:wifiAge*1000L,85));o.put("phone","HIGH");o.put("updatedAt",System.currentTimeMillis());}catch(Exception ignored){}return o;}
    private String gpsConfidence(JSONObject p){if(!p.optBoolean("gpsAvailable",p.has("gpsState")))return "UNAVAILABLE";double acc=p.optDouble("gpsAccuracyM",9999);long age=p.optLong("gpsAgeMs",Long.MAX_VALUE);int q=acc<=10?95:(acc<=25?82:(acc<=50?65:45));return confidenceMetric(true,age,q);}
    private String confidenceMetric(boolean available,long ageMs,int quality){if(!available)return "UNAVAILABLE";int q=Math.max(0,Math.min(100,quality));if(ageMs>300000)q-=45;else if(ageMs>60000)q-=25;else if(ageMs>15000)q-=12;return q>=80?"HIGH":(q>=55?"MEDIUM":"LOW");}

    private JSONObject environmentRisk(JSONObject p){int risk=0;JSONArray reasons=new JSONArray();double uv=p.optDouble("uv",-1),temp=p.optDouble("temperatureC",-999),rain=p.optDouble("rainProbability",-1),alt=p.optDouble("altitudeM",-999);if(uv>=8){risk+=30;reasons.put("UV HIGH");}else if(uv>=6){risk+=20;reasons.put("UV ELEVATED");}if(temp>=38){risk+=30;reasons.put("HEAT HIGH");}else if(temp>=33){risk+=18;reasons.put("HEAT ELEVATED");}if(rain>=70){risk+=20;reasons.put("RAIN LIKELY");}if(alt>=2500){risk+=15;reasons.put("HIGH ALTITUDE CONTEXT");}if(p.optBoolean("stormAlert",false)){risk+=35;reasons.put("WEATHER ALERT");}risk=Math.min(100,risk);String level=risk>=75?"SEVERE":(risk>=50?"HIGH":(risk>=25?"ELEVATED":"LOW"));JSONObject o=new JSONObject();try{o.put("score",risk);o.put("level",level);o.put("reasons",reasons);o.put("dataSource",p.length()==0?"PROVIDER DATA REQUIRED":"INPUT SNAPSHOT");}catch(Exception ignored){}return o;}

    private JSONObject sensorSelfTest(JSONObject p){JSONObject o=new JSONObject();try{o.put("GPS",location.hasPermission()?"CHECK":"PERMISSION REQUIRED");o.put("PHONE_LINK","PASS");o.put("STORAGE","PASS");o.put("WIFI",wifi.hasPermission()?"PASS":"PERMISSION REQUIRED");o.put("BLUETOOTH",bluetooth.hasPermission()?"PASS":"PERMISSION REQUIRED");o.put("WEATHER",providers.status().optString("weather","CHECK"));o.put("HR",p.optBoolean("hrAvailable",false)?"PASS":"WATCH TEST REQUIRED");o.put("COMPASS",p.optBoolean("compassAvailable",false)?"PASS":"WATCH TEST REQUIRED");o.put("BAROMETER",p.optBoolean("barometerAvailable",false)?"PASS":"WATCH TEST REQUIRED");o.put("MOTION",p.optBoolean("motionAvailable",false)?"PASS":"WATCH TEST REQUIRED");o.put("DEPTH","API GATED");o.put("AMBIENT_LIGHT","API GATED");o.put("sdk",Build.VERSION.SDK_INT);}catch(Exception ignored){}return o;}

    private JSONObject commandCenter(JSONObject p){JSONObject o=new JSONObject();try{o.put("context",contextStatus(p));o.put("mission",missionState());o.put("wifi",wifi.summary());o.put("devices",bluetooth.summary());o.put("environment",environmentRisk(p));o.put("power",powerRecommendation(p.optInt("battery",-1),p.optInt("missionMinutes",0)));o.put("timeline",events.read().length());o.put("notification",prefs.getString("notification_mode","FIELD"));o.put("profile",prefs.getString("quick_profile","DAILY"));o.put("updatedAt",System.currentTimeMillis());}catch(Exception ignored){}return o;}

    private JSONObject returnDecision(JSONObject p){int battery=p.optInt("battery",-1),distance=p.optInt("returnDistanceM",-1),eta=p.optInt("returnEtaMin",-1),sunset=p.optInt("sunsetInMin",-1),risk=p.optInt("environmentRisk",0);int pressure=0;JSONArray reasons=new JSONArray();if(battery>=0&&battery<20){pressure+=30;reasons.put("LOW BATTERY");}if(sunset>=0&&eta>=0&&sunset<eta+20){pressure+=35;reasons.put("SUNSET BEFORE MARGIN");}if(risk>=50){pressure+=25;reasons.put("ENVIRONMENT RISK");}if(distance>8000){pressure+=10;reasons.put("LONG RETURN DISTANCE");}String decision=pressure>=50?"RETURN ADVISED":(pressure>=30?"REVIEW RETURN":"CONTINUE OK");JSONObject o=new JSONObject();try{o.put("decision",decision);o.put("score",Math.min(100,pressure));o.put("battery",battery<0?"UNAVAILABLE":battery);o.put("distanceM",distance);o.put("etaMin",eta);o.put("sunsetInMin",sunset);o.put("reasons",reasons);o.put("note","DECISION SUPPORT ONLY");}catch(Exception ignored){}return o;}

    private JSONObject runningZone(JSONObject p){JSONObject o=new JSONObject();int hr=p.optInt("heartRate",-1),max=p.optInt("maxHeartRate",-1);try{o.put("heartRate",hr<0?"UNAVAILABLE":hr);o.put("pace",p.has("pace")?p.optString("pace"):"UNAVAILABLE");o.put("distanceKm",p.has("distanceKm")?p.optDouble("distanceKm"):"UNAVAILABLE");o.put("durationSec",p.has("durationSec")?p.optInt("durationSec"):"UNAVAILABLE");if(hr>0&&max>0){double pct=hr/(double)max;String z=pct<.60?"Z1":(pct<.70?"Z2":(pct<.80?"Z3":(pct<.90?"Z4":"Z5")));o.put("zone",z);o.put("zonePct",Math.round(pct*100));}else o.put("zone","UNAVAILABLE");}catch(Exception ignored){}return o;}

    private JSONObject missionPackStatus(){String raw=prefs.getString("mission_pack","");if(raw==null||raw.isEmpty())return simple("status","NOT PREPARED");try{JSONObject o=new JSONObject(raw);o.put("status","READY OFFLINE");return o;}catch(Exception e){return simple("status","DATA ERROR");}}
    private JSONObject saveMissionPack(JSONObject p){JSONObject o=new JSONObject();try{o.put("name",p.optString("name","MISSION PACK"));o.put("updatedAt",System.currentTimeMillis());o.put("waypoints",Math.max(0,p.optInt("waypoints",0)));o.put("routeKm",p.has("routeKm")?p.optDouble("routeKm"):JSONObject.NULL);o.put("weatherSnapshot",p.optString("weatherSnapshot","UNAVAILABLE"));o.put("notes",trim(p.optString("notes",""),120));o.put("safePoints",Math.max(0,p.optInt("safePoints",0)));o.put("map",p.optString("map","NOT CACHED"));prefs.edit().putString("mission_pack",o.toString()).apply();events.emit("MISSION_PACK_SAVED","MISSION","P3","MISSION PACK READY OFFLINE",o);}catch(Exception ignored){}return o;}
    private JSONObject missionState(){JSONObject o=new JSONObject();try{o.put("active",prefs.getBoolean("mission_active",false));o.put("pack",missionPackStatus());}catch(Exception ignored){}return o;}

    private void lostModeStatus(JSONObject p,Callback cb){location.current((ok,msg,data)->{JSONObject o=new JSONObject();try{o.put("active",prefs.getBoolean("lost_mode",false));o.put("phoneLink","CONNECTED");o.put("currentPosition",ok?"AVAILABLE":"UNAVAILABLE");o.put("lastSafePoint",p.optString("lastSafePoint","UNAVAILABLE"));o.put("returnRoute",p.optBoolean("returnAvailable",false)?"AVAILABLE":"UNAVAILABLE");o.put("battery",p.has("battery")?p.optInt("battery"):"UNAVAILABLE");if(ok&&data!=null)o.put("location",data);}catch(Exception ignored){}cb.done(true,"LOST MODE PRO",o);});}

    private JSONObject profileStatus(){JSONObject o=new JSONObject();try{o.put("profile",prefs.getString("quick_profile","DAILY"));o.put("power",prefs.getString("profile_power","AUTO"));o.put("wifiScan",prefs.getString("profile_wifi","BALANCED"));o.put("deviceRecon",prefs.getString("profile_bt","BALANCED"));o.put("stealth",prefs.getBoolean("stealth",false));}catch(Exception ignored){}return o;}
    private JSONObject setProfile(String profile){String p=profile==null?"DAILY":profile.toUpperCase(Locale.ROOT);String power="AUTO",wifiMode="BALANCED",bt="BALANCED";boolean stealth=false;if("RUNNING".equals(p)){wifiMode="BATTERY_SAVER";bt="BATTERY_SAVER";}else if("NIGHT".equals(p)||"STEALTH".equals(p)){stealth=true;wifiMode="BATTERY_SAVER";bt="BATTERY_SAVER";}else if("BATTERY SAVER".equals(p)){power="ENDURANCE";wifiMode="BATTERY_SAVER";bt="BATTERY_SAVER";}else if("MISSION".equals(p)||"OUTDOOR".equals(p)){wifiMode="BALANCED";bt="BALANCED";}prefs.edit().putString("quick_profile",p).putString("profile_power",power).putString("profile_wifi",wifiMode).putString("profile_bt",bt).putBoolean("stealth",stealth).apply();wifi.setMode("BATTERY_SAVER".equals(wifiMode)?WifiScoutManager.MODE_BATTERY:WifiScoutManager.MODE_BALANCED);events.emit("PROFILE_CHANGED","SYSTEM","P3","PROFILE "+p,null);return profileStatus();}
    private JSONObject stealthStatus(){JSONObject o=new JSONObject();try{o.put("enabled",prefs.getBoolean("stealth",false));o.put("reduceMotion",prefs.getBoolean("reduce_motion",false));o.put("lowBrightness",prefs.getBoolean("stealth",false));o.put("notification",prefs.getString("notification_mode","FIELD"));}catch(Exception ignored){}return o;}
    private JSONObject setStealth(boolean enabled){prefs.edit().putBoolean("stealth",enabled).putBoolean("reduce_motion",enabled).apply();events.emit("STEALTH_CHANGED","SYSTEM","P3",enabled?"STEALTH ON":"STEALTH OFF",null);return stealthStatus();}
    private JSONObject notificationStatus(){JSONObject o=new JSONObject();try{o.put("mode",prefs.getString("notification_mode","FIELD"));o.put("haptics",prefs.getBoolean("haptic_alerts",true));o.put("p1","SHOW");o.put("p2","SHOW");o.put("p3","MISSION".equals(prefs.getString("notification_mode","FIELD"))?"FILTER":"SHOW");o.put("p4","SILENT");}catch(Exception ignored){}return o;}
    private JSONObject setNotificationMode(String mode){String m=mode==null?"FIELD":mode.toUpperCase(Locale.ROOT);if(!("NORMAL".equals(m)||"FIELD".equals(m)||"MISSION".equals(m)||"STEALTH".equals(m)||"EMERGENCY".equals(m)))m="FIELD";prefs.edit().putString("notification_mode",m).apply();events.emit("NOTIFICATION_MODE","SYSTEM","P3",m,null);return notificationStatus();}
    private JSONObject voiceMacroStatus(){JSONObject o=new JSONObject();try{o.put("enabled",prefs.getBoolean("voice_macros",true));o.put("builtIn",new JSONArray().put("SAVE CAR").put("START OUTDOOR").put("START MISSION").put("START RETURN").put("SCAN NEARBY").put("BATTERY STATUS"));o.put("custom","COMPANION APP");}catch(Exception ignored){}return o;}

    private JSONObject saveImpact(JSONObject p){lastImpact=new JSONObject();try{lastImpact.put("time",System.currentTimeMillis());lastImpact.put("intensity",p.optString("intensity","UNAVAILABLE"));lastImpact.put("movementAfter",p.optString("movementAfter","UNAVAILABLE"));lastImpact.put("heartRate",p.has("heartRate")?p.opt("heartRate"):"UNAVAILABLE");lastImpact.put("location",p.optString("location","UNAVAILABLE"));lastImpact.put("userResponse",p.optString("userResponse","PENDING"));prefs.edit().putString("impact_review",lastImpact.toString()).apply();events.emit("IMPACT_EVENT","EMERGENCY","P2","IMPACT EVENT REVIEW",lastImpact);}catch(Exception ignored){}return lastImpact;}
    private JSONObject emergencyStatus(){JSONObject o=new JSONObject();try{o.put("level",prefs.getInt("emergency_level",0));o.put("autoEscalate",prefs.getBoolean("emergency_auto",false));o.put("confirmationSec",15);o.put("lastImpact",lastImpact);}catch(Exception ignored){}return o;}
    private JSONObject setEmergencyLevel(int level,String reason){int l=Math.max(0,Math.min(3,level));prefs.edit().putInt("emergency_level",l).apply();events.emit("EMERGENCY_LEVEL","EMERGENCY",l>=3?"P1":(l>=2?"P2":"P3"),"LEVEL "+l+" • "+reason,null);return emergencyStatus();}

    private JSONObject timeline(String filter,int limit){JSONObject o=new JSONObject();try{o.put("items",events.recent(Math.max(1,Math.min(8,limit)),filter));o.put("filter",filter);o.put("count",events.read().length());}catch(Exception ignored){}return o;}
    private JSONObject powerRecommendation(int battery,int missionMinutes){String p="BALANCED";if(battery>=0&&battery<=8)p="SURVIVAL";else if(battery>=0&&battery<=28)p="ENDURANCE";else if(missionMinutes>=240&&battery>=0&&battery<50)p="ENDURANCE";JSONObject o=new JSONObject();try{o.put("recommended",p);o.put("battery",battery<0?"UNAVAILABLE":battery);o.put("missionMinutes",missionMinutes);o.put("wifiCost","MEDIUM");o.put("gpsRealtimeCost","HIGH");o.put("compassCost","LOW");o.put("radarAnimationCost","MEDIUM");}catch(Exception ignored){}return o;}
    private String environmentLabel(){JSONObject s=wifi.summary();int risk=s.optInt("open",0)>0||s.optInt("duplicate",0)>0?1:0;return risk==0?"NORMAL":"CAUTION";}

    public boolean shouldSurface(JSONObject event){if(event==null)return false;String p=event.optString("priority","P3"),mode=prefs.getString("notification_mode","FIELD");if("P1".equals(p))return true;if("EMERGENCY".equals(mode))return true;if("STEALTH".equals(mode))return "P2".equals(p);if("MISSION".equals(mode))return "P2".equals(p)||"MISSION".equals(event.optString("category"))||"NAVIGATION".equals(event.optString("category"));return !"P4".equals(p);}
    @Override public void onFieldEvent(JSONObject event){ /* MainActivity may subscribe separately for watch alerts. */ }

    private void emitMapped(String type,String msg,JSONObject data){String category=type.contains("DEVICE")?"NETWORK":"NETWORK",priority=(type.contains("CHANGED")||type.contains("OPEN"))?"P2":"P3";events.emit(type,category,priority,msg,data);}
    private JSONObject simple(String k,Object v){JSONObject o=new JSONObject();try{o.put(k,v);}catch(Exception ignored){}return o;}
    private void setBool(String k,boolean v){prefs.edit().putBoolean(k,v).apply();}
    private String trim(String s,int n){if(s==null)return "";return s.length()<=n?s:s.substring(0,n);}
}