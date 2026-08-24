package com.riptwosec.fieldcore;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import org.json.JSONArray;
import org.json.JSONObject;

/** Local-only Wi-Fi history/trust store. No cloud sync. */
public final class WifiScoutStore extends SQLiteOpenHelper {
    private static final String DB_NAME="fieldcore_wifi_scout.db";
    private static final int DB_VERSION=1;

    public WifiScoutStore(Context context){ super(context,DB_NAME,null,DB_VERSION); }

    @Override public void onCreate(SQLiteDatabase db){
        db.execSQL("CREATE TABLE networks("+
                "bssid TEXT PRIMARY KEY,"+
                "ssid TEXT NOT NULL DEFAULT '',"+
                "security TEXT NOT NULL DEFAULT 'UNKNOWN',"+
                "band TEXT NOT NULL DEFAULT 'UNKNOWN',"+
                "channel INTEGER NOT NULL DEFAULT 0,"+
                "first_seen INTEGER NOT NULL,"+
                "last_seen INTEGER NOT NULL,"+
                "last_rssi INTEGER NOT NULL,"+
                "strongest_rssi INTEGER NOT NULL,"+
                "sightings INTEGER NOT NULL DEFAULT 1,"+
                "trusted INTEGER NOT NULL DEFAULT 0,"+
                "hidden INTEGER NOT NULL DEFAULT 0,"+
                "security_changed INTEGER NOT NULL DEFAULT 0)" );
        db.execSQL("CREATE INDEX idx_networks_last_seen ON networks(last_seen DESC)");
        db.execSQL("CREATE INDEX idx_networks_ssid ON networks(ssid)");
    }
    @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){ /* additive schema reserved */ }

    public synchronized JSONObject upsert(String ssid,String bssid,int rssi,String security,String band,int channel,boolean hidden,long now){
        JSONObject change=new JSONObject();
        if(bssid==null||bssid.length()==0)return change;
        SQLiteDatabase db=getWritableDatabase();
        String oldSecurity=null;boolean existed=false;int trusted=0;long first=now;int strongest=rssi;int sightings=0;
        try(Cursor c=db.query("networks",new String[]{"security","trusted","first_seen","strongest_rssi","sightings"},"bssid=?",new String[]{bssid},null,null,null)){
            if(c.moveToFirst()){existed=true;oldSecurity=c.getString(0);trusted=c.getInt(1);first=c.getLong(2);strongest=Math.max(c.getInt(3),rssi);sightings=c.getInt(4);}
        }
        boolean securityChanged=existed&&oldSecurity!=null&&!oldSecurity.equals(security);
        ContentValues v=new ContentValues();v.put("bssid",bssid);v.put("ssid",ssid==null?"":ssid);v.put("security",security);v.put("band",band);v.put("channel",channel);v.put("first_seen",first);v.put("last_seen",now);v.put("last_rssi",rssi);v.put("strongest_rssi",strongest);v.put("sightings",sightings+1);v.put("trusted",trusted);v.put("hidden",hidden?1:0);v.put("security_changed",securityChanged?1:0);
        db.insertWithOnConflict("networks",null,v,SQLiteDatabase.CONFLICT_REPLACE);
        try{change.put("new",!existed);change.put("securityChanged",securityChanged);change.put("trusted",trusted==1);change.put("oldSecurity",oldSecurity==null?"":oldSecurity);}catch(Exception ignored){}
        return change;
    }

    public synchronized void setTrusted(String bssid,boolean trusted){ContentValues v=new ContentValues();v.put("trusted",trusted?1:0);getWritableDatabase().update("networks",v,"bssid=?",new String[]{bssid});}
    public synchronized boolean isTrusted(String bssid){try(Cursor c=getReadableDatabase().query("networks",new String[]{"trusted"},"bssid=?",new String[]{bssid},null,null,null)){return c.moveToFirst()&&c.getInt(0)==1;}}

    public synchronized JSONObject get(String bssid){
        try(Cursor c=getReadableDatabase().query("networks",null,"bssid=?",new String[]{bssid},null,null,null)){if(c.moveToFirst())return row(c);}catch(Exception ignored){}
        return null;
    }

    public synchronized JSONArray history(int limit){
        JSONArray a=new JSONArray();int safe=Math.max(1,Math.min(50,limit));
        try(Cursor c=getReadableDatabase().query("networks",null,null,null,null,null,"last_seen DESC",String.valueOf(safe))){while(c.moveToNext())a.put(row(c));}catch(Exception ignored){}
        return a;
    }

    public synchronized JSONArray trusted(int limit){
        JSONArray a=new JSONArray();int safe=Math.max(1,Math.min(50,limit));
        try(Cursor c=getReadableDatabase().query("networks",null,"trusted=1",null,null,null,"last_seen DESC",String.valueOf(safe))){while(c.moveToNext())a.put(row(c));}catch(Exception ignored){}
        return a;
    }

    public synchronized int count(){try(Cursor c=getReadableDatabase().rawQuery("SELECT COUNT(*) FROM networks",null)){return c.moveToFirst()?c.getInt(0):0;}}

    private JSONObject row(Cursor c){
        JSONObject o=new JSONObject();try{
            o.put("ssid",c.getString(c.getColumnIndexOrThrow("ssid")));o.put("bssid",c.getString(c.getColumnIndexOrThrow("bssid")));o.put("security",c.getString(c.getColumnIndexOrThrow("security")));o.put("band",c.getString(c.getColumnIndexOrThrow("band")));o.put("channel",c.getInt(c.getColumnIndexOrThrow("channel")));o.put("firstSeen",c.getLong(c.getColumnIndexOrThrow("first_seen")));o.put("lastSeen",c.getLong(c.getColumnIndexOrThrow("last_seen")));o.put("rssi",c.getInt(c.getColumnIndexOrThrow("last_rssi")));o.put("strongest",c.getInt(c.getColumnIndexOrThrow("strongest_rssi")));o.put("sightings",c.getInt(c.getColumnIndexOrThrow("sightings")));o.put("trusted",c.getInt(c.getColumnIndexOrThrow("trusted"))==1);o.put("hidden",c.getInt(c.getColumnIndexOrThrow("hidden"))==1);o.put("securityChanged",c.getInt(c.getColumnIndexOrThrow("security_changed"))==1);
        }catch(Exception ignored){}return o;
    }
}