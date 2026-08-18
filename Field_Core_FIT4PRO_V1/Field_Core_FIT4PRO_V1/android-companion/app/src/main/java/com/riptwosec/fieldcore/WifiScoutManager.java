package com.riptwosec.fieldcore;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Phone-side Wi-Fi scanner for FIELD CORE. The watch never claims direct Wi-Fi scan capability.
 * Results are local-only and watch payloads are deliberately compact for Wear Engine P2P.
 */
public final class WifiScoutManager {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    public interface EventSink { void event(String type,String message,JSONObject data); }

    public static final String MODE_ACTIVE="ACTIVE", MODE_BALANCED="BALANCED", MODE_BATTERY="BATTERY_SAVER";
    private final Context context;
    private final WifiManager wifi;
    private final WifiScoutStore store;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final EventSink events;
    private final List<Network> current=new ArrayList<>();
    private final Set<String> sessionSeen=new HashSet<>();
    private final Map<String,Integer> previousRssi=new HashMap<>();
    private boolean registered=false,scanPending=false,outdoorActive=false;
    private long lastScanAt=0,sessionStartedAt=0;
    private int sessionNew=0,sessionOpen=0;
    private String scanMode=MODE_BALANCED;
    private Callback pending;

    public WifiScoutManager(Context c,EventSink sink){
        context=c.getApplicationContext();events=sink;wifi=(WifiManager)context.getSystemService(Context.WIFI_SERVICE);store=new WifiScoutStore(context);register();
    }

    public void close(){try{if(registered)context.unregisterReceiver(receiver);}catch(Exception ignored){}registered=false;store.close();}

