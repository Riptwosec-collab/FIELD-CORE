from pathlib import Path

ROOT = Path('Field_Core_FIT4PRO_V1/Field_Core_FIT4PRO_V1')
HML = ROOT / 'watch-lite/entry/src/main/js/MainAbility/pages/index/index.hml'
CSS = ROOT / 'watch-lite/entry/src/main/js/MainAbility/pages/index/index.css'

HML_MARK = '<!-- FIELD CORE VISUAL V4: DISTINCT ALL-PAGE MASTERPIECE -->'
CSS_MARK = '/* FIELD CORE VISUAL V4: DISTINCT ALL-PAGE MASTERPIECE */'

hml = HML.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')

if HML_MARK not in hml:
    hml = hml.replace('<stack class="root" onswipe="swipeEvent">', '<stack class="root" onswipe="swipeEvent">\n  ' + HML_MARK, 1)

    # Keep the original Masterpiece information architecture but match the chosen
    # visual reference: FIELD CORE is the main product title, FUSION OS is the subline.
    hml = hml.replace('<text class="page-title">FUSION OS</text>', '<text class="page-title">FIELD CORE</text>', 1)
    hml = hml.replace('<text class="page-subtitle">FIELD STATUS</text>', '<text class="page-subtitle">FUSION OS</text>', 1)

    # Add visual page identities without changing any handlers or runtime state.
    page_replacements = {
        '<div if="{{showBio}}" class="page masterpiece-page page-enter">': '<div if="{{showBio}}" class="page masterpiece-page bio-page-v4 page-enter">',
        '<div if="{{showSport}}" class="page masterpiece-page page-enter">': '<div if="{{showSport}}" class="page masterpiece-page sport-page-v4 page-enter">',
        '<div if="{{showNav}}" class="page masterpiece-page page-enter">': '<div if="{{showNav}}" class="page masterpiece-page nav-page-v4 page-enter">',
        '<div if="{{showEnv}}" class="page masterpiece-page page-enter">': '<div if="{{showEnv}}" class="page masterpiece-page env-page-v4 page-enter">',
        '<div if="{{showTactical}}" class="page masterpiece-page tactical-page page-enter">': '<div if="{{showTactical}}" class="page masterpiece-page tactical-page tactical-page-v4 page-enter">',
        '<div if="{{showSystem}}" class="page masterpiece-page page-enter">': '<div if="{{showSystem}}" class="page masterpiece-page system-page-v4 page-enter">',
        '<div if="{{view == \'detail\'}}" class="page masterpiece-page detail-page page-enter">': '<div if="{{view == \'detail\'}}" class="page masterpiece-page detail-page detail-page-v4 page-enter">',
        '<div if="{{view == \'advancedHub\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'advancedHub\'}}" class="page masterpiece-page utility-page advanced-hub-v4 page-enter">',
        '<div if="{{view == \'wifiScout\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'wifiScout\'}}" class="page masterpiece-page utility-page wifi-scout-v4 page-enter">',
        '<div if="{{view == \'wifiList\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'wifiList\'}}" class="page masterpiece-page utility-page wifi-list-v4 page-enter">',
        '<div if="{{view == \'wifiDetail\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'wifiDetail\'}}" class="page masterpiece-page utility-page wifi-detail-v4 page-enter">',
        '<div if="{{view == \'cyberSweep\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'cyberSweep\'}}" class="page masterpiece-page utility-page cyber-sweep-v4 page-enter">',
        '<div if="{{view == \'advanced\'}}" class="page masterpiece-page utility-page page-enter">': '<div if="{{view == \'advanced\'}}" class="page masterpiece-page utility-page advanced-page-v4 page-enter">',
        '<div if="{{view == \'emergencyConfirm\'}}" class="emergency-screen page-enter">': '<div if="{{view == \'emergencyConfirm\'}}" class="emergency-screen emergency-v4 page-enter">',
    }
    for old, new in page_replacements.items():
        if old in hml:
            hml = hml.replace(old, new, 1)

    # The Advanced result screen used one generic graphic.  Keep the shared status
    # summary, then add a different visual composition for every Advanced function.
    insertion_point = '    <div class="advanced-data-card">'
    if insertion_point not in hml:
        raise SystemExit('advanced-data-card insertion point not found')

    stages = r'''
    <!-- VISUAL V4: every Advanced function gets its own graphic composition -->
    <div if="{{advancedTitle == 'COMMAND CENTER'}}" class="v4-stage v4-command-stage">
      <div class="v4-terrain"><div class="v4-terrain-line tl1"></div><div class="v4-terrain-line tl2"></div><div class="v4-terrain-line tl3"></div><div class="v4-command-target"><text class="v4-target-text">CORE</text></div></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">MISSION</text><text class="v4-v">{{missionLabel}}</text></div><div class="v4-stat"><text class="v4-k">RISK</text><text class="v4-v">{{envRisk}}</text></div><div class="v4-stat"><text class="v4-k">WIFI / BT</text><text class="v4-v">{{wifiCount}} / {{btCount}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'FIELD CONTEXT'}}" class="v4-stage v4-context-stage">
      <div class="v4-context-wheel"><div class="v4-context-ring cr1"></div><div class="v4-context-ring cr2"></div><text class="v4-context-main">{{contextMode}}</text><text class="v4-context-conf">{{contextConfidence}}</text></div>
      <div class="v4-chip-grid"><text class="v4-chip">BIO</text><text class="v4-chip">NAV</text><text class="v4-chip">ENV</text><text class="v4-chip">POWER</text></div>
    </div>

    <div if="{{advancedTitle == 'TELEMETRY CONFIDENCE'}}" class="v4-stage v4-confidence-stage">
      <div class="v4-quality-row"><text class="v4-quality-label">GPS</text><div class="v4-quality-track"><div class="v4-quality-fill qf1"></div></div><text class="v4-quality-value">{{gpsState}}</text></div>
      <div class="v4-quality-row"><text class="v4-quality-label">HR</text><div class="v4-quality-track"><div class="v4-quality-fill qf2"></div></div><text class="v4-quality-value">{{heartRate}}</text></div>
      <div class="v4-quality-row"><text class="v4-quality-label">LINK</text><div class="v4-quality-track"><div class="v4-quality-fill qf3"></div></div><text class="v4-quality-value">{{connectionState}}</text></div>
      <div class="v4-quality-row"><text class="v4-quality-label">WIFI</text><div class="v4-quality-track"><div class="v4-quality-fill qf4"></div></div><text class="v4-quality-value">{{wifiAge}}s</text></div>
    </div>

    <div if="{{advancedTitle == 'LOST MODE PRO'}}" class="v4-stage v4-lost-stage">
      <div class="network-radar v4-lost-radar"><div class="radar-ring r1"></div><div class="radar-ring r2"></div><div class="radar-ring r3"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="radar-sweep"></div><div class="radar-core"><text class="radar-value">{{breadcrumbPoints}}</text><text class="radar-label">RETURN</text></div></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">GPS</text><text class="v4-v">{{gpsState}}</text></div><div class="v4-stat"><text class="v4-k">ROUTE</text><text class="v4-v">{{routeSummary}}</text></div><div class="v4-stat"><text class="v4-k">BATTERY</text><text class="v4-v">{{watchBattery}}%</text></div></div>
    </div>

    <div if="{{advancedTitle == 'MISSION PACK'}}" class="v4-stage v4-mission-stage">
      <div class="v4-mission-flow"><div class="v4-mission-node active-node"><text class="v4-node-k">CACHE</text><text class="v4-node-v">{{cacheState}}</text></div><div class="v4-mission-link"><div class="v4-flow-packet"></div></div><div class="v4-mission-node"><text class="v4-node-k">ROUTE</text><text class="v4-node-v">{{breadcrumbPoints}}</text></div><div class="v4-mission-link"><div class="v4-flow-packet fp2"></div></div><div class="v4-mission-node"><text class="v4-node-k">SAFE</text><text class="v4-node-v">{{anchorsCount}}</text></div></div>
      <text class="v4-stage-note">WEATHER {{weatherState}} • {{missionLabel}}</text>
    </div>

    <div if="{{advancedTitle == 'ENVIRONMENT RISK'}}" class="v4-stage v4-env-risk-stage">
      <div class="v4-risk-dial"><div class="v4-risk-ring"></div><text class="v4-risk-value">{{envRisk}}</text><text class="v4-risk-label">RISK</text></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">TEMP</text><text class="v4-v">{{weatherTemp}}</text></div><div class="v4-stat"><text class="v4-k">UV</text><text class="v4-v">{{weatherUV}}</text></div><div class="v4-stat"><text class="v4-k">PRESSURE</text><text class="v4-v">{{pressureTrend}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'SENSOR SELF-TEST'}}" class="v4-stage v4-sensor-stage">
      <div class="v4-sensor-grid"><div class="v4-sensor-cell"><text class="v4-k">GPS</text><text class="v4-sensor-icon">◎</text><text class="v4-v">{{gpsState}}</text></div><div class="v4-sensor-cell"><text class="v4-k">HR</text><text class="v4-sensor-icon">♥</text><text class="v4-v">{{heartRate}}</text></div><div class="v4-sensor-cell"><text class="v4-k">BARO</text><text class="v4-sensor-icon">◌</text><text class="v4-v">{{pressure}}</text></div><div class="v4-sensor-cell"><text class="v4-k">COMP</text><text class="v4-sensor-icon">◇</text><text class="v4-v">{{headingNameText}}</text></div><div class="v4-sensor-cell"><text class="v4-k">MOTION</text><text class="v4-sensor-icon">⌁</text><text class="v4-v">{{impactButtonLabel}}</text></div><div class="v4-sensor-cell"><text class="v4-k">LINK</text><text class="v4-sensor-icon">↔</text><text class="v4-v">{{connectionState}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'MISSION TIMELINE PRO'}}" class="v4-stage v4-timeline-stage">
      <div class="v4-timeline-rail"><div class="v4-timeline-pulse"></div></div><div class="v4-timeline-items"><text class="v4-timeline-item">{{timeline1}}</text><text class="v4-timeline-item">{{timeline2}}</text><text class="v4-timeline-item">{{timeline3}}</text><text class="v4-timeline-item">{{timeline4}}</text></div>
    </div>

    <div if="{{advancedTitle == 'VOICE MACRO ENGINE'}}" class="v4-stage v4-voice-stage">
      <div class="voice-core v4-voice-core"><div if="{{powerProfile != 'ENDURANCE'}}" class="voice-ring vr1"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="voice-ring vr2"></div><text class="voice-icon">MIC</text></div>
      <div class="v4-chip-grid"><text class="v4-chip">SAVE CAR</text><text class="v4-chip">RETURN</text><text class="v4-chip">WEATHER</text><text class="v4-chip">POWER</text></div>
    </div>

    <div if="{{advancedTitle == 'NOTIFICATION FILTER'}}" class="v4-stage v4-notify-stage">
      <div class="v4-alert-lane critical-lane"><text class="v4-alert-k">CRITICAL</text><div class="v4-alert-track"><div class="v4-alert-packet ap1"></div></div><text class="v4-alert-v">IMMEDIATE</text></div>
      <div class="v4-alert-lane warning-lane"><text class="v4-alert-k">WARNING</text><div class="v4-alert-track"><div class="v4-alert-packet ap2"></div></div><text class="v4-alert-v">FILTERED</text></div>
      <div class="v4-alert-lane info-lane"><text class="v4-alert-k">INFO</text><div class="v4-alert-track"><div class="v4-alert-packet ap3"></div></div><text class="v4-alert-v">QUIET</text></div>
    </div>

    <div if="{{advancedTitle == 'NEARBY DEVICE RECON'}}" class="v4-stage v4-bt-stage">
      <div class="network-radar v4-device-radar"><div class="radar-ring r1"></div><div class="radar-ring r2"></div><div class="radar-ring r3"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="radar-sweep"></div><div class="radar-core"><text class="radar-value">{{btCount}}</text><text class="radar-label">BLE</text></div></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">TRUSTED</text><text class="v4-v">{{btTrusted}}</text></div><div class="v4-stat"><text class="v4-k">UNKNOWN</text><text class="v4-v">{{btUnknown}}</text></div><div class="v4-stat"><text class="v4-k">MODE</text><text class="v4-v">PHONE</text></div></div>
    </div>

    <div if="{{advancedTitle == 'RUNNING ZONE HUD'}}" class="v4-stage v4-running-stage">
      <div class="sport-ring v4-run-ring"><div class="sport-ring-inner"><text class="sport-value">{{speedKmh}}</text><text class="sport-unit">KM/H</text></div></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">HR</text><text class="v4-v">{{heartRate}}</text></div><div class="v4-stat"><text class="v4-k">ALT</text><text class="v4-v">{{altitude}}</text></div><div class="v4-stat"><text class="v4-k">ZONE</text><text class="v4-v">LIVE</text></div></div>
    </div>

    <div if="{{advancedTitle == 'SKY SCANNER PRO'}}" class="v4-stage v4-sky-stage">
      <div class="sky-orbit v4-sky-orbit"><div class="sky-core">SKY</div><div class="sky-ring sr1"></div><div class="sky-ring sr2"></div><div class="sky-dot sk1"></div><div class="sky-dot sk2"></div><div class="sky-dot sk3"></div></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">SUN</text><text class="v4-v">{{weatherSun}}</text></div><div class="v4-stat"><text class="v4-k">WEATHER</text><text class="v4-v">{{weatherState}}</text></div><div class="v4-stat"><text class="v4-k">UV</text><text class="v4-v">{{weatherUV}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'NIGHT / STEALTH HUD'}}" class="v4-stage v4-stealth-stage">
      <div class="v4-stealth-core"><div class="v4-stealth-cross-h"></div><div class="v4-stealth-cross-v"></div><text class="v4-stealth-text">STEALTH</text></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">POWER</text><text class="v4-v">{{powerProfile}}</text></div><div class="v4-stat"><text class="v4-k">ALERT</text><text class="v4-v">{{notificationMode}}</text></div><div class="v4-stat"><text class="v4-k">MOTION</text><text class="v4-v">LOW</text></div></div>
    </div>

    <div if="{{advancedTitle == 'RETURN DECISION HUD'}}" class="v4-stage v4-return-stage">
      <div class="v4-return-route"><div class="v4-route-base">BASE</div><div class="v4-route-line"><div class="v4-route-packet"></div></div><div class="v4-route-user">YOU</div></div>
      <div class="v4-return-stats"><div class="v4-stat"><text class="v4-k">ROUTE</text><text class="v4-v">{{routeSummary}}</text></div><div class="v4-stat"><text class="v4-k">POWER</text><text class="v4-v">{{watchBattery}}%</text></div><div class="v4-stat"><text class="v4-k">WEATHER</text><text class="v4-v">{{weatherState}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'FIELD QUICK PROFILES'}}" class="v4-stage v4-profile-stage">
      <div class="v4-profile-grid"><div class="v4-profile-card"><text class="v4-profile-icon">◉</text><text class="v4-profile-name">DAILY</text></div><div class="v4-profile-card"><text class="v4-profile-icon">△</text><text class="v4-profile-name">OUTDOOR</text></div><div class="v4-profile-card"><text class="v4-profile-icon">⌁</text><text class="v4-profile-name">RUNNING</text></div><div class="v4-profile-card"><text class="v4-profile-icon">◐</text><text class="v4-profile-name">NIGHT</text></div></div>
    </div>

    <div if="{{advancedTitle == 'IMPACT REVIEW'}}" class="v4-stage v4-impact-stage">
      <div class="v4-impact-core"><div class="v4-impact-h"></div><div class="v4-impact-v"></div><text class="v4-impact-text">IMPACT</text></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">GPS</text><text class="v4-v">{{gpsState}}</text></div><div class="v4-stat"><text class="v4-k">HR</text><text class="v4-v">{{heartRate}}</text></div><div class="v4-stat"><text class="v4-k">ASSIST</text><text class="v4-v">{{impactButtonLabel}}</text></div></div>
    </div>

    <div if="{{advancedTitle == 'EMERGENCY ESCALATION'}}" class="v4-stage v4-escalation-stage">
      <div class="v4-escalation-ring"><div class="v4-escalation-inner"><text class="v4-escalation-title">L0–L3</text><text class="v4-escalation-state">{{advancedState}}</text></div></div>
      <div class="v4-level-grid"><text class="v4-level l0">L0 OK</text><text class="v4-level l1">L1 CHECK</text><text class="v4-level l2">L2 WARN</text><text class="v4-level l3">L3 SOS</text></div>
    </div>

    <div if="{{advancedTitle == 'FIELD CORE SETTINGS'}}" class="v4-stage v4-settings-stage">
      <div class="shield-core v4-settings-shield"><div if="{{powerProfile != 'ENDURANCE'}}" class="shield-ring"></div><text class="shield-text">LOCAL</text></div>
      <div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">SCAN</text><text class="v4-v">{{wifiScanMode}}</text></div><div class="v4-stat"><text class="v4-k">ALERT</text><text class="v4-v">{{notificationMode}}</text></div><div class="v4-stat"><text class="v4-k">PRIVACY</text><text class="v4-v">LOCAL FIRST</text></div></div>
    </div>

    <!-- Recon / utility Advanced pages also get distinct visual identities. -->
    <div if="{{advancedTitle == 'BEST WI-FI'}}" class="v4-stage v4-bestwifi-stage"><div class="v4-score-ring"><text class="v4-score">BEST</text><text class="v4-score-name">{{wifiBest}}</text></div><div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">OPEN</text><text class="v4-v">{{wifiOpen}}</text></div><div class="v4-stat"><text class="v4-k">SECURED</text><text class="v4-v">{{wifiSecured}}</text></div><div class="v4-stat"><text class="v4-k">AGE</text><text class="v4-v">{{wifiAge}}s</text></div></div></div>
    <div if="{{advancedTitle == 'CHANNELS'}}" class="v4-stage v4-channel-stage"><div class="v4-channel-bars"><div class="v4-channel-bar cb1"></div><div class="v4-channel-bar cb2"></div><div class="v4-channel-bar cb3"></div><div class="v4-channel-bar cb4"></div><div class="v4-channel-bar cb5"></div><div class="v4-channel-bar cb6"></div></div><text class="v4-stage-note">2.4 / 5 / 6 GHz LOAD</text></div>
    <div if="{{advancedTitle == 'SIGNAL HUNT'}}" class="v4-stage v4-signal-stage"><div class="eq-row v4-signal-eq"><div class="eq-bar eq1"></div><div class="eq-bar eq5"></div><div class="eq-bar eq2"></div><div class="eq-bar eq6"></div><div class="eq-bar eq3"></div><div class="eq-bar eq4"></div><div class="eq-bar eq7"></div></div><text class="v4-stage-note">RSSI TREND • NOT PHYSICAL DIRECTION</text></div>
    <div if="{{advancedTitle == 'DUPLICATE SSID'}}" class="v4-stage v4-duplicate-stage"><div class="v4-duplicate-node"><text class="v4-duplicate-icon">WIFI A</text></div><div class="v4-duplicate-link">?</div><div class="v4-duplicate-node"><text class="v4-duplicate-icon">WIFI B</text></div><text class="v4-stage-note">HEURISTIC ONLY • VERIFY BEFORE CONNECTING</text></div>
    <div if="{{advancedTitle == 'OUTDOOR SCAN'}}" class="v4-stage v4-outdoor-stage"><div class="network-radar v4-outdoor-radar"><div class="radar-ring r1"></div><div class="radar-ring r2"></div><div if="{{powerProfile != 'ENDURANCE'}}" class="radar-sweep"></div><div class="radar-core"><text class="radar-value">{{wifiCount}}</text><text class="radar-label">OUTDOOR</text></div></div><div class="v4-side-stats"><div class="v4-stat"><text class="v4-k">MODE</text><text class="v4-v">{{wifiScanMode}}</text></div><div class="v4-stat"><text class="v4-k">AGE</text><text class="v4-v">{{wifiAge}}s</text></div></div></div>
    <div if="{{advancedTitle == 'FIND PHONE'}}" class="v4-stage v4-findphone-stage"><div class="v4-phone-core"><div class="v4-phone-pulse pp1"></div><div class="v4-phone-pulse pp2"></div><text class="v4-phone-text">PHONE</text></div><text class="v4-stage-note">HAPTIC ALERT REQUEST</text></div>
    <div if="{{advancedTitle == 'DEVICE HISTORY'}}" class="v4-stage v4-history-stage"><div class="v4-history-line"><text class="v4-k">BLE HISTORY</text><text class="v4-v">{{btCount}}</text></div><div class="v4-history-line"><text class="v4-k">TRUSTED</text><text class="v4-v">{{btTrusted}}</text></div><div class="v4-history-line"><text class="v4-k">UNKNOWN</text><text class="v4-v">{{btUnknown}}</text></div></div>
'''
    hml = hml.replace(insertion_point, stages + '\n' + insertion_point, 1)

