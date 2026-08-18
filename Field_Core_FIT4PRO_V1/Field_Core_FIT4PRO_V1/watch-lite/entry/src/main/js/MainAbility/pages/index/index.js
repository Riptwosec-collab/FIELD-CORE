import app from '@system.app';
import battery from '@system.battery';
import vibrator from '@system.vibrator';
import geolocation from '@system.geolocation';
import sensor from '@system.sensor';
import storage from '@system.storage';
import { P2pClient, Message, Builder } from '../../wearengine/wearengine.js';
import { PHONE_PACKAGE, PHONE_FINGERPRINT } from '../../common/constants.js';
import { getFeature } from '../../common/featureCatalog.js';
import { POWER_PROFILES, adaptiveProfile, pressureTrend, fusionState, routeStats, impactUpdate, trimTimeline } from '../../common/fieldEngine.js';

var p2pClient=new P2pClient();
var msg=new Message();
var builder=new Builder();
var MAX_P2P_BYTES=1024;
function nowId(){return String(Date.now())+'-'+String(Math.floor(Math.random()*10000));}
function utf8Bytes(value){var s=String(value||''),bytes=0,i=0,c=0;for(i=0;i<s.length;i++){c=s.charCodeAt(i);if(c<0x80)bytes+=1;else if(c<0x800)bytes+=2;else if(c>=0xD800&&c<=0xDBFF&&i+1<s.length){bytes+=4;i++;}else bytes+=3;}return bytes;}
function pad2(v){v=String(v);return v.length<2?'0'+v:v;}
function timeText(ts){try{var d=new Date(Number(ts));return pad2(d.getHours())+':'+pad2(d.getMinutes());}catch(e){return '--:--';}}
function finite(v){var n=Number(v);return isFinite(n)?n:null;}

