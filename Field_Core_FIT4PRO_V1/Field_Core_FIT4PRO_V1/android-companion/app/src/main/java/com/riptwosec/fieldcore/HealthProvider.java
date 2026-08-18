package com.riptwosec.fieldcore;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import org.json.JSONObject;

/**
 * Health/session provider with a strict real-data-only policy.
 * User-entered/session state works locally now. Huawei Health Service Kit metrics stay gated
 * until the app has the SDK plus approved/user-granted scopes.
 */
public final class HealthProvider {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    private static final String PREF="fieldcore_health";
    private final Context context;
    private final SharedPreferences prefs;

    public HealthProvider(Context c){context=c.getApplicationContext();prefs=context.getSharedPreferences(PREF,Context.MODE_PRIVATE);}

    public JSONObject status(){
        JSONObject d=new JSONObject();
        try{
            d.put("huaweiHealthInstalled",isPackageInstalled("com.huawei.health"));
            d.put("healthSdkPresent",classPresent("com.huawei.hms.hihealth.HiHealth"));
            d.put("scopeState","APPROVAL_AND_USER_AUTH_REQUIRED");
            d.put("policy","REAL_DATA_ONLY");
            d.put("activeSession",prefs.getString("sessionType",""));
            d.put("hydrationCount",prefs.getInt("hydrationCount",0));
            d.put("golfScore",prefs.getInt("golfScore",0));
        }catch(Exception ignored){}
        return d;
    }

    public void execute(String action,JSONObject payload,Callback cb){
        if("SLEEP_REFRESH".equals(action)){
            cb.done(false,"HUAWEI HEALTH SCOPE REQUIRED",status());return;
        }
        if("BIO_SESSION_START".equals(action)){startSession("BIO",cb);return;}
        if("BIO_SESSION_STOP".equals(action)){stopSession(cb);return;}
        if("SPORT_RUN".equals(action)||"RUN_START".equals(action)){startSession("RUN",cb);return;}
        if("SPORT_HIKE".equals(action)){startSession("HIKE",cb);return;}
        if("SPORT_AQUA".equals(action)||"AQUA_START".equals(action)){startSession("AQUA",cb);return;}
        if("SPORT_CUSTOM".equals(action)){startSession("CUSTOM",cb);return;}
        if("RUN_STATUS".equals(action)||"AQUA_RETURN".equals(action)){sessionStatus(cb);return;}
        if("AQUA_STOP".equals(action)){stopSession(cb);return;}
        if("HYDRATION_LOG".equals(action)){logHydration(cb);return;}
        if("HYDRATION_SNOOZE".equals(action)){snoozeHydration(payload,cb);return;}
        if("GOLF_STATUS".equals(action)){golfStatus(cb);return;}
        if("GOLF_SCORE_PLUS".equals(action)){changeGolf(1,cb);return;}
        if("GOLF_SCORE_MINUS".equals(action)){changeGolf(-1,cb);return;}
        cb.done(false,"HEALTH PROVIDER ACTION UNSUPPORTED",status());
    }

    private void startSession(String type,Callback cb){
        long now=System.currentTimeMillis();prefs.edit().putString("sessionType",type).putLong("sessionStartedAt",now).apply();
        JSONObject d=new JSONObject();try{d.put("type",type);d.put("startedAt",now);d.put("metrics","LOCAL SESSION ONLY");}catch(Exception ignored){}
        cb.done(true,type+" SESSION STARTED",d);
    }
    private void stopSession(Callback cb){
        String type=prefs.getString("sessionType","");long start=prefs.getLong("sessionStartedAt",0),now=System.currentTimeMillis();
        if(type.length()==0||start==0){cb.done(false,"NO ACTIVE SESSION",null);return;}
        prefs.edit().remove("sessionType").remove("sessionStartedAt").apply();
        JSONObject d=new JSONObject();try{d.put("type",type);d.put("startedAt",start);d.put("endedAt",now);d.put("durationSec",Math.max(0,(now-start)/1000));}catch(Exception ignored){}
        cb.done(true,type+" SESSION SAVED",d);
    }
    private void sessionStatus(Callback cb){
        String type=prefs.getString("sessionType","");long start=prefs.getLong("sessionStartedAt",0),now=System.currentTimeMillis();
        JSONObject d=new JSONObject();try{d.put("active",type.length()>0);d.put("type",type);d.put("startedAt",start);d.put("durationSec",start>0?Math.max(0,(now-start)/1000):0);d.put("healthMetrics","SCOPE GATED");}catch(Exception ignored){}
        cb.done(true,type.length()>0?"SESSION ACTIVE":"NO ACTIVE SESSION",d);
    }
    private void logHydration(Callback cb){
        int count=prefs.getInt("hydrationCount",0)+1;long now=System.currentTimeMillis();prefs.edit().putInt("hydrationCount",count).putLong("lastHydrationAt",now).apply();
        JSONObject d=new JSONObject();try{d.put("count",count);d.put("lastAt",now);d.put("source","USER LOG");}catch(Exception ignored){}
        cb.done(true,"WATER LOGGED",d);
    }
    private void snoozeHydration(JSONObject payload,Callback cb){
        int min=Math.max(5,Math.min(180,payload==null?30:payload.optInt("minutes",30)));long until=System.currentTimeMillis()+min*60_000L;prefs.edit().putLong("hydrationSnoozeUntil",until).apply();
        JSONObject d=new JSONObject();try{d.put("minutes",min);d.put("until",until);}catch(Exception ignored){}
        cb.done(true,"HYDRATION SNOOZED",d);
    }
    private void golfStatus(Callback cb){JSONObject d=new JSONObject();try{d.put("score",prefs.getInt("golfScore",0));d.put("source","USER SCORECARD");}catch(Exception ignored){}cb.done(true,"GOLF SCORECARD",d);}
    private void changeGolf(int delta,Callback cb){int score=Math.max(0,prefs.getInt("golfScore",0)+delta);prefs.edit().putInt("golfScore",score).apply();golfStatus(cb);}
    private boolean classPresent(String name){try{Class.forName(name);return true;}catch(Throwable ignored){return false;}}
    private boolean isPackageInstalled(String pkg){try{context.getPackageManager().getPackageInfo(pkg,0);return true;}catch(PackageManager.NameNotFoundException e){return false;}}
}