if CSS_MARK not in css:
    css += r'''

/* FIELD CORE VISUAL V4: DISTINCT ALL-PAGE MASTERPIECE
   Visual-only extension.  Runtime commands, 28 feature IDs, storage and providers are unchanged.
*/
.bio-page-v4 .category-hero { border-color:#0d5361; }
.sport-page-v4 .sport-stage { border-color:#145464; background-color:#020a0f; }
.nav-page-v4 .nav-stage { border-color:#0b5c6c; }
.env-page-v4 .env-stage { border-color:#0e4d5c; background-color:#020b10; }
.system-page-v4 .system-core-panel { border-color:#15515f; }
.detail-page-v4 .module-stage { border-radius:12px; border-width:1px; border-color:#153b47; background-color:#02080b; }
.wifi-scout-v4 .wifi-stage { border-radius:12px; border-width:1px; border-color:#0c5666; background-color:#01080d; }
.wifi-list-v4 .wifi-network-row { border-color:#174957; }
.wifi-detail-v4 .wifi-detail-card { border-color:#155361; }
.cyber-sweep-v4 .cyber-sweep-stage { border-color:#0d5968; }
.advanced-hub-v4 .advanced-summary { border-radius:10px; border-width:1px; border-color:#174a57; background-color:#02090d; }
.advanced-page-v4 .advanced-core { height:64px; border-color:#174b58; background-color:#02090d; margin-bottom:4px; }
.advanced-page-v4 .command-core { width:92px; height:54px; border-radius:27px; }
.advanced-page-v4 .advanced-side { height:58px; }
.advanced-page-v4 .module-stat { height:27px; }
.advanced-page-v4 .advanced-data-card { min-height:50px; margin-top:4px; }

.v4-stage { width:452px; height:88px; border-radius:12px; border-width:1px; border-color:#174957; background-color:#01070b; margin-top:3px; margin-bottom:3px; flex-direction:row; align-items:center; justify-content:center; position:relative; overflow:hidden; }
.v4-stage-note { color:#708a95; font-size:6px; text-align:center; }
.v4-side-stats { width:250px; height:78px; flex-direction:column; justify-content:center; margin-left:12px; }
.v4-stat { width:242px; height:24px; border-bottom-width:1px; border-color:#0b2b34; flex-direction:row; justify-content:space-between; align-items:center; }
.v4-k { color:#617481; font-size:6px; }
.v4-v { color:#00e5ff; font-size:7px; }

/* Command Center: operational terrain / target view */
.v4-command-stage { justify-content:space-between; padding:4px 10px; }
.v4-terrain { width:170px; height:76px; position:relative; border-radius:8px; border-width:1px; border-color:#123c48; background-color:#01080c; }
.v4-terrain-line { position:absolute; left:8px; width:154px; height:1px; background-color:#00e5ff; opacity:0.25; transform-origin:77px 0px; }
.tl1 { top:24px; transform:rotate(-8deg); } .tl2 { top:39px; transform:rotate(6deg); } .tl3 { top:53px; transform:rotate(-3deg); }
.v4-command-target { position:absolute; left:64px; top:24px; width:42px; height:42px; border-radius:21px; border-width:2px; border-color:#00e5ff; align-items:center; justify-content:center; animation-name:ringPulse; animation-duration:1800ms; animation-iteration-count:infinite; }
.v4-target-text { color:#ffffff; font-size:7px; }

/* Context: concentric context wheel */
.v4-context-stage { justify-content:space-around; }
.v4-context-wheel { width:82px; height:82px; border-radius:41px; border-width:1px; border-color:#174957; position:relative; align-items:center; justify-content:center; flex-direction:column; }
.v4-context-ring { position:absolute; border-radius:50%; border-width:1px; border-color:#00e5ff; opacity:0.35; animation-name:ringPulse; animation-duration:1900ms; animation-iteration-count:infinite; }
.cr1 { left:7px; top:7px; width:68px; height:68px; } .cr2 { left:18px; top:18px; width:46px; height:46px; animation-delay:350ms; }
.v4-context-main { color:#ffffff; font-size:9px; z-index:2; } .v4-context-conf { color:#00e5ff; font-size:6px; z-index:2; }
.v4-chip-grid { width:300px; height:68px; flex-direction:row; flex-wrap:wrap; justify-content:space-around; align-items:center; }
.v4-chip { width:138px; height:25px; border-radius:7px; border-width:1px; border-color:#174957; background-color:#02090d; color:#00e5ff; font-size:7px; text-align:center; padding-top:7px; }

/* Telemetry Confidence: four independent quality lanes */
.v4-confidence-stage { flex-direction:column; justify-content:center; }
.v4-quality-row { width:420px; height:19px; flex-direction:row; align-items:center; justify-content:space-between; }
.v4-quality-label { width:48px; color:#7d8dae; font-size:6px; }
.v4-quality-track { width:238px; height:4px; border-radius:2px; background-color:#10232a; overflow:hidden; }
.v4-quality-fill { height:4px; background-color:#00e5ff; animation-name:dataFlow; animation-duration:1800ms; animation-iteration-count:infinite; }
.qf1 { width:214px; } .qf2 { width:184px; } .qf3 { width:226px; } .qf4 { width:164px; }
.v4-quality-value { width:110px; color:#00e5ff; font-size:6px; text-align:right; }

.v4-lost-stage, .v4-bt-stage, .v4-running-stage, .v4-sky-stage, .v4-env-risk-stage, .v4-settings-stage, .v4-outdoor-stage, .v4-bestwifi-stage { justify-content:center; }
.v4-lost-radar, .v4-device-radar, .v4-outdoor-radar { width:78px; height:78px; border-radius:39px; }
.v4-lost-radar .r1, .v4-device-radar .r1, .v4-outdoor-radar .r1 { left:9px; top:9px; width:60px; height:60px; }
.v4-lost-radar .r2, .v4-device-radar .r2, .v4-outdoor-radar .r2 { left:20px; top:20px; width:38px; height:38px; }
.v4-lost-radar .r3, .v4-device-radar .r3 { left:30px; top:30px; width:18px; height:18px; }
.v4-lost-radar .radar-sweep, .v4-device-radar .radar-sweep, .v4-outdoor-radar .radar-sweep { left:38px; top:7px; height:32px; transform-origin:1px 32px; }
.v4-lost-radar .radar-core, .v4-device-radar .radar-core, .v4-outdoor-radar .radar-core { left:18px; top:27px; width:42px; height:24px; }

/* Mission Pack: cache -> route -> safe-point data flow */
.v4-mission-stage { flex-direction:column; }
.v4-mission-flow { width:420px; height:56px; flex-direction:row; align-items:center; justify-content:center; }
.v4-mission-node { width:94px; height:44px; border-radius:8px; border-width:1px; border-color:#174957; background-color:#02090d; flex-direction:column; align-items:center; justify-content:center; }
.active-node { border-color:#00e5ff; background-color:#00242c; }
.v4-node-k { color:#7d8dae; font-size:6px; } .v4-node-v { color:#00e5ff; font-size:7px; margin-top:2px; }
.v4-mission-link { width:55px; height:2px; background-color:#15343d; position:relative; overflow:hidden; }
.v4-flow-packet { width:14px; height:2px; background-color:#00e5ff; animation-name:packetMove; animation-duration:1200ms; animation-iteration-count:infinite; }
.fp2 { animation-delay:400ms; }

/* Environmental Risk */
.v4-risk-dial { width:76px; height:76px; border-radius:38px; border-width:6px; border-style:dashed; border-color:#ffcc00; background-color:#080703; flex-direction:column; align-items:center; justify-content:center; animation-name:ringPulse; animation-duration:2200ms; animation-iteration-count:infinite; }
.v4-risk-value { color:#ffffff; font-size:10px; } .v4-risk-label { color:#ffcc00; font-size:6px; }

/* Sensor Self-Test matrix */
.v4-sensor-stage { flex-direction:column; }
.v4-sensor-grid { width:420px; height:78px; flex-direction:row; flex-wrap:wrap; justify-content:space-around; align-items:center; }
.v4-sensor-cell { width:132px; height:35px; border-radius:7px; border-width:1px; border-color:#16424d; background-color:#02090d; flex-direction:row; align-items:center; justify-content:space-around; }
.v4-sensor-icon { color:#00e5ff; font-size:10px; }

/* Timeline Pro */
.v4-timeline-stage { justify-content:flex-start; padding-left:18px; }
.v4-timeline-rail { width:12px; height:72px; border-left-width:2px; border-color:#00e5ff; position:relative; }
.v4-timeline-pulse { position:absolute; left:-4px; top:4px; width:7px; height:7px; border-radius:4px; background-color:#00e5ff; animation-name:timelineMove; animation-duration:2200ms; animation-iteration-count:infinite; }
.v4-timeline-items { width:392px; height:76px; flex-direction:column; justify-content:space-around; }
.v4-timeline-item { width:382px; height:16px; color:#b8cbd2; font-size:6px; border-bottom-width:1px; border-color:#0b2b34; }

/* Voice Macro */
.v4-voice-stage { justify-content:space-around; }
.v4-voice-core { width:78px; height:78px; }

/* Notification priority lanes */
.v4-notify-stage { flex-direction:column; justify-content:center; }
.v4-alert-lane { width:420px; height:23px; flex-direction:row; align-items:center; justify-content:space-between; }
.v4-alert-k { width:70px; font-size:6px; color:#7d8dae; }
.v4-alert-track { width:250px; height:3px; background-color:#12252c; overflow:hidden; }
.v4-alert-packet { width:44px; height:3px; background-color:#00e5ff; animation-name:packetMove; animation-duration:1600ms; animation-iteration-count:infinite; }
.ap2 { animation-delay:300ms; background-color:#ffcc00; } .ap3 { animation-delay:600ms; opacity:0.5; }
.v4-alert-v { width:80px; font-size:6px; color:#00e5ff; text-align:right; }
.critical-lane .v4-alert-k, .critical-lane .v4-alert-v { color:#ff335f; }
.warning-lane .v4-alert-k, .warning-lane .v4-alert-v { color:#ffcc00; }

/* Running Zone */
.v4-run-ring { width:76px; height:76px; border-radius:38px; }
.v4-run-ring .sport-ring-inner { width:54px; height:54px; border-radius:27px; }

/* Sky */
.v4-sky-orbit { width:78px; height:78px; }

/* Stealth: dark red low-motion crosshair */
.v4-stealth-stage { background-color:#070204; border-color:#52202b; }
.v4-stealth-core { width:76px; height:76px; border-radius:38px; border-width:1px; border-color:#ff335f; position:relative; align-items:center; justify-content:center; }
.v4-stealth-cross-h { position:absolute; left:9px; top:37px; width:58px; height:1px; background-color:#ff335f; opacity:0.55; }
.v4-stealth-cross-v { position:absolute; left:37px; top:9px; width:1px; height:58px; background-color:#ff335f; opacity:0.55; }
.v4-stealth-text { color:#ff335f; font-size:7px; }

/* Return Decision */
.v4-return-stage { flex-direction:column; }
.v4-return-route { width:410px; height:43px; flex-direction:row; align-items:center; justify-content:center; }
.v4-route-base, .v4-route-user { width:58px; height:28px; border-radius:8px; border-width:1px; border-color:#00e5ff; color:#00e5ff; font-size:6px; text-align:center; padding-top:9px; }
.v4-route-line { width:260px; height:2px; background-color:#15343d; overflow:hidden; }
.v4-route-packet { width:28px; height:2px; background-color:#00e5ff; animation-name:packetMove; animation-duration:1500ms; animation-iteration-count:infinite; }
.v4-return-stats { width:410px; height:34px; flex-direction:row; justify-content:space-between; }
.v4-return-stats .v4-stat { width:132px; height:31px; flex-direction:column; align-items:center; justify-content:center; border-width:1px; border-color:#174957; border-radius:7px; }

/* Quick Profiles */
.v4-profile-grid { width:420px; height:76px; flex-direction:row; justify-content:space-around; align-items:center; }
.v4-profile-card { width:96px; height:62px; border-radius:9px; border-width:1px; border-color:#174957; background-color:#02090d; flex-direction:column; align-items:center; justify-content:center; }
.v4-profile-icon { color:#00e5ff; font-size:16px; } .v4-profile-name { color:#ffffff; font-size:6px; margin-top:4px; }

/* Impact Review */
.v4-impact-core { width:76px; height:76px; border-radius:38px; border-width:2px; border-color:#ff335f; position:relative; align-items:center; justify-content:center; }
.v4-impact-h { position:absolute; left:7px; top:37px; width:62px; height:2px; background-color:#ff335f; }
.v4-impact-v { position:absolute; left:37px; top:7px; width:2px; height:62px; background-color:#ff335f; }
.v4-impact-text { color:#ffffff; font-size:7px; z-index:2; }

/* Emergency escalation */
.v4-escalation-stage { background-color:#080105; border-color:#6d1731; }
.v4-escalation-ring { width:76px; height:76px; border-radius:38px; border-width:6px; border-style:dashed; border-color:#ff335f; align-items:center; justify-content:center; animation-name:ringPulse; animation-duration:1200ms; animation-iteration-count:infinite; }
.v4-escalation-inner { width:52px; height:52px; border-radius:26px; border-width:1px; border-color:#8b2540; background-color:#16040a; flex-direction:column; align-items:center; justify-content:center; }
.v4-escalation-title { color:#ff335f; font-size:9px; } .v4-escalation-state { color:#ffffff; font-size:6px; }
.v4-level-grid { width:300px; height:66px; flex-direction:row; flex-wrap:wrap; justify-content:space-around; align-items:center; margin-left:14px; }
.v4-level { width:140px; height:27px; border-radius:7px; border-width:1px; border-color:#5b2735; color:#b68b97; font-size:6px; text-align:center; padding-top:8px; }
.l3 { border-color:#ff335f; color:#ff335f; }

/* Settings / privacy */
.v4-settings-shield { width:76px; height:76px; }

/* Recon utility screens */
.v4-score-ring { width:78px; height:78px; border-radius:39px; border-width:6px; border-style:dashed; border-color:#00e5ff; flex-direction:column; align-items:center; justify-content:center; }
.v4-score { color:#ffffff; font-size:8px; } .v4-score-name { width:62px; color:#00e5ff; font-size:6px; text-align:center; margin-top:3px; }
.v4-channel-stage { flex-direction:column; }
.v4-channel-bars { width:360px; height:58px; flex-direction:row; align-items:flex-end; justify-content:space-around; }
.v4-channel-bar { width:32px; background-color:#00e5ff; opacity:0.65; animation-name:eqBounce; animation-duration:900ms; animation-iteration-count:infinite; animation-direction:alternate; }
.cb1 { height:18px; } .cb2 { height:42px; animation-delay:100ms; } .cb3 { height:30px; animation-delay:200ms; } .cb4 { height:52px; animation-delay:300ms; } .cb5 { height:25px; animation-delay:150ms; } .cb6 { height:38px; animation-delay:70ms; }
.v4-signal-stage { flex-direction:column; } .v4-signal-eq { height:48px; }
.v4-duplicate-stage { flex-wrap:wrap; }
.v4-duplicate-node { width:120px; height:52px; border-radius:9px; border-width:1px; border-color:#ffcc00; background-color:#0c0902; align-items:center; justify-content:center; }
.v4-duplicate-icon { color:#ffcc00; font-size:7px; } .v4-duplicate-link { width:48px; color:#ffcc00; font-size:17px; text-align:center; }
.v4-duplicate-stage .v4-stage-note { width:420px; margin-top:2px; }
.v4-findphone-stage { flex-direction:column; }
.v4-phone-core { width:58px; height:58px; border-radius:12px; border-width:2px; border-color:#00e5ff; position:relative; align-items:center; justify-content:center; }
.v4-phone-pulse { position:absolute; border-radius:50%; border-width:1px; border-color:#00e5ff; animation-name:ringPulse; animation-duration:1500ms; animation-iteration-count:infinite; }
.pp1 { left:-9px; top:-9px; width:76px; height:76px; } .pp2 { left:-18px; top:-18px; width:94px; height:94px; animation-delay:300ms; }
.v4-phone-text { color:#ffffff; font-size:7px; }
.v4-history-stage { flex-direction:column; }
.v4-history-line { width:400px; height:24px; border-bottom-width:1px; border-color:#0b2b34; flex-direction:row; align-items:center; justify-content:space-between; }

/* Page family refinements copied from the selected concept: same palette, different layouts. */
.bio-page-v4 .page-subtitle, .sport-page-v4 .page-subtitle, .nav-page-v4 .page-subtitle, .env-page-v4 .page-subtitle, .system-page-v4 .page-subtitle { color:#00e5ff; }
.tactical-page-v4 .page-subtitle, .tactical-page-v4 .status-secure { color:#ff335f; }
.tactical-page-v4 .subtitle-line { background-color:#ff335f; }
.emergency-v4 { background-color:#090105; }
.emergency-v4 .emergency-dial { border-color:#ff335f; }
'''

