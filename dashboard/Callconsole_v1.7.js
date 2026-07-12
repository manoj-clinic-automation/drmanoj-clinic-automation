/**
 * CallConsole.gs  —  Call Console Step 1 (server data layer)
 * ==========================================================
 * Updated Session 140 · 12 Jul 2026 — v1.7 (K-2 + Block-C merge): ONE outcome-
 *   tab read per bundle build via cc_outcomeScan_() (was two separate whole-
 *   tab reads for missTotals + kLogged); NEW newLeads in the bundle — unknown-
 *   caller inquiries kept alive 3 days, derived from the SAME scan; a lead
 *   dies on Patient_Master conversion, a terminal outcome, or expiry.
 *   cc_patientMap_ memoised per execution (leads check = zero extra reads).
 *   No writer changed; WebApp.gs untouched (D34).
 * Dr. Manoj Agarwal Clinic, Bareilly.  Session 21 · 30 Jun 2026.
 * Updated Session 27 · 01 Jul 2026 — v1.1: adds LAST-VISIT to the patient
 *   context (spec v1.1 §4.4/§6, decision C16). Only change vs the v1.0 file.
 * Updated Session 31 · 02 Jul 2026 — v1.2: adds getFollowupClinicIds (D52) —
 *   phone→Clinic ID enrichment for follow-up rows, cloning the S27 last-visit
 *   pattern. Purely additive; no existing function changed.
 * Updated Session 135 · 11 Jul 2026 — v1.3 (F-34/D208): shared-family-mobile fix.
 *   getFollowupClinicIds + getFollowupLastVisits are now NAME-AWARE: on a mobile
 *   shared by several registered patients, each follow-up row is matched to its
 *   own patient by name (token overlap ≥ 0.7, mirroring the PC resolver). No
 *   confident match -> the entry is blank and the page shows a verify marker,
 *   never another family member's ID. Unique mobiles keep the legacy plain key,
 *   so an already-open (stale) page degrades to blank — never to a wrong ID.
 * Updated Session 136 · 11 Jul 2026 — v1.5 (same day, deploy 3): F-4 dead code
 *   REMOVED (logOutcome + cc_ensureOutcomesTab_ + the Outcomes_Log constants —
 *   called by nothing, tab never created, appended PHI to a ledger nobody read);
 *   D183 ADDED: sweepUnloggedCalls() — 21:30 digest to the doctor of every call,
 *   both directions, that ended the day without an outcome. installSweepTrigger()
 *   / removeSweepTrigger() are run once by the OWNER from the editor (D206).
 * Updated Session 136 · 11 Jul 2026 — v1.4 (Block C): quota + one-clock layer.
 *   ADDS ONLY — no existing function changed. getDashboardBundle(key, opts)
 *   returns everything the page shows in ONE server trip, behind a shared
 *   45-second CacheService entry (six devices -> one set of sheet reads).
 *   getCallDurationFast() reads only the LAST 200 rows of Call_Durations
 *   (the old whole-tab poll re-read everything every 6s). cc_todayIST_()
 *   is the ONE CLOCK: the server's IST date rides in every bundle; the page
 *   computes no dates (closes F-5 + F-13). cc_qcBump_() counts full builds
 *   per day into Script Property QC_BUNDLE_BUILDS for Health.gs (§4-Q3).
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
 *   logOutcome                    — REMOVED v1.5 (F-4): dead ledger, public
 *                                   writer, called by nothing since Step 2
 *                                   shipped a different save path.
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
var CC_TAB_DURATIONS = 'Call_Durations';   // D77: PHI-clean call-facts feed (VPS receiver writes it)
var CC_GATE_MIN_TALK = 15;                 // D77: seconds of PATIENT talk-time to unlock an outcome


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
  Logger.log('logOutcome removed v1.5 (F-4); no outcome ledger exists in this file.');
}


/**
 * getFollowupLastVisits(key) -> { ok, map:{ mobile(last10): lastVisitDate } }
 * Last-visit dates for the patients on TODAY's follow-up worklist, so the page can
 * show last-visit on follow-up rows WITHOUT editing WebApp.gs (Slice 2, additive).
 * Scoped to today's follow-up mobiles only -> small payload, not the whole patient DB.
 */
