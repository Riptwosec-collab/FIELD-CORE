package com.riptwosec.fieldcore;

import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.List;

/** Small local event bus + bounded persistent mission event log. */
public final class FieldEventBus {
    public interface Listener { void onFieldEvent(JSONObject event); }
    private final SharedPreferences prefs;
    private final List<Listener> listeners=new ArrayList<>();
    private static final int MAX_EVENTS=120;

    public FieldEventBus(Context c){prefs=c.getApplicationContext().getSharedPreferences("fieldcore_event_bus",Context.MODE_PRIVATE);}
    public synchronized void subscribe(Listener l){if(l!=null&&!listeners.contains(l))listeners.add(l);}
    public synchronized void unsubscribe(Listener l){listeners.remove(l);}

    public void emit(String type,String category,String priority,String message,JSONObject data){
        JSONObject e=new JSONObject();try{e.put("type",type==null?"FIELD_EVENT":type);e.put("category",category==null?"SYSTEM":category);e.put("priority",priority==null?"P3":priority);e.put("message",message==null?"":message);e.put("ts",System.currentTimeMillis());if(data!=null)e.put("data",data);}catch(Exception ignored){}
        append(e);List<Listener> copy; synchronized(this){copy=new ArrayList<>(listeners);}for(Listener l:copy)try{l.onFieldEvent(e);}catch(Exception ignored){}
    }

    private synchronized void append(JSONObject e){JSONArray old=read();JSONArray out=new JSONArray();int start=Math.max(0,old.length()-(MAX_EVENTS-1));for(int i=start;i<old.length();i++)out.put(old.opt(i));out.put(e);prefs.edit().putString("events",out.toString()).apply();}
    public synchronized JSONArray read(){try{return new JSONArray(prefs.getString("events","[]"));}catch(Exception e){return new JSONArray();}}
    public synchronized JSONArray recent(int limit,String category){JSONArray all=read(),out=new JSONArray();String c=category==null?"ALL":category;for(int i=all.length()-1;i>=0&&out.length()<Math.max(1,Math.min(20,limit));i--){JSONObject e=all.optJSONObject(i);if(e==null)continue;if("ALL".equalsIgnoreCase(c)||c.equalsIgnoreCase(e.optString("category")))out.put(e);}return out;}
    public synchronized void clear(){prefs.edit().putString("events","[]").apply();}
}