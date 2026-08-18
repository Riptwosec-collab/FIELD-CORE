package com.riptwosec.fieldcore;

import org.json.JSONObject;

public final class FieldCommandRouter {
    public interface Listener {
        void sendToWatch(JSONObject json);
        void status(String s);
        void requestVoice(String requestId);
        void sendEmergencyLocation(String requestId);
    }

    private final ProviderRegistry providers;
    private final PhoneLocationProvider location;
    private final Listener listener;

    public FieldCommandRouter(ProviderRegistry p, PhoneLocationProvider l, Listener li){providers=p;location=l;listener=li;}

    public void route(JSONObject e){
        final String id=e.optString("id","");
        final String action=e.optString("action","");
        JSONObject payload=e.optJSONObject("payload");if(payload==null)payload=new JSONObject();
        if(action.length()==0){result(id,action,false,"MISSING ACTION",null);return;}
        if("VOICE_PTT".equals(action)){listener.requestVoice(id);return;}
        if("EMERGENCY_SEND".equals(action)){listener.sendEmergencyLocation(id);return;}

        if("FIELD_SYNC".equals(action)||"DEVICE_STATUS".equals(action)){
            try{
                JSONObject d=providers.status();
                d.put("phone","READY");
                d.put("location",location.hasPermission()?"READY":"PERMISSION REQUIRED");
                result(id,action,true,"FIELD CAPABILITY STATUS",d);
            }catch(Exception ignored){}
            return;
        }

        if("WATCH_LOCATION_RESULT".equals(action)){result(id,action,true,"PHONE RECEIVED WATCH LOCATION",payload);return;}
        if("PHONE_LOCATION".equals(action)){location.current((ok,msg,data)->result(id,action,ok,msg,data));return;}
        if(providers.handles(action)){final JSONObject fp=payload;providers.execute(action,fp,(ok,msg,data)->result(id,action,ok,msg,data));return;}
        result(id,action,false,"UNSUPPORTED FIELD COMMAND",null);
    }

    private void result(String id,String action,boolean ok,String message,JSONObject data){
        try{
            JSONObject r=new JSONObject();r.put("v",1);r.put("type","result");r.put("id",id);r.put("action",action);r.put("ok",ok);r.put("message",message);
            if(data!=null)r.put("data",data);listener.sendToWatch(r);
        }catch(Exception ignored){}
    }
}