function getFollowupLastVisits(key) {
  // S135 (F-34/D208): delegates to the name-aware enricher; see cc_fuEnrich_.
  return cc_fuEnrich_(key, 'lastVisit');
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
  // S135 (F-34/D208): delegates to the name-aware enricher; see cc_fuEnrich_.
  return cc_fuEnrich_(key, 'clinicId');
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

// ===========================================================================
// DURATION GATE (D77) — after a follow-up call, the dashboard asks whether THAT
// exact call really connected long enough to allow an outcome to be logged.
// Reads the PHI-clean Call_Durations tab (written in real time by the VPS
// call-webhook receiver), matching on the call's client_ref_id. Read-only;
// WebApp.gs untouched (D34).
// ===========================================================================
/**
 * getCallDuration(key, clientRefId)
 *   -> { ok:true, found:false }                                   (no row yet)
 *   -> { ok:true, found:true, status, customerResult, talk, allowOutcome }
 *   -> { ok:false, error }
 * allowOutcome is TRUE only when the call bridged AND the patient leg was
 * answered AND the patient talk-time is >= CC_GATE_MIN_TALK seconds.
 * Fail-safe: any ambiguity or missing field -> allowOutcome:false.
 */
function getCallDuration(key, clientRefId) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ref = String(clientRefId || '').trim();
    if (!ref) return { ok: true, found: false };
    var vals = cc_sheetValues_(CC_TAB_DURATIONS);
    if (!vals || vals.length < 2) return { ok: true, found: false };
    var H = cc_lc_(vals[0]);
    var iRef  = cc_col_(H, ['client_ref_id', 'client ref id', 'clientrefid']);
    var iStat = cc_col_(H, ['status']);
    var iRes  = cc_col_(H, ['customer_result', 'customer result']);
    var iTalk = cc_col_(H, ['customer_talk_duration', 'customer talk duration', 'talk_duration']);
    if (iRef < 0) return { ok: true, found: false };
    var hit = null;
    for (var r = vals.length - 1; r >= 1; r--) {           // newest matching row wins
      if (String(vals[r][iRef] || '').trim() === ref) { hit = vals[r]; break; }
    }
    if (!hit) return { ok: true, found: false };
    var status = (iStat >= 0) ? String(hit[iStat] || '').trim().toLowerCase() : '';
    var cres   = (iRes  >= 0) ? String(hit[iRes]  || '').trim().toLowerCase() : '';
    var talk   = (iTalk >= 0) ? cc_int_(hit[iTalk]) : 0;
    var allow  = (status === 'bridged') && (cres === 'answered') && (talk >= CC_GATE_MIN_TALK);
    return { ok: true, found: true, status: status, customerResult: cres, talk: talk, allowOutcome: allow };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}


/**
 * getFollowupFreshness(key) -> { ok, stale, today, newestDue, rows }
 * Session 57: the DASHBOARD-side stale-list guard. Uses the SAME truth as the live
 * email sentinel (Diagnostics.gs::checkFollowupListFresh): the list is FRESH when the
 * newest Due Date on Followups_Today is >= today (yyyy-MM-dd strings sort chronologically).
 * Read-only. WebApp.gs untouched (D34). No patient data returned — dates + a count only.
 */
function cc_freshParseDate_(v) {
  // mirrors sentParseDate_: "03-Jul-2026", a Date, or an ISO string -> epoch ms (0 if unparseable)
  if (v instanceof Date) return v.getTime();
  var s = String(v == null ? '' : v).trim();
  if (!s) return 0;
  var MON = { jan:0, feb:1, mar:2, apr:3, may:4, jun:5, jul:6, aug:7, sep:8, oct:9, nov:10, dec:11 };
  var m = s.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);   // 03-Jul-2026
  if (m) {
    var mon = MON[m[2].toLowerCase()];
    if (mon != null) return new Date(parseInt(m[3], 10), mon, parseInt(m[1], 10)).getTime();
  }
  var d = new Date(s);
  return isNaN(d.getTime()) ? 0 : d.getTime();
}
function getFollowupFreshness(key) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var tz = Session.getScriptTimeZone();
    var todayStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
    var ss = cc_openSheet_();
    var sh = ss ? ss.getSheetByName('Followups_Today') : null;
    if (!sh) return { ok: true, stale: false, today: todayStr, newestDue: '', rows: 0, note: 'no-tab' };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, stale: false, today: todayStr, newestDue: '', rows: 0, note: 'empty' };
    var H = cc_lc_(vals[0]);
    var iDue = cc_col_(H, ['due date', 'due', 'follow up date', 'followup date', 'next follow up']);
    if (iDue < 0) return { ok: true, stale: false, today: todayStr, newestDue: '', rows: (vals.length - 1), note: 'no-due-col' };
    var newestEpoch = 0;
    for (var r = 1; r < vals.length; r++) {
      var t = cc_freshParseDate_(iDue < vals[r].length ? vals[r][iDue] : '');
      if (t && t > newestEpoch) newestEpoch = t;
    }
    var newestStr = newestEpoch ? Utilities.formatDate(new Date(newestEpoch), tz, 'yyyy-MM-dd') : '';
    var fresh = !!newestStr && (newestStr >= todayStr);   // same rule as the email sentinel
    return { ok: true, stale: !fresh, today: todayStr, newestDue: newestStr, rows: (vals.length - 1) };
  } catch (err) {
    // a broken guard must never block the dashboard -> report not-stale, carry the error
    return { ok: false, stale: false, error: String(err && err.message ? err.message : err) };
  }
}


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
/* ---------------------------------------------------------------------------
 * S135 (F-34/D208) \u2014 name-aware follow-up enrichment for shared family mobiles
 * ---------------------------------------------------------------------------
 * Root cause fixed here: cc_patientMap_() keeps ONE patient per mobile
 * ("first wins"), so on a shared family mobile every follow-up row inherited
 * the FIRST registered family member's Clinic ID and last-visit date
 * (incident 11-Jul-2026: Raj Rani shown with Ekta's ID). This block matches
 * each follow-up row to its OWN patient by name. Map keys:
 *   phone10                -> value   (only when the mobile has ONE patient)
 *   phone10 + '|' + name   -> value   (shared mobile, name matched; '' = no
 *                                      confident match -> page shows a verify
 *                                      marker instead of a wrong ID)
 * cc_patientMap_() itself is untouched \u2014 the incoming-call tiles still use it,
 * where caller-ID alone is all we can ever have.
 * ------------------------------------------------------------------------- */
