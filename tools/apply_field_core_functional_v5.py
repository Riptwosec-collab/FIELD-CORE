from pathlib import Path

ROOT = Path('Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1')
HML = ROOT / 'watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml'
CSS = ROOT / 'watch-lite/entry/src/main/js/MainAbility/pages/index/index.css'
JS = ROOT / 'watch-lite/entry/src/main/js/MainAbility/pages/index/index.js'

HML_MARK = '<!-- FIELD CORE FUNCTIONAL V5: WRIST-FIRST ACTION LAYOUT -->'
CSS_MARK = '/* FIELD CORE FUNCTIONAL V5: WRIST-FIRST ACTION LAYOUT */'
JS_MARK = '/* FIELD CORE FUNCTIONAL V5: WRIST-FIRST ACTION HELPERS */'

hml = HML.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
js = JS.read_text(encoding='utf-8')


def insert_category_quickbar(text, start_token, end_token, block):
    start = text.find(start_token)
    if start < 0:
        raise SystemExit('missing category start: ' + start_token)
    end = text.find(end_token, start)
    if end < 0:
        raise SystemExit('missing category end: ' + end_token)
    section = text[start:end]
    if 'v5-quickbar' in section:
        return text
    list_at = section.find('<list class="feature-list')
    if list_at < 0:
        raise SystemExit('missing feature list in: ' + start_token)
    pos = start + list_at
    return text[:pos] + block + '\n    ' + text[pos:]


