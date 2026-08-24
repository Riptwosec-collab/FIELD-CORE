package com.riptwosec.fieldcore;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

/**
 * Opt-in foreground scanner used by Outdoor Scan. Android scan throttling still applies;
 * WifiScoutManager falls back to cached scan results when the platform rejects a scan.
 */
public final class ReconScanService extends Service {
    public static final String ACTION_START="com.riptwosec.fieldcore.RECON_START";
    public static final String ACTION_STOP="com.riptwosec.fieldcore.RECON_STOP";
    public static final String EXTRA_MODE="mode";
    private static final String CHANNEL="fieldcore_recon";
    private final Handler handler=new Handler(Looper.getMainLooper());
    private WifiScoutManager wifi;
    private boolean active=false;

    @Override public void onCreate(){super.onCreate();FieldEventBus bus=new FieldEventBus(this);wifi=new WifiScoutManager(this,(t,m,d)->bus.emit(t,"NETWORK",t.contains("OPEN")||t.contains("CHANGED")?"P2":"P3",m,d));createChannel();}
    @Override public int onStartCommand(Intent intent,int flags,int startId){String action=intent==null?ACTION_START:intent.getAction();if(ACTION_STOP.equals(action)){stopSelf();return START_NOT_STICKY;}String mode=intent==null?WifiScoutManager.MODE_BALANCED:intent.getStringExtra(EXTRA_MODE);wifi.setMode(mode);active=true;startForeground(4301,notification("Outdoor Scan • "+wifi.getMode()));schedule(0);return START_STICKY;}
    @Override public void onDestroy(){active=false;handler.removeCallbacksAndMessages(null);if(wifi!=null)wifi.close();super.onDestroy();}
    @Override public IBinder onBind(Intent intent){return null;}

    private void schedule(long delay){handler.postDelayed(()->{if(!active||wifi==null)return;wifi.scan((ok,msg,data)->{updateNotification("Outdoor Scan • "+wifi.getMode()+" • "+(ok?data.optInt("count",0)+" networks":msg));schedule(Math.max(30000L,wifi.intervalMs()));});},delay);}
    private void createChannel(){if(Build.VERSION.SDK_INT>=26){NotificationManager nm=getSystemService(NotificationManager.class);if(nm!=null)nm.createNotificationChannel(new NotificationChannel(CHANNEL,"FIELD CORE Outdoor Scan",NotificationManager.IMPORTANCE_LOW));}}
    private Notification notification(String text){Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(this,CHANNEL):new Notification.Builder(this);return b.setSmallIcon(android.R.drawable.stat_sys_wifi).setContentTitle("FIELD CORE").setContentText(text).setOngoing(true).build();}
    private void updateNotification(String text){NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);if(nm!=null)nm.notify(4301,notification(text));}
}