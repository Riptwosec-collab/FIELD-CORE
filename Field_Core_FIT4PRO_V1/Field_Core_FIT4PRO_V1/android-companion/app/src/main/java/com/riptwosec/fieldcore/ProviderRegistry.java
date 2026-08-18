package com.riptwosec.fieldcore;

import org.json.JSONObject;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Provider abstraction. Missing providers must return UNAVAILABLE instead of fabricated data. */
public final class ProviderRegistry {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    private final Set<String> externalActions=new HashSet<>(Arrays.asList(
        "WEATHER_REFRESH","UV_REFRESH","SUN_REFRESH","THERMAL_REFRESH","ALTITUDE_REFRESH","SKY_REFRESH","ASTRO_REFRESH",
        "SLEEP_REFRESH","SPORT_RUN","SPORT_HIKE","SPORT_AQUA","SPORT_CUSTOM","RUN_START","RUN_STATUS","AQUA_START","AQUA_RETURN","AQUA_STOP",
        "GOLF_STATUS","GOLF_SCORE_PLUS","GOLF_SCORE_MINUS","TRANSIT_START","TRANSIT_STATUS","TRANSIT_STOP","SILENT_NAV_START","SILENT_NAV_STATUS","SILENT_NAV_STOP",
        "NAV_REFRESH","ACOUSTIC_STATUS","DEPTH_STATUS","LIGHT_STATUS","BIO_SESSION_START","BIO_SESSION_STOP","HYDRATION_LOG","HYDRATION_SNOOZE"
    ));
    public boolean handles(String action){return externalActions.contains(action);}
    public void execute(String action,JSONObject payload,Callback cb){
        // Plug WeatherProvider / HealthProvider / TransitProvider / WorkoutProvider here.
        cb.done(false,"PROVIDER NOT CONFIGURED: "+action,null);
    }
}
