package com.riptwosec.fieldcore;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Phone-side BLE discovery. RSSI is proximity only; no meter-distance claims. */
public final class BluetoothReconManager {
    public interface Callback { void done(boolean ok,String message,JSONObject data); }
    public interface EventSink { void event(String type,String message,JSONObject data); }

    private final Context context;
    private final BluetoothAdapter adapter;
    private final Handler main=new Handler(Looper.getMainLooper());
    private final SharedPreferences prefs;
    private final EventSink events;
    private final Map<String,DeviceInfo> current=new LinkedHashMap<>();
    private final Map<String,Long> history=new LinkedHashMap<>();
    private boolean scanning=false;
    private Callback pending;

    public BluetoothReconManager(Context c,EventSink sink){
        context=c.getApplicationContext();events=sink;BluetoothManager m=(BluetoothManager)context.getSystemService(Context.BLUETOOTH_SERVICE);adapter=m==null?null:m.getAdapter();prefs=context.getSharedPreferences("fieldcore_bt_recon",Context.MODE_PRIVATE);loadHistory();
    }

    public boolean hasPermission(){return Build.VERSION.SDK_INT<31||context.checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN)==PackageManager.PERMISSION_GRANTED;}
    public boolean enabled(){return adapter!=null&&adapter.isEnabled();}

    public void scan(Callback cb){
        if(cb==null)return;if(adapter==null){cb.done(false,"BLUETOOTH UNAVAILABLE",status());return;}if(!hasPermission()){cb.done(false,"BLUETOOTH PERMISSION REQUIRED",status());return;}if(!enabled()){cb.done(false,"BLUETOOTH OFF",status());return;}BluetoothLeScanner scanner=adapter.getBluetoothLeScanner();if(scanner==null){cb.done(false,"BLE SCANNER UNAVAILABLE",status());return;}if(scanning){cb.done(true,"BLE SCAN ACTIVE",summary());return;}
        current.clear();pending=cb;scanning=true;try{scanner.startScan(callback);}catch(SecurityException e){scanning=false;pending=null;cb.done(false,"BLUETOOTH PERMISSION REQUIRED",status());return;}catch(Exception e){scanning=false;pending=null;cb.done(false,"BLE SCAN ERROR",status());return;}
        main.postDelayed(()->stopScan("SCAN COMPLETE"),8000L);
    }

    public JSONObject status(){JSONObject o=summary();try{o.put("permission",hasPermission()?"READY":"PERMISSION REQUIRED");o.put("bluetooth",enabled()?"ON":"OFF");o.put("scanning",scanning);}catch(Exception ignored){}return o;}
    public JSONObject summary(){List<DeviceInfo> list=list();int trusted=0,newCount=0,unknown=0;for(DeviceInfo d:list){if(d.trusted)trusted++;if(d.isNew)newCount++;if("UNKNOWN".equals(d.type))unknown++;}JSONObject o=new JSONObject();try{o.put("count",list.size());o.put("trusted",trusted);o.put("new",newCount);o.put("unknown",unknown);if(!list.isEmpty())o.put("strongest",list.get(0).compact());}catch(Exception ignored){}return o;}
    public JSONObject page(int page,int size,String filter){List<DeviceInfo> list=list();String f=filter==null?"ALL":filter.toUpperCase(Locale.ROOT);List<DeviceInfo> filtered=new ArrayList<>();for(DeviceInfo d:list){if("ALL".equals(f)||("TRUSTED".equals(f)&&d.trusted)||("NEW".equals(f)&&d.isNew)||("UNKNOWN".equals(f)&&"UNKNOWN".equals(d.type)))filtered.add(d);}int safe=Math.max(1,Math.min(5,size)),start=Math.max(0,page)*safe;JSONArray a=new JSONArray();for(int i=start;i<Math.min(filtered.size(),start+safe);i++)a.put(filtered.get(i).compact());JSONObject o=new JSONObject();try{o.put("page",Math.max(0,page));o.put("total",filtered.size());o.put("items",a);}catch(Exception ignored){}return o;}
    public JSONObject setTrusted(String address,boolean trusted){if(address==null)address="";prefs.edit().putBoolean("trusted_"+address,trusted).apply();DeviceInfo d=current.get(address);if(d!=null)d.trusted=trusted;JSONObject o=new JSONObject();try{o.put("address",address);o.put("trusted",trusted);}catch(Exception ignored){}return o;}

    private final ScanCallback callback=new ScanCallback(){
        @Override public void onScanResult(int callbackType,ScanResult result){accept(result);}
        @Override public void onBatchScanResults(List<ScanResult> results){if(results!=null)for(ScanResult r:results)accept(r);}
        @Override public void onScanFailed(int errorCode){stopScan("BLE SCAN FAILED "+errorCode);}
    };

    private void accept(ScanResult r){if(r==null||r.getDevice()==null)return;BluetoothDevice d=r.getDevice();String address;String name="";try{address=d.getAddress();name=d.getName();}catch(SecurityException e){return;}if(address==null)return;long now=System.currentTimeMillis();boolean isNew=!history.containsKey(address);DeviceInfo x=current.get(address);if(x==null)x=new DeviceInfo();x.address=address;x.name=name==null||name.trim().isEmpty()?"UNKNOWN DEVICE":name;x.rssi=r.getRssi();x.type=classify(d,x.name);x.proximity=proximity(x.rssi);x.trusted=prefs.getBoolean("trusted_"+address,false);x.isNew=isNew;x.lastSeen=now;current.put(address,x);history.put(address,now);if(isNew){saveHistory();emit("NEW_DEVICE",x.name,x.compact());}if(x.trusted)emit("TRUSTED_DEVICE_FOUND",x.name,x.compact());}

    private void stopScan(String reason){if(!scanning)return;scanning=false;try{BluetoothLeScanner s=adapter==null?null:adapter.getBluetoothLeScanner();if(s!=null&&hasPermission())s.stopScan(callback);}catch(Exception ignored){}saveHistory();Callback cb=pending;pending=null;if(cb!=null)cb.done(!reason.startsWith("BLE SCAN FAILED"),reason,summary());}
    private List<DeviceInfo> list(){List<DeviceInfo> l=new ArrayList<>(current.values());l.sort(Comparator.comparingInt((DeviceInfo d)->d.rssi).reversed());return l;}
    private String classify(BluetoothDevice d,String name){String n=name==null?"":name.toLowerCase(Locale.ROOT);if(n.contains("airpod")||n.contains("buds")||n.contains("headphone")||n.contains("ear"))return "HEADPHONES";if(n.contains("speaker"))return "SPEAKER";if(n.contains("watch")||n.contains("band"))return "WATCH";if(n.contains("phone")||n.contains("iphone")||n.contains("galaxy")||n.contains("pixel"))return "PHONE";if(n.contains("pc")||n.contains("laptop")||n.contains("surface")||n.contains("macbook"))return "PC";try{if(d.getType()==BluetoothDevice.DEVICE_TYPE_LE)return "BLE DEVICE";}catch(Exception ignored){}return "UNKNOWN";}
    private String proximity(int rssi){if(rssi>=-49)return "VERY NEAR";if(rssi>=-59)return "NEAR";if(rssi>=-69)return "MEDIUM";if(rssi>=-79)return "FAR";return "VERY FAR";}
    private void emit(String type,String msg,JSONObject data){if(events!=null)events.event(type,msg,data);}
    private void loadHistory(){String raw=prefs.getString("history","");if(raw==null||raw.isEmpty())return;String[] rows=raw.split(";");for(String row:rows){String[] p=row.split(",");if(p.length==2)try{history.put(p[0],Long.parseLong(p[1]));}catch(Exception ignored){}}}
    private void saveHistory(){StringBuilder b=new StringBuilder();int kept=0;long cutoff=System.currentTimeMillis()-30L*24L*3600L*1000L;for(Map.Entry<String,Long> e:history.entrySet()){if(e.getValue()<cutoff)continue;if(kept++>=150)break;if(b.length()>0)b.append(';');b.append(e.getKey()).append(',').append(e.getValue());}prefs.edit().putString("history",b.toString()).apply();}

    static final class DeviceInfo{
        String address,name,type,proximity;int rssi;boolean trusted,isNew;long lastSeen;
        JSONObject compact(){JSONObject o=new JSONObject();try{o.put("n",name);o.put("a",address);o.put("r",rssi);o.put("type",type);o.put("prox",proximity);o.put("t",trusted);o.put("new",isNew);o.put("ts",lastSeen);}catch(Exception ignored){}return o;}
    }
}