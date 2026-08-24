export const POWER_PROFILES = {
  PERFORMANCE:{breadcrumbMs:10000,cacheMs:30000,label:'PERFORMANCE'},
  BALANCED:{breadcrumbMs:30000,cacheMs:60000,label:'BALANCED'},
  ENDURANCE:{breadcrumbMs:60000,cacheMs:120000,label:'ENDURANCE'},
  GRID:{breadcrumbMs:120000,cacheMs:300000,label:'GRID'}
};

export function clamp(v,min,max){v=Number(v);if(!isFinite(v))return min;return Math.max(min,Math.min(max,v));}
export function safeNumber(v,fallback){var n=Number(v);return isFinite(n)?n:(typeof fallback==='undefined'?null:fallback);}

export function adaptiveProfile(batteryPct,active){
  var b=safeNumber(batteryPct,100),a=active||{};
  if(b<=15)return 'GRID';
  if(b<=30)return 'ENDURANCE';
  if(b<=60)return 'BALANCED';
  if(a.emergency||a.returning||a.workout)return 'PERFORMANCE';
  return 'BALANCED';
}

export function pressureTrend(history){
  var h=history||[];if(h.length<2)return {delta:0,label:'STABLE'};
  var first=h[0],last=h[h.length-1],d=safeNumber(last.value,0)-safeNumber(first.value,0);
  var label=Math.abs(d)<0.8?'STABLE':(d<=-2.5?'FALLING FAST':(d<0?'FALLING':(d>=2.5?'RISING FAST':'RISING')));
  return {delta:Math.round(d*10)/10,label:label};
}

export function heatLoad(tempC,apparentC,uv){
  var t=Math.max(safeNumber(tempC,0),safeNumber(apparentC,0)),u=safeNumber(uv,0),score=0;
  if(t>=36)score+=3;else if(t>=32)score+=2;else if(t>=28)score+=1;
  if(u>=8)score+=2;else if(u>=6)score+=1;
  return score>=4?'VERY HIGH':(score>=3?'HIGH':(score>=2?'MODERATE':'LOW'));
}

export function fusionState(s){
  s=s||{};var hr=safeNumber(s.hr,null),speed=safeNumber(s.speedKmh,0),altDelta=safeNumber(s.altitudeDeltaM,0),trend=s.pressureTrend||'STABLE';
  if(s.emergency)return {state:'EMERGENCY',reason:'EMERGENCY MODE'};
  if(s.impactPending)return {state:'CHECK USER',reason:'HIGH IMPACT'};
  if(speed>2&&altDelta>20&&hr!==null&&hr>110)return {state:'ASCENT',reason:'MOVING + ALT + HR'};
  if(trend==='FALLING FAST')return {state:'WEATHER WATCH',reason:'PRESSURE DROP'};
  if(hr!==null&&hr>145&&speed<0.5)return {state:'RECOVERY WATCH',reason:'HIGH HR / LOW MOTION'};
  if(s.returning)return {state:'RETURNING',reason:'NAV ACTIVE'};
  return {state:'NORMAL',reason:'FIELD NOMINAL'};
}

export function routeStats(current,route,distanceFn,bearingFn){
  route=route||[];if(!current||!route.length)return null;
  var base=route[0],last=route[route.length-1],distBase=Math.round(distanceFn(current,base)),distLast=Math.round(distanceFn(current,last));
  var bearing=Math.round(bearingFn(current,base)),routeDistance=0,gain=0,loss=0,i=1,a1,a2,dAlt;
  for(i=1;i<route.length;i++){
    routeDistance+=distanceFn(route[i-1],route[i]);a1=safeNumber(route[i-1].altitude,null);a2=safeNumber(route[i].altitude,null);
    if(a1!==null&&a2!==null){dAlt=a2-a1;if(dAlt>0)gain+=dAlt;else loss+=Math.abs(dAlt);}
  }
  var speed=safeNumber(current.speedKmh,null);if(speed===null){var ms=safeNumber(current.speed,null);if(ms!==null)speed=ms*3.6;}
  var etaMin=null;if(speed!==null&&speed>0.5)etaMin=Math.max(1,Math.round((distBase/1000)/speed*60));
  return {distanceToBaseM:distBase,distanceToLastM:distLast,bearing:bearing,routeDistanceM:Math.round(routeDistance),altitudeGainM:Math.round(gain),altitudeLossM:Math.round(loss),etaMin:etaMin,points:route.length};
}

export function impactUpdate(sample,state,now){
  state=state||{impactAt:0,stillSince:0,pending:false};now=now||Date.now();sample=sample||{};
  var mag=safeNumber(sample.accelMag,0),motion=safeNumber(sample.motionMag,0);
  if(mag>=24){state.impactAt=now;state.stillSince=0;state.pending=false;}
  if(state.impactAt&&now-state.impactAt<15000){
    if(motion<1.2){if(!state.stillSince)state.stillSince=now;if(now-state.stillSince>=5000)state.pending=true;}
    else state.stillSince=0;
  }
  if(state.impactAt&&now-state.impactAt>=15000&&!state.pending){state.impactAt=0;state.stillSince=0;}
  return state;
}

export function readiness(input){
  input=input||{};var parts=0,total=0;
  function add(v,min,max,weight){if(v===null||typeof v==='undefined')return;var n=clamp((Number(v)-min)/(max-min),0,1);parts+=n*weight;total+=weight;}
  add(input.sleepHours,4,9,45);add(input.recoveryScore,0,100,35);add(input.restingHrQuality,0,100,20);
  if(!total)return null;var score=Math.round(parts/total*100);return {score:score,label:score>=80?'READY':(score>=60?'GOOD':(score>=40?'MODERATE':'LOW'))};
}

export function trimTimeline(items,max){items=items||[];max=max||80;if(items.length<=max)return items;return items.slice(items.length-max);}
