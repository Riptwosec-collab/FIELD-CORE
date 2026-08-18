package com.riptwosec.fieldcore;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import org.json.JSONObject;

public final class PhoneLocationProvider {
    public interface Callback { void done(boolean ok, String message, JSONObject data); }
    private static final long STALE_LOCATION_MS = 2L * 60L * 1000L;
    private final Context context;

    public PhoneLocationProvider(Context c){context=c;}

    public boolean hasPermission(){
        return context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED
            || context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;
    }

    public void lastKnown(Callback cb){
        if(!hasPermission()){cb.done(false,"LOCATION PERMISSION REQUIRED",null);return;}
        try{
            LocationManager lm=(LocationManager)context.getSystemService(Context.LOCATION_SERVICE);
            if(lm==null){cb.done(false,"LOCATION SERVICE UNAVAILABLE",null);return;}
            Location best=null;
            for(String p:lm.getProviders(true)){
                Location l=lm.getLastKnownLocation(p);
                if(l!=null&&(best==null||l.getTime()>best.getTime()))best=l;
            }
            if(best==null){cb.done(false,"NO PHONE LOCATION",null);return;}

            long ageMs=Math.max(0L,System.currentTimeMillis()-best.getTime());
            JSONObject j=new JSONObject();
            j.put("latitude",best.getLatitude());
            j.put("longitude",best.getLongitude());
            j.put("accuracy",best.getAccuracy());
            j.put("altitude",best.hasAltitude()?best.getAltitude():JSONObject.NULL);
            j.put("timestamp",best.getTime());
            j.put("ageMs",ageMs);
            j.put("stale",ageMs>STALE_LOCATION_MS);
            cb.done(true,ageMs>STALE_LOCATION_MS?"PHONE LOCATION STALE":"PHONE LOCATION",j);
        }catch(SecurityException e){
            cb.done(false,"LOCATION PERMISSION REQUIRED",null);
        }catch(Exception e){
            cb.done(false,"LOCATION ERROR: "+e.getMessage(),null);
        }
    }
}
