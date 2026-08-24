package com.riptwosec.fieldcore;

import android.content.Context;
import org.json.JSONObject;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Provider router. Missing/gated providers fail closed instead of fabricating data. */
public final class ProviderRegistry {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }

    private final WeatherProvider weather;
    private final HealthProvider health;
    private final PhoneLocationProvider location;

    private final Set<String> weatherActions=new HashSet<>(Arrays.asList(
        "WEATHER_REFRESH","UV_REFRESH","SUN_REFRESH","THERMAL_REFRESH","SKY_REFRESH","ASTRO_REFRESH"
    ));
    private final Set<String> healthActions=new HashSet<>(Arrays.asList(
        "SLEEP_REFRESH","SPORT_RUN","SPORT_HIKE","SPORT_AQUA","SPORT_CUSTOM","RUN_START","RUN_STATUS",
        "AQUA_START","AQUA_RETURN","AQUA_STOP","GOLF_STATUS","GOLF_SCORE_PLUS","GOLF_SCORE_MINUS",
        "BIO_SESSION_START","BIO_SESSION_STOP","HYDRATION_LOG","HYDRATION_SNOOZE"
    ));
    private final Set<String> externalActions=new HashSet<>(Arrays.asList(
        "TRANSIT_START","TRANSIT_STATUS","TRANSIT_STOP","SILENT_NAV_START","SILENT_NAV_STATUS","SILENT_NAV_STOP",
        "NAV_REFRESH","ACOUSTIC_STATUS","DEPTH_STATUS","LIGHT_STATUS","ALTITUDE_REFRESH"
    ));

    public ProviderRegistry(Context context,PhoneLocationProvider location){
        this.location=location;
        this.weather=new WeatherProvider(location);
        this.health=new HealthProvider(context);
    }

    public boolean handles(String action){return weatherActions.contains(action)||healthActions.contains(action)||externalActions.contains(action);}

    public JSONObject status(){
        JSONObject d=new JSONObject();
        try{
            d.put("weather","READY_KEYLESS");
            d.put("health",health.status());
            d.put("transit","NOT CONFIGURED");
            d.put("route","NOT CONFIGURED");
            d.put("acoustic","API GATED");
            d.put("depth","API GATED");
            d.put("ambientLight","API GATED");
        }catch(Exception ignored){}
        return d;
    }

    public void execute(String action,JSONObject payload,Callback cb){
        if(weatherActions.contains(action)){weather.execute(action,cb::done);return;}
        if(healthActions.contains(action)){health.execute(action,payload,cb::done);return;}
        if("ALTITUDE_REFRESH".equals(action)){
            location.lastKnown((ok,msg,data)->cb.done(ok,ok?"PHONE ALTITUDE":"ALTITUDE UNAVAILABLE",data));return;
        }
        if("DEPTH_STATUS".equals(action)){cb.done(false,"DEPTH API GATED",status());return;}
        if("LIGHT_STATUS".equals(action)){cb.done(false,"AMBIENT LIGHT API GATED",status());return;}
        if("ACOUSTIC_STATUS".equals(action)){cb.done(false,"AUDIO EXPOSURE PROVIDER NOT CONFIGURED",status());return;}
        if("NAV_REFRESH".equals(action)){cb.done(false,"ROUTE PROVIDER NOT CONFIGURED",status());return;}
        if(action.startsWith("TRANSIT_")){cb.done(false,"TRANSIT PROVIDER NOT CONFIGURED",status());return;}
        if(action.startsWith("SILENT_NAV_")){cb.done(false,"SILENT NAV PROVIDER NOT CONFIGURED",status());return;}
        cb.done(false,"PROVIDER NOT CONFIGURED: "+action,status());
    }
}
