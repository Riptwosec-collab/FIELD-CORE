package com.riptwosec.fieldcore;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Locale;

public class MainActivity extends Activity implements WearBridge.Listener, FieldCommandRouter.Listener {
    private static final int REQ_LOCATION=5101, REQ_VOICE=5102;
    private TextView log;
    private WearBridge wear;
    private FieldCommandRouter router;
    private PhoneLocationProvider location;
    private ProviderRegistry providers;
    private String pendingVoiceRequestId="";

    @Override protected void onCreate(Bundle b){
        super.onCreate(b);buildUi();wear=new WearBridge(this,this);location=new PhoneLocationProvider(this);providers=new ProviderRegistry(this,location);router=new FieldCommandRouter(providers,location,this);
    }
    @Override protected void onDestroy(){if(wear!=null)wear.unregister();super.onDestroy();}

    private void buildUi(){
        ScrollView sc=new ScrollView(this);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(28,28,28,28);root.setBackgroundColor(Color.rgb(2,10,11));sc.addView(root);
        root.addView(txt("FIELD CORE\nFIT 4 PRO COMPANION",22,Color.rgb(42,255,213)));
        root.addView(btn("1. AUTHORIZE WEAR ENGINE",v->wear.authorize(this)));
        root.addView(btn("2. FIND / REGISTER WATCH",v->wear.discover()));
        root.addView(btn("3. GRANT LOCATION",v->requestLocation()));
        root.addView(btn("4. SEND FIELD STATUS",v->sendSnapshot()));
        root.addView(btn("5. TEST PHONE LOCATION",v->location.lastKnown((ok,msg,data)->status(msg+" "+(data==null?"":data.toString())))));
        root.addView(btn("6. TEST LIVE WEATHER",v->providers.execute("WEATHER_REFRESH",new JSONObject(),(ok,msg,data)->status(msg+" "+(data==null?"":data.toString())))));
        root.addView(btn("7. PROVIDER STATUS",v->status(providers.status().toString())));
        log=txt("READY",13,Color.LTGRAY);log.setPadding(0,24,0,80);root.addView(log);setContentView(sc);
    }
    private Button btn(String t,View.OnClickListener l){Button b=new Button(this);b.setText(t);b.setOnClickListener(l);return b;}
    private TextView txt(String s,int sp,int c){TextView t=new TextView(this);t.setText(s);t.setTextSize(sp);t.setTextColor(c);return t;}

    private void requestLocation(){
        ArrayList<String> p=new ArrayList<>();if(checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.ACCESS_COARSE_LOCATION);if(checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED)p.add(Manifest.permission.ACCESS_FINE_LOCATION);
        if(p.isEmpty())status("LOCATION READY");else requestPermissions(p.toArray(new String[0]),REQ_LOCATION);
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grantResults){super.onRequestPermissionsResult(requestCode,permissions,grantResults);if(requestCode==REQ_LOCATION)status(location!=null&&location.hasPermission()?"LOCATION READY":"LOCATION PERMISSION REQUIRED");}

    @Override public void onStatus(final String s){runOnUiThread(()->status(s));}
    @Override public void onMessage(String json){try{router.route(new JSONObject(json));}catch(Exception e){status("WATCH JSON ERROR: "+e.getMessage());}}
    @Override public void sendToWatch(JSONObject j){wear.sendJson(j.toString());}
    @Override public void status(String s){runOnUiThread(()->{if(log!=null)log.setText(s+"\n\n"+log.getText());});}