if HML_MARK not in hml:
    marker = '<!-- FIELD CORE VISUAL V4: DISTINCT ALL-PAGE MASTERPIECE -->'
    if marker not in hml:
        raise SystemExit('Visual V4 marker missing; V5 requires V4 baseline')
    hml = hml.replace(marker, marker + '\n  ' + HML_MARK, 1)

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showBio}}"',
        '<div if="{{showSport}}"',
        '''    <div class="v5-quickbar bio-quickbar">
      <input type="button" class="v5-quick active-state" value="START HR" onclick="v5BioStart"/>
      <input type="button" class="v5-quick" value="STOP HR" onclick="v5BioStop"/>
      <input type="button" class="v5-quick" value="READINESS" onclick="v5Readiness"/>
      <input type="button" class="v5-quick warning-btn" value="IMPACT" onclick="v5Impact"/>
    </div>''')

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showSport}}"',
        '<div if="{{showNav}}"',
        '''    <div class="v5-quickbar sport-quickbar">
      <input type="button" class="v5-quick active-state" value="RUN" onclick="v5Run"/>
      <input type="button" class="v5-quick" value="HIKE" onclick="v5Hike"/>
      <input type="button" class="v5-quick" value="RUN ZONE" onclick="v5RunZone"/>
      <input type="button" class="v5-quick" value="STATUS" onclick="v5RunStatus"/>
    </div>''')

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showNav}}"',
        '<div if="{{showEnv}}"',
        '''    <div class="v5-quickbar nav-quickbar">
      <input type="button" class="v5-quick active-state" value="LOCATE" onclick="v5Locate"/>
      <input type="button" class="v5-quick" value="COMPASS" onclick="v5Compass"/>
      <input type="button" class="v5-quick" value="BREADCRUMB" onclick="v5Breadcrumb"/>
      <input type="button" class="v5-quick" value="RETURN" onclick="v5Return"/>
    </div>''')

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showEnv}}"',
        '<div if="{{showTactical}}"',
        '''    <div class="v5-quickbar env-quickbar">
      <input type="button" class="v5-quick active-state" value="WEATHER" onclick="v5Weather"/>
      <input type="button" class="v5-quick" value="PRESSURE" onclick="v5Pressure"/>
      <input type="button" class="v5-quick" value="RISK" onclick="v5EnvRisk"/>
      <input type="button" class="v5-quick" value="SKY" onclick="v5Sky"/>
    </div>''')

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showTactical}}"',
        '<div if="{{showSystem}}"',
        '''    <div class="v5-quickbar tactical-quickbar">
      <input type="button" class="v5-quick active-state" value="RED LIGHT" onclick="v5RedLight"/>
      <input type="button" class="v5-quick danger-btn" value="SOS LIGHT" onclick="v5SosLight"/>
      <input type="button" class="v5-quick" value="GRID-DOWN" onclick="v5Grid"/>
      <input type="button" class="v5-quick danger-btn" value="EMERGENCY" onclick="v5Emergency"/>
    </div>''')

    hml = insert_category_quickbar(
        hml,
        '<div if="{{showSystem}}"',
        '<div if="{{view == \'detail\'}}"',
        '''    <div class="v5-quickbar system-quickbar">
      <input type="button" class="v5-quick active-state" value="AUTO POWER" onclick="v5PowerAuto"/>
      <input type="button" class="v5-quick" value="ENDURANCE" onclick="v5Endurance"/>
      <input type="button" class="v5-quick" value="SENSOR TEST" onclick="v5SensorTest"/>
      <input type="button" class="v5-quick" value="SETTINGS" onclick="v5Settings"/>
    </div>''')

    # Add wrist-first identity classes to the operational utility surfaces.
    class_replacements = {
        'class="page masterpiece-page detail-page detail-page-v4 page-enter"': 'class="page masterpiece-page detail-page detail-page-v4 functional-detail-v5 page-enter"',
        'class="page masterpiece-page utility-page page-enter"': 'class="page masterpiece-page utility-page functional-utility-v5 page-enter"',
        'class="page masterpiece-page utility-page advanced-hub-v4 page-enter"': 'class="page masterpiece-page utility-page advanced-hub-v4 functional-advanced-hub-v5 page-enter"',
        'class="page masterpiece-page utility-page wifi-scout-v4 page-enter"': 'class="page masterpiece-page utility-page wifi-scout-v4 functional-wifi-v5 page-enter"',
        'class="page masterpiece-page utility-page wifi-list-v4 page-enter"': 'class="page masterpiece-page utility-page wifi-list-v4 functional-wifi-list-v5 page-enter"',
        'class="page masterpiece-page utility-page wifi-detail-v4 page-enter"': 'class="page masterpiece-page utility-page wifi-detail-v4 functional-wifi-detail-v5 page-enter"',
        'class="page masterpiece-page utility-page cyber-sweep-v4 page-enter"': 'class="page masterpiece-page utility-page cyber-sweep-v4 functional-sweep-v5 page-enter"',
        'class="page masterpiece-page utility-page advanced-page-v4 page-enter"': 'class="page masterpiece-page utility-page advanced-page-v4 functional-advanced-v5 page-enter"',
        'class="emergency-screen emergency-v4 page-enter"': 'class="emergency-screen emergency-v4 functional-emergency-v5 page-enter"',
    }
    for old, new in class_replacements.items():
        hml = hml.replace(old, new)

    # Add context-first decision strips to the most action-critical detail pages.
    insertion = '    <div class="detail-actions">'
    if insertion not in hml:
        raise SystemExit('detail action insertion point missing')
    decision = r'''    <div class="v5-decision-strip">
      <div if="{{selectedId == '1'}}" class="v5-decision-row"><text class="v5-decision-k">PRIMARY</text><text class="v5-decision-v">HR {{heartRate}} BPM</text><text class="v5-decision-k">SENSOR</text><text class="v5-decision-v">{{featureState}}</text></div>
      <div if="{{selectedId == '5'}}" class="v5-decision-row"><text class="v5-decision-k">SPEED</text><text class="v5-decision-v">{{speedKmh}}</text><text class="v5-decision-k">HR</text><text class="v5-decision-v">{{heartRate}}</text></div>
      <div if="{{selectedId == '8'}}" class="v5-decision-row"><text class="v5-decision-k">HEADING</text><text class="v5-decision-v">{{headingNameText}}</text><text class="v5-decision-k">GPS</text><text class="v5-decision-v">{{gpsState}}</text></div>
      <div if="{{selectedId == '10'}}" class="v5-decision-row"><text class="v5-decision-k">POINTS</text><text class="v5-decision-v">{{breadcrumbPoints}}</text><text class="v5-decision-k">RETURN</text><text class="v5-decision-v">{{returning}}</text></div>
      <div if="{{selectedId == '11'}}" class="v5-decision-row"><text class="v5-decision-k">ANCHORS</text><text class="v5-decision-v">{{anchorsCount}} / 20</text><text class="v5-decision-k">GPS</text><text class="v5-decision-v">{{gpsState}}</text></div>
      <div if="{{selectedId == '13'}}" class="v5-decision-row"><text class="v5-decision-k">PRESS</text><text class="v5-decision-v">{{pressure}}</text><text class="v5-decision-k">TREND</text><text class="v5-decision-v">{{pressureTrend}}</text></div>
      <div if="{{selectedId == '19'}}" class="v5-decision-row"><text class="v5-decision-k">LIGHT</text><text class="v5-decision-v">SCREEN</text><text class="v5-decision-k">POWER</text><text class="v5-decision-v">{{powerProfile}}</text></div>
      <div if="{{selectedId == '21'}}" class="v5-decision-row danger-decision"><text class="v5-decision-k">GPS</text><text class="v5-decision-v">{{gpsState}}</text><text class="v5-decision-k">IMPACT</text><text class="v5-decision-v">{{impactButtonLabel}}</text></div>
      <div if="{{selectedId == '24'}}" class="v5-decision-row"><text class="v5-decision-k">BATTERY</text><text class="v5-decision-v">{{watchBattery}}%</text><text class="v5-decision-k">PROFILE</text><text class="v5-decision-v">{{powerProfile}}</text></div>
      <div if="{{selectedId == '27'}}" class="v5-decision-row"><text class="v5-decision-k">LINK</text><text class="v5-decision-v">{{connectionState}}</text><text class="v5-decision-k">RECON</text><text class="v5-decision-v">WIFI {{wifiCount}}</text></div>
    </div>
'''
    hml = hml.replace(insertion, decision + insertion, 1)