# Sanity checks: the visual update must not remove any original feature surface.
for i in range(28):
    token = "selectedId == '%d'" % i
    if token not in hml:
        raise SystemExit('missing feature visual token: ' + token)

for title in [
    'COMMAND CENTER','FIELD CONTEXT','TELEMETRY CONFIDENCE','LOST MODE PRO','MISSION PACK',
    'ENVIRONMENT RISK','SENSOR SELF-TEST','MISSION TIMELINE PRO','VOICE MACRO ENGINE',
    'NOTIFICATION FILTER','NEARBY DEVICE RECON','RUNNING ZONE HUD','SKY SCANNER PRO',
    'NIGHT / STEALTH HUD','RETURN DECISION HUD','FIELD QUICK PROFILES','IMPACT REVIEW',
    'EMERGENCY ESCALATION','FIELD CORE SETTINGS','BEST WI-FI','CHANNELS','SIGNAL HUNT',
    'DUPLICATE SSID','OUTDOOR SCAN','FIND PHONE','DEVICE HISTORY'
]:
    if title not in hml:
        raise SystemExit('missing V4 advanced visual: ' + title)

HML.write_text(hml, encoding='utf-8')
CSS.write_text(css, encoding='utf-8')
print('FIELD CORE Visual V4 applied: distinct Masterpiece layouts across all feature families and Advanced pages.')
