package com.riptwosec.fieldcore;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import java.util.concurrent.atomic.AtomicBoolean;

public final class PhoneLocationProvider {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    private static final long STALE_LOCATION_MS=2L*60L*1000L;
    private static final long CURRENT_TIMEOUT_MS=6000L;
    private final Context context;

    public PhoneLocationProvider(Context c){context=c;}

    public boolean hasPermission(){
        return context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED
            || context.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;
    }

    public void current(Callback cb){
        if(!hasPermission()){cb.done(false,"LOCATION PERMISSION REQUIRED",null);return;}
        try{
            LocationManager lm=(LocationManager)context.getSystemService(Context.LOCATION_SERVICE);
            if(lm==null){cb.done(false,"LOCATION SERVICE UNAVAILABLE",null);return;}
            String provider=pickProvider(lm);
            if(provider==null){lastKnown(cb);return;}
            AtomicBoolean delivered=new AtomicBoolean(false);
            Handler handler=new Handler(Looper.getMainLooper());
            Runnable timeout=()->{if(delivered.compareAndSet(false,true))lastKnown(cb);};
            handler.postDelayed(timeout,CURRENT_TIMEOUT_MS);
            if(Build.VERSION.SDK_INT>=30){
                lm.getCurrentLocation(provider,null,context.getMainExecutor(),loc->{
                    if(delivered.compareAndSet(false,true)){handler.removeCallbacks(timeout);deliver(loc,"PHONE LOCATION LIVE",cb);}
                });
            }else{
                LocationListener listener=new LocationListener(){
                    @Override public void onLocationChanged(Location loc){if(delivered.compareAndSet(false,true)){handler.removeCallbacks(timeout);deliver(loc,"PHONE LOCATION LIVE",cb);}}
                    @Override public void onStatusChanged(String p,int status,Bundle extras){}
                    @Override public void onProviderEnabled(String p){}
                    @Override public void onProviderDisabled(String p){}
                };
                lm.requestSingleUpdate(provider,listener,Looper.getMainLooper());
            }
        }catch(SecurityException e){cb.done(false,"LOCATION PERMISSION REQUIRED",null);}catch(Exception e){lastKnown(cb);}
    }

    public void lastKnown(Callback cb){
        if(!hasPermission()){cb.done(false,"LOCATION PERMISSION REQUIRED",null);return;}
        try{
            LocationManager lm=(LocationManager)context.getSystemService(Context.LOCATION_SERVICE);
            if(lm==null){cb.done(false,"LOCATION SERVICE UNAVAILABLE",null);return;}
            Location best=null;
            for(String p:lm.getProviders(true)){Location l=lm.getLastKnownLocation(p);if(l!=null&&(best==null||l.getTime()>best.getTime()))best=l;}
            if(best==null){cb.done(false,"NO PHONE LOCATION",null);return;}
            long ageMs=Math.max(0L,System.currentTimeMillis()-best.getTime());
            deliver(best,ageMs>STALE_LOCATION_MS?"PHONE LOCATION STALE":"PHONE LOCATION",cb);
        }catch(SecurityException e){cb.done(false,"LOCATION PERMISSION REQUIRED",null);}catch(Exception e){cb.done(false,"LOCATION ERROR: "+e.getMessage(),null);}
    }

    private String pickProvider(LocationManager lm){
        try{if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))return LocationManager.GPS_PROVIDER;}catch(Exception ignored){}
        try{if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))return LocationManager.NETWORK_PROVIDER;}catch(Exception ignored){}
        try{java.util.List<String> p=lm.getProviders(true);return p.isEmpty()?null:p.get(0);}catch(Exception e){return null;}
    }
    private void deliver(Location l,String message,Callback cb){
        if(l==null){lastKnown(cb);return;}
        try{
            long ageMs=Math.max(0L,System.currentTimeMillis()-l.getTime());JSONObject j=new JSONObject();j.put("latitude",l.getLatitude());j.put("longitude",l.getLongitude());j.put("accuracy",l.getAccuracy());j.put("altitude",l.hasAltitude()?l.getAltitude():JSONObject.NULL);j.put("speedMps",l.hasSpeed()?l.getSpeed():JSONObject.NULL);j.put("timestamp",l.getTime());j.put("ageMs",ageMs);j.put("stale",ageMs>STALE_LOCATION_MS);cb.done(true,message,j);
        }catch(Exception e){cb.done(false,"LOCATION JSON ERROR",null);}
    }
}
