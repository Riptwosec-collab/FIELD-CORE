package com.riptwosec.fieldcore;

import android.content.Context;
import java.nio.charset.StandardCharsets;
import java.util.List;
import com.huawei.hmf.tasks.OnFailureListener;
import com.huawei.hmf.tasks.OnSuccessListener;
import com.huawei.wearengine.HiWear;
import com.huawei.wearengine.auth.AuthCallback;
import com.huawei.wearengine.auth.Permission;
import com.huawei.wearengine.device.Device;
import com.huawei.wearengine.device.DeviceClient;
import com.huawei.wearengine.p2p.Message;
import com.huawei.wearengine.p2p.P2pClient;
import com.huawei.wearengine.p2p.Receiver;
import com.huawei.wearengine.p2p.SendCallback;

public final class WearBridge {
    public interface Listener { void onStatus(String status); void onMessage(String json); }
    private static final int MAX_P2P_BYTES = 1024;

    private final Listener listener;
    private final P2pClient p2pClient;
    private final DeviceClient deviceClient;
    private Device connectedDevice;
    private boolean receiverRegistered;

    public WearBridge(Context context, Listener listener){
        this.listener=listener;
        p2pClient=HiWear.getP2pClient(context);
        deviceClient=HiWear.getDeviceClient(context);
        p2pClient.setPeerPkgName(BuildConfig.WATCH_PACKAGE);
        p2pClient.setPeerFingerPrint(BuildConfig.WATCH_FINGERPRINT);
    }

    public void authorize(Context context){
        HiWear.getAuthClient(context).requestPermission(new AuthCallback(){
            @Override public void onOk(Permission[] p){status("WEAR ENGINE AUTHORIZED");discover();}
            @Override public void onCancel(){status("WEAR ENGINE AUTH CANCELED");}
        }, Permission.DEVICE_MANAGER);
    }

    public void discover(){
        deviceClient.getBondedDevices().addOnSuccessListener(new OnSuccessListener<List<Device>>(){
            @Override public void onSuccess(List<Device> devices){
                connectedDevice=null;
                if(devices!=null){
                    for(Device d:devices){
                        if(d!=null&&d.isConnected()){connectedDevice=d;break;}
                    }
                }
                if(connectedDevice!=null){status("WATCH CONNECTED");registerReceiver();}
                else {receiverRegistered=false;status("NO CONNECTED HUAWEI WATCH");}
            }
        }).addOnFailureListener(new OnFailureListener(){
            @Override public void onFailure(Exception e){status("WATCH DISCOVERY ERROR: "+safeMessage(e));}
        });
    }

    private final Receiver receiver=new Receiver(){
        @Override public void onReceiveMessage(Message m){
            if(m==null||m.getData()==null)return;
            String json=new String(m.getData(),StandardCharsets.UTF_8);
            if(listener!=null)listener.onMessage(json);
        }
    };

    public void registerReceiver(){
        if(receiverRegistered||connectedDevice==null||!connectedDevice.isConnected())return;
        try{
            p2pClient.registerReceiver(connectedDevice,receiver)
                .addOnSuccessListener(v->{receiverRegistered=true;status("WATCH RECEIVER READY");})
                .addOnFailureListener(e->{receiverRegistered=false;status("RECEIVER ERROR: "+safeMessage(e));});
        }catch(Exception e){
            receiverRegistered=false;
            status("RECEIVER ERROR: "+safeMessage(e));
        }
    }

    public void unregister(){
        if(!receiverRegistered)return;
        try{p2pClient.unregisterReceiver(receiver);}catch(Exception ignored){}
        receiverRegistered=false;
    }

    public void sendJson(String json){
        if(json==null){status("WATCH MESSAGE EMPTY");return;}
        byte[] payload=json.getBytes(StandardCharsets.UTF_8);
        if(payload.length>MAX_P2P_BYTES){status("WATCH MESSAGE > 1KB: "+payload.length+" BYTES");return;}
        if(connectedDevice==null||!connectedDevice.isConnected()){
            receiverRegistered=false;
            status("WATCH OFFLINE — DISCOVER AGAIN");
            return;
        }

        Message.Builder b=new Message.Builder();
        b.setPayload(payload);
        Message m=b.build();
        p2pClient.send(connectedDevice,m,new SendCallback(){
            @Override public void onSendResult(int code){status("WATCH SEND RESULT "+code);}
            @Override public void onSendProgress(long progress){}
        }).addOnSuccessListener(v->status("WATCH SYNC QUEUED"))
          .addOnFailureListener(e->status("WATCH SEND FAILED: "+safeMessage(e)));
    }

    private String safeMessage(Exception e){return e==null||e.getMessage()==null?"UNKNOWN":e.getMessage();}
    private void status(String s){if(listener!=null)listener.onStatus(s);}
}