function cc_normName_(s) {
  return String(s || '').toLowerCase()
    .replace(/[^a-z0-9\u0900-\u097F ]+/g, ' ')
    .replace(/\s+/g, ' ').trim();
}
function cc_nameScore_(a, b) {   // token overlap / max tokens (mirrors the PC resolver)
  var ta = String(a || '').split(' ').filter(String);
  var tb = String(b || '').split(' ').filter(String);
  if (!ta.length || !tb.length) return 0;
  var setB = {}; for (var i = 0; i < tb.length; i++) setB[tb[i]] = true;
  var ov = 0; for (var j = 0; j < ta.length; j++) { if (setB[ta[j]]) ov++; }
  return ov / Math.max(ta.length, tb.length);
}
function cc_patientMultiMap_() {   // phone10 -> ARRAY of every patient on that mobile
  var map = {};
  try {
    var vals = cc_sheetValues_(CC_TAB_PATIENT);
    if (vals.length < 2) return map;
    var H = cc_lc_(vals[0]);
    var iPhone = cc_col_(H, ['mobile', 'phone number', 'mobile number', 'phone', 'number', 'phone10']);
    var iName  = cc_col_(H, ['patient name', 'name']);
    var iId    = cc_col_(H, ['clinic_specific_id', 'clinic specific id', 'clinic id', 'clinic_id', 'patient id']);
    var iLast  = cc_col_(H, ['last visit', 'consultation date', 'last seen', 'seen']);
    if (iPhone < 0) return map;
    for (var r = 1; r < vals.length; r++) {
      var row = vals[r];
      var ph = cc_last10_(iPhone < row.length ? row[iPhone] : '');
      if (!ph) continue;
      if (!map[ph]) map[ph] = [];
      map[ph].push({
        name:      (iName >= 0 && iName < row.length) ? String(row[iName]).trim() : '',
        clinicId:  (iId   >= 0 && iId   < row.length) ? String(row[iId]).trim()   : '',
        lastVisit: (iLast >= 0 && iLast < row.length) ? cc_dateStr_(row[iLast])    : ''
      });
    }
  } catch (e) {}
  return map;
}
function cc_fuEnrich_(key, field) {   // shared engine for ClinicIds + LastVisits
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ss = cc_openSheet_();
    var sh = ss.getSheetByName('Followups_Today');   // read-only here
    if (!sh) return { ok: true, map: {} };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, map: {} };
    var H = cc_lc_(vals[0]);
    var iMob  = cc_col_(H, ['mobile', 'phone number', 'mobile number', 'phone', 'number']);
    var iName = cc_col_(H, ['patient name', 'name']);
    if (iMob < 0) return { ok: true, map: {} };
    var mmap = cc_patientMultiMap_();
    var out = {};
    for (var r = 1; r < vals.length; r++) {
      var row = vals[r];
      var ph = cc_last10_(iMob < row.length ? row[iMob] : '');
      if (!ph) continue;
      var cands = mmap[ph] || [];
      if (cands.length === 1) {                       // unique mobile: legacy plain key
        if (out[ph] === undefined) out[ph] = (cands[0][field] || '');
        continue;
      }
      var rowName = cc_normName_(iName >= 0 && iName < row.length ? row[iName] : '');
      var k = ph + '|' + rowName;
      if (out[k] !== undefined) continue;
      if (!cands.length || !rowName) { out[k] = ''; continue; }
      var best = null, bestScore = 0;
      for (var c = 0; c < cands.length; c++) {
        var s = cc_nameScore_(rowName, cc_normName_(cands[c].name));
        if (s > bestScore) { bestScore = s; best = cands[c]; }
      }
      out[k] = (best && bestScore >= 0.7) ? (best[field] || '') : '';
    }
    return { ok: true, map: out };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

