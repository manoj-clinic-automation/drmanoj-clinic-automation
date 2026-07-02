/**
 * CallConsole.gs  —  Call Console Step 1 (server data layer)
 * ==========================================================
 * Dr. Manoj Agarwal Clinic, Bareilly.  Session 21 · 30 Jun 2026.
 * Updated Session 27 · 01 Jul 2026 — v1.1: adds LAST-VISIT to the patient
 *   context (spec v1.1 §4.4/§6, decision C16). Only change vs the v1.0 file.
 * Updated Session 31 · 02 Jul 2026 — v1.2: adds getFollowupClinicIds (D52) —
 *   phone→Clinic ID enrichment for follow-up rows, cloning the S27 last-visit
 *   pattern. Purely additive; no existing function changed.
 * Spec: Call_Console_Evolution_Spec v1.1, §5 + §7 Step 1.
 * Session 27 fix: clinicId now reads the NUMERIC 'Clinic_Specific_Id' column
 *   IF a Clinic_Specific_Id column exists in Patient_Master; blank otherwise.
 *   Never shows the alphanumeric Patient UID or the patient name as the ID.
 *   (Patient_Master currently has: mobile, patient name, diagnosis, age, gender,
 *    last visit, patient uid — no numeric Clinic ID yet. Add that column and the
 *    numeric ID appears automatically, no code change.)
 *
 * WHY A SEPARATE FILE (not an edit to WebApp.gs):
 *   The spec said "add these functions to WebApp.gs". A new file in the same
 *   Apps Script project is functionally identical — all .gs files share one
 *   global scope — but it touches the LIVE WebApp.gs ZERO times. That removes
 *   all risk to the running dashboard and keeps the manual/existing flow intact.
 *   This is purely ADDITIVE: nothing here is called by the current Dashboard.html,
 *   so deploying it changes NOTHING the dashboard shows today. Step 2 (the UI)
 *   will call these functions.
 *
 * WHAT THIS PROVIDES (the three Step-1 pieces):
 *   getAllCallsToday(key, force)  — every call today (both directions, all
 *                                   statuses), patient-enriched, newest first.
 *   getAgentIdentity(key)         — { name, ext } for the logged-in agent.
 *   logOutcome(key, payload)      — appends one row to the Outcomes_Log tab
 *                                   (the permanent Excel replacement). Creates
 *                                   the tab + header on first use.
 *
 * SAFE EXTERNAL CALLS (confirmed present in this project):
 *   fetchCallsBetween_(startDate, endDate)   — MyOperator.gs (returns enriched
 *                                              records: phone10, direction,
 *                                              duration_seconds, is_missed,
 *                                              status, start_time, filename)
 *   dashRole_(key)                            — WebApp.gs ('full'|'staff'|'none')
 *   agentInfoForKey_(key)                     — WebApp.gs ({ext,name,userId,...})
 * Everything else (patient map, agent map, day bounds, formatting) is read
 * DEFENSIVELY inside this file, so it does not depend on any other helper's
 * exact return shape.  All private helpers are prefixed cc_ to avoid clashes.
 *
 * NAMING NOTE: the public entry points do NOT end in "_", so Step 2's page can
 * call them via google.script.run. (Apps Script will not expose names ending
 * in "_" to the client.)
 */

// ---------------------------------------------------------------------------
// CONFIG (identifiers only — no secrets)
// ---------------------------------------------------------------------------
var CC_TZ            = 'Asia/Kolkata';
var CC_SHEET_ID_PROP = 'SHEET_ID';   // Script Property holding the spreadsheet id
var CC_SHEET_ID_FALLBACK = '1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0';
var CC_TAB_PATIENT   = 'Patient_Master';
var CC_TAB_AGENTS    = 'Agents';
var CC_TAB_OUTCOMES  = 'Outcomes_Log';

var CC_OUTCOMES_HEADER = [
  'Timestamp', 'Agent Name', 'Ext', 'Direction', 'Number (last-4)',
  'Patient Name', 'Clinic ID', 'Outcome', 'Notes', 'Call Duration',
  'Recording filename'
];

// ===========================================================================
// PUBLIC ENTRY POINTS  (callable from the page via google.script.run)
// ===========================================================================