if JS_MARK not in js:
    anchor = '  openFeature(id){'
    if anchor not in js:
        raise SystemExit('openFeature anchor missing')
    helpers = r'''  /* FIELD CORE FUNCTIONAL V5: WRIST-FIRST ACTION HELPERS */
  v5BioStart(){this.openFeature('1');this.sendCommand('BIO_START');},
  v5BioStop(){this.openFeature('1');this.sendCommand('BIO_STOP');},
  v5Readiness(){this.openFeature('2');this.sendCommand('SLEEP_REFRESH');},
  v5Impact(){this.advImpactReview();},

  v5Run(){this.openFeature('5');this.sendCommand('RUN_START');},
  v5Hike(){this.openFeature('4');this.sendCommand('SPORT_HIKE');},
  v5RunZone(){this.advRunZone();},
  v5RunStatus(){this.openFeature('5');this.sendCommand('RUN_STATUS');},

  v5Locate(){this.openFeature('8');this.sendCommand('FIELD_LOCATION');},
  v5Compass(){this.openFeature('8');this.sendCommand('COMPASS_START');},
  v5Breadcrumb(){this.openFeature('10');},
  v5Return(){this.openFeature('10');this.sendCommand('BREADCRUMB_RETURN');},

  v5Weather(){this.openFeature('13');this.sendCommand('WEATHER_REFRESH');},
  v5Pressure(){this.openFeature('13');this.sendCommand('BAROMETER_START');},
  v5EnvRisk(){this.advEnvRisk();},
  v5Sky(){this.advSkyPro();},

  v5RedLight(){this.openFeature('19');this.sendCommand('TACTICAL_LIGHT_RED');},
  v5SosLight(){this.openFeature('19');this.sendCommand('TACTICAL_LIGHT_SOS');},
  v5Grid(){this.openFeature('20');this.sendCommand('GRID_ARM');},
  v5Emergency(){this.openFeature('21');},

  v5PowerAuto(){this.openFeature('24');this.enableAutoPower();},
  v5Endurance(){this.openFeature('24');this.sendCommand('POWER_ENDURANCE');},
  v5SensorTest(){this.advSensorTest();},
  v5Settings(){this.advSettings();},

'''
    js = js.replace(anchor, helpers + anchor, 1)