    @Override public void requestVoice(String requestId){
        pendingVoiceRequestId=requestId==null?"":requestId;
        runOnUiThread(()->{try{Intent i=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE,Locale.getDefault());i.putExtra(RecognizerIntent.EXTRA_PROMPT,"Field Core command");startActivityForResult(i,REQ_VOICE);}catch(Exception e){status("VOICE RECOGNITION UNAVAILABLE");sendVoiceResult(pendingVoiceRequestId,false,"",null,null,"VOICE RECOGNITION UNAVAILABLE");pendingVoiceRequestId="";}});
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(request!=REQ_VOICE)return;String requestId=pendingVoiceRequestId;pendingVoiceRequestId="";
        if(result==RESULT_OK&&data!=null){ArrayList<String> r=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);handleVoice(requestId,r!=null&&!r.isEmpty()?r.get(0):"");}
        else sendVoiceResult(requestId,false,"",null,null,"VOICE CANCELED");
    }

    private void handleVoice(String requestId,String speech){
        String s=speech==null?"":speech.toLowerCase(Locale.ROOT);String action=null,slot=null;
        slot=anchorSlot(s);
        boolean returnWord=s.contains("return")||s.contains("กลับ")||s.contains("ย้อน");
        if(returnWord&&slot!=null)action="GEO_RETURN_NAMED";
        else if((s.contains("anchor")||s.contains("save location")||s.contains("บันทึกตำแหน่ง")||s.contains("ปักหมุด"))&&!returnWord)action="GEO_SAVE_TEMP";
        else if(s.contains("navigation")||s.contains("compass")||s.contains("นำทาง")||s.contains("เข็มทิศ"))action="COMPASS_START";
        else if(s.contains("weather")||s.contains("อากาศ"))action="WEATHER_REFRESH";
        else if(s.contains("emergency")||s.contains("sos")||s.contains("ฉุกเฉิน"))action="OPEN_EMERGENCY";
        else if(s.contains("breadcrumb")||s.contains("return route")||s.contains("ย้อนทาง")||s.contains("กลับทางเดิม"))action="BREADCRUMB_RETURN";
        else if(s.contains("endurance")||s.contains("ประหยัด"))action="POWER_ENDURANCE";
        else if(s.contains("performance")||s.contains("แรงสุด")||s.contains("ประสิทธิภาพ"))action="POWER_PERFORMANCE";
        else if(s.contains("balanced")||s.contains("สมดุล"))action="POWER_BALANCED";
        else if(s.contains("grid")||s.contains("ฉุกเฉินแบต")||s.contains("แบตต่ำ"))action="POWER_GRID";
        else if(s.contains("device status")||s.contains("capability")||s.contains("สถานะอุปกรณ์"))action="DEVICE_STATUS";
        else if(s.contains("timeline")||s.contains("field log")||s.contains("ประวัติภาคสนาม"))action="OPEN_TIMELINE";
        sendVoiceResult(requestId,action!=null,speech,action,slot,action==null?"VOICE INTENT UNKNOWN":"VOICE: "+action);
    }
    private String anchorSlot(String s){
        if(s.contains("car")||s.contains("รถ"))return "CAR";if(s.contains("camp")||s.contains("แคมป์")||s.contains("เต็นท์"))return "CAMP";
        if(s.contains("hotel")||s.contains("โรงแรม")||s.contains("ที่พัก"))return "HOTEL";if(s.contains("home")||s.contains("บ้าน"))return "HOME";return null;
    }
    private void sendVoiceResult(String requestId,boolean ok,String speech,String action,String slot,String message){
        try{JSONObject d=new JSONObject();d.put("speech",speech==null?"":speech);d.put("intent",action==null?"UNKNOWN":action);if(slot!=null)d.put("slot",slot);JSONObject r=new JSONObject();r.put("v",1);r.put("type","result");r.put("id",requestId==null?"":requestId);r.put("ok",ok);r.put("action","VOICE_PTT");r.put("message",message);r.put("data",d);wear.sendJson(r.toString());}catch(Exception ignored){}
    }

    @Override public void sendEmergencyLocation(String requestId){
        location.lastKnown((ok,msg,data)->{try{JSONObject r=new JSONObject();r.put("v",1);r.put("type","result");r.put("id",requestId==null?"":requestId);r.put("ok",ok);r.put("action","EMERGENCY_SEND");r.put("message",ok?"EMERGENCY LOCATION PACKET READY":"LOCATION UNAVAILABLE");if(data!=null){data.put("packetType","FIELD_CORE_SOS");data.put("generatedAt",System.currentTimeMillis());r.put("data",data);}sendToWatch(r);}catch(Exception ignored){}});
    }

    private void sendSnapshot(){
        try{JSONObject snap=new JSONObject();snap.put("type","snapshot");snap.put("ts",System.currentTimeMillis());JSONObject f=providers.status();f.put("state","PHONE READY");f.put("location",location!=null&&location.hasPermission()?"READY":"PERMISSION REQUIRED");snap.put("field",f);snap.put("summary","FIELD CORE COMPANION ONLINE");wear.sendJson(snap.toString());}catch(Exception e){status("SNAPSHOT ERROR: "+e.getMessage());}
    }
}
