import app from '@system.app';
import battery from '@system.battery';
import vibrator from '@system.vibrator';
import geolocation from '@system.geolocation';
import sensor from '@system.sensor';
import storage from '@system.storage';
import { P2pClient, Message, Builder } from '../../wearengine/wearengine.js';
import { PHONE_PACKAGE, PHONE_FINGERPRINT } from '../../common/constants.js';
import { getFeature } from '../../common/featureCatalog.js';

var p2pClient = new P2pClient();
var msg = new Message();
var builder = new Builder();
function nowId(){ return String(Date.now())+'-'+String(Math.floor(Math.random()*10000)); }

export default {
  data:{
    view:'home', category:'NAV', showBio:false, showSport:false, showNav:false, showEnv:false, showTactical:false, showSystem:false,
    connectionState:'OFFLINE', watchBattery:0, heartRate:'--', fieldState:'READY', pressure:'--', heading:'--',
    selectedId:'', selectedTitle:'', selectedSource:'', selectedDesc:'', featureState:'READY', featureData:'-', message:'READY',
    action1Label:'',action2Label:'',action3Label:'',action4Label:'',action1Command:'',action2Command:'',action3Command:'',action4Command:'',
    hrSubscribed:false,motionArmed:false,motionCalibrating:false,compassActive:false,barometerActive:false,breadcrumbActive:false,breadcrumbPoints:0,powerProfile:'BALANCED',sosConfirmUntil:0
  },

  onInit(){ this.refreshBattery(); this.setupWearEngine(); },
  onDestroy(){ this.stopHeartRate(); this.stopMotion(); this.stopCompass(); this.stopBarometer(); this.stopBreadcrumb(); this.stopLight(); try{p2pClient.unregisterReceiver({onSuccess:function(){},onFailure:function(){}});}catch(e){} },

  setupWearEngine(){ var self=this; try{
    p2pClient.setPeerPkgName(PHONE_PACKAGE); p2pClient.setPeerFingerPrint(PHONE_FINGERPRINT);
    p2pClient.registerReceiver({
      onSuccess:function(){self.connectionState='CONNECTED';self.message='PHONE LINK READY';},
      onFailure:function(){self.connectionState='OFFLINE';self.message='WEAR ENGINE OFFLINE';},
      onReceiveMessage:function(data){self.onPhoneMessage(data);}
    });
  }catch(e){this.connectionState='OFFLINE';this.message='INSTALL OFFICIAL WEAR ENGINE';} },

  onPhoneMessage(data){ if(!data||data.isFileType)return; try{
    var raw=(typeof data.data!=='undefined')?data.data:data; var obj=JSON.parse(String(raw));
    if(obj.type==='snapshot'){
      this.connectionState='CONNECTED';
      if(obj.field&&obj.field.state)this.fieldState=obj.field.state;
      if(obj.summary)this.featureData=String(obj.summary);
      this.message='FIELD SYNC';
    }else if(obj.type==='result'){
      this.featureState=obj.ok?'READY':'ERROR';
      this.message=(obj.ok?'OK: ':'ERROR: ')+(obj.message||obj.action||'');
      if(typeof obj.data!=='undefined')this.featureData=(typeof obj.data==='object')?JSON.stringify(obj.data):String(obj.data);
    }else if(obj.type==='haptic'){
      this.haptic(obj.pattern||'short');
      this.message=obj.message||'NAV HAPTIC';
    }
  }catch(e){this.message='RX DATA';} },

  sendCommand(action,extra){ var self=this;if(!action)return;
    if(action==='BIO_START'){this.startHeartRate();return;} if(action==='BIO_STOP'){this.stopHeartRate();return;}
    if(action==='MOTION_ARM'){this.startMotion();return;} if(action==='MOTION_DISARM'){this.stopMotion();return;} if(action==='MOTION_CALIBRATE'){this.calibrateMotion();return;}
    if(action==='COMPASS_START'){this.startCompass();return;} if(action==='COMPASS_STOP'){this.stopCompass();return;}
    if(action==='BAROMETER_START'){this.startBarometer();return;} if(action==='BAROMETER_STOP'){this.stopBarometer();return;}
    if(action==='TACTICAL_LIGHT_RED'){this.startLight('red');return;} if(action==='TACTICAL_LIGHT_WHITE'){this.startLight('white');return;} if(action==='TACTICAL_LIGHT_SOS'){this.confirmSosLight();return;}
    if(action==='FIELD_LOCATION'||action==='GEO_SAVE_TEMP'||action==='BREADCRUMB_MARK'){this.captureLocation(action);return;}
    if(action==='BREADCRUMB_START'){this.startBreadcrumb();return;} if(action==='BREADCRUMB_STOP'){this.stopBreadcrumb();return;} if(action==='BREADCRUMB_RETURN'){this.returnBreadcrumb();return;}
    if(action==='GEO_LAST'||action==='GEO_RETURN'){this.showLastAnchor(action==='GEO_RETURN');return;}
    if(action.indexOf('POWER_')===0){this.applyPowerProfile(action);return;}
    if(action==='HAPTIC_TEST'||action==='COGNITIVE_RESET'){this.haptic('short');this.message=action;return;}
    if(action==='GRID_ARM'){this.applyPowerProfile('POWER_GRID');this.fieldState='GRID-DOWN';this.message='GRID-DOWN ACTIVE';this.haptic('long');return;}

    var envelope={v:1,id:nowId(),ts:Date.now(),type:'command',action:action,source:'FIELD_CORE_FIT4PRO',payload:extra||{}};
    try{builder.setDescription(JSON.stringify(envelope));msg.builder=builder;p2pClient.send(msg,{onSuccess:function(){self.connectionState='CONNECTED';self.message='SENT '+action;},onFailure:function(){self.connectionState='OFFLINE';self.message='PHONE LINK FAILED';self.haptic('long');},onSendResult:function(){},onSendProgress:function(){}});}catch(e){this.connectionState='OFFLINE';this.message='OFFLINE: '+action;}
  },

  refreshBattery(){var self=this;try{battery.getStatus({success:function(d){self.watchBattery=Math.round((d.level||0)*100);},fail:function(){}});}catch(e){}},
  haptic(mode){try{vibrator.vibrate({mode:mode||'short',success:function(){},fail:function(){}});}catch(e){}},

  startHeartRate(){var self=this;if(this.hrSubscribed)return;try{sensor.subscribeHeartRate({success:function(ret){self.heartRate=ret.heartRate||ret.rate||ret.value||'--';self.featureData=self.heartRate+' BPM';},fail:function(){self.featureState='NO PERMISSION';self.message='HEALTH PERMISSION REQUIRED';}});this.hrSubscribed=true;this.featureState='ACTIVE';this.message='HEART RATE ACTIVE';}catch(e){this.featureState='UNAVAILABLE';this.message='HEART RATE API UNAVAILABLE';}},
  stopHeartRate(){if(!this.hrSubscribed)return;try{sensor.unsubscribeHeartRate();}catch(e){}this.hrSubscribed=false;this.message='HEART RATE STOPPED';},

  getLocationOnce(cb){try{geolocation.getLocation({success:function(d){cb(null,{lat:Number(d.latitude),lon:Number(d.longitude),accuracy:d.accuracy||null,altitude:d.altitude||null,ts:Date.now()});},fail:function(data,code){cb('LOCATION '+code,null);}});}catch(e){cb('LOCATION API',null);}},
  captureLocation(reason){var self=this;this.featureState='INITIALIZING';this.getLocationOnce(function(err,p){if(err||!p){self.featureState='NO LOCATION';self.message=err||'NO LOCATION';self.haptic('long');return;}self.featureData=String(p.lat).substring(0,9)+', '+String(p.lon).substring(0,9);self.featureState='READY';self.fieldState='GPS READY';self.haptic('short');if(reason==='GEO_SAVE_TEMP'||reason==='BREADCRUMB_MARK'){storage.set({key:'fieldcore_last_anchor',value:JSON.stringify(p),success:function(){},fail:function(){}});}self.sendCommand('WATCH_LOCATION_RESULT',{reason:reason,latitude:p.lat,longitude:p.lon,accuracy:p.accuracy,altitude:p.altitude});});},
  distanceM(a,b){var R=6371000;var p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180;var dp=(b.lat-a.lat)*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180;var x=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));},
  bearingDeg(a,b){var p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180;var y=Math.sin(dl)*Math.cos(p2);var x=Math.cos(p1)*Math.sin(p2)-Math.sin(p1)*Math.cos(p2)*Math.cos(dl);return (Math.atan2(y,x)*180/Math.PI+360)%360;},
  headingName(d){var a=['N','NE','E','SE','S','SW','W','NW'];return a[Math.round(((d%360)+360)%360/45)%8];},

  breadcrumbTimer:null,breadcrumbRoute:[],
  startBreadcrumb(){var self=this;if(this.breadcrumbActive)return;this.breadcrumbActive=true;this.breadcrumbRoute=[];this.breadcrumbPoints=0;this.featureState='ACTIVE';this.message='BREADCRUMB START';var sample=function(){self.getLocationOnce(function(err,p){if(err||!p){self.message='BREADCRUMB NO GPS';return;}var route=self.breadcrumbRoute;var last=route.length?route[route.length-1]:null;var save=!last||self.distanceM(last,p)>=50;if(save){route.push(p);if(route.length>120)route.shift();self.breadcrumbPoints=route.length;self.featureData=route.length+' POINTS';storage.set({key:'fieldcore_breadcrumb_route',value:JSON.stringify(route),success:function(){},fail:function(){}});}});};sample();this.breadcrumbTimer=setInterval(sample,(this.powerProfile==='ENDURANCE'||this.powerProfile==='GRID')?60000:30000);this.haptic('short');},
  stopBreadcrumb(){if(this.breadcrumbTimer){clearInterval(this.breadcrumbTimer);this.breadcrumbTimer=null;}this.breadcrumbActive=false;this.featureState='READY';this.message='BREADCRUMB SAVED '+this.breadcrumbPoints;this.haptic('short');},
  returnBreadcrumb(){var self=this;storage.get({key:'fieldcore_breadcrumb_route',success:function(v){try{var route=JSON.parse(v||'[]');if(!route.length){self.featureState='NO DATA';self.message='NO BREADCRUMB';return;}var base=route[0];self.getLocationOnce(function(err,cur){if(err||!cur){self.featureState='NO LOCATION';self.message='RETURN NEEDS GPS';return;}var dist=Math.round(self.distanceM(cur,base));var bearing=Math.round(self.bearingDeg(cur,base));self.featureData=dist+' M | '+bearing+'° '+self.headingName(bearing);self.featureState='RETURN';self.message='RETURN TO BASE';self.haptic('long');});}catch(e){self.featureState='ERROR';self.message='ROUTE DATA ERROR';}},fail:function(){self.featureState='NO DATA';self.message='NO BREADCRUMB';}});},
  showLastAnchor(returnMode){var self=this;storage.get({key:'fieldcore_last_anchor',success:function(v){try{var a=JSON.parse(v||'{}');if(typeof a.lat==='undefined'){self.featureState='NO DATA';self.message='NO ANCHOR';return;}if(!returnMode){self.featureData=String(a.lat).substring(0,9)+', '+String(a.lon).substring(0,9);self.message='LAST ANCHOR';return;}self.getLocationOnce(function(err,cur){if(err||!cur){self.featureState='NO LOCATION';self.message='ANCHOR RETURN NEEDS GPS';return;}var dist=Math.round(self.distanceM(cur,a));var b=Math.round(self.bearingDeg(cur,a));self.featureData=dist+' M | '+b+'° '+self.headingName(b);self.featureState='RETURN';self.message='RETURN TO ANCHOR';});}catch(e){self.featureState='ERROR';self.message='ANCHOR DATA ERROR';}},fail:function(){self.featureState='NO DATA';self.message='NO ANCHOR';}});},

  startCompass(){var self=this;if(this.compassActive)return;try{sensor.subscribeCompass({success:function(r){var d=Math.round(Number(r.direction||0));self.heading=d;self.featureData=d+'° '+self.headingName(d);self.featureState='ACTIVE';self.fieldState='COMPASS '+self.headingName(d);},fail:function(d,c){self.featureState='UNAVAILABLE';self.message='COMPASS ERROR '+c;}});this.compassActive=true;this.message='COMPASS ACTIVE';}catch(e){this.featureState='UNAVAILABLE';this.message='COMPASS API UNAVAILABLE';}},
  stopCompass(){try{sensor.unsubscribeCompass();}catch(e){}this.compassActive=false;this.message='COMPASS STOPPED';},
  startBarometer(){var self=this;if(this.barometerActive)return;try{sensor.subscribeBarometer({success:function(r){var pa=Number(r.pressure||0);var h=(pa/100).toFixed(1);self.pressure=h;self.featureData=h+' hPa';self.featureState='ACTIVE';},fail:function(d,c){self.featureState='UNAVAILABLE';self.message='BAROMETER ERROR '+c;}});this.barometerActive=true;this.message='PRESSURE ACTIVE';}catch(e){this.featureState='UNAVAILABLE';this.message='BAROMETER API UNAVAILABLE';}},
  stopBarometer(){try{sensor.unsubscribeBarometer();}catch(e){}this.barometerActive=false;this.message='PRESSURE STOPPED';},

  motionState:{baseX:0,baseY:0,baseZ:0,calCount:0,sumX:0,sumY:0,sumZ:0,lastGesture:0,lastTwist:0,twistCount:0,shakeCount:0,shakeWindow:0},
  startMotion(){var self=this;if(this.motionArmed)return;this.motionArmed=true;this.featureState='ACTIVE';this.message='MOTION ARMED';try{sensor.subscribeAccelerometer({interval:'ui',success:function(r){self.onAccel(r);},fail:function(d,c){self.motionArmed=false;self.featureState='NO PERMISSION';self.message='ACCEL ERROR '+c;}});sensor.subscribeGyroscope({interval:'ui',success:function(r){self.onGyro(r);},fail:function(){self.message='GYRO LIMITED';}});}catch(e){this.motionArmed=false;this.featureState='UNAVAILABLE';this.message='MOTION API UNAVAILABLE';}},
  stopMotion(){try{sensor.unsubscribeAccelerometer();}catch(e){}try{sensor.unsubscribeGyroscope();}catch(e){}this.motionArmed=false;this.motionCalibrating=false;this.message='MOTION DISARMED';},
  calibrateMotion(){var st=this.motionState;st.calCount=0;st.sumX=0;st.sumY=0;st.sumZ=0;this.motionCalibrating=true;this.message='CALIBRATE 0/20';if(!this.motionArmed)this.startMotion();},
  onAccel(r){var st=this.motionState;var x=Number(r.x||0),y=Number(r.y||0),z=Number(r.z||0);if(this.motionCalibrating){st.sumX+=x;st.sumY+=y;st.sumZ+=z;st.calCount++;this.message='CALIBRATE '+st.calCount+'/20';if(st.calCount>=20){st.baseX=st.sumX/20;st.baseY=st.sumY/20;st.baseZ=st.sumZ/20;this.motionCalibrating=false;this.message='CALIBRATION GOOD';this.haptic('short');}return;}var now=Date.now();if(now-st.lastGesture<900)return;var dx=x-st.baseX,dy=y-st.baseY,dz=z-st.baseZ;var mag=Math.sqrt(dx*dx+dy*dy+dz*dz);if(dx>11&&Math.abs(dy)<10){this.motionGesture('FLICK RIGHT','OPEN_NAV',90);return;}if(dx<-11&&Math.abs(dy)<10){this.motionGesture('FLICK LEFT','OPEN_HOME',90);return;}if(mag>18){if(now-st.shakeWindow>800){st.shakeWindow=now;st.shakeCount=0;}st.shakeCount++;if(st.shakeCount>=3){st.shakeCount=0;this.motionGesture('SHAKE','OPEN_EMERGENCY',92);}}},
  onGyro(r){var st=this.motionState;var now=Date.now();var z=Math.abs(Number(r.z||0));if(z>3.0){if(now-st.lastTwist<700)st.twistCount++;else st.twistCount=1;st.lastTwist=now;if(st.twistCount>=2&&now-st.lastGesture>900){st.twistCount=0;this.motionGesture('DOUBLE TWIST','SAVE_ANCHOR',90);}}},
  motionGesture(name,cmd,confidence){if(confidence<85)return;this.motionState.lastGesture=Date.now();this.featureData=name+' '+confidence+'%';this.message='GESTURE '+name;this.haptic('short');if(cmd==='OPEN_NAV')this.openFeature('8');else if(cmd==='OPEN_HOME')this.goHome();else if(cmd==='OPEN_EMERGENCY')this.openFeature('21');else if(cmd==='SAVE_ANCHOR')this.captureLocation('GEO_SAVE_TEMP');},

  applyPowerProfile(action){var p=action.replace('POWER_','');this.powerProfile=p;this.featureData=p;this.message='POWER '+p;if(p==='ENDURANCE'||p==='GRID'){this.stopMotion();this.stopBarometer();if(p==='GRID')this.stopCompass();}this.haptic('short');},

  lightTimer:null,
  startLight(mode){this.sosConfirmUntil=0;if(this.lightTimer){clearInterval(this.lightTimer);this.lightTimer=null;}this.view=mode==='white'?'lightWhite':'lightRed';this.message='TACTICAL LIGHT '+mode.toUpperCase();},
  confirmSosLight(){var now=Date.now();if(now>this.sosConfirmUntil){this.sosConfirmUntil=now+5000;this.message='SOS: TAP AGAIN WITHIN 5 SEC';this.haptic('long');return;}this.sosConfirmUntil=0;this.startSosLight();},
  startSosLight(){var self=this;var on=true;this.view='lightRed';this.message='SOS FLASH ACTIVE';this.haptic('long');this.lightTimer=setInterval(function(){on=!on;self.view=on?'lightRed':'lightBlack';},450);},
  stopLight(){if(this.lightTimer){clearInterval(this.lightTimer);this.lightTimer=null;}if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack')this.view='detail';this.sosConfirmUntil=0;},

  openFeature(id){var f=getFeature(id);if(!f)return;this.selectedId=String(id);this.selectedTitle=f.title;this.selectedSource=f.source;this.selectedDesc=f.desc;this.action1Label=f.actions[0]?f.actions[0].label:'';this.action1Command=f.actions[0]?f.actions[0].command:'';this.action2Label=f.actions[1]?f.actions[1].label:'';this.action2Command=f.actions[1]?f.actions[1].command:'';this.action3Label=f.actions[2]?f.actions[2].label:'';this.action3Command=f.actions[2]?f.actions[2].command:'';this.action4Label=f.actions[3]?f.actions[3].label:'';this.action4Command=f.actions[3]?f.actions[3].command:'';this.featureState=f.source==='UNAVAILABLE'?'API GATED':'READY';this.featureData='-';this.message='MODULE READY';this.category=f.category;this.view='detail';this.haptic('short');},
  setCategory(c){this.category=c;this.view='list';this.showBio=c==='BIO';this.showSport=c==='SPORT';this.showNav=c==='NAV';this.showEnv=c==='ENV';this.showTactical=c==='TACTICAL';this.showSystem=c==='SYSTEM';},
  goHome(){this.view='home';this.showBio=false;this.showSport=false;this.showNav=false;this.showEnv=false;this.showTactical=false;this.showSystem=false;this.refreshBattery();},
  goList(){this.setCategory(this.category);},catBio(){this.setCategory('BIO');},catSport(){this.setCategory('SPORT');},catNav(){this.setCategory('NAV');},catEnv(){this.setCategory('ENV');},catTactical(){this.setCategory('TACTICAL');},catSystem(){this.setCategory('SYSTEM');},
  quickAnchor(){this.openFeature('11');},quickBreadcrumb(){this.openFeature('10');},quickNav(){this.openFeature('8');},quickEmergency(){this.openFeature('21');},
  detailAction1(){this.sendCommand(this.action1Command);},detailAction2(){this.sendCommand(this.action2Command);},detailAction3(){this.sendCommand(this.action3Command);},detailAction4(){this.sendCommand(this.action4Command);},
  swipeEvent(e){if(e.direction==='right'){if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack'){this.stopLight();return;}if(this.view==='home')app.terminate();else if(this.view==='detail')this.goList();else this.goHome();}},
  f0(){this.openFeature('0');},
  f1(){this.openFeature('1');},
  f2(){this.openFeature('2');},
  f3(){this.openFeature('3');},
  f4(){this.openFeature('4');},
  f5(){this.openFeature('5');},
  f6(){this.openFeature('6');},
  f7(){this.openFeature('7');},
  f8(){this.openFeature('8');},
  f9(){this.openFeature('9');},
  f10(){this.openFeature('10');},
  f11(){this.openFeature('11');},
  f12(){this.openFeature('12');},
  f13(){this.openFeature('13');},
  f14(){this.openFeature('14');},
  f15(){this.openFeature('15');},
  f16(){this.openFeature('16');},
  f17(){this.openFeature('17');},
  f18(){this.openFeature('18');},
  f19(){this.openFeature('19');},
  f20(){this.openFeature('20');},
  f21(){this.openFeature('21');},
  f22(){this.openFeature('22');},
  f23(){this.openFeature('23');},
  f24(){this.openFeature('24');},
  f25(){this.openFeature('25');},
  f26(){this.openFeature('26');},
  f27(){this.openFeature('27');},
};