    private void register(){if(registered)return;IntentFilter f=new IntentFilter(WifiManager.SCAN_RESULTS_AVAILABLE_ACTION);try{if(Build.VERSION.SDK_INT>=33)context.registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED);else context.registerReceiver(receiver,f);registered=true;}catch(Exception ignored){registered=false;}}
    private final BroadcastReceiver receiver=new BroadcastReceiver(){@Override public void onReceive(Context c,Intent i){if(!WifiManager.SCAN_RESULTS_AVAILABLE_ACTION.equals(i.getAction()))return;boolean updated=Build.VERSION.SDK_INT<23||i.getBooleanExtra(WifiManager.EXTRA_RESULTS_UPDATED,false);consumeResults(updated?"LIVE":"CACHED");}};

    public boolean hasPermission(){return context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
    public boolean wifiEnabled(){return wifi!=null&&wifi.isWifiEnabled();}
    public boolean locationEnabled(){try{LocationManager lm=(LocationManager)context.getSystemService(Context.LOCATION_SERVICE);return lm!=null&&lm.isLocationEnabled();}catch(Exception e){return false;}}

    public void setMode(String mode){String m=mode==null?"":mode.toUpperCase(Locale.ROOT);if(MODE_ACTIVE.equals(m)||MODE_BALANCED.equals(m)||MODE_BATTERY.equals(m))scanMode=m;}
    public String getMode(){return scanMode;}
    public long intervalMs(){return MODE_ACTIVE.equals(scanMode)?30000L:(MODE_BATTERY.equals(scanMode)?90000L:60000L);}

    public void scan(Callback cb){
        if(cb==null)return;if(wifi==null){cb.done(false,"WI-FI UNAVAILABLE",status());return;}if(!hasPermission()){cb.done(false,"PERMISSION REQUIRED",status());return;}if(!locationEnabled()){cb.done(false,"LOCATION SERVICES REQUIRED FOR WI-FI SCAN",status());return;}if(!wifiEnabled()){cb.done(false,"WI-FI DISABLED",status());return;}
        long age=System.currentTimeMillis()-lastScanAt;if(age<Math.min(15000L,intervalMs()/2)&&!current.isEmpty()){cb.done(true,"CACHED • SCAN INTERVAL",summary());return;}
        pending=cb;scanPending=true;boolean started=false;try{started=wifi.startScan();}catch(SecurityException e){pending=null;scanPending=false;cb.done(false,"PERMISSION REQUIRED",status());return;}catch(Exception e){pending=null;scanPending=false;cb.done(false,"WI-FI SCAN ERROR",status());return;}
        if(!started){scanPending=false;consumeResults("THROTTLED/CACHED");}
        else main.postDelayed(()->{if(scanPending){scanPending=false;consumeResults("TIMEOUT/CACHED");}},9000L);
    }

    @SuppressWarnings("deprecation") private void consumeResults(String source){
        List<ScanResult> raw;try{raw=wifi.getScanResults();}catch(Exception e){raw=Collections.emptyList();}
        long now=System.currentTimeMillis();List<Network> next=new ArrayList<>();Map<String,Integer> ssidCounts=new HashMap<>();
        if(raw!=null){for(ScanResult r:raw){if(r==null)continue;Network n=Network.from(r,now);next.add(n);if(n.ssid.length()>0)ssidCounts.put(n.ssid,ssidCounts.getOrDefault(n.ssid,0)+1);}}
        next.sort((a,b)->Integer.compare(b.rssi,a.rssi));int newCount=0,open=0,hidden=0,secured=0;
        for(Network n:next){n.duplicate=n.ssid.length()>0&&ssidCounts.getOrDefault(n.ssid,0)>1;JSONObject change=store.upsert(n.ssid,n.bssid,n.rssi,n.security,n.band,n.channel,n.hidden,now);n.isNew=change.optBoolean("new",false);n.securityChanged=change.optBoolean("securityChanged",false);n.trusted=change.optBoolean("trusted",false);n.risk=risk(n);if(n.isNew){newCount++;if(outdoorActive&&!sessionSeen.contains(n.bssid)){sessionNew++;emit("NEW_NETWORK",n.ssid,n.compact());}}if(n.securityChanged)emit("NETWORK_CHANGED",n.ssid+" SECURITY CHANGED",n.compact());if(n.trusted)emit("TRUSTED_NETWORK_FOUND",n.ssid,n.compact());if("OPEN".equals(n.security)){open++;if(n.isNew)emit("NEW_OPEN_WIFI",n.ssid,n.compact());}else secured++;if(n.hidden)hidden++;sessionSeen.add(n.bssid);previousRssi.put(n.bssid,n.rssi);}
        synchronized(current){current.clear();current.addAll(next);}lastScanAt=now;if(outdoorActive)sessionOpen=open;scanPending=false;
        JSONObject out=summary();try{out.put("source",source);out.put("new",newCount);out.put("secured",secured);out.put("hidden",hidden);}catch(Exception ignored){}
        Callback cb=pending;pending=null;if(cb!=null)cb.done(true,"WI-FI SCAN "+source,out);
    }

    public JSONObject status(){JSONObject o=summary();try{o.put("permission",hasPermission()?"READY":"PERMISSION REQUIRED");o.put("wifi",wifiEnabled()?"ON":"OFF");o.put("locationService",locationEnabled()?"ON":"OFF");o.put("scanMode",scanMode);o.put("outdoor",outdoorActive);o.put("history",store.count());}catch(Exception ignored){}return o;}

    public JSONObject summary(){List<Network> list=snapshot();int open=0,secured=0,hidden=0,trusted=0,duplicate=0,newCount=0;for(Network n:list){if("OPEN".equals(n.security))open++;else secured++;if(n.hidden)hidden++;if(n.trusted)trusted++;if(n.duplicate)duplicate++;if(n.isNew)newCount++;}JSONObject o=new JSONObject();try{o.put("count",list.size());o.put("open",open);o.put("secured",secured);o.put("hidden",hidden);o.put("trusted",trusted);o.put("duplicate",duplicate);o.put("new",newCount);o.put("updatedAt",lastScanAt);o.put("ageSec",lastScanAt==0?-1:Math.max(0,(System.currentTimeMillis()-lastScanAt)/1000));o.put("mode",scanMode);if(!list.isEmpty()){Network b=bestNetwork(list);if(b!=null)o.put("best",b.compact());o.put("strongest",list.get(0).compact());}}catch(Exception ignored){}return o;}

    public JSONObject networkPage(int page,int pageSize,String filter,String sort){List<Network> list=filtered(filter);sort(list,sort);int size=Math.max(1,Math.min(5,pageSize)),start=Math.max(0,page)*size;JSONArray a=new JSONArray();for(int i=start;i<Math.min(list.size(),start+size);i++)a.put(list.get(i).compact());JSONObject o=new JSONObject();try{o.put("page",Math.max(0,page));o.put("total",list.size());o.put("items",a);o.put("updatedAt",lastScanAt);}catch(Exception ignored){}return o;}
    public JSONObject detail(String bssid){Network n=find(bssid);if(n==null){JSONObject cached=store.get(bssid);return cached==null?new JSONObject():cached;}return n.detail();}
    public JSONObject best(){Network n=bestNetwork(snapshot());JSONObject o=new JSONObject();try{if(n==null)o.put("status","NO NETWORKS");else{o.put("network",n.detail());o.put("score",score(n));}}catch(Exception ignored){}return o;}
    public JSONObject channels(){Map<String,Integer> counts=new HashMap<>();for(Network n:snapshot()){String k=n.band+"/"+n.channel;counts.put(k,counts.getOrDefault(k,0)+1);}JSONArray a=new JSONArray();for(Map.Entry<String,Integer> e:counts.entrySet()){String[] p=e.getKey().split("/");JSONObject c=new JSONObject();try{int count=e.getValue();c.put("band",p[0]);c.put("channel",Integer.parseInt(p[1]));c.put("aps",count);c.put("load",count>=5?"BUSY":(count>=3?"MEDIUM":"CLEAR"));a.put(c);}catch(Exception ignored){}}JSONObject o=new JSONObject();try{o.put("channels",a);o.put("updatedAt",lastScanAt);}catch(Exception ignored){}return o;}
    public JSONObject history(int limit){JSONObject o=new JSONObject();try{o.put("items",store.history(Math.max(1,Math.min(8,limit))));}catch(Exception ignored){}return o;}
    public JSONObject trusted(int limit){JSONObject o=new JSONObject();try{o.put("items",store.trusted(Math.max(1,Math.min(8,limit))));}catch(Exception ignored){}return o;}
    public JSONObject setTrusted(String bssid,boolean trusted){store.setTrusted(bssid,trusted);Network n=find(bssid);if(n!=null)n.trusted=trusted;JSONObject o=new JSONObject();try{o.put("bssid",bssid);o.put("trusted",trusted);}catch(Exception ignored){}return o;}

    public JSONObject signalHunt(String bssid){Network n=find(bssid);JSONObject o=new JSONObject();try{if(n==null){o.put("status","TARGET NOT VISIBLE");return o;}Integer prev=previousRssi.get(bssid);String trend=prev==null?"WAITING":(n.rssi>=prev+3?"STRONGER":(n.rssi<=prev-3?"WEAKER":"STABLE"));o.put("ssid",n.ssid);o.put("bssid",n.bssid);o.put("rssi",n.rssi);o.put("proximity",proximity(n.rssi));o.put("trend",trend);o.put("directionEstimate",trend);previousRssi.put(bssid,n.rssi);}catch(Exception ignored){}return o;}

    public JSONObject duplicateSummary(){Map<String,List<Network>> groups=new HashMap<>();for(Network n:snapshot())if(n.ssid.length()>0)groups.computeIfAbsent(n.ssid,k->new ArrayList<>()).add(n);JSONArray out=new JSONArray();for(Map.Entry<String,List<Network>> e:groups.entrySet())if(e.getValue().size()>1){JSONObject g=new JSONObject();try{g.put("ssid",e.getKey());g.put("aps",e.getValue().size());JSONArray b=new JSONArray();for(int i=0;i<Math.min(3,e.getValue().size());i++){Network n=e.getValue().get(i);JSONObject x=new JSONObject();x.put("bssid",n.bssid);x.put("rssi",n.rssi);x.put("security",n.security);b.put(x);}g.put("items",b);out.put(g);}catch(Exception ignored){}}JSONObject o=new JSONObject();try{o.put("duplicates",out);}catch(Exception ignored){}return o;}

    public JSONObject startOutdoor(){outdoorActive=true;sessionStartedAt=System.currentTimeMillis();sessionSeen.clear();sessionNew=0;sessionOpen=0;emit("OUTDOOR_SCAN_STARTED","OUTDOOR SCAN",null);JSONObject o=status();try{o.put("startedAt",sessionStartedAt);}catch(Exception ignored){}return o;}
    public JSONObject stopOutdoor(){outdoorActive=false;long duration=Math.max(0,System.currentTimeMillis()-sessionStartedAt);JSONObject o=new JSONObject();try{o.put("durationSec",duration/1000);o.put("networks",sessionSeen.size());o.put("new",sessionNew);o.put("open",sessionOpen);Network s=snapshot().isEmpty()?null:snapshot().get(0);if(s!=null)o.put("strongest",s.compact());}catch(Exception ignored){}emit("OUTDOOR_SCAN_STOPPED","SCAN SUMMARY",o);return o;}

    private List<Network> snapshot(){synchronized(current){return new ArrayList<>(current);}}
    private Network find(String bssid){if(bssid==null)return null;for(Network n:snapshot())if(bssid.equalsIgnoreCase(n.bssid))return n;return null;}
    private List<Network> filtered(String filter){String f=filter==null?"ALL":filter.toUpperCase(Locale.ROOT);List<Network> out=new ArrayList<>();for(Network n:snapshot()){boolean ok="ALL".equals(f)||("OPEN".equals(f)&&"OPEN".equals(n.security))||("SECURED".equals(f)&&!"OPEN".equals(n.security))||("TRUSTED".equals(f)&&n.trusted)||("NEW".equals(f)&&n.isNew)||("2.4G".equals(f)&&"2.4GHz".equals(n.band))||("5G".equals(f)&&"5GHz".equals(n.band));if(ok)out.add(n);}return out;}
    private void sort(List<Network> list,String sort){String s=sort==null?"SIGNAL":sort.toUpperCase(Locale.ROOT);if("NAME".equals(s))list.sort(Comparator.comparing(a->a.ssid.toLowerCase(Locale.ROOT)));else if("SECURITY".equals(s))list.sort((a,b)->Integer.compare(securityScore(b.security),securityScore(a.security)));else if("BAND".equals(s))list.sort(Comparator.comparing(a->a.band));else if("NEW".equals(s))list.sort((a,b)->Boolean.compare(b.isNew,a.isNew));else list.sort((a,b)->Integer.compare(b.rssi,a.rssi));}
    private Network bestNetwork(List<Network> list){Network best=null;int bestScore=-1;for(Network n:list){int s=score(n);if("OPEN".equals(n.security))s-=15;if(s>bestScore){best=n;bestScore=s;}}return best;}
    private int score(Network n){int signal=Math.max(0,Math.min(100,2*(n.rssi+100)));int sec=securityScore(n.security);int band="5GHz".equals(n.band)?90:("6GHz".equals(n.band)?95:70);int stability=Math.max(40,100-Math.min(60,Math.abs(n.strongestRssi-n.rssi)*2));return Math.max(0,Math.min(100,(signal*40+sec*30+stability*20+band*10)/100));}
    private int risk(Network n){int r=0;if("OPEN".equals(n.security))r+=35;if("WEP".equals(n.security))r+=30;if(n.isNew)r+=15;if(n.duplicate)r+=15;if(n.securityChanged)r+=35;if(n.rssi>-45&&!n.trusted)r+=5;return Math.min(100,r);}
    private int securityScore(String s){if("WPA3".equals(s))return 100;if("WPA2".equals(s))return 82;if("WPA".equals(s))return 55;if("WEP".equals(s))return 20;if("OPEN".equals(s))return 10;return 35;}
    private String proximity(int rssi){if(rssi>=-49)return "VERY NEAR";if(rssi>=-59)return "NEAR";if(rssi>=-69)return "MEDIUM";if(rssi>=-79)return "FAR";return "VERY FAR";}
    private void emit(String type,String msg,JSONObject data){if(events!=null)events.event(type,msg,data);}

    static String security(ScanResult r){String c=r.capabilities==null?"":r.capabilities.toUpperCase(Locale.ROOT);if(c.contains("SAE")||c.contains("WPA3"))return "WPA3";if(c.contains("RSN")||c.contains("WPA2"))return "WPA2";if(c.contains("WPA"))return "WPA";if(c.contains("WEP"))return "WEP";return c.length()==0||c.contains("ESS")?"OPEN":"UNKNOWN";}
    static String band(int f){if(f>=5925)return "6GHz";if(f>=4900)return "5GHz";if(f>=2400)return "2.4GHz";return "UNKNOWN";}
    static int channel(int f){if(f==2484)return 14;if(f>=2412&&f<=2472)return (f-2407)/5;if(f>=5000&&f<5925)return (f-5000)/5;if(f>=5955&&f<=7115)return (f-5950)/5;return 0;}

    static final class Network {
        String ssid,bssid,security,band;int rssi,frequency,channel,strongestRssi,risk;long seenAt;boolean hidden,trusted,isNew,duplicate,securityChanged;
        static Network from(ScanResult r,long now){Network n=new Network();n.ssid=r.SSID==null?"":r.SSID;n.hidden=n.ssid.trim().length()==0;n.bssid=r.BSSID==null?"":r.BSSID;n.rssi=r.level;n.strongestRssi=r.level;n.frequency=r.frequency;n.channel=WifiScoutManager.channel(r.frequency);n.band=WifiScoutManager.band(r.frequency);n.security=WifiScoutManager.security(r);n.seenAt=now;return n;}
        JSONObject compact(){JSONObject o=new JSONObject();try{o.put("s",hidden?"HIDDEN":ssid);o.put("b",bssid);o.put("r",rssi);o.put("sec",security);o.put("band",band);o.put("ch",channel);o.put("t",trusted);o.put("n",isNew);o.put("d",duplicate);o.put("risk",risk);o.put("prox",rssi>=-49?"VERY NEAR":(rssi>=-59?"NEAR":(rssi>=-69?"MEDIUM":(rssi>=-79?"FAR":"VERY FAR"))));}catch(Exception ignored){}return o;}
        JSONObject detail(){JSONObject o=compact();try{o.put("ssid",hidden?"":ssid);o.put("bssid",bssid);o.put("rssi",rssi);o.put("frequency",frequency);o.put("security",security);o.put("band",band);o.put("channel",channel);o.put("hidden",hidden);o.put("trusted",trusted);o.put("new",isNew);o.put("duplicate",duplicate);o.put("securityChanged",securityChanged);o.put("risk",risk);o.put("lastSeen",seenAt);}catch(Exception ignored){}return o;}
    }
}