package com.riptwosec.fieldcore;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Keyless Open-Meteo adapter. Provider/network failures never produce fabricated values. */
public final class WeatherProvider {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    private final PhoneLocationProvider location;
    public WeatherProvider(PhoneLocationProvider location){this.location=location;}

    public void execute(String action,Callback cb){
        location.current((ok,msg,loc)->{
            if(!ok||loc==null){cb.done(false,"WEATHER NEEDS PHONE LOCATION",null);return;}
            final double lat=loc.optDouble("latitude",Double.NaN),lon=loc.optDouble("longitude",Double.NaN);
            if(Double.isNaN(lat)||Double.isNaN(lon)){cb.done(false,"WEATHER LOCATION INVALID",null);return;}
            new Thread(()->fetch(action,lat,lon,loc,cb),"fieldcore-weather").start();
        });
    }

    private void fetch(String action,double lat,double lon,JSONObject loc,Callback cb){
        HttpURLConnection conn=null;
        try{
            String base="https://api.open-meteo.com/v1/forecast";
            String query=String.format(Locale.US,"?latitude=%.6f&longitude=%.6f&current=temperature_2m,apparent_temperature,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,weather_code&daily=uv_index_max,sunrise,sunset,moonrise,moonset,moon_phase&forecast_days=1&timezone=auto",lat,lon);
            conn=(HttpURLConnection)new URL(base+query).openConnection();conn.setConnectTimeout(8000);conn.setReadTimeout(8000);conn.setRequestMethod("GET");conn.setRequestProperty("Accept","application/json");
            int code=conn.getResponseCode();if(code<200||code>=300){cb.done(false,"WEATHER HTTP "+code,null);return;}
            BufferedReader r=new BufferedReader(new InputStreamReader(conn.getInputStream(),StandardCharsets.UTF_8));StringBuilder b=new StringBuilder();String line;while((line=r.readLine())!=null)b.append(line);r.close();
            JSONObject root=new JSONObject(b.toString()),current=root.optJSONObject("current"),daily=root.optJSONObject("daily"),out=new JSONObject();
            out.put("source","OPEN_METEO");out.put("fetchedAt",System.currentTimeMillis());out.put("locationAgeMs",loc.optLong("ageMs",0));
            if(current!=null){copyNumber(current,out,"temperature_2m","temperatureC");copyNumber(current,out,"apparent_temperature","apparentC");copyNumber(current,out,"relative_humidity_2m","humidityPct");copyNumber(current,out,"pressure_msl","pressureMslHpa");copyNumber(current,out,"wind_speed_10m","windKmh");copyNumber(current,out,"wind_direction_10m","windDirectionDeg");copyNumber(current,out,"weather_code","weatherCode");}
            if(daily!=null){copyFirstNumber(daily,out,"uv_index_max","uvIndexMax");copyFirstString(daily,out,"sunrise","sunrise");copyFirstString(daily,out,"sunset","sunset");copyFirstString(daily,out,"moonrise","moonrise");copyFirstString(daily,out,"moonset","moonset");copyFirstNumber(daily,out,"moon_phase","moonPhase");}
            if(loc.has("altitude")&&!loc.isNull("altitude"))out.put("phoneAltitudeM",loc.optDouble("altitude"));
            if("UV_REFRESH".equals(action))compact(out,new String[]{"source","uvIndexMax","fetchedAt"});
            else if("SUN_REFRESH".equals(action))compact(out,new String[]{"source","sunrise","sunset","fetchedAt"});
            else if("SKY_REFRESH".equals(action)||"ASTRO_REFRESH".equals(action))compact(out,new String[]{"source","sunrise","sunset","moonrise","moonset","moonPhase","fetchedAt"});
            else if("THERMAL_REFRESH".equals(action)){double t=out.optDouble("temperatureC",Double.NaN),a=out.optDouble("apparentC",Double.NaN),uv=out.optDouble("uvIndexMax",0);out.put("heatLoad",heatLoad(t,a,uv));compact(out,new String[]{"source","temperatureC","apparentC","humidityPct","uvIndexMax","heatLoad","fetchedAt"});}
            cb.done(true,"LIVE WEATHER",out);
        }catch(Exception e){cb.done(false,"WEATHER ERROR: "+safe(e.getMessage()),null);}finally{if(conn!=null)conn.disconnect();}
    }

    private static String heatLoad(double t,double apparent,double uv){double v=Math.max(Double.isNaN(t)?0:t,Double.isNaN(apparent)?0:apparent);int score=0;if(v>=36)score+=3;else if(v>=32)score+=2;else if(v>=28)score+=1;if(uv>=8)score+=2;else if(uv>=6)score+=1;return score>=4?"VERY HIGH":score>=3?"HIGH":score>=2?"MODERATE":"LOW";}
    private static void copyNumber(JSONObject src,JSONObject dst,String from,String to)throws Exception{if(src.has(from)&&!src.isNull(from))dst.put(to,src.optDouble(from));}
    private static void copyFirstNumber(JSONObject src,JSONObject dst,String from,String to)throws Exception{JSONArray a=src.optJSONArray(from);if(a!=null&&a.length()>0&&!a.isNull(0))dst.put(to,a.optDouble(0));}
    private static void copyFirstString(JSONObject src,JSONObject dst,String from,String to)throws Exception{JSONArray a=src.optJSONArray(from);if(a!=null&&a.length()>0&&!a.isNull(0))dst.put(to,a.optString(0));}
    private static void compact(JSONObject o,String[] keep)throws Exception{JSONObject c=new JSONObject();for(String k:keep)if(o.has(k))c.put(k,o.get(k));String[] names=JSONObject.getNames(o);if(names!=null)for(String k:names)o.remove(k);String[] cn=JSONObject.getNames(c);if(cn!=null)for(String k:cn)o.put(k,c.get(k));}
    private static String safe(String s){if(s==null)return "UNKNOWN";return s.length()>80?s.substring(0,80):s;}
}