export default {
  data:{
    view:'home',category:'NAV',showBio:false,showSport:false,showNav:false,showEnv:false,showTactical:false,showSystem:false,
    connectionState:'OFFLINE',watchBattery:0,heartRate:'--',fieldState:'NORMAL',fusionReason:'FIELD NOMINAL',pressure:'--',pressureTrend:'STABLE',heading:'--',headingNameText:'--',
    gpsState:'IDLE',altitude:'--',speedKmh:'--',routeSummary:'NO ROUTE',powerProfile:'BALANCED',powerAuto:true,powerLabel:'AUTO • BALANCED',cacheState:'EMPTY',lastSync:'--',
    weatherTemp:'--',weatherUV:'--',weatherSun:'--',weatherState:'NO DATA',impactAssist:false,impactButtonLabel:'IMPACT OFF',impactPending:false,emergencyCountdown:0,
    anchorsCount:0,anchorPage:0,anchor1:'-',anchor2:'-',anchor3:'-',anchor4:'-',anchor1Meta:'',anchor2Meta:'',anchor3Meta:'',anchor4Meta:'',
    timelinePage:0,timeline1:'-',timeline2:'-',timeline3:'-',timeline4:'-',capabilityText:'LOCAL\nGPS ?  HR ?  COMPASS ?\nBAROMETER ?  MOTION ?\n\nPHONE\nOFFLINE',
    selectedId:'',selectedTitle:'',selectedSource:'',selectedDesc:'',featureState:'READY',featureData:'-',message:'READY',
    action1Label:'',action2Label:'',action3Label:'',action4Label:'',action1Command:'',action2Command:'',action3Command:'',action4Command:'',
    hrSubscribed:false,motionArmed:false,motionCalibrating:false,compassActive:false,barometerActive:false,breadcrumbActive:false,breadcrumbPoints:0,returning:false,sosConfirmUntil:0,
    advancedTitle:'COMMAND CENTER',advancedSubtitle:'FIELD INTELLIGENCE',advancedState:'NO DATA',advancedData:'NO DATA',advancedAction:'',
    wifiCount:'--',wifiOpen:'--',wifiSecured:'--',wifiBest:'NO DATA',wifiAge:'--',btCount:'--',btTrusted:'--',btUnknown:'--',
    contextMode:'UNKNOWN',contextConfidence:'--',missionLabel:'INACTIVE',envRisk:'--',quickProfile:'DAILY',notificationMode:'FIELD',stealthMode:false,fieldSettings:'--'
  },

  anchors:[],timeline:[],breadcrumbRoute:[],pressureHistory:[],lastLocation:null,previousLocation:null,weatherCache:null,phoneCapabilities:null,
  breadcrumbTimer:null,returnTimer:null,cacheTimer:null,lightTimer:null,emergencyTimer:null,lastOffRouteWarn:0,lastPressureStore:0,
  motionState:{baseX:0,baseY:0,baseZ:0,calCount:0,sumX:0,sumY:0,sumZ:0,lastGesture:0,lastTwist:0,twistCount:0,shakeCount:0,shakeWindow:0},
  impactState:{impactAt:0,stillSince:0,pending:false},

  onInit(){this.restoreLocalState();this.refreshBattery();this.setupWearEngine();this.scheduleCache();},
  onDestroy(){this.stopHeartRate();this.stopMotion();this.stopCompass();this.stopBarometer();this.stopReturn();if(this.breadcrumbTimer){clearInterval(this.breadcrumbTimer);this.breadcrumbTimer=null;}if(this.cacheTimer){clearInterval(this.cacheTimer);this.cacheTimer=null;}if(this.emergencyTimer){clearInterval(this.emergencyTimer);this.emergencyTimer=null;}this.stopLight();this.saveOfflineCache();try{p2pClient.unregisterReceiver({onSuccess:function(){},onFailure:function(){}});}catch(e){}},

  restoreLocalState(){var self=this;
    try{storage.get({key:'fieldcore_power_profile',success:function(v){if(v)self.powerProfile=String(v);self.refreshPowerLabel();},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_power_auto',success:function(v){if(v!=='')self.powerAuto=String(v)!=='false';self.refreshPowerLabel();},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_breadcrumb_route',success:function(v){try{var r=JSON.parse(v||'[]');if(r&&r.length){self.breadcrumbRoute=r;self.breadcrumbPoints=r.length;self.routeSummary=r.length+' PTS SAVED';}}catch(ignore){}},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_anchors',success:function(v){try{self.anchors=JSON.parse(v||'[]')||[];self.refreshAnchorPage();}catch(ignore){}},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_timeline',success:function(v){try{self.timeline=JSON.parse(v||'[]')||[];self.refreshTimelinePage();}catch(ignore){}},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_pressure_history',success:function(v){try{self.pressureHistory=JSON.parse(v||'[]')||[];self.updateFusion();}catch(ignore){}},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_impact_assist',success:function(v){self.impactAssist=String(v)==='true';self.impactButtonLabel=self.impactAssist?'IMPACT ON':'IMPACT OFF';if(self.impactAssist&&!self.motionArmed)self.startMotion();},fail:function(){}});}catch(e){}
    try{storage.get({key:'fieldcore_offline_cache',success:function(v){try{var c=JSON.parse(v||'{}');if(c&&c.ts){self.cacheState='READY '+timeText(c.ts);if(c.weather){self.weatherCache=c.weather;self.applyWeatherCache(c.weather,true);}}}catch(ignore){}},fail:function(){}});}catch(e){}
  },

  setupWearEngine(){var self=this;try{p2pClient.setPeerPkgName(PHONE_PACKAGE);p2pClient.setPeerFingerPrint(PHONE_FINGERPRINT);p2pClient.registerReceiver({
    onSuccess:function(){self.connectionState='CONNECTED';self.message='PHONE LINK READY';self.logEvent('LINK','PHONE CONNECTED');},
    onFailure:function(){self.connectionState='OFFLINE';self.message='WEAR ENGINE OFFLINE';},
    onReceiveMessage:function(data){self.onPhoneMessage(data);}
  });}catch(e){this.connectionState='OFFLINE';this.message='INSTALL OFFICIAL WEAR ENGINE';}},

  onPhoneMessage(data){if(!data||data.isFileType)return;try{
    var raw=(typeof data.data!=='undefined')?data.data:data;var obj=JSON.parse(String(raw));this.connectionState='CONNECTED';this.lastSync=timeText(Date.now());
    if(obj.type==='snapshot'){
      if(obj.field){this.phoneCapabilities=obj.field;this.updateCapabilityText();}if(obj.summary)this.featureData=String(obj.summary);this.message='FIELD SYNC';this.logEvent('SYNC','PHONE SNAPSHOT');
    }else if(obj.type==='result'){
      this.handleResult(obj);
      if(obj.action==='VOICE_PTT'&&obj.ok&&obj.data&&obj.data.intent)this.applyVoiceIntent(String(obj.data.intent),obj.data);
    }else if(obj.type==='haptic'){this.haptic(obj.pattern||'short');this.message=obj.message||'NAV HAPTIC';}
  }catch(e){this.message='RX DATA ERROR';}},

  handleResult(obj){var action=String(obj.action||'');this.featureState=obj.ok?'READY':'ERROR';this.message=(obj.ok?'OK: ':'ERROR: ')+(obj.message||action||'');
    if(this.isAdvancedAction(action)){this.applyAdvancedResult(action,obj);return;}
    if(action==='DEVICE_STATUS'||action==='FIELD_SYNC'){if(obj.data){this.phoneCapabilities=obj.data;this.updateCapabilityText();}return;}
    if(action==='WEATHER_REFRESH'||action==='UV_REFRESH'||action==='SUN_REFRESH'||action==='THERMAL_REFRESH'||action==='SKY_REFRESH'||action==='ASTRO_REFRESH'){
      if(obj.ok&&obj.data){this.weatherCache=this.mergeObject(this.weatherCache||{},obj.data);this.applyWeatherCache(this.weatherCache,false);this.persistWeather();this.logEvent('ENV',action.replace('_REFRESH',''));}
      else if(this.weatherCache){this.featureState='CACHED';this.applyWeatherCache(this.weatherCache,true);this.message='CACHED • '+(obj.message||'PROVIDER OFFLINE');}
      return;
    }
    if(action==='EMERGENCY_SEND'&&obj.ok){this.featureData='SOS LOCATION READY';this.logEvent('SOS','LOCATION PACKET READY');return;}
    if(typeof obj.data!=='undefined')this.featureData=this.compactData(obj.data);
  },

  mergeObject(a,b){var o={},k;for(k in a)if(a.hasOwnProperty(k))o[k]=a[k];for(k in b)if(b.hasOwnProperty(k))o[k]=b[k];return o;},
  compactData(v){if(v===null||typeof v==='undefined')return '-';if(typeof v!=='object')return String(v);var keys=['score','type','durationSec','count','heatLoad','uvIndexMax','temperatureC','apparentC','sunrise','sunset','golfScore','active'];var out=[],i,k;for(i=0;i<keys.length;i++){k=keys[i];if(typeof v[k]!=='undefined')out.push(k.toUpperCase()+': '+String(v[k]));}if(out.length)return out.join(' • ');try{var s=JSON.stringify(v);return s.length>160?s.substring(0,157)+'...':s;}catch(e){return 'DATA';}},
  applyWeatherCache(w,cached){if(!w)return;if(typeof w.temperatureC!=='undefined')this.weatherTemp=String(Math.round(Number(w.temperatureC)))+'°C';if(typeof w.uvIndexMax!=='undefined')this.weatherUV='UV '+String(Math.round(Number(w.uvIndexMax)*10)/10);if(w.sunset)this.weatherSun=String(w.sunset).substring(11,16)||String(w.sunset);this.weatherState=(cached?'CACHED ':'LIVE ')+(w.source||'PROVIDER');
    var parts=[];if(typeof w.temperatureC!=='undefined')parts.push(this.weatherTemp);if(typeof w.apparentC!=='undefined')parts.push('FEELS '+Math.round(Number(w.apparentC))+'°');if(typeof w.uvIndexMax!=='undefined')parts.push(this.weatherUV);if(w.heatLoad)parts.push('LOAD '+w.heatLoad);if(w.sunrise)parts.push('SUN '+String(w.sunrise).substring(11,16)+'-'+String(w.sunset||'').substring(11,16));this.featureData=parts.join(' • ')||'WEATHER CACHE';this.updateFusion();},
  persistWeather(){var self=this;try{storage.set({key:'fieldcore_weather_cache',value:JSON.stringify(this.weatherCache||{}),success:function(){self.saveOfflineCache();},fail:function(){}});}catch(e){}},

  isAdvancedAction(action){return action.indexOf('WIFI_')===0||action.indexOf('BT_RECON_')===0||action.indexOf('FIELD_CONTEXT')===0||action.indexOf('TELEMETRY_CONFIDENCE')===0||action.indexOf('LOST_MODE')===0||action.indexOf('MISSION_')===0||action.indexOf('ENV_RISK')===0||action.indexOf('SENSOR_SELF_TEST')===0||action.indexOf('TIMELINE_PRO')===0||action.indexOf('VOICE_MACRO')===0||action.indexOf('NOTIFICATION_FILTER')===0||action.indexOf('RUN_ZONE')===0||action.indexOf('SKY_PRO')===0||action.indexOf('STEALTH')===0||action.indexOf('RETURN_DECISION')===0||action.indexOf('QUICK_PROFILE')===0||action.indexOf('IMPACT_REVIEW')===0||action.indexOf('COMMAND_CENTER')===0||action.indexOf('CYBER_SWEEP')===0||action.indexOf('OUTDOOR_SCAN')===0||action.indexOf('EMERGENCY_ESCALATION')===0||action.indexOf('ALERT_')===0;},
  pick(o,k,fallback){return o&&typeof o[k]!=='undefined'?o[k]:fallback;},
  compactAdvanced(v){if(!v)return 'NO DATA';if(typeof v!=='object')return String(v);var keys=['status','mode','decision','profile','recommended','level','score','confidence','count','networks','open','secured','trusted','new','unknown','durationSec','ageSec','active'],out=[],i,k;for(i=0;i<keys.length;i++){k=keys[i];if(typeof v[k]!=='undefined'&&v[k]!==null)out.push(k.toUpperCase()+': '+String(v[k]));}if(out.length)return out.join(' • ');try{var s=JSON.stringify(v);return s.length>230?s.substring(0,227)+'...':s;}catch(e){return 'DATA READY';}},
  applyAdvancedResult(action,obj){var d=obj&&obj.data?obj.data:{};this.advancedState=obj&&obj.ok?'READY':'ERROR';this.advancedData=this.compactAdvanced(d);this.featureData=this.advancedData;this.message=(obj&&obj.ok?'OK: ':'ERROR: ')+(obj&&obj.message?obj.message:action);this.lastSync=timeText(Date.now());
    if(action.indexOf('WIFI_')===0||action.indexOf('OUTDOOR_SCAN')===0){this.wifiCount=this.pick(d,'count',this.pick(d,'total',this.pick(d,'networks',this.wifiCount)));this.wifiOpen=this.pick(d,'open',this.wifiOpen);this.wifiSecured=this.pick(d,'secured',this.wifiSecured);this.wifiAge=this.pick(d,'ageSec',this.wifiAge);var b=d.best&&d.best.network?d.best.network:(d.best||d.strongest||null);if(b)this.wifiBest=String(this.pick(b,'s',this.pick(b,'ssid','AVAILABLE')));}
    if(action.indexOf('BT_RECON_')===0){this.btCount=this.pick(d,'count',this.pick(d,'total',this.btCount));this.btTrusted=this.pick(d,'trusted',this.btTrusted);this.btUnknown=this.pick(d,'unknown',this.btUnknown);}
    if(action==='CYBER_SWEEP'){var w=d.wifi||{},b2=d.bluetooth||{};this.wifiCount=this.pick(w,'count',this.wifiCount);this.wifiOpen=this.pick(w,'open',this.wifiOpen);this.btCount=this.pick(b2,'count',this.btCount);this.btTrusted=this.pick(b2,'trusted',this.btTrusted);this.btUnknown=this.pick(b2,'unknown',this.btUnknown);}
    if(action==='FIELD_CONTEXT_STATUS'){this.contextMode=String(this.pick(d,'mode','UNKNOWN'));this.contextConfidence=String(this.pick(d,'confidence','--'));}
    if(action==='ENV_RISK_STATUS'){this.envRisk=String(this.pick(d,'level','--'));}
    if(action==='MISSION_STATUS'||action==='MISSION_START'||action==='MISSION_STOP'){this.missionLabel=this.pick(d,'active',false)?'ACTIVE':'INACTIVE';}
    if(action==='QUICK_PROFILE_STATUS'||action==='QUICK_PROFILE_SET'){this.quickProfile=String(this.pick(d,'profile',this.quickProfile));var pp=String(this.pick(d,'power','AUTO'));if(pp==='ENDURANCE')this.applyPowerProfileInternal('ENDURANCE',false);else if(pp==='AUTO')this.enableAutoPower();}
    if(action==='STEALTH_STATUS'||action==='STEALTH_SET'){this.stealthMode=!!this.pick(d,'enabled',this.stealthMode);}
    if(action==='FIELD_SETTINGS_STATUS'||action==='FIELD_SETTINGS_SET'){this.fieldSettings=this.compactAdvanced(d);this.notificationMode=String(this.pick(d,'notificationFilter',this.notificationMode));}
    if(action==='NOTIFICATION_FILTER_STATUS'||action==='NOTIFICATION_FILTER_SET'){this.notificationMode=String(this.pick(d,'mode',this.notificationMode));}
    if(action==='COMMAND_CENTER'){var c=d.context||{},w2=d.wifi||{},bt=d.devices||{},env=d.environment||{},ms=d.mission||{};this.contextMode=String(this.pick(c,'mode',this.contextMode));this.contextConfidence=String(this.pick(c,'confidence',this.contextConfidence));this.wifiCount=this.pick(w2,'count',this.wifiCount);this.wifiOpen=this.pick(w2,'open',this.wifiOpen);this.btCount=this.pick(bt,'count',this.btCount);this.btTrusted=this.pick(bt,'trusted',this.btTrusted);this.envRisk=String(this.pick(env,'level',this.envRisk));this.missionLabel=this.pick(ms,'active',false)?'ACTIVE':'INACTIVE';this.quickProfile=String(this.pick(d,'profile',this.quickProfile));this.notificationMode=String(this.pick(d,'notification',this.notificationMode));}
    this.logEvent('ADV',action+' '+(obj&&obj.ok?'OK':'ERROR'));
  },
  advancedPayload(extra){var p={battery:this.watchBattery,heartRate:this.heartRate,speedKmh:this.speedKmh,altitude:this.altitude,gpsState:this.gpsState,gpsAvailable:!!this.lastLocation,gpsAccuracyM:this.lastLocation&&this.lastLocation.accuracy?Number(this.lastLocation.accuracy):null,gpsAgeMs:this.lastLocation?Date.now()-Number(this.lastLocation.ts||0):null,hrAvailable:this.hrSubscribed,compassAvailable:this.compassActive,barometerAvailable:this.barometerActive,motionAvailable:this.motionArmed,emergency:this.emergencyCountdown>0||this.impactPending,returnAvailable:this.breadcrumbRoute.length>0,missionMinutes:0,weatherState:this.weatherState};if(this.lastLocation&&this.breadcrumbRoute.length){var rs=routeStats(this.lastLocation,this.breadcrumbRoute,(function(self){return function(a,b){return self.distanceM(a,b);};})(this),(function(self){return function(a,b){return self.bearingDeg(a,b);};})(this));if(rs){p.returnDistanceM=rs.distanceToBaseM;p.returnEtaMin=rs.etaMin;}}var k;if(extra)for(k in extra)if(extra.hasOwnProperty(k))p[k]=extra[k];return p;},
  openAdvanced(title,subtitle,action,extra){this.advancedTitle=title;this.advancedSubtitle=subtitle||'FIELD INTELLIGENCE';this.advancedAction=action||'';this.advancedState='LOADING';this.advancedData='WAITING FOR PHONE';this.view='advanced';if(action)this.sendCommand(action,this.advancedPayload(extra));this.haptic('short');},
  openAdvancedHub(){this.view='advancedHub';this.haptic('short');},
  openCommandCenter(){this.openAdvanced('COMMAND CENTER','UNIFIED FIELD CORE','COMMAND_CENTER');},
  openWifiScout(){this.view='wifiScout';this.advancedTitle='WI-FI SCOUT';this.advancedSubtitle='PHONE SCAN • LOCAL DATA';this.sendCommand('WIFI_STATUS',this.advancedPayload());this.haptic('short');},
  openReconHub(){this.openWifiScout();},
  advancedRefresh(){if(this.advancedAction)this.sendCommand(this.advancedAction,this.advancedPayload());},
  advancedBack(){if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';else this.goHome();},
  advContext(){this.openAdvanced('FIELD CONTEXT','CONTEXT AWARENESS','FIELD_CONTEXT_STATUS');},
  advTelemetry(){this.openAdvanced('TELEMETRY CONFIDENCE','DATA QUALITY','TELEMETRY_CONFIDENCE');},
  advLostMode(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STATUS');},
  advMissionPack(){this.openAdvanced('MISSION PACK','OFFLINE MISSION DATA','MISSION_PACK_STATUS');},
  advEnvRisk(){var temp=String(this.weatherTemp||'').replace(/[^0-9.-]/g,''),uv=String(this.weatherUV||'').replace(/[^0-9.]/g,'');this.openAdvanced('ENVIRONMENT RISK','DECISION SUPPORT','ENV_RISK_STATUS',{temperatureC:finite(temp),uv:finite(uv),altitudeM:this.lastLocation&&finite(this.lastLocation.altitude)!==null?Number(this.lastLocation.altitude):null});},
  advSensorTest(){this.openAdvanced('SENSOR SELF-TEST','DIAGNOSTICS','SENSOR_SELF_TEST');},
  advTimeline(){this.openAdvanced('MISSION TIMELINE PRO','UNIFIED EVENT LOG','TIMELINE_PRO',{filter:'ALL',limit:6});},
  advVoiceMacro(){this.openAdvanced('VOICE MACRO ENGINE','WHITELISTED COMMANDS','VOICE_MACRO_STATUS');},
  advNotification(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_STATUS');},
  advBtRecon(){this.openAdvanced('NEARBY DEVICE RECON','PHONE BLE SCAN','BT_RECON_STATUS');},
  advBtScan(){this.openAdvanced('NEARBY DEVICE RECON','PHONE BLE SCAN','BT_RECON_SCAN');},
  advRunZone(){this.openAdvanced('RUNNING ZONE HUD','REAL RUN TELEMETRY','RUN_ZONE_STATUS');},
  advSkyPro(){this.openAdvanced('SKY SCANNER PRO','OUTDOOR / PHOTO','SKY_PRO_STATUS');},
  advStealth(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_STATUS');},
  advReturnDecision(){this.openAdvanced('RETURN DECISION HUD','DECISION SUPPORT','RETURN_DECISION',{battery:this.watchBattery,returnDistanceM:-1,returnEtaMin:-1,sunsetInMin:-1});},
  advProfiles(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_STATUS');},
  advImpactReview(){this.openAdvanced('IMPACT REVIEW','EVENT SNAPSHOT','IMPACT_REVIEW_STATUS');},
  advEmergencyEscalation(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_STATUS');},
  advPowerAuto(){this.openFeature('24');},
  advSmartAnchor(){this.openFeature('11');},
  advSettings(){this.openAdvanced('FIELD CORE SETTINGS','PRIVACY / POWER / ALERTS','FIELD_SETTINGS_STATUS');},
  advStealthOn(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:true});},
  advStealthOff(){this.openAdvanced('NIGHT / STEALTH HUD','LOW MOTION / LOW ALERT','STEALTH_SET',{enabled:false});},
  advProfileDaily(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'DAILY'});},
  advProfileOutdoor(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'OUTDOOR'});},
  advProfileRunning(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'RUNNING'});},
  advProfileNight(){this.openAdvanced('FIELD QUICK PROFILES','MULTI-SYSTEM PRESETS','QUICK_PROFILE_SET',{profile:'NIGHT'});},
  advMissionStart(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_START');},advMissionStop(){this.openAdvanced('MISSION PACK','MISSION CONTROL','MISSION_STOP');},
  advLostStart(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');},advLostStop(){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_STOP');},
  advNotifyField(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'FIELD'});},advNotifyMission(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'MISSION'});},advNotifyStealth(){this.openAdvanced('NOTIFICATION FILTER','FIELD PRIORITIES','NOTIFICATION_FILTER_SET',{mode:'STEALTH'});},
  advEmergencyLevel0(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:0,reason:'USER'});},advEmergencyLevel1(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:1,reason:'USER CHECK'});},advEmergencyLevel2(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:2,reason:'USER WARNING'});},advEmergencyLevel3(){this.openAdvanced('EMERGENCY ESCALATION','LEVEL 0–3','EMERGENCY_ESCALATION_SET',{level:3,reason:'USER SOS'});},
  advBtHistory(){this.openAdvanced('DEVICE HISTORY','LOCAL BLE HISTORY','BT_RECON_HISTORY',{limit:6});},
  advWifiSignal(){this.openAdvanced('SIGNAL HUNT','RSSI TREND • NOT DIRECTION','WIFI_SIGNAL_HUNT');},
  advWifiDuplicates(){this.openAdvanced('DUPLICATE SSID','CHECK BEFORE CONNECTING','WIFI_DUPLICATES');},

  advWifiScan(){this.view='wifiScout';this.advancedState='SCANNING';this.advancedData='WAITING FOR PHONE SCAN';this.sendCommand('WIFI_SCAN',this.advancedPayload());},
  advWifiNetworks(){this.openAdvanced('NEARBY NETWORKS','RSSI STRONGEST FIRST','WIFI_NETWORKS',{page:0,size:4,filter:'ALL',sort:'SIGNAL'});},
  advWifiOpen(){this.openAdvanced('OPEN WI-FI','OPEN DOES NOT MEAN FREE','WIFI_OPEN',{page:0});},
  advWifiBest(){this.openAdvanced('BEST WI-FI','QUALITY RECOMMENDATION','WIFI_BEST');},
  advWifiChannels(){this.openAdvanced('CHANNELS','CHANNEL LOAD','WIFI_CHANNELS');},
  advWifiHistory(){this.openAdvanced('WI-FI HISTORY','LOCAL ONLY','WIFI_HISTORY');},
  advWifiTrusted(){this.openAdvanced('TRUSTED WI-FI','USER TRUST LIST','WIFI_TRUSTED');},
  advWifiOutdoor(){this.openAdvanced('OUTDOOR SCAN','BALANCED BACKGROUND SCAN','OUTDOOR_SCAN_START',{mode:'BALANCED'});},
  advCyberSweep(){this.openAdvanced('CYBER SWEEP','WI-FI + BLUETOOTH','CYBER_SWEEP');},
  applyVoiceIntent(intent,data){var slot=data&&data.slot?String(data.slot):null;
    if(intent==='OPEN_EMERGENCY'){this.openFeature('21');this.message='VOICE: EMERGENCY CORE';return;}
    if(intent==='GEO_SAVE_TEMP'){this.saveAnchor(slot);return;}
    if(intent==='GEO_RETURN_NAMED'){this.returnNamedAnchor(slot);return;}
    if(intent==='COMPASS_START'){this.openFeature('8');this.startCompass();return;}
    if(intent==='BREADCRUMB_RETURN'){this.openFeature('10');this.returnBreadcrumb();return;}
    if(intent==='WEATHER_REFRESH'){this.openFeature('13');this.sendCommand('WEATHER_REFRESH');return;}
    if(intent.indexOf('POWER_')===0){this.openFeature('24');this.applyPowerProfile(intent);return;}
    if(intent==='DEVICE_STATUS'){this.openCapabilities();this.sendCommand('DEVICE_STATUS');return;}
    if(intent==='OPEN_TIMELINE'){this.openTimeline();return;}
    if(intent==='CYBER_SWEEP'){this.advCyberSweep();return;}
    if(intent==='WIFI_SCAN'){this.openWifiScout();this.advWifiScan();return;}
    if(intent==='OUTDOOR_SCAN_START'){this.advWifiOutdoor();return;}
    if(intent==='MISSION_START'){this.openAdvanced('MISSION','MISSION CONTROL','MISSION_START');return;}
    if(intent==='COMMAND_CENTER'){this.openCommandCenter();return;}
    if(intent==='LOST_MODE_START'){this.openAdvanced('LOST MODE PRO','RETURN / PHONE / SAFE POINT','LOST_MODE_START');return;}
    this.message='VOICE INTENT UNSUPPORTED';
  },

  sendCommand(action,extra){var self=this;if(!action)return;
    if(action==='BIO_START'){this.startHeartRate();return;}if(action==='BIO_STOP'){this.stopHeartRate();return;}
    if(action==='MOTION_ARM'){this.startMotion();return;}if(action==='MOTION_DISARM'){this.stopMotion();return;}if(action==='MOTION_CALIBRATE'){this.calibrateMotion();return;}
    if(action==='COMPASS_START'){this.startCompass();return;}if(action==='COMPASS_STOP'){this.stopCompass();return;}
    if(action==='BAROMETER_START'){this.startBarometer();return;}if(action==='BAROMETER_STOP'){this.stopBarometer();return;}
    if(action==='TACTICAL_LIGHT_RED'){this.startLight('red');return;}if(action==='TACTICAL_LIGHT_WHITE'){this.startLight('white');return;}if(action==='TACTICAL_LIGHT_SOS'){this.confirmSosLight();return;}
    if(action==='FIELD_LOCATION'){this.captureLocation('FIELD_LOCATION');return;}if(action==='GEO_SAVE_TEMP'){this.saveAnchor(extra&&extra.name?extra.name:null);return;}if(action==='BREADCRUMB_MARK'){this.captureLocation('BREADCRUMB_MARK');return;}
    if(action==='BREADCRUMB_START'){this.startBreadcrumb();return;}if(action==='BREADCRUMB_STOP'){this.stopBreadcrumb();return;}if(action==='BREADCRUMB_RETURN'){this.returnBreadcrumb();return;}
    if(action==='GEO_LAST'){this.showLastAnchor(false);return;}if(action==='GEO_RETURN'){this.showLastAnchor(true);return;}if(action==='OPEN_ANCHORS'){this.openAnchors();return;}
    if(action==='OPEN_TIMELINE'){this.openTimeline();return;}if(action==='OPEN_CAPABILITIES'){this.openCapabilities();return;}if(action==='FIELD_FUSION'){this.updateFusion();this.featureData=this.fieldState+' • '+this.fusionReason+' • P '+this.pressureTrend;return;}
    if(action==='POWER_AUTO'){this.enableAutoPower();return;}if(action.indexOf('POWER_')===0){this.applyPowerProfile(action);return;}
    if(action==='HAPTIC_TEST'||action==='COGNITIVE_RESET'){this.haptic('short');this.message=action;return;}
    if(action==='GRID_ARM'){this.powerAuto=false;this.applyPowerProfileInternal('GRID',true);this.fieldState='GRID-DOWN';this.message='GRID-DOWN ACTIVE';this.logEvent('POWER','GRID-DOWN ACTIVE');this.haptic('long');return;}

    var envelope={v:1,id:nowId(),ts:Date.now(),type:'command',action:action,source:'FIELD_CORE_FIT4PRO',payload:extra||{}};var wire=JSON.stringify(envelope);
    if(utf8Bytes(wire)>MAX_P2P_BYTES){this.featureState='ERROR';this.message='P2P PAYLOAD > 1KB';this.haptic('long');return;}
    try{builder.setDescription(wire);msg.builder=builder;p2pClient.send(msg,{onSuccess:function(){self.connectionState='CONNECTED';self.message='SENT '+action;},onFailure:function(){self.connectionState='OFFLINE';self.message='PHONE LINK FAILED';self.haptic('long');},onSendResult:function(){},onSendProgress:function(){}});}catch(e){this.connectionState='OFFLINE';this.message='OFFLINE: '+action;}
  },

  refreshBattery(){var self=this;try{battery.getStatus({success:function(d){var level=Number(d.level||0);self.watchBattery=Math.round(level<=1?level*100:level);self.updateAdaptivePower();self.updateFusion();},fail:function(){}});}catch(e){}},
  haptic(mode){try{vibrator.vibrate({mode:mode||'short',success:function(){},fail:function(){}});}catch(e){}},

  startHeartRate(){var self=this;if(this.hrSubscribed)return;try{sensor.subscribeHeartRate({success:function(ret){self.hrSubscribed=true;self.heartRate=ret.heartRate||ret.rate||ret.value||'--';self.featureData=self.heartRate+' BPM';self.featureState='ACTIVE';self.updateFusion();},fail:function(){self.hrSubscribed=false;self.featureState='NO PERMISSION';self.message='HEALTH PERMISSION REQUIRED';self.updateCapabilityText();}});this.featureState='INITIALIZING';this.message='HEART RATE STARTING';this.logEvent('BIO','HEART RATE START');}catch(e){this.hrSubscribed=false;this.featureState='UNAVAILABLE';this.message='HEART RATE API UNAVAILABLE';}},
  stopHeartRate(){try{sensor.unsubscribeHeartRate();}catch(e){}this.hrSubscribed=false;this.message='HEART RATE STOPPED';this.logEvent('BIO','HEART RATE STOP');this.updateCapabilityText();},

  getLocationOnce(cb){var self=this;try{geolocation.getLocation({success:function(d){var p={lat:Number(d.latitude),lon:Number(d.longitude),accuracy:d.accuracy||null,altitude:typeof d.altitude!=='undefined'?d.altitude:null,speed:typeof d.speed!=='undefined'?d.speed:null,ts:Date.now()};self.acceptLocation(p);cb(null,p);},fail:function(data,code){self.gpsState='ERROR';cb('LOCATION '+code,null);}});}catch(e){this.gpsState='UNAVAILABLE';cb('LOCATION API',null);}},
  acceptLocation(p){if(!p)return;this.previousLocation=this.lastLocation;this.lastLocation=p;this.gpsState='LOCK ±'+(p.accuracy?Math.round(Number(p.accuracy)):'?')+'m';if(p.altitude!==null&&typeof p.altitude!=='undefined')this.altitude=Math.round(Number(p.altitude))+'m';
    var speed=finite(p.speed);if(speed!==null)this.speedKmh=(Math.round(speed*3.6*10)/10).toFixed(1);else if(this.previousLocation&&p.ts>this.previousLocation.ts){var dt=(p.ts-this.previousLocation.ts)/1000,dm=this.distanceM(this.previousLocation,p);if(dt>0&&dt<300)this.speedKmh=(Math.round((dm/dt*3.6)*10)/10).toFixed(1);}
    this.saveOfflineCache();this.updateFusion();},
  captureLocation(reason){var self=this;this.featureState='INITIALIZING';this.getLocationOnce(function(err,p){if(err||!p){self.featureState='NO LOCATION';self.message=err||'NO LOCATION';self.haptic('long');return;}self.featureData=String(p.lat).substring(0,9)+', '+String(p.lon).substring(0,9);self.featureState='READY';self.haptic('short');if(reason==='BREADCRUMB_MARK')self.appendBreadcrumbPoint(p,true);self.logEvent('GPS',reason);self.sendCommand('WATCH_LOCATION_RESULT',{reason:reason,latitude:p.lat,longitude:p.lon,accuracy:p.accuracy,altitude:p.altitude});});},
  distanceM(a,b){var R=6371000,p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180,dp=(b.lat-a.lat)*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180,x=Math.sin(dp/2)*Math.sin(dp/2)+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)*Math.sin(dl/2);return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));},
  bearingDeg(a,b){var p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180,y=Math.sin(dl)*Math.cos(p2),x=Math.cos(p1)*Math.sin(p2)-Math.sin(p1)*Math.cos(p2)*Math.cos(dl);return (Math.atan2(y,x)*180/Math.PI+360)%360;},
  headingName(d){var a=['N','NE','E','SE','S','SW','W','NW'];return a[Math.round(((d%360)+360)%360/45)%8];},

  saveAnchor(name){var self=this;this.getLocationOnce(function(err,p){if(err||!p){self.featureState='NO LOCATION';self.message='ANCHOR NEEDS GPS';return;}var n=name?String(name).toUpperCase():'ANCHOR '+String(self.anchors.length+1);var a={id:nowId(),name:n,lat:p.lat,lon:p.lon,accuracy:p.accuracy,altitude:p.altitude,ts:p.ts};
      var i=-1,j;for(j=0;j<self.anchors.length;j++)if(String(self.anchors[j].name).toUpperCase()===n){i=j;break;}if(i>=0)self.anchors.splice(i,1);self.anchors.push(a);if(self.anchors.length>20)self.anchors.shift();
      try{storage.set({key:'fieldcore_anchors',value:JSON.stringify(self.anchors),success:function(){},fail:function(){}});storage.set({key:'fieldcore_last_anchor',value:JSON.stringify(a),success:function(){},fail:function(){}});}catch(e){}
      self.featureData=n+' SAVED';self.message='ANCHOR SAVED';self.refreshAnchorPage();self.logEvent('ANCHOR',n+' SAVED');self.haptic('short');});},
  findAnchor(name){if(!name)return null;var n=String(name).toUpperCase(),i;for(i=this.anchors.length-1;i>=0;i--)if(String(this.anchors[i].name).toUpperCase()===n)return this.anchors[i];return null;},
  returnNamedAnchor(name){var a=this.findAnchor(name);if(!a){this.message='ANCHOR '+String(name||'')+' NOT FOUND';this.openAnchors();return;}this.returnToAnchor(a);},
  returnToAnchor(a){var self=this;if(!a)return;this.getLocationOnce(function(err,cur){if(err||!cur){self.featureState='NO LOCATION';self.message='ANCHOR RETURN NEEDS GPS';return;}var dist=Math.round(self.distanceM(cur,a)),b=Math.round(self.bearingDeg(cur,a));self.featureData=a.name+' • '+dist+'m • '+b+'° '+self.headingName(b);self.featureState='RETURN';self.message='RETURN TO '+a.name;self.logEvent('NAV','RETURN '+a.name);self.haptic('long');});},
  showLastAnchor(returnMode){var a=this.anchors.length?this.anchors[this.anchors.length-1]:null;if(a){if(returnMode)this.returnToAnchor(a);else{this.featureData=a.name+' • '+String(a.lat).substring(0,9)+', '+String(a.lon).substring(0,9);this.message='LAST ANCHOR';}return;}var self=this;try{storage.get({key:'fieldcore_last_anchor',success:function(v){try{var x=JSON.parse(v||'{}');if(typeof x.lat==='undefined'){self.message='NO ANCHOR';return;}if(returnMode)self.returnToAnchor(x);else self.featureData=String(x.lat).substring(0,9)+', '+String(x.lon).substring(0,9);}catch(e){self.message='ANCHOR DATA ERROR';}},fail:function(){self.message='NO ANCHOR';}});}catch(e){}},
  openAnchors(){this.refreshAnchorPage();this.view='anchors';this.haptic('short');},
  refreshAnchorPage(){this.anchorsCount=this.anchors.length;var start=this.anchorPage*4;if(start>=this.anchors.length&&this.anchorPage>0){this.anchorPage--;start=this.anchorPage*4;}var i,a,labels=[],meta=[];for(i=0;i<4;i++){a=this.anchors[start+i];labels[i]=a?(a.name||('ANCHOR '+(start+i+1))):'-';meta[i]=a?(timeText(a.ts)+' • '+(a.altitude!==null&&typeof a.altitude!=='undefined'?Math.round(Number(a.altitude))+'m':'GPS')):'';}this.anchor1=labels[0];this.anchor2=labels[1];this.anchor3=labels[2];this.anchor4=labels[3];this.anchor1Meta=meta[0];this.anchor2Meta=meta[1];this.anchor3Meta=meta[2];this.anchor4Meta=meta[3];},
  anchorPrev(){if(this.anchorPage>0)this.anchorPage--;this.refreshAnchorPage();},anchorNext(){if((this.anchorPage+1)*4<this.anchors.length)this.anchorPage++;this.refreshAnchorPage();},
  returnAnchorAt(offset){var a=this.anchors[this.anchorPage*4+offset];if(a)this.returnToAnchor(a);},anchor1Return(){this.returnAnchorAt(0);},anchor2Return(){this.returnAnchorAt(1);},anchor3Return(){this.returnAnchorAt(2);},anchor4Return(){this.returnAnchorAt(3);},
  deleteLastAnchor(){if(!this.anchors.length){this.message='NO ANCHOR';return;}var a=this.anchors.pop();try{storage.set({key:'fieldcore_anchors',value:JSON.stringify(this.anchors),success:function(){},fail:function(){}});}catch(e){}this.logEvent('ANCHOR','DELETE '+a.name);this.refreshAnchorPage();},

  breadcrumbIntervalMs(){var p=POWER_PROFILES[this.powerProfile]||POWER_PROFILES.BALANCED;return p.breadcrumbMs;},
  breadcrumbMinDistance(){return this.powerProfile==='PERFORMANCE'?15:(this.powerProfile==='BALANCED'?30:(this.powerProfile==='ENDURANCE'?60:100));},
  appendBreadcrumbPoint(p,force){var route=this.breadcrumbRoute||[],last=route.length?route[route.length-1]:null;if(!force&&last&&this.distanceM(last,p)<this.breadcrumbMinDistance())return false;route.push(p);if(route.length>120)route.shift();this.breadcrumbRoute=route;this.breadcrumbPoints=route.length;this.routeSummary=route.length+' PTS • '+this.powerProfile;try{storage.set({key:'fieldcore_breadcrumb_route',value:JSON.stringify(route),success:function(){},fail:function(){}});}catch(e){}return true;},
  sampleBreadcrumb(){var self=this;this.getLocationOnce(function(err,p){if(err||!p){self.message='BREADCRUMB NO GPS';return;}self.appendBreadcrumbPoint(p,false);});},
  scheduleBreadcrumb(){var self=this;if(this.breadcrumbTimer){clearInterval(this.breadcrumbTimer);this.breadcrumbTimer=null;}if(this.breadcrumbActive)this.breadcrumbTimer=setInterval(function(){self.sampleBreadcrumb();},this.breadcrumbIntervalMs());},
  startBreadcrumb(){if(this.breadcrumbActive)return;this.breadcrumbActive=true;this.featureState='ACTIVE';this.message=this.breadcrumbRoute.length?'BREADCRUMB RESUMED':'BREADCRUMB START';this.sampleBreadcrumb();this.scheduleBreadcrumb();this.logEvent('ROUTE',this.breadcrumbRoute.length?'RESUME':'START');this.haptic('short');},
  newBreadcrumb(){this.stopReturn();this.breadcrumbRoute=[];this.breadcrumbPoints=0;this.routeSummary='NEW ROUTE';try{storage.set({key:'fieldcore_breadcrumb_route',value:'[]',success:function(){},fail:function(){}});}catch(e){}this.breadcrumbActive=false;this.startBreadcrumb();},
  stopBreadcrumb(){if(this.breadcrumbTimer){clearInterval(this.breadcrumbTimer);this.breadcrumbTimer=null;}this.breadcrumbActive=false;this.featureState='READY';this.message='BREADCRUMB SAVED '+this.breadcrumbPoints;this.logEvent('ROUTE','SAVED '+this.breadcrumbPoints+' PTS');this.haptic('short');},
  returnBreadcrumb(){if(!this.breadcrumbRoute.length){this.featureState='NO DATA';this.message='NO BREADCRUMB';return;}this.returning=true;this.updateReturnGuidance();this.scheduleReturn();this.updateAdaptivePower();this.logEvent('NAV','RETURN TO BASE');},
  scheduleReturn(){var self=this;if(this.returnTimer){clearInterval(this.returnTimer);this.returnTimer=null;}this.returnTimer=setInterval(function(){self.updateReturnGuidance();},Math.max(10000,Math.min(30000,this.breadcrumbIntervalMs())));},
  updateReturnGuidance(){var self=this;if(!this.returning)return;this.getLocationOnce(function(err,cur){if(err||!cur){self.message='RETURN NEEDS GPS';return;}var stats=routeStats(cur,self.breadcrumbRoute,function(a,b){return self.distanceM(a,b);},function(a,b){return self.bearingDeg(a,b);});if(!stats)return;var eta=stats.etaMin!==null?' • ETA '+stats.etaMin+'m':'';self.featureData=stats.distanceToBaseM+'m • '+stats.bearing+'° '+self.headingName(stats.bearing)+eta;self.routeSummary='BASE '+stats.distanceToBaseM+'m • '+stats.points+' PTS';self.featureState='RETURN';self.message='RETURN TO BASE';
      var nearest=999999,i,d;for(i=0;i<self.breadcrumbRoute.length;i++){d=self.distanceM(cur,self.breadcrumbRoute[i]);if(d<nearest)nearest=d;}if(nearest>120&&Date.now()-self.lastOffRouteWarn>30000){self.lastOffRouteWarn=Date.now();self.message='OFF ROUTE '+Math.round(nearest)+'m';self.haptic('long');self.logEvent('NAV','OFF ROUTE '+Math.round(nearest)+'m');}
      if(stats.distanceToBaseM<25){self.message='BASE REACHED';self.haptic('long');self.stopReturn();}});},
  stopReturn(){if(this.returnTimer){clearInterval(this.returnTimer);this.returnTimer=null;}this.returning=false;this.updateAdaptivePower();},

  startCompass(){var self=this;if(this.compassActive)return;try{sensor.subscribeCompass({success:function(r){self.compassActive=true;var d=Math.round(Number(r.direction||0));self.heading=d;self.headingNameText=self.headingName(d);self.featureData=d+'° '+self.headingNameText;self.featureState='ACTIVE';self.updateFusion();},fail:function(d,c){self.compassActive=false;self.featureState='UNAVAILABLE';self.message='COMPASS ERROR '+c;self.updateCapabilityText();}});this.featureState='INITIALIZING';this.message='COMPASS STARTING';this.logEvent('NAV','COMPASS START');}catch(e){this.compassActive=false;this.featureState='UNAVAILABLE';this.message='COMPASS API UNAVAILABLE';}},
  stopCompass(){try{sensor.unsubscribeCompass();}catch(e){}this.compassActive=false;this.message='COMPASS STOPPED';this.updateCapabilityText();},
  startBarometer(){var self=this;if(this.barometerActive)return;try{sensor.subscribeBarometer({success:function(r){self.barometerActive=true;var pa=Number(r.pressure||0),h=(pa/100).toFixed(1);self.pressure=h;self.featureData=h+' hPa';self.featureState='ACTIVE';self.recordPressure(Number(h));self.updateFusion();},fail:function(d,c){self.barometerActive=false;self.featureState='UNAVAILABLE';self.message='BAROMETER ERROR '+c;self.updateCapabilityText();}});this.featureState='INITIALIZING';this.message='PRESSURE STARTING';this.logEvent('ENV','BAROMETER START');}catch(e){this.barometerActive=false;this.featureState='UNAVAILABLE';this.message='BAROMETER API UNAVAILABLE';}},
  stopBarometer(){try{sensor.unsubscribeBarometer();}catch(e){}this.barometerActive=false;this.message='PRESSURE STOPPED';this.updateCapabilityText();},
  recordPressure(v){var now=Date.now();if(!this.pressureHistory.length||now-this.lastPressureStore>=600000){this.lastPressureStore=now;this.pressureHistory.push({ts:now,value:v});if(this.pressureHistory.length>36)this.pressureHistory.shift();try{storage.set({key:'fieldcore_pressure_history',value:JSON.stringify(this.pressureHistory),success:function(){},fail:function(){}});}catch(e){}}},

  startMotion(){var self=this;if(this.motionArmed)return;this.motionArmed=true;this.featureState='ACTIVE';this.message='MOTION ARMED';try{sensor.subscribeAccelerometer({interval:'ui',success:function(r){self.onAccel(r);},fail:function(d,c){self.motionArmed=false;self.featureState='NO PERMISSION';self.message='ACCEL ERROR '+c;self.updateCapabilityText();}});sensor.subscribeGyroscope({interval:'ui',success:function(r){self.onGyro(r);},fail:function(){self.message='GYRO LIMITED';}});this.logEvent('MOTION','ARMED');}catch(e){this.motionArmed=false;this.featureState='UNAVAILABLE';this.message='MOTION API UNAVAILABLE';}},
  stopMotion(){try{sensor.unsubscribeAccelerometer();}catch(e){}try{sensor.unsubscribeGyroscope();}catch(e){}this.motionArmed=false;this.motionCalibrating=false;this.message='MOTION DISARMED';this.updateCapabilityText();},
  calibrateMotion(){var st=this.motionState;st.calCount=0;st.sumX=0;st.sumY=0;st.sumZ=0;this.motionCalibrating=true;this.message='CALIBRATE 0/20';if(!this.motionArmed)this.startMotion();},
  onAccel(r){var st=this.motionState,x=Number(r.x||0),y=Number(r.y||0),z=Number(r.z||0),rawMag=Math.sqrt(x*x+y*y+z*z),motionMag=Math.abs(rawMag-9.81);
    if(this.impactAssist){var prevPending=this.impactState.pending;this.impactState=impactUpdate({accelMag:rawMag,motionMag:motionMag},this.impactState,Date.now());if(this.impactState.pending&&!prevPending&&!this.impactPending)this.onImpactPending();}
    if(this.motionCalibrating){st.sumX+=x;st.sumY+=y;st.sumZ+=z;st.calCount++;this.message='CALIBRATE '+st.calCount+'/20';if(st.calCount>=20){st.baseX=st.sumX/20;st.baseY=st.sumY/20;st.baseZ=st.sumZ/20;this.motionCalibrating=false;this.message='CALIBRATION GOOD';this.haptic('short');}return;}
    var now=Date.now();if(now-st.lastGesture<900)return;var dx=x-st.baseX,dy=y-st.baseY,dz=z-st.baseZ,mag=Math.sqrt(dx*dx+dy*dy+dz*dz);if(dx>11&&Math.abs(dy)<10){this.motionGesture('FLICK RIGHT','OPEN_NAV',90);return;}if(dx<-11&&Math.abs(dy)<10){this.motionGesture('FLICK LEFT','OPEN_HOME',90);return;}if(mag>18){if(now-st.shakeWindow>800){st.shakeWindow=now;st.shakeCount=0;}st.shakeCount++;if(st.shakeCount>=3){st.shakeCount=0;this.motionGesture('SHAKE','OPEN_EMERGENCY',92);}}},
  onGyro(r){var st=this.motionState,now=Date.now(),z=Math.abs(Number(r.z||0));if(z>3.0){if(now-st.lastTwist<700)st.twistCount++;else st.twistCount=1;st.lastTwist=now;if(st.twistCount>=2&&now-st.lastGesture>900){st.twistCount=0;this.motionGesture('DOUBLE TWIST','SAVE_ANCHOR',90);}}},
  motionGesture(name,cmd,confidence){if(confidence<85)return;this.motionState.lastGesture=Date.now();this.featureData=name+' '+confidence+'%';this.message='GESTURE '+name;this.haptic('short');if(cmd==='OPEN_NAV')this.openFeature('8');else if(cmd==='OPEN_HOME')this.goHome();else if(cmd==='OPEN_EMERGENCY')this.openFeature('21');else if(cmd==='SAVE_ANCHOR')this.saveAnchor(null);},
  toggleImpactAssist(){this.impactAssist=!this.impactAssist;this.impactButtonLabel=this.impactAssist?'IMPACT ON':'IMPACT OFF';try{storage.set({key:'fieldcore_impact_assist',value:String(this.impactAssist),success:function(){},fail:function(){}});}catch(e){}if(this.impactAssist&&!this.motionArmed)this.startMotion();this.logEvent('SOS','IMPACT ASSIST '+(this.impactAssist?'ON':'OFF'));this.haptic('short');},
  onImpactPending(){this.impactPending=true;this.logEvent('SOS','HIGH IMPACT / STILLNESS');this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:'HIGH',movementAfter:'LOW',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'PENDING'});this.sendCommand('EMERGENCY_ESCALATION_EVENT',{type:'IMPACT',confidence:0.90});this.startEmergencyCountdown('IMPACT');},
  startEmergencyCountdown(reason){var self=this;if(this.emergencyTimer){clearInterval(this.emergencyTimer);this.emergencyTimer=null;}this.impactPending=reason==='IMPACT';this.emergencyCountdown=15;this.view='emergencyConfirm';this.message=reason+' CHECK';this.haptic('long');this.emergencyTimer=setInterval(function(){self.emergencyCountdown--;if(self.emergencyCountdown<=0){clearInterval(self.emergencyTimer);self.emergencyTimer=null;self.triggerEmergency(reason);}},1000);},
  cancelEmergency(){if(this.emergencyTimer){clearInterval(this.emergencyTimer);this.emergencyTimer=null;}this.emergencyCountdown=0;this.impactPending=false;this.impactState={impactAt:0,stillSince:0,pending:false};this.view='detail';this.message='EMERGENCY CANCELED';this.logEvent('SOS','CANCELED');this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:'EVENT',movementAfter:'AVAILABLE',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'I AM OK'});this.sendCommand('EMERGENCY_ESCALATION_SET',{level:0,reason:'USER OK'});},
  triggerEmergency(reason){this.emergencyCountdown=0;this.impactPending=false;this.view='detail';this.openFeature('21');this.message='SOS LOCATION SENDING';this.logEvent('SOS',reason+' TRIGGER');this.sendCommand('EMERGENCY_ESCALATION_SET',{level:3,reason:reason});this.sendCommand('IMPACT_REVIEW_SAVE',{intensity:reason,movementAfter:'UNAVAILABLE',heartRate:this.heartRate,location:this.lastLocation?'AVAILABLE':'UNAVAILABLE',userResponse:'SOS'});this.sendCommand('EMERGENCY_SEND',{reason:reason,battery:this.watchBattery});this.haptic('long');},
  sendEmergencyNow(){if(this.emergencyTimer){clearInterval(this.emergencyTimer);this.emergencyTimer=null;}this.triggerEmergency('MANUAL');},

  updateFusion(){var t=pressureTrend(this.pressureHistory);this.pressureTrend=t.label+(t.delta?' '+(t.delta>0?'+':'')+t.delta+'hPa':'');var altDelta=0;if(this.previousLocation&&this.lastLocation&&finite(this.previousLocation.altitude)!==null&&finite(this.lastLocation.altitude)!==null)altDelta=Number(this.lastLocation.altitude)-Number(this.previousLocation.altitude);
    var f=fusionState({hr:finite(this.heartRate),speedKmh:finite(this.speedKmh),altitudeDeltaM:altDelta,pressureTrend:t.label,emergency:this.emergencyCountdown>0,impactPending:this.impactPending,returning:this.returning});this.fieldState=f.state;this.fusionReason=f.reason;this.updateAdaptivePower();},
  updateAdaptivePower(){if(!this.powerAuto)return;var next=adaptiveProfile(this.watchBattery,{emergency:this.emergencyCountdown>0,returning:this.returning,workout:false});if(next!==this.powerProfile)this.applyPowerProfileInternal(next,false);else this.refreshPowerLabel();},
  enableAutoPower(){this.powerAuto=true;try{storage.set({key:'fieldcore_power_auto',value:'true',success:function(){},fail:function(){}});}catch(e){}this.updateAdaptivePower();this.refreshPowerLabel();this.message='AUTO POWER ACTIVE';this.logEvent('POWER','AUTO ON');},
  applyPowerProfile(action){this.powerAuto=false;try{storage.set({key:'fieldcore_power_auto',value:'false',success:function(){},fail:function(){}});}catch(e){}this.applyPowerProfileInternal(action.replace('POWER_',''),true);},
  applyPowerProfileInternal(p,user){if(!POWER_PROFILES[p])p='BALANCED';var changed=p!==this.powerProfile;this.powerProfile=p;try{storage.set({key:'fieldcore_power_profile',value:p,success:function(){},fail:function(){}});}catch(e){}if((p==='ENDURANCE'||p==='GRID')&&!this.impactAssist)this.stopMotion();if(p==='GRID'&&!this.returning)this.stopCompass();if(this.breadcrumbActive)this.scheduleBreadcrumb();if(this.returning)this.scheduleReturn();this.scheduleCache();this.refreshPowerLabel();if(changed||user){this.message='POWER '+p;this.logEvent('POWER',(this.powerAuto?'AUTO ':'')+p);var sm=p==='PERFORMANCE'?'ACTIVE':((p==='ENDURANCE'||p==='GRID')?'BATTERY_SAVER':'BALANCED');if(this.connectionState==='CONNECTED')this.sendCommand('WIFI_SCAN_MODE',{mode:sm});if(user)this.haptic('short');}},
  refreshPowerLabel(){this.powerLabel=(this.powerAuto?'AUTO • ':'MANUAL • ')+this.powerProfile;},

  scheduleCache(){var self=this;if(this.cacheTimer){clearInterval(this.cacheTimer);this.cacheTimer=null;}var p=POWER_PROFILES[this.powerProfile]||POWER_PROFILES.BALANCED;this.cacheTimer=setInterval(function(){self.saveOfflineCache();self.refreshBattery();},p.cacheMs);},
  saveOfflineCache(){var c={ts:Date.now(),location:this.lastLocation,weather:this.weatherCache,field:this.fieldState,power:this.powerProfile,routePoints:this.breadcrumbRoute.length,anchorCount:this.anchors.length};try{storage.set({key:'fieldcore_offline_cache',value:JSON.stringify(c),success:function(){},fail:function(){}});this.cacheState='READY '+timeText(c.ts);}catch(e){}},

  logEvent(type,text){var item={ts:Date.now(),type:String(type||'FIELD'),text:String(text||'')};this.timeline.push(item);this.timeline=trimTimeline(this.timeline,80);try{storage.set({key:'fieldcore_timeline',value:JSON.stringify(this.timeline),success:function(){},fail:function(){}});}catch(e){}this.refreshTimelinePage();},
  openTimeline(){this.timelinePage=0;this.refreshTimelinePage();this.view='timeline';this.haptic('short');},
  refreshTimelinePage(){var start=Math.max(0,this.timeline.length-4-(this.timelinePage*4)),items=[],i,idx;for(i=0;i<4;i++){idx=start+(3-i);if(idx>=0&&idx<this.timeline.length){var e=this.timeline[idx];items[i]=timeText(e.ts)+' '+e.type+' • '+e.text;}else items[i]='-';}this.timeline1=items[0];this.timeline2=items[1];this.timeline3=items[2];this.timeline4=items[3];},
  timelineOlder(){if((this.timelinePage+1)*4<this.timeline.length)this.timelinePage++;this.refreshTimelinePage();},timelineNewer(){if(this.timelinePage>0)this.timelinePage--;this.refreshTimelinePage();},
  clearTimeline(){this.timeline=[];this.timelinePage=0;try{storage.set({key:'fieldcore_timeline',value:'[]',success:function(){},fail:function(){}});}catch(e){}this.refreshTimelinePage();},

  openCapabilities(){this.updateCapabilityText();this.view='capabilities';this.haptic('short');},
  updateCapabilityText(){var local='LOCAL\nGPS '+(this.lastLocation?'✓':'?')+'  HR '+(this.hrSubscribed?'✓':'?')+'  COMPASS '+(this.compassActive?'✓':'?')+'\nBAROMETER '+(this.barometerActive?'✓':'?')+'  MOTION '+(this.motionArmed?'✓':'?');var phone='\n\nPHONE\n'+this.connectionState;var provider='';if(this.phoneCapabilities){try{provider='\nWEATHER '+String(this.phoneCapabilities.weather||'READY')+'\nTRANSIT '+String(this.phoneCapabilities.transit||'NOT CONFIGURED')+'\nDEPTH '+String(this.phoneCapabilities.depth||'API GATED')+'\nLIGHT '+String(this.phoneCapabilities.ambientLight||'API GATED');}catch(e){}}this.capabilityText=local+phone+provider;},

  startLight(mode){this.sosConfirmUntil=0;if(this.lightTimer){clearInterval(this.lightTimer);this.lightTimer=null;}this.view=mode==='white'?'lightWhite':'lightRed';this.message='TACTICAL LIGHT '+mode.toUpperCase();},
  confirmSosLight(){var now=Date.now();if(now>this.sosConfirmUntil){this.sosConfirmUntil=now+5000;this.message='SOS: TAP AGAIN WITHIN 5 SEC';this.haptic('long');return;}this.sosConfirmUntil=0;this.startSosLight();},
  startSosLight(){var self=this,on=true;this.view='lightRed';this.message='SOS FLASH ACTIVE';this.haptic('long');this.lightTimer=setInterval(function(){on=!on;self.view=on?'lightRed':'lightBlack';},450);this.logEvent('SOS','FLASH ACTIVE');},
  stopLight(){if(this.lightTimer){clearInterval(this.lightTimer);this.lightTimer=null;}if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack')this.view='detail';this.sosConfirmUntil=0;},

  openFeature(id){var f=getFeature(id);if(!f)return;this.selectedId=String(id);this.selectedTitle=f.title;this.selectedSource=f.source;this.selectedDesc=f.desc;this.action1Label=f.actions[0]?f.actions[0].label:'';this.action1Command=f.actions[0]?f.actions[0].command:'';this.action2Label=f.actions[1]?f.actions[1].label:'';this.action2Command=f.actions[1]?f.actions[1].command:'';this.action3Label=f.actions[2]?f.actions[2].label:'';this.action3Command=f.actions[2]?f.actions[2].command:'';this.action4Label=f.actions[3]?f.actions[3].label:'';this.action4Command=f.actions[3]?f.actions[3].command:'';this.featureState=(f.source==='UNAVAILABLE'||f.source==='API GATED')?'API GATED':'READY';this.featureData='-';this.message='MODULE READY';this.category=f.category;this.view='detail';this.haptic('short');},
  setCategory(c){this.category=c;this.view='list';this.showBio=c==='BIO';this.showSport=c==='SPORT';this.showNav=c==='NAV';this.showEnv=c==='ENV';this.showTactical=c==='TACTICAL';this.showSystem=c==='SYSTEM';},
  goHome(){this.view='home';this.showBio=false;this.showSport=false;this.showNav=false;this.showEnv=false;this.showTactical=false;this.showSystem=false;this.refreshBattery();this.updateFusion();},
  goList(){this.setCategory(this.category);},catBio(){this.setCategory('BIO');},catSport(){this.setCategory('SPORT');},catNav(){this.setCategory('NAV');},catEnv(){this.setCategory('ENV');},catTactical(){this.setCategory('TACTICAL');},catSystem(){this.setCategory('SYSTEM');},
  quickAnchor(){this.openFeature('11');},quickBreadcrumb(){this.openFeature('10');},quickNav(){this.openFeature('8');},quickEmergency(){this.openFeature('21');},
  detailAction1(){this.sendCommand(this.action1Command);},detailAction2(){this.sendCommand(this.action2Command);},detailAction3(){this.sendCommand(this.action3Command);},detailAction4(){this.sendCommand(this.action4Command);},
  swipeEvent(e){if(e.direction==='right'){if(this.view==='lightRed'||this.view==='lightWhite'||this.view==='lightBlack'){this.stopLight();return;}if(this.view==='home')app.terminate();else if(this.view==='detail')this.goList();else if(this.view==='advanced'||this.view==='wifiScout')this.view='advancedHub';else if(this.view==='advancedHub'||this.view==='anchors'||this.view==='timeline'||this.view==='capabilities'||this.view==='emergencyConfirm')this.goHome();else this.goHome();}},
  f0(){this.openFeature('0');},f1(){this.openFeature('1');},f2(){this.openFeature('2');},f3(){this.openFeature('3');},f4(){this.openFeature('4');},f5(){this.openFeature('5');},f6(){this.openFeature('6');},f7(){this.openFeature('7');},f8(){this.openFeature('8');},f9(){this.openFeature('9');},f10(){this.openFeature('10');},f11(){this.openFeature('11');},f12(){this.openFeature('12');},f13(){this.openFeature('13');},f14(){this.openFeature('14');},f15(){this.openFeature('15');},f16(){this.openFeature('16');},f17(){this.openFeature('17');},f18(){this.openFeature('18');},f19(){this.openFeature('19');},f20(){this.openFeature('20');},f21(){this.openFeature('21');},f22(){this.openFeature('22');},f23(){this.openFeature('23');},f24(){this.openFeature('24');},f25(){this.openFeature('25');},f26(){this.openFeature('26');},f27(){this.openFeature('27');}
};