if CSS_MARK not in css:
    css += r'''

/* FIELD CORE FUNCTIONAL V5: WRIST-FIRST ACTION LAYOUT
   Keeps Original Masterpiece palette/theme while making each surface task-first.
*/
.v5-quickbar { width:452px; height:38px; flex-direction:row; justify-content:space-between; align-items:center; margin-top:2px; margin-bottom:2px; }
.v5-quick { width:108px; height:32px; border-radius:8px; border-width:1px; border-color:#234653; background-color:#010507; color:#8ca0aa; font-size:7px; }
.v5-quick.active-state { border-color:#00e5ff; background-color:#00313a; color:#ffffff; animation-name:buttonPulse; animation-duration:1800ms; animation-iteration-count:infinite; }
.v5-quick.warning-btn { border-color:#ffcc00; color:#ffcc00; background-color:#0d0a02; }
.v5-quick.danger-btn { border-color:#ff335f; color:#ff6684; background-color:#180309; }

.bio-page-v4 .feature-list, .sport-page-v4 .feature-list, .nav-page-v4 .feature-list, .env-page-v4 .feature-list, .tactical-page-v4 .feature-list, .system-page-v4 .feature-list { height:108px; }
.bio-page-v4 .category-hero { height:82px; }
.bio-page-v4 .signal-strip { height:32px; }
.sport-page-v4 .sport-stage { height:88px; }
.sport-page-v4 .sport-ring { width:76px; height:76px; border-radius:38px; }
.sport-page-v4 .sport-ring-inner { width:54px; height:54px; border-radius:27px; }
.nav-page-v4 .nav-stage, .env-page-v4 .env-stage { height:96px; }
.nav-page-v4 .network-radar, .env-page-v4 .atmo-dial { transform:scale(0.82); }
.tactical-page-v4 .tactical-hero { height:82px; }
.tactical-page-v4 .v5-quick { border-color:#6c1b35; background-color:#150309; color:#ff6684; }
.tactical-page-v4 .v5-quick.active-state { border-color:#ff335f; background-color:#310610; color:#ffffff; }
.system-page-v4 .system-core-panel { height:88px; }

.functional-detail-v5 .module-stage { height:96px; }
.functional-detail-v5 .module-desc { max-height:28px; font-size:7px; }
.functional-detail-v5 .detail-actions { min-height:74px; align-items:stretch; }
.functional-detail-v5 .hud-action { height:36px; font-size:8px; }
.functional-detail-v5 .detail-extra { margin-top:3px; }
.functional-detail-v5 .mini-extra, .functional-detail-v5 .wide-extra { height:31px; font-size:7px; }
.v5-decision-strip { width:452px; min-height:0px; }
.v5-decision-row { width:452px; height:28px; border-radius:8px; border-width:1px; border-color:#143a45; background-color:#01070a; flex-direction:row; align-items:center; justify-content:space-around; }
.v5-decision-k { width:64px; color:#617481; font-size:6px; text-align:center; }
.v5-decision-v { width:142px; color:#00e5ff; font-size:7px; text-align:center; }
.danger-decision { border-color:#6f1835; background-color:#120308; }
.danger-decision .v5-decision-v { color:#ff335f; }

.functional-utility-v5 .anchor-card { min-height:64px; }
.functional-utility-v5 .anchor-go { height:30px; }
.functional-utility-v5 .timeline-card { min-height:39px; }
.functional-utility-v5 .cap-panel { min-height:92px; }

.functional-wifi-v5 .wifi-stage { height:100px; }
.functional-wifi-v5 .wifi-btn { height:34px; font-size:7px; }
.functional-wifi-list-v5 .wifi-network-row { height:52px; }
.functional-wifi-list-v5 .wifi-network-btn { height:34px; font-size:8px; }
.functional-wifi-detail-v5 .wifi-detail-card { min-height:112px; }
.functional-wifi-detail-v5 .wifi-detail-btn { height:38px; font-size:8px; }
.functional-sweep-v5 .cyber-sweep-stage { height:112px; }

.functional-advanced-hub-v5 .advanced-row { min-height:36px; }
.functional-advanced-hub-v5 .advanced-btn { height:32px; font-size:7px; }
.functional-advanced-v5 .advanced-core { height:58px; }
.functional-advanced-v5 .v4-stage { height:96px; }
.functional-advanced-v5 .advanced-data-card { min-height:40px; margin-top:3px; }
.functional-advanced-v5 .mini-extra, .functional-advanced-v5 .profile-btn, .functional-advanced-v5 .wide-extra { height:34px; font-size:7px; }

.functional-emergency-v5 { background-color:#090105; }
.functional-emergency-v5 .emergency-dial { width:190px; height:190px; border-color:#ff335f; }
.functional-emergency-v5 .countdown { font-size:48px; }
.functional-emergency-v5 .emergency-send, .functional-emergency-v5 .emergency-cancel { width:360px; height:42px; font-size:10px; }
.light-red .light-stop, .light-white .light-stop, .light-black .light-stop { width:320px; height:44px; font-size:10px; }
'''

HML.write_text(hml, encoding='utf-8')
CSS.write_text(css, encoding='utf-8')
JS.write_text(js, encoding='utf-8')
print('FIELD CORE Functional V5 applied')