var CC_PMAP_MEMO = null;   // S140: one execution = one Patient_Master read
function cc_patientMap_() {
  if (CC_PMAP_MEMO) return CC_PMAP_MEMO;
  return (CC_PMAP_MEMO = cc_patientMapBuild_());
}
function cc_patientMapBuild_() {
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
// ===========================================================================
// BLOCK C (Session 136) — one clock + quota load (F-5/F-13 + F-6/F-12)
// ===========================================================================
// Everything below is ADDITIVE. The old per-function endpoints still exist and
// still answer, so an already-open (stale) page keeps working until reloaded.

var CC_BUNDLE_TTL_S = 45;      // shared cache lifetime, seconds (< the 60s page refresh)
var CC_DUR_WINDOW   = 200;     // bounded poll: last N data rows of Call_Durations
var CC_QC_PROP      = 'QC_BUNDLE_BUILDS';   // daily build counter for Health.gs

/** THE one clock: today's date in IST, as the server sees it. */
function cc_todayIST_() {
  return Utilities.formatDate(new Date(), CC_TZ, 'yyyy-MM-dd');
}

/**
 * getDashboardBundle(key, opts) -> ONE trip carrying everything the page
 * shows each minute: dash stats, follow-ups + all three enrichment maps,
 * send-backs, today's calls, freshness — plus escalations + outcome log on
 * the doctor's key. opts = { force:bool, olDay:'today'|'yyyy-MM-dd' }.
 *
 * QUOTA MODEL: the assembled payload is cached per ROLE for CC_BUNDLE_TTL_S
 * seconds, so six open devices share ONE set of sheet reads instead of six.
 * force=true (Refresh button / post-save) bypasses AND REFILLS the cache, so
 * a just-saved outcome is what every other device sees next.
 * The staff cache and the full cache are separate keys — a staff login can
 * never be served the doctor's escalations or outcome log.
 * Fail-safe: any cache error falls through to a plain build; a build error
 * returns { ok:false, error } and the page shows "Reconnecting…".
 */
function getDashboardBundle(key, opts) {
  try {
    var role = dashRole_(key);
    if (role === 'none') return { ok: false, error: 'Not authorized. Please sign in again.' };
    opts = opts || {};
    var force = !!opts.force;
    var olDay = String(opts.olDay || 'today');
    var cacheable = (olDay === 'today');           // reviewing an OLD day is never cached
    var cKey = 'CC_BUNDLE_' + role + '_' + olDay;
    var cache = null;
    try { cache = CacheService.getScriptCache(); } catch (e0) { cache = null; }
    if (cache && cacheable && !force) {
      try {
        var hit = cache.get(cKey);
        if (hit) {
          var got = JSON.parse(hit);
          got.cached = true;
          got.todayIST = cc_todayIST_();           // the clock is NEVER served stale
          return got;
        }
      } catch (e1) { /* fall through to a fresh build */ }
    }
    var out = {
      ok: true,
      cached: false,
      todayIST: cc_todayIST_(),
      role: role,
      dash:       getDashboardData(key, force),
      followups:  getFollowups(key),
      lastVisits: getFollowupLastVisits(key),
      recordings: getFollowupRecordings(key),
      clinicIds:  getFollowupClinicIds(key),
      sendbacks:  getReviewSendbacks(key),
      allCalls:   getAllCallsToday(key, force),
      freshness:  getFollowupFreshness(key),
      missTotals: null,                             // filled from the ONE scan below (S140)
      kLogged:    null,
      newLeads:   null
    };
    var scan = cc_outcomeScan_();                   // S140: one read serves all three
    out.missTotals = scan.missTotals;
    out.kLogged    = scan.kLogged;
    out.newLeads   = scan.leads;
    if (role === 'full') out.kStrikes = cc_kStrikesToday_();   // doctor 3rd-strike band (read-only)
    if (role === 'full') {
      out.escalations = getEscalations(key);
      out.outcomeLog  = getOutcomeLog(key, olDay);
    }
    if (cache && cacheable) {
      try { cache.put(cKey, JSON.stringify(out), CC_BUNDLE_TTL_S); }
      catch (e2) { /* payload over the 100KB cache limit -> simply not cached */ }
    }
    cc_qcBump_();
    return out;
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/**
 * Daily counter of FULL bundle builds (each build = ~11 whole/bounded tab
 * reads). Read by Health.gs §4b. Rolls itself over at the IST midnight;
 * yesterday's total survives one day in prevDate/prevBuilds so the 08:00
 * report can print it. A counter failure must never break the board.
 */
function cc_qcBump_() {
  try {
    var sp = PropertiesService.getScriptProperties();
    var today = cc_todayIST_();
    var cur = {};
    try { cur = JSON.parse(sp.getProperty(CC_QC_PROP) || '{}') || {}; } catch (e) { cur = {}; }
    if (cur.date !== today) {
      cur = { date: today, builds: 0, prevDate: cur.date || '', prevBuilds: cur.builds || 0 };
    }
    cur.builds = (cur.builds || 0) + 1;
    sp.setProperty(CC_QC_PROP, JSON.stringify(cur));
  } catch (e3) { /* never block the board over a counter */ }
}

/**
 * getCallDurationFast(key, clientRefId) — the bounded twin of
 * getCallDuration(). Same contract, same gate, same fail-safe — but it reads
 * only the LAST CC_DUR_WINDOW data rows of Call_Durations instead of the
 * whole tab. Safe because the VPS receiver APPENDS: today's call is always
 * within the last rows. Not found in the window -> { found:false }, exactly
 * what the old function returns while the row hasn't landed yet; the page's
 * own 3-minute timeout (unchanged) still bounds the wait.
 */
function getCallDurationFast(key, clientRefId) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, error: 'Not authorized.' };
    var ref = String(clientRefId || '').trim();
    if (!ref) return { ok: true, found: false };
    var ss = cc_openSheet_();
    var sh = ss ? ss.getSheetByName(CC_TAB_DURATIONS) : null;
    if (!sh) return { ok: true, found: false };
    var lastRow = sh.getLastRow(), lastCol = sh.getLastColumn();
    if (lastRow < 2 || lastCol < 1) return { ok: true, found: false };
    var H = cc_lc_(sh.getRange(1, 1, 1, lastCol).getValues()[0]);
    var iRef  = cc_col_(H, ['client_ref_id', 'client ref id', 'clientrefid']);
    var iStat = cc_col_(H, ['status']);
    var iRes  = cc_col_(H, ['customer_result', 'customer result']);
    var iTalk = cc_col_(H, ['customer_talk_duration', 'customer talk duration', 'talk_duration']);
    if (iRef < 0) return { ok: true, found: false };
    var n = Math.min(CC_DUR_WINDOW, lastRow - 1);
    var vals = sh.getRange(lastRow - n + 1, 1, n, lastCol).getValues();
    var hit = null;
    for (var r = vals.length - 1; r >= 0; r--) {           // newest matching row wins
      if (String(vals[r][iRef] || '').trim() === ref) { hit = vals[r]; break; }
    }
    if (!hit) return { ok: true, found: false };
    var status = (iStat >= 0) ? String(hit[iStat] || '').trim().toLowerCase() : '';
    var cres   = (iRes  >= 0) ? String(hit[iRes]  || '').trim().toLowerCase() : '';
    var talk   = (iTalk >= 0) ? cc_int_(hit[iTalk]) : 0;
    var allow  = (status === 'bridged') && (cres === 'answered') && (talk >= CC_GATE_MIN_TALK);
    return { ok: true, found: true, status: status, customerResult: cres, talk: talk, allowOutcome: allow };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}
// ===========================================================================
// D183 (Session 136, deploy 3) — NOTHING ENDS THE DAY UNLOGGED
// ===========================================================================
// At 21:30 IST the doctor receives ONE digest: every call today, BOTH
// directions, whose number has no outcome row filed today. Read-only — it
// writes nothing, moves no tile, and a failure sends nothing rather than
// something wrong. Names on shared family mobiles are NOT guessed (D208):
// the digest says '(shared family mobile)' instead of naming a relative.
// The trigger is installed ONCE, BY THE OWNER, from the editor (D206):
// run installSweepTrigger() — or removeSweepTrigger() to disarm.

function sweepUnloggedCalls() {
  try {
    var today = cc_todayIST_();

    // -- 1. today's calls, both directions (same source as the dashboard) ---
    var raw = [];
    try {
      var b = dayBounds_(0);
      raw = fetchCallsBetween_(b.start, b.end) || [];
    } catch (e0) { raw = []; }

    // -- 2. numbers with an outcome filed TODAY (Followup_Outcomes) ---------
    var logged = {};
    try {
      var ss = cc_openSheet_();
      var sh = ss ? ss.getSheetByName('Followup_Outcomes') : null;
      if (sh && sh.getLastRow() > 1) {
        var vals = sh.getDataRange().getValues();
        var H = cc_lc_(vals[0]);
        var iWhen = cc_col_(H, ['when']);
        var iMob  = cc_col_(H, ['mobile']);
        for (var r = 1; r < vals.length; r++) {
          if (cc_sweepDay_(iWhen >= 0 ? vals[r][iWhen] : '') !== today) continue;
          var mo = cc_last10_(iMob >= 0 ? vals[r][iMob] : '');
          if (mo) logged[mo] = 1;
        }
      }
    } catch (e1) { /* unreadable outcomes -> everything unlogged is still true */ }

    // -- 3. group unlogged calls by number ----------------------------------
    var multi = {};
    try { multi = cc_patientMultiMap_() || {}; } catch (e2) { multi = {}; }
    var pmap = {};
    try { pmap = cc_patientMap_() || {}; } catch (e3) { pmap = {}; }

    var byNum = {}, order = [], totalCalls = 0;
    for (var i = 0; i < raw.length; i++) {
      var s = raw[i] || {};
      var ph = cc_last10_(cc_pick_(s, ['phone10', 'caller_number_raw', 'caller_number', 'number']));
      if (!ph || logged[ph]) continue;
      var startUnix = cc_int_(cc_pick_(s, ['start_time', 'synced_time', 'time']));
      var dirRaw = String(cc_pick_(s, ['direction', 'type', 'call_type']) || '');
      var dir = (dirRaw.toLowerCase().indexOf('out') >= 0) ? 'OUT' : 'IN ';
      var missed = (typeof s.is_missed === 'boolean') ? s.is_missed
                 : (String(cc_pick_(s, ['status', 'call_status'])) === '2');
      if (!byNum[ph]) {
        var famList = multi[ph];
        var nm = (famList && famList.length > 1) ? '(shared family mobile)'
               : ((pmap[ph] && pmap[ph].name) ? pmap[ph].name : 'not in patient list');
        byNum[ph] = { name: nm, items: [] };
        order.push(ph);
      }
      byNum[ph].items.push(dir + ' ' +
        (startUnix ? Utilities.formatDate(new Date(startUnix * 1000), CC_TZ, 'HH:mm') : '--:--') +
        (missed ? ' missed' : ' connected'));
      totalCalls++;
    }

    // -- 4. compose + send ---------------------------------------------------
    var subject, body;
    if (!order.length) {
      subject = '\u2705 Every call logged today \u2014 ' + today;
      body = 'Unlogged-call sweep (D183), 21:30 IST.\n\n' +
             'Every number that called or was called today has an outcome row.\n' +
             (raw.length ? ('Calls seen today: ' + raw.length + '.\n')
                         : 'No calls found for today (also worth a look if the clinic was open).\n');
    } else {
      subject = '\ud83d\udccb ' + order.length + ' number(s), ' + totalCalls +
                ' call(s) ended today UNLOGGED \u2014 ' + today;
      var lines = [];
      var cap = Math.min(order.length, 60);
      for (var k = 0; k < cap; k++) {
        var ph2 = order[k], e = byNum[ph2];
        lines.push('\u2026' + ph2.slice(-4) + '  ' + e.name + '\n      ' + e.items.join(' \u00b7 '));
      }
      if (order.length > cap) lines.push('\u2026 and ' + (order.length - cap) + ' more numbers.');
      body = 'Unlogged-call sweep (D183), 21:30 IST \u2014 both directions.\n' +
             'A number is UNLOGGED when no outcome row was filed for it today.\n\n' +
             lines.join('\n') + '\n\n' +
             'Log them from the dashboard (Today\u2019s calls \u2192 Log outcome), or let\n' +
             'them ride \u2014 this mail is a mirror, it moves nothing.\n';
    }
    if (typeof healthAlert_ === 'function') healthAlert_(order.length > 0, subject, body);
    return { ok: true, numbers: order.length, calls: totalCalls };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/** yyyy-MM-dd of an outcome 'When' cell (Date, ISO string, or blank). */
function cc_sweepDay_(v) {
  if (v instanceof Date) return Utilities.formatDate(v, CC_TZ, 'yyyy-MM-dd');
  var s = String(v == null ? '' : v).trim();
  var m = s.match(/^(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : '';
}

/** OWNER runs this ONCE from the editor (D206). Idempotent. */
function installSweepTrigger() {
  removeSweepTrigger();
  ScriptApp.newTrigger('sweepUnloggedCalls').timeBased()
    .atHour(21).nearMinute(30).everyDays(1).create();
  Logger.log('sweepUnloggedCalls armed daily ~21:30 IST.');
}
function removeSweepTrigger() {
  var ts = ScriptApp.getProjectTriggers();
  for (var i = 0; i < ts.length; i++) {
    if (ts[i].getHandlerFunction() === 'sweepUnloggedCalls') ScriptApp.deleteTrigger(ts[i]);
  }
  Logger.log('sweepUnloggedCalls trigger(s) removed.');
}


/* ===========================================================================
 * K-1 ONE-TAP STAFF UI - server side (Session 139; Console Spec v2.2 SK.6)
 * ---------------------------------------------------------------------------
 * ADDS ONLY. WebApp.gs is never touched (D34). The cross-day miss counter
 * lives HERE, in the bundle, so the frozen per-day logic in WebApp stays
 * byte-identical (which the SK.6.6 parallel run requires anyway).
 *
 * Codes written (outcome column), always with source='K' (the ui=K marker):
 *   K_COMING     -> 'k_coming'      settle='settle'
 *   K_NOT_COMING -> 'k_not_coming'  settle='settle'
 *   K_CALL_AGAIN -> 'k_call_again'  settle='retry'
 *   K_NO_CONTACT -> 'no_answer'     settle='retry'   (keeps ALL existing
 *                    snooze / per-day machinery + verdict joins working;
 *                    K identity preserved by source='K')
 *   K_TO_DOCTOR  -> delegated to saveFollowupOutcome('problem') so the
 *                    Escalations tab keeps its existing writer, no new one.
 *
 * 3rd strike (D215/D216): fires ONLY when this save transitions the
 * cross-day count to EXACTLY 3 - never on historical >=3 - so a deploy can
 * never mass-fire. Template drmanoj_followup_due via the EXISTING VPS relay
 * (WA_SEND_URL + '/template', X-Send-Key). Relay missing/erroring NEVER
 * blocks the save (fail-open, SJ.4).
 * ======================================================================== */

var K_CODE_MAP = {
  K_COMING:     { code: 'k_coming',      settle: 'settle' },
  K_NOT_COMING: { code: 'k_not_coming',  settle: 'settle' },
  K_CALL_AGAIN: { code: 'k_call_again',  settle: 'retry'  },
  K_NO_CONTACT: { code: 'no_answer',     settle: 'retry'  }
};
var K_STRIKE_N     = 3;                    // cumulative cross-day misses -> WABA
var K_STRIKES_TAB  = 'K_Strikes';
var K_STRIKES_HEADERS = ['When','Key','Name','Mobile','Tries','Template','Message Id','By'];

/** Cross-day miss counter: key -> {n, lastT}. A miss = outcome 'no_answer'
 *  (old flow and K button 4 alike). ANY other outcome row for that key
 *  resets the count (D215: contact of any kind zeroes it). */
function cc_missTotals_() {
  var out = {};
  try {
    var ss = fuSheet_(); if (!ss) return out;
    var rows = fuReadObjects_(ss, FU_TAB_OUTCOMES);
    // chronological scan; rows are appended in time order, trust sheet order
    rows.forEach(function (o) {
      var k = String(o['key'] || '').trim(); if (!k) return;
      var code = String(o['outcome'] || '').trim().toLowerCase().replace(/[^a-z]+/g, '_');
      var t = 0; try { t = dateVal_(o['when']) || 0; } catch (e) { t = 0; }
      if (code === FU_NOANSWER_CODE) {
        var m = out[k] || (out[k] = { n: 0, lastT: 0 });
        m.n++; if (t > m.lastT) m.lastT = t;
      } else {
        out[k] = { n: 0, lastT: 0 };            // any contact resets
      }
    });
  } catch (err) { /* counter is advisory; never break the bundle */ }
  return out;
}

/** Per-agent completion numerator: handler -> outcomes logged TODAY (any code). */
function cc_kLoggedToday_() {
  var out = {};
  try {
    var ss = fuSheet_(); if (!ss) return out;
    var tz = Session.getScriptTimeZone();
    var today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
    fuReadObjects_(ss, FU_TAB_OUTCOMES).forEach(function (o) {
      var t = dateVal_(o['when']); if (!t) return;
      if (Utilities.formatDate(new Date(t), tz, 'yyyy-MM-dd') !== today) return;
      var h = String(o['handled by'] || o['handledby'] || '').trim(); if (!h) return;
      out[h] = (out[h] || 0) + 1;
    });
  } catch (err) { /* advisory */ }
  return out;
}

/* ---------------------------------------------------------------------------
 * S140 (K-2 / Block-C merge): ONE scan of Followup_Outcomes computes all
 * three read-side products the bundle needs — missTotals (K-1 counter,
 * byte-identical rule), kLogged (completion numerator, same rule) and
 * newLeads (unknown-caller inquiries, 3-day keep-alive). Replaces the two
 * separate whole-tab reads of v1.6. A lead LIVES while: its latest
 * incoming-section outcome is one of LEAD_ALIVE, is <= LEAD_TTL_DAYS old,
 * and the number is NOT yet in Patient_Master (registration = automatic
 * death — the conversion signal). Escalated leads live in the doctor's
 * escalation queue instead — never on two boards at once.
 * ------------------------------------------------------------------------ */
var LEAD_TTL_DAYS = 3;
var LEAD_ALIVE = { in_appointment_booked: 1, in_will_come: 1,
                   in_needs_callback: 1, in_enquiry_only: 1,
                   in_info_given_will_act: 1 };

function cc_outcomeScan_() {
  var out = { missTotals: {}, kLogged: {}, leads: [] };
  try {
    var ss = fuSheet_(); if (!ss) return out;
    var tz = Session.getScriptTimeZone();
    var today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
    var latestIn = {};                     // phone10 -> latest incoming-section row
    fuReadObjects_(ss, FU_TAB_OUTCOMES).forEach(function (o) {
      var code = String(o['outcome'] || '').trim().toLowerCase().replace(/[^a-z]+/g, '_');
      var t = 0; try { t = dateVal_(o['when']) || 0; } catch (e) { t = 0; }

      // (1) K-1 cross-day miss counter — byte-identical rule to v1.6
      var k = String(o['key'] || '').trim();
      if (k) {
        if (code === FU_NOANSWER_CODE) {
          var m = out.missTotals[k] || (out.missTotals[k] = { n: 0, lastT: 0 });
          m.n++; if (t > m.lastT) m.lastT = t;
        } else {
          out.missTotals[k] = { n: 0, lastT: 0 };     // any contact resets
        }
      }

      // (2) per-agent completion numerator (today only) — same rule as v1.6
      if (t && Utilities.formatDate(new Date(t), tz, 'yyyy-MM-dd') === today) {
        var h = String(o['handled by'] || o['handledby'] || '').trim();
        if (h) out.kLogged[h] = (out.kLogged[h] || 0) + 1;
      }

      // (3) latest incoming-section row per number (feeds the leads band)
      if (String(o['section'] || '').trim().toLowerCase() === 'incoming') {
        var ph = String(o['mobile'] || '').replace(/\D/g, '').slice(-10);
        if (ph.length === 10) {
          var cur = latestIn[ph];
          if (!cur || t >= cur.t) {
            latestIn[ph] = { t: t, code: code,
              identity: String(o['identity'] || '').trim().toLowerCase(),
              name: String(o['patient'] || '').trim(),
              detail: String(o['detail'] || '').trim() };
          }
        }
      }
    });

    // assemble the live leads: alive code, young enough, not yet a patient
    var pmap = cc_patientMap_();           // memoised — zero extra reads
    var now = Date.now(), ttl = LEAD_TTL_DAYS * 24 * 3600 * 1000;
    Object.keys(latestIn).forEach(function (ph) {
      var L = latestIn[ph];
      if (!LEAD_ALIVE[L.code]) return;                       // terminal / escalated
      if (L.identity === 'non_patient' || L.identity === 'existing_new_number') return;
      if (!L.t || (now - L.t) > ttl) return;                 // expired (3 days)
      if (pmap[ph]) return;                                  // converted — now a patient
      out.leads.push({ number: ph, name: L.name, code: L.code,
        when: Utilities.formatDate(new Date(L.t), CC_TZ, 'dd MMM HH:mm'),
        daysAgo: Math.floor((now - L.t) / 86400000),
        detail: L.detail, t: L.t });
    });
    out.leads.sort(function (a, b) { return (b.t || 0) - (a.t || 0); });
    if (out.leads.length > 30) out.leads = out.leads.slice(0, 30);
  } catch (err) { /* advisory — never break the bundle */ }
  return out;
}

/** Today's 3rd-strike rows for the doctor's read-only band. */
function cc_kStrikesToday_() {
  var out = [];
  try {
    var ss = fuSheet_(); if (!ss) return out;
    var sh = ss.getSheetByName(K_STRIKES_TAB); if (!sh) return out;
    var tz = Session.getScriptTimeZone();
    var today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
    var vals = sh.getDataRange().getValues();
    for (var i = 1; i < vals.length; i++) {
      var when = String(vals[i][0] || '');
      if (when.slice(0, 10) !== today) continue;
      out.push({ when: when.slice(11, 16), name: String(vals[i][2] || ''),
                 tries: vals[i][4], sent: !!String(vals[i][6] || '') });
    }
  } catch (err) { /* advisory */ }
  return out;
}

/** Fire drmanoj_followup_due through the EXISTING System-B relay. Never throws. */
function cc_fireStrikeWaba_(mobile, name, dueDate) {
  var res = { sent: false, message_id: '', reason: '' };
  try {
    var secret = waSendSecret_();
    if (!secret) { res.reason = 'no relay secret'; return res; }
    var resp = UrlFetchApp.fetch(WA_SEND_URL + '/template', {
      method: 'post', contentType: 'application/json',
      headers: { 'X-Send-Key': secret },
      payload: JSON.stringify({ number: String(mobile || ''),
        template: 'drmanoj_followup_due',
        vars: { '1': String(name || 'ji'), '2': String(dueDate || '') } }),
      muteHttpExceptions: true
    });
    var body = {}; try { body = JSON.parse(resp.getContentText()); } catch (e) {}
    res.sent = !!(body && body.sent);
    res.message_id = (body && body.message_id) || '';
    res.reason = (body && body.reason) || ('HTTP ' + resp.getResponseCode());
  } catch (err) { res.reason = String(err && err.message ? err.message : err); }
  return res;
}

/**
 * saveKOutcome(key, p) - one tap files one outcome row (SK.6.3).
 * p = { rowKey, kcode(K_COMING|K_NOT_COMING|K_CALL_AGAIN|K_NO_CONTACT|K_TO_DOCTOR),
 *       name, mobile, section, diagnosis, clinicId, lastVisit, due, note }
 */
function saveKOutcome(key, p) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, reason: 'Not authorized.' };
    p = p || {};
    var kc = String(p.kcode || '').trim();

    // Button 5: reuse the proven escalation writer - no new Escalations writer.
    if (kc === 'K_TO_DOCTOR') {
      var r5 = saveFollowupOutcome(key, {
        rowKey: p.rowKey, name: p.name, mobile: p.mobile, section: p.section,
        diagnosis: p.diagnosis, clinicId: p.clinicId, lastVisit: p.lastVisit,
        outcome: 'problem', source: 'K',
        detail: ('[K] \u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u094b \u0926\u093f\u0916\u093e\u0928\u093e \u0939\u0948' +
                 (p.note ? (' \u2014 ' + String(p.note)) : ''))
      });
      if (r5 && r5.ok) r5.kcode = kc;
      return r5;
    }

    var m = K_CODE_MAP[kc];
    if (!m) return { ok: false, reason: 'Unknown K code.' };
    var ss = fuSheet_(); if (!ss) return { ok: false, reason: 'Sheet not configured.' };
    var info = agentInfoForKey_(key);
    var handler = (info && info.name) ? info.name : (dashRole_(key) === 'full' ? 'Doctor' : 'Staff');
    var ext = (info && info.ext) ? info.ext : '';
    var tz = Session.getScriptTimeZone();
    var whenStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd HH:mm');
    var mobile = String(p.mobile || '').replace(/\D/g, '').slice(-10);

    var shO = fuEnsureTab_(ss, FU_TAB_OUTCOMES, FU_OUTCOME_HEADERS);
    shO.appendRow([ whenStr, String(p.rowKey || '').trim(), String(p.name || '').trim(),
      mobile, String(p.section || '').trim(), m.code,
      'K',                                   // source = ui marker (SK.6.3)
      '', '', String(p.note || '').trim(), handler, ext, m.settle ]);

    var out = { ok: true, kcode: kc, outcome: m.code, settle: m.settle };

    // 3rd strike - only on the transition to EXACTLY K_STRIKE_N
    if (m.code === FU_NOANSWER_CODE) {
      var tot = cc_missTotals_()[String(p.rowKey || '').trim()];
      var n = tot ? tot.n : 0;
      out.missCount = n;
      if (n === K_STRIKE_N) {
        var due = String(p.due || '').trim() ||
                  Utilities.formatDate(new Date(), tz, 'dd MMM yyyy');
        var fire = cc_fireStrikeWaba_(mobile, p.name, due);
        try {
          var shS = fuEnsureTab_(ss, K_STRIKES_TAB, K_STRIKES_HEADERS);
          shS.appendRow([ whenStr, String(p.rowKey || '').trim(),
            String(p.name || '').trim(), mobile, n,
            'drmanoj_followup_due', fire.message_id || '', handler ]);
        } catch (eS) { /* strike record is best-effort */ }
        out.strike = { fired: fire.sent, reason: fire.reason };
      }
    }
    return out;
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}