/**
 * Every call today, both directions, all statuses, newest first, enriched with
 * patient name + Clinic ID. `force` is accepted for API symmetry (no cache here;
 * the spec polls live every 30s).
 * Returns { ok:true, updated, calls:[...] } or { ok:false, error }.
 */
function getAllCallsToday(key, force) {
  try {
    if (dashRole_(key) === 'none') {
      return { ok: false, error: 'Not authorized. Please sign in again.' };
    }
    var calls = cc_buildAllCallsToday_();
    return {
      ok: true,
      updated: Utilities.formatDate(new Date(), CC_TZ, 'HH:mm:ss'),
      calls: calls
    };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/**
 * Identity for the top-bar badge + outcome logging. Server-derived from the
 * login key — never trusts the page.
 * Returns { ok:true, name, ext } or { ok:false, error }.
 */
function getAgentIdentity(key) {
  try {
    if (dashRole_(key) === 'none') {
      return { ok: false, error: 'Not authorized.' };
    }
    var info = agentInfoForKey_(key);
    return {
      ok: true,
      name: (info && info.name) ? info.name : '',
      ext:  (info && info.ext)  ? info.ext  : ''
    };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/**
 * Append ONE outcome row to Outcomes_Log (the permanent activity record / Excel
 * replacement). The agent is resolved SERVER-SIDE from `key`; the page never
 * supplies the agent. The phone number is stored masked (last-4 only).
 *
 * payload (all optional except outcome):
 *   { direction, number, patientName, clinicId, outcome, notes,
 *     durationSec, recording }
 * Returns { ok:true } or { ok:false, error }.
 */
function logOutcome(key, payload) {
  try {
    if (dashRole_(key) === 'none') {
      return { ok: false, error: 'Not authorized. Please sign in again.' };
    }
    payload = payload || {};
    if (!String(payload.outcome || '').trim()) {
      return { ok: false, error: 'No outcome given.' };
    }

    var info = agentInfoForKey_(key) || {};
    var ss = cc_openSheet_();
    var sh = cc_ensureOutcomesTab_(ss);

    var row = [
      Utilities.formatDate(new Date(), CC_TZ, 'yyyy-MM-dd HH:mm:ss'),
      info.name || '',
      info.ext || '',
      cc_dir_(payload.direction),
      cc_last4_(payload.number),
      String(payload.patientName || ''),
      String(payload.clinicId || ''),
      String(payload.outcome || ''),
      String(payload.notes || ''),
      cc_mmss_(cc_int_(payload.durationSec)),
      String(payload.recording || '')
    ];
    sh.appendRow(row);
    return { ok: true };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/**
 * Editor-only self test (safe). Run from the Apps Script editor, then read
 * View -> Execution log. Prints counts + one sample row. Writes NOTHING and
 * prints no secrets / no full numbers.
 */
function CC_SELFTEST() {
  var sp = PropertiesService.getScriptProperties();
  var key = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
  Logger.log('key present: %s  role: %s', key ? 'yes' : 'NO', dashRole_(key));

  var ident = getAgentIdentity(key);
  Logger.log('identity: %s', JSON.stringify(ident));

  var res = getAllCallsToday(key, true);
  if (!res.ok) { Logger.log('getAllCallsToday ERROR: %s', res.error); return; }
  Logger.log('calls today: %s (updated %s)', res.calls.length, res.updated);
  if (res.calls.length) {
    var c = res.calls[0];
    Logger.log('sample: time=%s dir=%s name=%s id=%s dx=%s lastVisit=%s agent=%s dur=%s status=%s',
      c.time, c.direction, c.name, c.clinicId, c.diagnosis, c.lastVisit, c.agent, c.duration, c.status);
  }
  // Diagnostic: Patient_Master header names + which column we detect as Clinic ID (NO patient data printed).
  try {
    var pv = cc_sheetValues_(CC_TAB_PATIENT);
    if (pv.length) {
      var Hh = cc_lc_(pv[0]);
      Logger.log('Patient_Master headers: %s', JSON.stringify(Hh));
      var ix = cc_col_(Hh, ['clinic_specific_id','clinic specific id','clinic id','clinic_id','patient id']);
      Logger.log('clinic-id header match index: %s (0-based; column B = 1). Using column %s.', ix, (ix<0?1:ix));
    }
  } catch (e) { Logger.log('header diagnostic error: %s', e); }
  Logger.log('Outcomes_Log will be created on first logOutcome() call. No write done here.');
}


/**
 * getFollowupLastVisits(key) -> { ok, map:{ mobile(last10): lastVisitDate } }
 * Last-visit dates for the patients on TODAY's follow-up worklist, so the page can
 * show last-visit on follow-up rows WITHOUT editing WebApp.gs (Slice 2, additive).
 * Scoped to today's follow-up mobiles only -> small payload, not the whole patient DB.
 */
function getFollowupLastVisits(key) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ss = cc_openSheet_();
    var sh = ss.getSheetByName('Followups_Today');   // FU_TAB_TODAY (read-only here)
    if (!sh) return { ok: true, map: {} };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, map: {} };
    var H = cc_lc_(vals[0]);
    var iMob = cc_col_(H, ['mobile', 'phone number', 'mobile number', 'phone', 'number']);
    if (iMob < 0) return { ok: true, map: {} };
    var pmap = cc_patientMap_();     // phone10 -> {name, clinicId, diagnosis, lastVisit}
    var out = {};
    for (var r = 1; r < vals.length; r++) {
      var ph = cc_last10_(iMob < vals[r].length ? vals[r][iMob] : '');
      if (!ph || out[ph] !== undefined) continue;
      var pinfo = pmap[ph];
      out[ph] = (pinfo && pinfo.lastVisit) ? pinfo.lastVisit : '';
    }
    return { ok: true, map: out };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}


/**
 * getFollowupClinicIds(key) -> { ok, map:{ mobile(last10): clinicId } }
 * Session 31 (D52): numeric Clinic ID for the patients on TODAY's follow-up
 * worklist, enriched from Patient_Master by phone — exact clone of the proven
 * getFollowupLastVisits pattern (S27). Followups_Today itself carries no Clinic
 * ID column, and its row builder (getFollowups) lives in the protected
 * WebApp.gs, so this stays additive: WebApp.gs and the push scripts untouched.
 * Only returns an entry when the patient's phone matches Patient_Master AND a
 * numeric Clinic_Specific_Id is present (graceful blank otherwise).
 */
function getFollowupClinicIds(key) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ss = cc_openSheet_();
    var sh = ss.getSheetByName('Followups_Today');   // read-only here
    if (!sh) return { ok: true, map: {} };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, map: {} };
    var H = cc_lc_(vals[0]);
    var iMob = cc_col_(H, ['mobile', 'phone number', 'mobile number', 'phone', 'number']);
    if (iMob < 0) return { ok: true, map: {} };
    var pmap = cc_patientMap_();     // phone10 -> {name, clinicId, diagnosis, lastVisit}
    var out = {};
    for (var r = 1; r < vals.length; r++) {
      var ph = cc_last10_(iMob < vals[r].length ? vals[r][iMob] : '');
      if (!ph || out[ph] !== undefined) continue;
      var pinfo = pmap[ph];
      out[ph] = (pinfo && pinfo.clinicId) ? pinfo.clinicId : '';
    }
    return { ok: true, map: out };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}


/**
 * getFollowupRecordings(key) -> { ok, map:{ phone10: { fileId, date } } }
 * The most-recent ARCHIVED recording (permanent Drive copy) for each patient on TODAY's
 * follow-up worklist, so a follow-up row can offer "listen to their last call". Matches by
 * phone10, parsed from the Call_Recordings Join Key (= phone10 + "_" + start_unix). Scoped
 * to today's follow-up mobiles -> small result. Additive; WebApp.gs untouched.
 */
function getFollowupRecordings(key) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ss = cc_openSheet_();
    var fu = ss.getSheetByName('Followups_Today');
    if (!fu) return { ok: true, map: {} };
    var fv = fu.getDataRange().getValues();
    if (fv.length < 2) return { ok: true, map: {} };
    var FH = cc_lc_(fv[0]);
    var iMob = cc_col_(FH, ['mobile', 'phone number', 'mobile number', 'phone', 'number']);
    if (iMob < 0) return { ok: true, map: {} };
    var want = {};
    for (var r = 1; r < fv.length; r++) {
      var ph = cc_last10_(iMob < fv[r].length ? fv[r][iMob] : '');
      if (ph) want[ph] = 1;
    }
    var rec = ss.getSheetByName('Call_Recordings');
    if (!rec) return { ok: true, map: {} };
    var rv = rec.getDataRange().getValues();
    if (rv.length < 2) return { ok: true, map: {} };
    var RH = cc_lc_(rv[0]);
    var iKey  = cc_col_(RH, ['join key', 'join_key', 'key']);
    var iFile = cc_col_(RH, ['drive file id', 'drive_file_id', 'file id']);
    var iDate = cc_col_(RH, ['date']);
    if (iKey < 0 || iFile < 0) return { ok: true, map: {} };
    var best = {};   // phone10 -> { su, fileId, date }
    for (var q = 1; q < rv.length; q++) {
      var jk = String(rv[q][iKey] || '').trim();
      if (!jk) continue;
      var us = jk.indexOf('_');
      var ph2 = (us > 0) ? cc_last10_(jk.slice(0, us)) : cc_last10_(jk);
      if (!want[ph2]) continue;
      var su = (us > 0) ? cc_int_(jk.slice(us + 1)) : 0;
      var fileId = String((iFile < rv[q].length ? rv[q][iFile] : '') || '').trim();
      if (!fileId) continue;
      if (!best[ph2] || su > best[ph2].su) {
        best[ph2] = { su: su, fileId: fileId, date: (iDate >= 0 ? cc_dateStr_(rv[q][iDate]) : '') };
      }
    }
    var out = {};
    Object.keys(best).forEach(function (p) { out[p] = { fileId: best[p].fileId, date: best[p].date }; });
    return { ok: true, map: out };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/**
 * getArchivedRecordingAudio(key, fileId) -> { dataUri } | { error }
 * Streams a permanently-archived recording straight from the owner's Drive by File ID.
 * The web app runs AS the owner, so it can read the restricted recordings folder — this
 * works for OLD calls, where the 24h MyOperator on-demand link is long gone.
 * (First Drive use in this project -> a one-time Google re-authorization is expected.)
 */
function getArchivedRecordingAudio(key, fileId) {
  try {
    if (dashRole_(key) === 'none') return { error: 'Not authorized.' };
    fileId = String(fileId || '').trim();
    if (!fileId) return { error: 'No recording.' };
    var bytes = DriveApp.getFileById(fileId).getBlob().getBytes();
    if (!bytes || !bytes.length) return { error: 'Empty audio.' };
    return { dataUri: 'data:audio/mpeg;base64,' + Utilities.base64Encode(bytes) };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

// ===========================================================================
// CORE BUILDER
// ===========================================================================

function cc_buildAllCallsToday_() {
  var b = cc_todayBounds_();
  var raw = fetchCallsBetween_(b.start, b.end) || [];

  var pmap = cc_patientMap_();   // phone10 -> {name, clinicId, diagnosis}
  var amap = cc_agentMap_();     // userId/ext -> agent name

  var out = [];
  for (var i = 0; i < raw.length; i++) {
    var s = raw[i] || {};
    var ph = cc_pick_(s, ['phone10', 'caller_number_raw', 'caller_number', 'number']);
    ph = cc_last10_(ph);

    var startUnix = cc_int_(cc_pick_(s, ['start_time', 'synced_time', 'time']));
    var when = startUnix ? new Date(startUnix * 1000) : null;

    var dirRaw = String(cc_pick_(s, ['direction', 'type', 'call_type']) || '');
    var direction = (dirRaw.toLowerCase().indexOf('out') >= 0) ? 'outgoing' : 'incoming';

    var durSec = cc_int_(cc_pick_(s, ['duration_seconds', 'duration', 'seconds']));

    // status: enriched is_missed first, else status==2 means missed.
    var missed;
    if (typeof s.is_missed === 'boolean') {
      missed = s.is_missed;
    } else {
      missed = (String(cc_pick_(s, ['status', 'call_status'])) === '2');
    }
    var status = missed ? 'missed' : 'connected';

    var pinfo = pmap[ph] || null;
    var agent = cc_agentName_(s, amap);

    out.push({
      id:        ph + '_' + (startUnix || i),     // stable across polls
      time:      when ? Utilities.formatDate(when, CC_TZ, 'HH:mm') : '',
      startUnix: startUnix,
      direction: direction,
      number4:   cc_last4_(ph),
      name:      pinfo ? (pinfo.name || 'Unknown') : 'Unknown',
      clinicId:  pinfo ? (pinfo.clinicId || '') : '',
      diagnosis: pinfo ? (pinfo.diagnosis || '') : '',
      lastVisit: pinfo ? (pinfo.lastVisit || '') : '',
      agent:     agent,
      durationSec: durSec,
      duration:  cc_mmss_(durSec),
      status:    status,
      recording: String(cc_pick_(s, ['filename', 'recording_filename']) || '')
    });
  }

  // newest first
  out.sort(function (a, c) { return (c.startUnix || 0) - (a.startUnix || 0); });
  return out;
}

// ===========================================================================
// DEFENSIVE READERS (self-contained — no dependence on other files' shapes)
// ===========================================================================

function cc_openSheet_() {
  var id = (PropertiesService.getScriptProperties().getProperty(CC_SHEET_ID_PROP) || '').trim();
  if (id) {
    try { return SpreadsheetApp.openById(id); } catch (e) {}
  }
  var active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) return active;
  return SpreadsheetApp.openById(CC_SHEET_ID_FALLBACK);
}

function cc_sheetValues_(tabName) {
  var ss = cc_openSheet_();
  var sh = ss.getSheetByName(tabName);
  if (!sh) return [];
  var rng = sh.getDataRange();
  if (!rng) return [];
  return rng.getValues() || [];
}

/** Patient_Master -> { phone10: {name, clinicId, diagnosis} } */
function cc_patientMap_() {
  var map = {};
  try {
    var vals = cc_sheetValues_(CC_TAB_PATIENT);
    if (vals.length < 2) return map;
    var H = cc_lc_(vals[0]);
    var iPhone = cc_col_(H, ['mobile', 'phone number', 'mobile number', 'phone', 'number', 'phone10']);
    var iName  = cc_col_(H, ['patient name', 'name']);
    var iId    = cc_col_(H, ['clinic_specific_id', 'clinic specific id', 'clinic id', 'clinic_id', 'patient id']);  // numeric Clinic ID column IF present in Patient_Master; blank if absent (never the UID/name)
    var iDx    = cc_col_(H, ['diagnosis']);
    var iLast  = cc_col_(H, ['last visit', 'consultation date', 'last seen', 'seen']);
    if (iPhone < 0) return map;
    for (var r = 1; r < vals.length; r++) {
      var row = vals[r];
      var ph = cc_last10_(iPhone < row.length ? row[iPhone] : '');
      if (!ph) continue;
      if (map[ph]) continue;   // first wins
      map[ph] = {
        name:      (iName >= 0 && iName < row.length) ? String(row[iName]).trim() : '',
        clinicId:  (iId   >= 0 && iId   < row.length) ? String(row[iId]).trim()   : '',
        diagnosis: (iDx   >= 0 && iDx   < row.length) ? String(row[iDx]).trim()   : '',
        lastVisit: (iLast >= 0 && iLast < row.length) ? cc_dateStr_(row[iLast])    : ''
      };
    }
  } catch (e) {}
  return map;
}

/** Agents -> { userId: name, ext: name } so we can name a call by either key. */
function cc_agentMap_() {
  var map = {};
  try {
    var vals = cc_sheetValues_(CC_TAB_AGENTS);
    if (vals.length < 2) return map;
    var H = cc_lc_(vals[0]);
    var iExt  = cc_col_(H, ['ext', 'extension']);
    var iName = cc_col_(H, ['name', 'agent', 'agent name']);
    var iUid  = cc_col_(H, ['userid', 'user id', 'user_id']);
    for (var r = 1; r < vals.length; r++) {
      var row = vals[r];
      var name = (iName >= 0 && iName < row.length) ? String(row[iName]).trim() : '';
      if (!name) continue;
      if (iUid >= 0 && iUid < row.length) {
        var uid = String(row[iUid]).trim();
        if (uid) map['uid:' + uid] = name;
      }
      if (iExt >= 0 && iExt < row.length) {
        var ext = String(row[iExt]).trim();
        if (ext) map['ext:' + ext] = name;
      }
    }
  } catch (e) {}
  return map;
}

/** Best-effort agent name for one call record. */
function cc_agentName_(s, amap) {
  // 1) name embedded in the log record
  try {
    if (s.log_details && s.log_details.length) {
      var ld = s.log_details[0];
      if (ld && ld.received_by && ld.received_by.length && ld.received_by[0].name) {
        return String(ld.received_by[0].name).trim();
      }
    }
  } catch (e) {}
  // 2) map by user id
  var uid = String(cc_pick_(s, ['_hit_user_id', 'user_id', 'allcaller_id']) || '').trim();
  if (uid && amap['uid:' + uid]) return amap['uid:' + uid];
  // 3) nothing reliable
  return '';
}

function cc_ensureOutcomesTab_(ss) {
  var sh = ss.getSheetByName(CC_TAB_OUTCOMES);
  if (!sh) {
    sh = ss.insertSheet(CC_TAB_OUTCOMES);
    sh.appendRow(CC_OUTCOMES_HEADER);
    return sh;
  }
  // ensure a header exists on an empty tab
  if (sh.getLastRow() === 0) sh.appendRow(CC_OUTCOMES_HEADER);
  return sh;
}

// ===========================================================================
// SMALL UTILITIES
// ===========================================================================

/** Start/end Date for "today" in clinic time (Asia/Kolkata). */
function cc_todayBounds_() {
  var now = new Date();
  var ymd = Utilities.formatDate(now, CC_TZ, 'yyyy-MM-dd');
  // Build IST midnight + next IST midnight as real instants.
  var start = new Date(ymd + 'T00:00:00+05:30');
  var end   = new Date(start.getTime() + 24 * 3600 * 1000);
  return { start: start, end: end };
}

function cc_lc_(arr) {
  return (arr || []).map(function (x) { return String(x == null ? '' : x).trim().toLowerCase(); });
}

/** First header index whose cell equals or contains a candidate. */
function cc_col_(headerLc, candidates) {
  for (var i = 0; i < candidates.length; i++) {
    var c = candidates[i];
    var k = headerLc.indexOf(c);
    if (k >= 0) return k;
  }
  for (var j = 0; j < candidates.length; j++) {
    for (var h = 0; h < headerLc.length; h++) {
      if (headerLc[h].indexOf(candidates[j]) >= 0) return h;
    }
  }
  return -1;
}

/** First present, non-empty value from a record by candidate keys. */
function cc_pick_(obj, keys) {
  for (var i = 0; i < keys.length; i++) {
    var v = obj ? obj[keys[i]] : null;
    if (v !== undefined && v !== null && v !== '') return v;
  }
  return '';
}

/** Normalise a last-visit cell: a real Date -> yyyy-MM-dd; anything else -> trimmed text. */
function cc_dateStr_(v) {
  if (v instanceof Date && !isNaN(v.getTime())) return Utilities.formatDate(v, CC_TZ, 'yyyy-MM-dd');
  return String(v == null ? '' : v).trim();
}

function cc_last10_(v) {
  var d = String(v == null ? '' : v).replace(/\D/g, '');
  return d.length > 10 ? d.slice(-10) : d;
}

function cc_last4_(v) {
  var d = String(v == null ? '' : v).replace(/\D/g, '');
  return d ? d.slice(-4) : '';
}

function cc_int_(v) {
  var n = Number(v);
  return isNaN(n) ? 0 : Math.round(n);
}

function cc_dir_(v) {
  var s = String(v || '').toLowerCase();
  if (s.indexOf('out') >= 0) return 'outgoing';
  if (s.indexOf('in')  >= 0) return 'incoming';
  return s || '';
}

function cc_mmss_(sec) {
  sec = cc_int_(sec);
  var m = Math.floor(sec / 60);
  var s = sec % 60;
  return m + ':' + (s < 10 ? '0' + s : '' + s);
}
