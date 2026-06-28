/**
 * WebApp.gs — live "needs a callback now" dashboard (HTML web app)
 *             with patient-CSV context + WhatsApp activity alongside.
 * ---------------------------------------------------------------------------
 * One URL, served from THIS project. Always-live callback state, refreshes
 * itself, and for every number it now shows:
 *   - PATIENT CONTEXT  — matched from a "Patient_Master" sheet tab (your CSV).
 *   - WHATSAPP ACTIVITY — recent inbound/outbound messages for that number,
 *                          read from a "WA_Inbox" sheet tab.
 *
 * DATA SOURCES (all optional; the page degrades gracefully if a tab is absent):
 *   1. MyOperator Call/Logs API  — live, via fetchCallsBetween_ (already built).
 *   2. Callbacks_Today tab        — staff "Done/Booked/Called" status.
 *   3. Patient_Master tab         — your patient CSV (see PATIENT MATCH below).
 *   4. WA_Inbox tab               — WhatsApp messages (see WHATSAPP below).
 *
 * PATIENT MATCH: import your patient CSV into a tab named "Patient_Master"
 *   (same spreadsheet, or a separate one — set Script Property PATIENT_SHEET_ID
 *   to that spreadsheet's ID to keep patient data separate). The code finds the
 *   columns by header name, so the exact CSV layout does not matter as long as
 *   there is a phone column and (ideally) name / diagnosis / age / gender / last-visit.
 *
 * WHATSAPP: MyOperator's WhatsApp API has NO "fetch past messages" endpoint —
 *   inbound messages arrive via Webhooks v2 (push). A webhook receiver (the VPS,
 *   per the project plan) must APPEND each message to a "WA_Inbox" tab with the
 *   columns documented at the bottom of this file. This dashboard only READS that
 *   tab. Until the receiver is wired, the WhatsApp panels simply stay empty.
 *
 * DEPLOY / PRIVACY: see the handoff. "Only myself" is safest; if you use
 *   "Anyone with the link", also set Script Property DASH_KEY and open with ?k=KEY.
 */

var DASH_CACHE_KEY = 'dash_live_v2';
var DASH_CACHE_TTL = 90;          // seconds — throttles the API even if the page polls faster
var PATIENT_TAB    = 'Patient_Master';
var WA_TAB         = 'WA_Inbox';
var WA_LOOKBACK_HOURS = 48;       // consider WhatsApp activity from the last N hours
var WA_RECENT_MAX     = 12;       // size of the "Recent WhatsApp" panel
var WA_SNIPPET_MAX    = 90;       // characters of message text to keep

// --- WhatsApp free-text reply (component 2): the dashboard asks the VPS relay
//     to send; the relay runs the proven 24h-window-guarded sender. The WhatsApp
//     token never reaches Apps Script - only the relay gate secret does. ---
var WA_SEND_URL = 'https://followup.dr-manoj.in/wa-send';   // relay base (NOT a secret)
var CALL_URL    = 'https://followup.dr-manoj.in/call';      // OBD click-to-call relay (NOT a secret)

/** Optional one-time helpers: set the access keys from the editor. */
function setDashboardKey(k) {
  PropertiesService.getScriptProperties().setProperty('DASH_KEY', String(k || ''));
  Logger.log('DASH_KEY (full access) set.');
}
function setStaffKey(k) {
  PropertiesService.getScriptProperties().setProperty('STAFF_KEY', String(k || ''));
  Logger.log('STAFF_KEY (read-only) set.');
}

/**
 * ACCESS MODEL (server-enforced, not cosmetic):
 *   DASH_KEY  -> 'full'  : doctor; sees everything, including the WhatsApp Reply box.
 *   STAFF_KEY -> 'staff' : reception; read-only, NO Reply box, cannot send.
 *   anything else -> 'none' : the dashboard HTML is NEVER served; only the login page.
 * The send functions (checkWindow/sendReply) re-check the FULL key server-side, so a
 * staff key can never send even if a request is forged.
 */
// --- Per-agent identity (server-enforced + roster-driven) -------------------
//   * Each agent logs in with their OWN key (Script Property AKEY_<ext>; the
//     doctor's DASH_KEY = ext 10). The key -> ext mapping is the bind.
//   * The "Agents" tab of the tracker sheet is the roster: Ext | Name | UserId
//     | Active. It drives the display name, the user_id we dial as, and an
//     Active flag (set Active = no to instantly off-board someone).
//   * The agent is ALWAYS derived here from the key, NEVER from the page.
//   * Degrade-safe: if the Agents tab can't be read, fall back to the built-in
//     7 below and DO NOT lock anyone out.
// ---------------------------------------------------------------------------
var AGENTS_TAB = 'Agents';
var AGENT_NAME_BY_EXT = {
  '10': 'Dr Manoj Agarwal', '11': 'Shavez Ahmed', '12': 'Shivani Srivastava',
  '13': 'Manoj Bhati', '14': 'Alisha Khan', '15': 'Darpan Robert', '16': 'Reception Mobile'
};
var AGENT_USERID_BY_EXT = {
  '10': '6838435041f29988', '11': '686cf49a692bb162', '12': '686cf557c4f09495',
  '13': '686cf5a29a97d527', '14': '69cfa941359e1649', '15': '6a2017dd50280597',
  '16': '6a2018cda8975829'
};

/** Read the Agents roster tab -> { ext: {name, userId, active(bool)} }, or null
 *  if it can't be read (caller then uses the built-in fallback, never locking out). */
function rosterByExt_() {
  try {
    var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
    if (!id) return null;
    var sh = SpreadsheetApp.openById(id).getSheetByName(AGENTS_TAB);
    if (!sh) return null;
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return null;
    var head = vals[0].map(function (h) { return String(h || '').trim().toLowerCase(); });
    var iExt = head.indexOf('ext'), iName = head.indexOf('name'),
        iUid = head.indexOf('userid'), iAct = head.indexOf('active');
    if (iExt < 0) return null;
    var out = {};
    for (var r = 1; r < vals.length; r++) {
      var ext = String(vals[r][iExt] || '').replace(/\D/g, '');
      if (!ext) continue;
      var act = (iAct >= 0) ? String(vals[r][iAct] || '').trim().toLowerCase() : 'yes';
      out[ext] = {
        name:   iName >= 0 ? String(vals[r][iName] || '').trim() : '',
        userId: iUid  >= 0 ? String(vals[r][iUid]  || '').trim() : '',
        active: !(act === 'no' || act === 'n' || act === 'false' || act === '0')
      };
    }
    return out;
  } catch (err) { return null; }   // degrade-safe
}

/** Return the agent extension bound to this login key, or '' if none.
 *  Candidate extensions = the built-in 7 plus any rows added in the roster,
 *  so a brand-new agent works from a sheet row + AKEY_<ext> with no code edit. */
function agentExtForKey_(key, roster) {
  var sp = PropertiesService.getScriptProperties();
  key = String(key || '').trim();
  if (!key) return '';
  var full = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
  if (full && key === full) return '10';        // the doctor's key = Dr Manoj
  var cand = { '10':1, '11':1, '12':1, '13':1, '14':1, '15':1, '16':1 };
  if (roster) { for (var k in roster) { if (roster.hasOwnProperty(k)) cand[k] = 1; } }
  for (var e in cand) {
    if (!cand.hasOwnProperty(e)) continue;
    var v = (sp.getProperty('AKEY_' + e) || '').trim();
    if (v && key === v) return e;
  }
  return '';
}

/** Full identity for a login key: { ext, name, userId, active, isMaster } or null. */
function agentInfoForKey_(key) {
  var sp = PropertiesService.getScriptProperties();
  var full = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
  var isMaster = !!(full && String(key || '').trim() === full);
  var roster = rosterByExt_();
  var ext = agentExtForKey_(key, roster);
  if (!ext) return null;
  var row = (roster && roster[ext]) ? roster[ext] : null;
  var name   = (row && row.name)   ? row.name   : (AGENT_NAME_BY_EXT[ext]   || '');
  var userId = (row && row.userId) ? row.userId : (AGENT_USERID_BY_EXT[ext] || '');
  // Active: the master key is never gated; if a roster row exists honour its flag;
  // if there is no row (or the roster is unreadable) default active, never lock out.
  var active = isMaster ? true : (row ? row.active : true);
  return { ext: ext, name: name, userId: userId, active: active, isMaster: isMaster };
}

function dashRole_(key) {
  var sp = PropertiesService.getScriptProperties();
  var full  = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();   // SECRET_KEY = your existing full key
  var staff = (sp.getProperty('STAFF_KEY') || '').trim();
  key = String(key || '').trim();
  if (full  && key === full)  return 'full';            // master key, never roster-gated
  var info = agentInfoForKey_(key);
  if (info) return info.active ? 'staff' : 'none';      // Active=no off-boards entirely
  if (staff && key === staff) return 'staff';           // legacy shared key -> view only
  return 'none';
}

/** TEMP diagnostic. Run from the editor, then open View -> Execution log. Prints NO secret. */
function keyInfo() {
  var sp = PropertiesService.getScriptProperties();
  ['DASH_KEY', 'SECRET_KEY', 'STAFF_KEY'].forEach(function (name) {
    var raw = sp.getProperty(name);
    if (raw == null) { Logger.log(name + ': NOT SET'); return; }
    Logger.log(name + ': length=' + raw.length
      + ', leadingSpace=' + (raw !== raw.replace(/^\s+/, ''))
      + ', trailingSpace=' + (raw !== raw.replace(/\s+$/, '')));
  });
}

/** The page calls this to learn its own access level (so it can hide the Reply box). */
function getAccess(key) {
  var info = agentInfoForKey_(key);
  return {
    role: dashRole_(key),
    agentExt:  info ? info.ext : '',
    agentName: (info && info.active) ? info.name : ''
  };
}

/** Serve the dashboard page (access is enforced inside the page + on every data call). */
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Dashboard')
    .setTitle('Clinic Callbacks \u2014 Live')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/**
 * Called by the page via google.script.run. Returns a plain object
 * (strings / numbers / arrays only). force=true (Refresh button) bypasses cache.
 */
function getDashboardData(key, force) {
  if (dashRole_(key) === 'none') return { error: 'Not authorized. Please sign in again.' };
  var cache = CacheService.getScriptCache();
  if (!force) {
    var hit = cache.get(DASH_CACHE_KEY);
    if (hit) return JSON.parse(hit);
  }
  var data;
  try { data = computeDashboard_(); }
  catch (err) {
    return { error: String(err && err.message ? err.message : err),
             updated: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'h:mm:ss a') };
  }
  cache.put(DASH_CACHE_KEY, JSON.stringify(data), DASH_CACHE_TTL);
  return data;
}

/** Build the live dashboard snapshot for today. */
function computeDashboard_() {
  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var net = computeNetMissed_(raw);
  var s = computeMonitorStats_(raw);
  var staff = staffStatusMap_();           // phone10 -> staff status text
  var pat = patientLookup_();              // phone10 -> patient context
  var wa = waLookup_();                    // { byNum: phone10 -> latest msg, recent: [...] }

  var rate = s.incoming ? Math.round((s.incomingMissed / s.incoming) * 100) : 0;

  function decoratePatient(item) {
    var p = pat[item.number];
    if (p) item.patient = { name: p.name, dx: p.dx, age: p.age, sex: p.sex,
                            last: p.last, uid: p.uid, more: p.more || 0 };
  }
  function decorate(item) {
    decoratePatient(item);
    var w = wa.byNum[item.number];
    if (w) item.wa = { text: w.text, time: w.time, dir: w.dir, count: w.count };
  }

  var outMap = outboundAttempts_(raw);            // num -> [Date,...] of outgoing calls
  var pending = [], handled = [];
  net.entries.forEach(function (en) {
    var st = staff[en.number] || '';
    var item = {
      number: en.number, attempts: en.attempts, times: attemptTimesStr_(en),
      lastCall: fmtClock_(en.lastTs), priority: !!en.priority,
      afterHours: !!en.afterHours, staffStatus: st
    };
    // A real callback is an OUTGOING call AFTER the patient's first missed call.
    var firstMissTs = en.firstTs ? en.firstTs.getTime() : 0;
    var cbs = (outMap[en.number] || []).filter(function (t) { return t && t.getTime() >= firstMissTs; });
    if (cbs.length) {
      cbs.sort(function (a, b) { return a.getTime() - b.getTime(); });   // chronological
      item.triedOut = { count: cbs.length, times: cbs.map(fmtClock_).join(', ') };
    }
    if (isDoneStatus_(st)) handled.push(item); else pending.push(item);
  });
  pending.sort(function (a, c) {
    if (a.priority !== c.priority) return a.priority ? -1 : 1;
    return c.attempts - a.attempts;
  });
  pending.forEach(decorate);
  handled.forEach(decorate);

  // NEW: resolved callbacks — missed callers who later connected, with detail.
  var resolved = resolvedCallbacks_(raw);
  resolved.forEach(decoratePatient);

  var recentWA = wa.recent.map(function (m) {
    var p = pat[m.ph];
    return { number: m.ph, name: p ? p.name : '', time: m.time, dir: m.dir, text: m.text, full: m.full };
  });

  var callsByAgent = agentCallsMap_(raw, pat);
  var agents = agentRows_(s).map(function (a) {
    return { name: a.name, answered: a.answered, talkMin: a.talkMin, callbacks: a.outMade,
             calls: callsByAgent[a.name] || [] };
  });
  // include anyone with connected calls who wasn't already in the summary rows
  Object.keys(callsByAgent).forEach(function (n) {
    if (!agents.some(function (a) { return a.name === n; })) {
      agents.push({ name: n, answered: 0, talkMin: 0, callbacks: 0, calls: callsByAgent[n] });
    }
  });

  var tz = Session.getScriptTimeZone();
  return {
    updated: Utilities.formatDate(new Date(), tz, 'h:mm:ss a'),
    dateLabel: Utilities.formatDate(b.start, tz, 'EEE d MMM yyyy'),
    build: 'v17.1 \u00b7 inbound',
    kpis: {
      awaiting: pending.length, missed: s.incomingMissed, missedRate: rate,
      total: s.total, incoming: s.incoming, resolved: net.stats.resolved,
      longestWait: (s.longestWaitSec >= 0 ? secsToMS_(s.longestWaitSec) : '—'),
      waCount: recentWA.length
    },
    pending: pending, resolved: resolved, handled: handled,
    recentWA: recentWA, agents: agents
  };
}

/* ---------------------------------------------------------------------------
 * Lookups (all read-only; each is wrapped so a missing tab never breaks the page)
 * ------------------------------------------------------------------------- */

/**
 * outboundAttempts_(raw) -> { phone10: {count, lastTs, connected} }
 * Counts the DESK's outgoing calls to each number today, so a pending row can show
 * "desk already called back" instead of looking like an untouched missed call.
 */
function outboundAttempts_(raw) {
  var m = {};
  raw.forEach(function (r) {
    var isOut = (String(r.direction) === 'outgoing') || (String(r.event) === '2');
    if (!isOut) return;
    var num = r.phone10 || last10_(r.caller_number_raw || r.caller_number || '');
    if (!num) return;
    var startSec = Number(r.start_time) || 0;
    if (!startSec) return;
    (m[num] || (m[num] = [])).push(new Date(startSec * 1000));   // every outgoing call time
  });
  return m;
}

/**
 * agentCallsMap_(raw, pat) -> { agentName: [ {number,time,dur,dir,patient,recFile,_t}, ... ] }
 * For the Clinic Team dropdowns: every CONNECTED call today (incoming answered OR
 * outgoing connected) grouped by the staff member on it, newest first. Only connected
 * calls are included because only they have a recording. Patient name is matched from
 * the Patient_Master lookup passed in. Reuses existing helpers (callAgentInfo_, last10_,
 * fmtClock_, secsToMS_); no engine files are modified.
 */
function agentCallsMap_(raw, pat) {
  var m = {};
  raw.forEach(function (r) {
    var missed = (r.is_missed === true) || String(r.status) === '2';
    if (missed) return;                                  // only connected calls have audio
    var info = callAgentInfo_(r);
    var name = (info && info.agent) ? String(info.agent).trim() : '';
    if (!name) return;                                   // skip system / unassigned legs
    var isOut = (String(r.direction) === 'outgoing') || (String(r.event) === '2');
    var num = r.phone10 || last10_(r.caller_number_raw || r.caller_number || '');
    var startSec = Number(r.start_time) || 0;
    var ts = startSec ? new Date(startSec * 1000) : null;
    var p = pat[num];
    (m[name] || (m[name] = [])).push({
      number: num,
      time: fmtClock_(ts),
      dur: secsToMS_(info.talkSec || 0),
      dir: isOut ? 'out' : 'in',
      patient: p ? p.name : '',
      recFile: r.filename ? String(r.filename) : '',
      _t: ts ? ts.getTime() : 0
    });
  });
  Object.keys(m).forEach(function (n) {
    m[n].sort(function (a, b) { return b._t - a._t; });  // newest first
  });
  return m;
}

/** Map phone10 -> Staff Status from Callbacks_Today. */
function staffStatusMap_() {
  var map = {};
  try {
    var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
    if (!id) return map;
    var sh = SpreadsheetApp.openById(id).getSheetByName(CFG.TAB_CALLBACKS);
    if (!sh) return map;
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return map;
    var iPhone = vals[0].indexOf('Phone'), iStaff = vals[0].indexOf('Staff Status');
    if (iPhone < 0 || iStaff < 0) return map;
    for (var r = 1; r < vals.length; r++) {
      var ph = last10_(vals[r][iPhone]);
      if (ph) map[ph] = String(vals[r][iStaff] || '').trim();
    }
  } catch (err) { /* optional */ }
  return map;
}

/** A caller is "handled" if staff wrote a done-ish word (but not "callback"). */
function isDoneStatus_(s) {
  s = String(s || '').toLowerCase();
  if (!s) return false;
  if (s.indexOf('callback') >= 0) return false;
  var done = ['done', 'booked', 'resolved', 'complete', 'reached', 'called', 'spoke', 'connected'];
  for (var i = 0; i < done.length; i++) if (s.indexOf(done[i]) >= 0) return true;
  return false;
}

/** Header-tolerant column finder: returns index of first matching header (lowercased). */
function findCol_(headerLower, candidates) {
  for (var i = 0; i < candidates.length; i++) {
    var k = headerLower.indexOf(candidates[i]);
    if (k >= 0) return k;
  }
  return -1;
}
function dateVal_(v) {
  if (v instanceof Date) return v.getTime();
  var d = new Date(v);
  return isNaN(d.getTime()) ? 0 : d.getTime();
}
function fmtDateCell_(v) {
  var t = dateVal_(v);
  return t ? Utilities.formatDate(new Date(t), Session.getScriptTimeZone(), 'd MMM yyyy')
           : String(v == null ? '' : v).trim();
}

/**
 * NEW — resolvedCallbacks_(raw)
 * A "resolved callback" is a number that had at least one MISSED incoming call
 * today AND also had a CONNECTED call (either direction) — i.e. the patient got
 * through, or the desk called back and connected. We surface the resolving call's
 * agent, time, and talk duration, plus how many missed attempts preceded it.
 *
 * Reuses globals defined elsewhere in the project:
 *   last10_, hhmmssToSeconds_ (MyOperator.gs); callAgentInfo_, secsToMS_,
 *   fmtClock_ (Monitor.gs). The core engine files are NOT modified.
 */
function resolvedCallbacks_(raw) {
  var groups = {};                                  // phone10 -> [raw records]
  raw.forEach(function (r) {
    var num = r.phone10 || last10_(r.caller_number_raw || r.caller_number || '');
    if (!num) return;
    (groups[num] || (groups[num] = [])).push(r);
  });

  var out = [];
  Object.keys(groups).forEach(function (num) {
    var missedTimes = [];                            // Date[] of missed incoming legs
    var connects = [];                               // {ts, agent, talkSec, how}
    groups[num].forEach(function (r) {
      var isOut  = (String(r.direction) === 'outgoing') || (String(r.event) === '2');
      var missed = (r.is_missed === true) || String(r.status) === '2';
      var startSec = Number(r.start_time) || 0;
      var ts = startSec ? new Date(startSec * 1000) : null;
      if (!isOut && missed) {
        missedTimes.push(ts);
      } else if (!missed) {
        var info = callAgentInfo_(r);
        connects.push({ ts: ts, agent: info.agent, talkSec: info.talkSec,
                        how: isOut ? 'Called back' : 'Got through',
                        file: (r.filename ? String(r.filename) : '') });
      }
    });
    if (!missedTimes.length || !connects.length) return;   // not a resolved callback

    missedTimes.sort(function (a, b) { return (a ? a.getTime() : 0) - (b ? b.getTime() : 0); });
    connects.sort(function (a, b) { return (a.ts ? a.ts.getTime() : 0) - (b.ts ? b.ts.getTime() : 0); });

    var firstMissT = missedTimes[0] ? missedTimes[0].getTime() : 0;
    var resolver = null;
    for (var i = 0; i < connects.length; i++) {
      if (connects[i].ts && connects[i].ts.getTime() >= firstMissT) { resolver = connects[i]; break; }
    }
    if (!resolver) resolver = connects[connects.length - 1];

    var recFile = resolver.file || '';
    if (!recFile) {
      for (var ci = 0; ci < connects.length; ci++) { if (connects[ci].file) { recFile = connects[ci].file; break; } }
    }
    out.push({
      number: num,
      attempts: missedTimes.length,
      agent: resolver.agent || '',
      time: fmtClock_(resolver.ts),
      durationSec: resolver.talkSec || 0,
      duration: secsToMS_(resolver.talkSec || 0),
      how: resolver.how,
      recFile: recFile,
      _sortT: resolver.ts ? resolver.ts.getTime() : 0
    });
  });

  out.sort(function (a, b) { return b._sortT - a._sortT; });   // most recently resolved first
  return out;
}

/**
 * getRecordingAudio(filename) — called from the page when "▶ Recording" is tapped.
 * Server-side only: fetches a fresh 24h link from /recordings/link using the Calling
 * token (kept in Script Properties), then downloads the audio and returns it as a
 * base64 data-URI. The MyOperator link and the token NEVER reach the browser.
 * Returns { dataUri } on success or { error } on failure.
 */
function getRecordingAudio(key, filename) {
  try {
    if (dashRole_(key) === 'none') return { error: 'Not authorized.' };
    filename = String(filename || '').trim();
    if (!filename) return { error: 'No recording for this call.' };
    var token = PropertiesService.getScriptProperties().getProperty(CFG.TOKEN_PROP);
    if (!token) return { error: 'Recording token not set.' };

    var linkUrl = 'https://developers.myoperator.co/recordings/link?token=' +
                  encodeURIComponent(token) + '&file=' + encodeURIComponent(filename);
    var r1 = UrlFetchApp.fetch(linkUrl, { method: 'get', muteHttpExceptions: true });
    if (r1.getResponseCode() !== 200) return { error: 'Link HTTP ' + r1.getResponseCode() };

    var link = '';
    var body = r1.getContentText();
    try { link = findFirstUrl_(JSON.parse(body)); }
    catch (e) { var t = body.trim(); if (t.indexOf('http') === 0) link = t; }
    if (!link) return { error: 'No download link returned.' };

    var r2 = UrlFetchApp.fetch(link, { method: 'get', muteHttpExceptions: true });
    if (r2.getResponseCode() !== 200) return { error: 'Audio HTTP ' + r2.getResponseCode() };

    var bytes = r2.getBlob().getBytes();
    if (!bytes || !bytes.length) return { error: 'Empty audio.' };
    // These are .mp3 files (grabber confirmed mpeg frames) — force audio/mpeg so the
    // browser's <audio> plays them regardless of the server's content-type label.
    return { dataUri: 'data:audio/mpeg;base64,' + Utilities.base64Encode(bytes) };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

/** Return the first http(s) string found anywhere in a parsed JSON value. */
function findFirstUrl_(o) {
  if (typeof o === 'string') return o.indexOf('http') === 0 ? o : '';
  if (o && typeof o === 'object') {
    for (var k in o) { if (o.hasOwnProperty(k)) { var u = findFirstUrl_(o[k]); if (u) return u; } }
  }
  return '';
}

/* ---------------------------------------------------------------------------
 * WHATSAPP REPLY — free-text send via the VPS relay (component 2)
 * ---------------------------------------------------------------------------
 * checkWindow(number)        -> is the 24h window open for this number? (no send)
 * sendReply(number, message) -> send a free-text reply (guarded server-side)
 * Both authenticate to the relay with the gate secret in Script Property
 * SEND_API_SECRET (set once in Project Settings -> Script Properties). The
 * WhatsApp token lives only on the VPS and never reaches this project.
 * ------------------------------------------------------------------------- */
function waSendSecret_() {
  return PropertiesService.getScriptProperties().getProperty('SEND_API_SECRET') || '';
}

/** Window status for a number (no send). Called when a Reply box opens. */
function checkWindow(key, number) {
  try {
    if (dashRole_(key) !== 'full') return { ok: false, reason: 'Not authorized.' };
    var num = String(number || '').replace(/\D/g, '');
    if (num.length < 10) return { ok: false, reason: 'Bad number.' };
    var secret = waSendSecret_();
    if (!secret) return { ok: false, reason: 'Reply not configured (SEND_API_SECRET missing).' };
    var url = WA_SEND_URL + '/check?number=' + encodeURIComponent(num);
    var resp = UrlFetchApp.fetch(url, {
      method: 'get',
      headers: { 'X-Send-Key': secret },
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code === 403) return { ok: false, reason: 'Relay rejected the key (403).' };
    var out = {};
    try { out = JSON.parse(resp.getContentText()); } catch (e) { out = {}; }
    if (code !== 200 || !out) return { ok: false, reason: 'Relay HTTP ' + code };
    return out;   // { ok, number, window_open, last_inbound, hours_since }
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/** Send a free-text WhatsApp reply via the relay (24h window enforced server-side). */
function sendReply(key, number, message) {
  try {
    if (dashRole_(key) !== 'full') return { ok: false, sent: false, reason: 'Not authorized.' };
    var num = String(number || '').replace(/\D/g, '');
    var msg = String(message == null ? '' : message).trim();
    if (num.length < 10) return { ok: false, sent: false, reason: 'Bad number.' };
    if (!msg)            return { ok: false, sent: false, reason: 'Empty message.' };
    if (msg.length > 4000) return { ok: false, sent: false, reason: 'Message too long (max 4000).' };
    var secret = waSendSecret_();
    if (!secret) return { ok: false, sent: false, reason: 'Reply not configured (SEND_API_SECRET missing).' };

    var resp = UrlFetchApp.fetch(WA_SEND_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: { 'X-Send-Key': secret },
      payload: JSON.stringify({ number: num, message: msg }),
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code === 403) return { ok: false, sent: false, reason: 'Relay rejected the key (403).' };
    var out = {};
    try { out = JSON.parse(resp.getContentText()); } catch (e) { out = {}; }
    if (!out || typeof out !== 'object') return { ok: false, sent: false, reason: 'Relay HTTP ' + code };
    return out;   // { sent, ok, window_open, message_id, http_status, reason, ... }
  } catch (err) {
    return { ok: false, sent: false, reason: String(err && err.message ? err.message : err) };
  }
}

/* ---------------------------------------------------------------------------
 * CLICK-TO-CALL — place a real MyOperator OBD call via the VPS /call relay.
 * ---------------------------------------------------------------------------
 * triggerCall(key, agent, number, rowId)
 *   Rings the chosen agent's OWN mobile first; when they answer, MyOperator
 *   dials the patient and bridges them. MyOperator logs it AS THAT AGENT
 *   (we send the agent's panel user_id, resolved on the VPS from name/ext).
 * The OBD secrets live ONLY on the VPS; this project holds only the gate
 * secret CALL_API_SECRET (Project Settings -> Script Properties).
 * Both reception (staff) and the doctor (full) may place callbacks.
 * ------------------------------------------------------------------------- */
function callApiSecret_() {
  return PropertiesService.getScriptProperties().getProperty('CALL_API_SECRET') || '';
}

function triggerCall(key, number, rowId) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, accepted: false, reason: 'Not authorized.' };
    var info = agentInfoForKey_(key);   // agent is bound to the login, never sent by the page
    if (!info) return { ok: false, accepted: false, reason: 'Your login is not linked to an agent. Ask the doctor to set your key.' };
    if (!info.active) return { ok: false, accepted: false, reason: 'This agent is set inactive. Ask the doctor.' };
    var num = String(number || '').replace(/\D/g, '');
    if (num.length < 10) return { ok: false, accepted: false, reason: 'Bad number.' };
    var secret = callApiSecret_();
    if (!secret) return { ok: false, accepted: false, reason: 'Calling not configured (CALL_API_SECRET missing).' };

    var resp = UrlFetchApp.fetch(CALL_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: { 'X-Call-Key': secret },
      payload: JSON.stringify({ agent: info.ext, user_id: info.userId, patient_number: num, reference_id: String(rowId || num) }),
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code === 403) return { ok: false, accepted: false, reason: 'Relay rejected the key (403).' };
    var out = {};
    try { out = JSON.parse(resp.getContentText()); } catch (e) { out = {}; }
    if (!out || typeof out !== 'object') return { ok: false, accepted: false, reason: 'Relay HTTP ' + code };
    return out;   // { ok, accepted, agent, agent_ext, reference_id, unique_id, reason, http_status }
  } catch (err) {
    return { ok: false, accepted: false, reason: String(err && err.message ? err.message : err) };
  }
}

/**
 * getThread(key, number) -> { ok, number, messages:[{time,dir,type,text,status}] }
 * Every WhatsApp message (incoming + outgoing) for one number, OLDEST first, for
 * the conversation/thread view. Read-only; any valid key (full or staff) may read.
 * Outgoing rows are written by the VPS relay (wa_send_api.py v2) as direction="out".
 */
function getThread(key, number) {
  if (dashRole_(key) === 'none') return { ok: false, reason: 'Not authorized.' };
  var want = last10_(number);
  if (!want) return { ok: false, reason: 'Bad number.' };
  try {
    var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
    if (!id) return { ok: true, number: want, messages: [] };
    var sh = SpreadsheetApp.openById(id).getSheetByName(WA_TAB);
    if (!sh) return { ok: true, number: want, messages: [] };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, number: want, messages: [] };
    var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });
    var iTime  = findCol_(H, ['timestamp', 'time', 'received_at', 'date']);
    var iPhone = findCol_(H, ['phone', 'number', 'customer_number', 'from', 'mobile']);
    var iDir   = findCol_(H, ['direction', 'dir']);
    var iText  = findCol_(H, ['message', 'text', 'body', 'snippet']);
    var iType  = findCol_(H, ['type', 'message_type']);
    var iStat  = findCol_(H, ['status']);
    if (iPhone < 0) return { ok: true, number: want, messages: [] };
    var tz = Session.getScriptTimeZone(), rows = [];
    for (var r = 1; r < vals.length; r++) {
      if (last10_(vals[r][iPhone]) !== want) continue;
      var t = iTime >= 0 ? dateVal_(vals[r][iTime]) : 0;
      var type = iType >= 0 ? String(vals[r][iType] || '').trim() : '';
      var text = iText >= 0 ? String(vals[r][iText] || '').trim() : '';
      if (!text) text = '[' + (type || 'message') + ']';
      rows.push({
        _t: t,
        time: t ? Utilities.formatDate(new Date(t), tz, 'd MMM h:mm a') : '',
        dir: iDir >= 0 ? (String(vals[r][iDir] || '').toLowerCase().indexOf('out') >= 0 ? 'out' : 'in') : 'in',
        type: type, text: text,
        status: iStat >= 0 ? String(vals[r][iStat] || '').trim() : ''
      });
    }
    rows.sort(function (a, b) { return a._t - b._t; });   // oldest first (chat order)
    return { ok: true, number: want, messages: rows.map(function (m) {
      return { time: m.time, dir: m.dir, type: m.type, text: m.text, status: m.status };
    }) };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/** Map phone10 -> patient context from the Patient_Master tab (your CSV). */
function patientLookup_() {
  var map = {};
  try {
    var id = PropertiesService.getScriptProperties().getProperty('PATIENT_SHEET_ID')
          || PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
    if (!id) return map;
    var sh = SpreadsheetApp.openById(id).getSheetByName(PATIENT_TAB);
    if (!sh) return map;
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return map;
    var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });

    var iPhone = findCol_(H, ['phone number', 'mobile number', 'mobile no', 'mobile', 'phone', 'number', 'phone10']);
    var iName  = findCol_(H, ['patient name', 'name', 'first name']);
    var iDx    = findCol_(H, ['diagnosis', 'dx', 'purpose of visit', 'purpose']);
    var iAge   = findCol_(H, ['age']);
    var iSex   = findCol_(H, ['gender', 'sex']);
    var iLast  = findCol_(H, ['last visit', 'consultation date', 'last seen', 'seen']);
    var iUid   = findCol_(H, ['patient uid', 'uid', 'clinic specific id', 'clinic id']);
    if (iPhone < 0) return map;

    for (var r = 1; r < vals.length; r++) {
      var ph = last10_(vals[r][iPhone]);
      if (!ph) continue;
      var rec = {
        name: iName >= 0 ? String(vals[r][iName] || '').trim() : '',
        dx:   iDx   >= 0 ? String(vals[r][iDx]   || '').trim() : '',
        age:  iAge  >= 0 ? String(vals[r][iAge]  || '').trim() : '',
        sex:  iSex  >= 0 ? String(vals[r][iSex]  || '').trim() : '',
        last: iLast >= 0 ? fmtDateCell_(vals[r][iLast])        : '',
        uid:  iUid  >= 0 ? String(vals[r][iUid]  || '').trim() : '',
        _sort: iLast >= 0 ? dateVal_(vals[r][iLast]) : 0,
        more: 0
      };
      if (!map[ph]) { map[ph] = rec; }
      else {
        var more = (map[ph].more || 0) + 1;            // multiple patients share this number
        if (rec._sort > (map[ph]._sort || 0)) { rec.more = more; map[ph] = rec; } // keep most recent
        else { map[ph].more = more; }
      }
    }
  } catch (err) { /* optional */ }
  return map;
}

/** WhatsApp activity from the WA_Inbox tab: latest per number + a recent feed. */
function waLookup_() {
  var res = { byNum: {}, recent: [] };
  try {
    var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
    if (!id) return res;
    var sh = SpreadsheetApp.openById(id).getSheetByName(WA_TAB);
    if (!sh) return res;
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return res;
    var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });

    var iTime  = findCol_(H, ['timestamp', 'time', 'received_at', 'date']);
    var iPhone = findCol_(H, ['phone', 'number', 'customer_number', 'from', 'mobile']);
    var iDir   = findCol_(H, ['direction', 'dir']);
    var iText  = findCol_(H, ['message', 'text', 'body', 'snippet']);
    var iType  = findCol_(H, ['type', 'message_type']);
    if (iPhone < 0) return res;

    var cutoff = Date.now() - WA_LOOKBACK_HOURS * 3600 * 1000;
    var tz = Session.getScriptTimeZone();
    var rows = [];
    for (var r = 1; r < vals.length; r++) {
      var ph = last10_(vals[r][iPhone]);
      if (!ph) continue;
      var t = iTime >= 0 ? dateVal_(vals[r][iTime]) : 0;
      if (t && t < cutoff) continue;
      var type = iType >= 0 ? String(vals[r][iType] || '').trim() : '';
      var full = iText >= 0 ? String(vals[r][iText] || '').trim() : '';
      if (!full) full = '[' + (type || 'message') + ']';
      var text = full;
      if (text.length > WA_SNIPPET_MAX) text = text.slice(0, WA_SNIPPET_MAX - 1) + '…';
      rows.push({
        ph: ph, t: t,
        time: t ? Utilities.formatDate(new Date(t), tz, 'd MMM h:mm a') : '',
        dir: iDir >= 0 ? (String(vals[r][iDir] || '').toLowerCase().indexOf('out') >= 0 ? 'out' : 'in') : 'in',
        text: text, full: full
      });
    }
    rows.sort(function (a, b) { return b.t - a.t; });
    rows.forEach(function (m) {
      if (!res.byNum[m.ph]) res.byNum[m.ph] = { text: m.text, time: m.time, dir: m.dir, count: 0 };
      res.byNum[m.ph].count++;
    });
    res.recent = rows.slice(0, WA_RECENT_MAX);
  } catch (err) { /* optional */ }
  return res;
}

/* ---------------------------------------------------------------------------
 * WA_Inbox tab contract (what the webhook layer must append per message)
 * ---------------------------------------------------------------------------
 * Row 1 = headers (any order; matched by name). Recommended columns:
 *   Timestamp | Phone | Direction | Type | Message | Message ID | Conversation ID | Status
 *     Timestamp       : when the message happened (a real date/datetime cell is best)
 *     Phone           : customer number (10-digit or with country code — both fine)
 *     Direction       : "in" (from patient) or "out" (sent by clinic)
 *     Type            : text / image / button / etc.
 *     Message         : the text (or a short description for media)
 *     Message ID      : MyOperator message_id (for de-dupe / webhook joins)
 *     Conversation ID : MyOperator conversation_id (also parse "conversaton_id")
 *     Status          : received / delivered / read / failed
 * The dashboard reads only Timestamp, Phone, Direction, Type, Message.
 * ------------------------------------------------------------------------- */

/* ===========================================================================
 * PHASE 1 — FOLLOW-UP CALL LOOP  (added v16)
 * ---------------------------------------------------------------------------
 * The dashboard's "Today's follow-up calls" worklist + outcome capture.
 *
 * TABS (all in the same tracker spreadsheet, resolved via CFG.SHEET_ID_PROP):
 *   Followups_Today      READ  - written each morning by push_followups_today.py
 *                              headers: Key, Section, PR, Patient Name, Mobile,
 *                                       Diagnosis, Due Date, OD, Status
 *   Followups_Settled    READ  - returned/dropout history (same script)
 *   Followup_Outcomes    WRITE - THIS file is the only writer. One row per
 *                              logged outcome. The morning re-push NEVER touches
 *                              this tab, so results are never wiped.
 *   Followup_Escalations WRITE - THIS file is the only writer. Items the doctor
 *                              must personally resolve; persist until resolved.
 *
 * SETTLE MODEL (mirrors the Umbrella outcome model, D13):
 *   - settling outcomes  -> row leaves the worklist (Coming / Out of town /
 *                           On medication).
 *   - non-settling       -> "Couldn't communicate" stays on the worklist (retry).
 *   - escalating         -> also appended to Followup_Escalations and persists
 *                           there until the doctor picks a resolution
 *                           (Dikha chuke / Problem / Close follow-up /
 *                            Not interested / Treatment elsewhere).
 *
 * ACCESS:
 *   - Any valid key (staff or full) may read the worklist and LOG an outcome
 *     (same as triggerCall, which both reception and the doctor may use).
 *   - The Escalations VIEW + resolving an escalation = FULL (doctor) key only.
 * ========================================================================= */

var FU_TAB_TODAY    = 'Followups_Today';
var FU_TAB_SETTLED  = 'Followups_Settled';
var FU_TAB_OUTCOMES = 'Followup_Outcomes';
var FU_TAB_ESCAL    = 'Followup_Escalations';

var FU_OUTCOME_HEADERS = ['When', 'Key', 'Patient', 'Mobile', 'Section',
                          'Outcome', 'Source', 'Days', 'Expected Date',
                          'Detail', 'Handled By', 'Agent Ext', 'Settle',
                          'Identity', 'Reason', 'Channel', 'For Whom', 'Clinic ID'];
var FU_ESCAL_HEADERS = ['Raised', 'Key', 'Patient', 'Clinic ID', 'Diagnosis',
                        'Mobile', 'Last Visit', 'Reason', 'Detail',
                        'Raised By', 'Status', 'Resolution', 'Resolved When'];

/** Which outcome codes settle the row, which escalate, which persist (retry). */
var FU_SETTLING  = { coming: 1, out_of_town: 1, on_medication: 1 };
var FU_ESCALATING = { dikha_chuke: 1, problem: 1, close_followup: 1,
                      not_interested: 1, treatment_elsewhere: 1 };
// 'cant_communicate' is neither: it stays on the worklist for a retry.

/** Open spreadsheet by the shared Script Property (same as every other reader). */
function fuSheet_() {
  var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
  if (!id) return null;
  return SpreadsheetApp.openById(id);
}

/** Read a whole tab as array-of-objects keyed by lower-cased header. */
function fuReadObjects_(ss, tabName) {
  var out = [];
  var sh = ss.getSheetByName(tabName);
  if (!sh) return out;
  var vals = sh.getDataRange().getValues();
  if (vals.length < 2) return out;
  var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });
  for (var r = 1; r < vals.length; r++) {
    var o = {};
    for (var c = 0; c < H.length; c++) o[H[c]] = vals[r][c];
    out.push(o);
  }
  return out;
}

/** Today's set of keys that already have a SETTLING or ESCALATING outcome today,
 *  plus the latest non-settling note, so the worklist can drop/annotate rows.
 *  Returns { settledKeys:{key:outcome}, retryKeys:{key:detail} }. */
function fuTodaysOutcomeState_(ss) {
  var res = { settledKeys: {}, retryKeys: {} };
  var rows = fuReadObjects_(ss, FU_TAB_OUTCOMES);
  if (!rows.length) return res;
  var tz = Session.getScriptTimeZone();
  var todayStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  rows.forEach(function (o) {
    var key = String(o['key'] || '').trim();
    if (!key) return;
    var whenT = dateVal_(o['when']);
    var whenStr = whenT ? Utilities.formatDate(new Date(whenT), tz, 'yyyy-MM-dd') : '';
    if (whenStr && whenStr !== todayStr) return;     // only today's outcomes affect today's list
    var code = String(o['outcome'] || '').trim().toLowerCase().replace(/[^a-z]+/g, '_');
    var settle = String(o['settle'] || '').trim().toLowerCase();
    if (settle === 'settle' || FU_SETTLING[code] || FU_ESCALATING[code]) {
      res.settledKeys[key] = code;                   // leaves the worklist
    } else {
      res.retryKeys[key] = String(o['detail'] || o['outcome'] || '').trim();  // stays, annotated
    }
  });
  return res;
}

/** getFollowups(key) -> the live worklist + settled history for the page. */
function getFollowups(key) {
  if (dashRole_(key) === 'none') return { error: 'Not authorized. Please sign in again.' };
  try {
    var ss = fuSheet_();
    if (!ss) return { today: [], settled: [], bySection: {}, counts: { open: 0, retry: 0, settled: 0 } };

    var state = fuTodaysOutcomeState_(ss);
    var rawToday = fuReadObjects_(ss, FU_TAB_TODAY);

    var open = [], settledToday = 0, retryCount = 0;
    rawToday.forEach(function (o) {
      var key0 = String(o['key'] || '').trim();
      if (key0 && state.settledKeys[key0]) { settledToday++; return; }   // already handled -> drop
      var mobile = String(o['mobile'] || '').replace(/\D/g, '');
      if (mobile.length > 10) mobile = mobile.slice(-10);
      var retryNote = (key0 && state.retryKeys[key0]) ? state.retryKeys[key0] : '';
      if (retryNote) retryCount++;
      open.push({
        key:       key0,
        section:   String(o['section'] || 'Follow-up').trim() || 'Follow-up',
        pr:        String(o['pr'] || '').trim(),
        name:      String(o['patient name'] || o['patient'] || o['name'] || '').trim(),
        mobile:    mobile,
        diagnosis: String(o['diagnosis'] || '').trim(),
        due:       fmtDateCell_(o['due date'] || o['due'] || ''),
        od:        String(o['od'] || '').trim(),
        status:    String(o['status'] || '').trim(),
        retry:     retryNote
      });
    });

    // group by section, then by priority (PR ascending, blanks last)
    function prNum(p) { var n = parseInt(String(p).replace(/\D/g, ''), 10); return isNaN(n) ? 9999 : n; }
    open.sort(function (a, b) {
      if (a.section !== b.section) return a.section < b.section ? -1 : 1;
      return prNum(a.pr) - prNum(b.pr);
    });
    var bySection = {};
    open.forEach(function (it) { (bySection[it.section] || (bySection[it.section] = [])).push(it); });

    // settled history (read-only view)
    var settled = fuReadObjects_(ss, FU_TAB_SETTLED).map(function (o) {
      return {
        due:     fmtDateCell_(o['due'] || ''),
        patient: String(o['patient'] || '').trim(),
        mobile:  String(o['mobile'] || '').replace(/\D/g, '').slice(-10),
        clinicId:String(o['clinic id'] || o['clinicid'] || '').trim(),
        outcome: String(o['outcome'] || '').trim(),
        by:      String(o['handled by'] || o['handledby'] || '').trim(),
        when:    fmtDateCell_(o['when'] || '')
      };
    });

    return {
      today: open, bySection: bySection, settled: settled,
      counts: { open: open.length, retry: retryCount, settled: settledToday },
      updated: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'h:mm:ss a')
    };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

/** Ensure a tab exists with the given headers; return the sheet. */
function fuEnsureTab_(ss, tabName, headers) {
  var sh = ss.getSheetByName(tabName);
  if (!sh) {
    sh = ss.insertSheet(tabName);
    sh.getRange(1, 1, 1, headers.length).setValues([headers]);
    return sh;
  }
  if (sh.getLastRow() === 0) {
    sh.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  return sh;
}

/**
 * saveFollowupOutcome(key, payload) — log one follow-up call outcome.
 * payload = { rowKey, name, mobile, section, outcome, source, days,
 *             expected, detail, clinicId, diagnosis, lastVisit }
 * 'outcome' is a code: coming | out_of_town | on_medication | cant_communicate |
 *           dikha_chuke | problem | close_followup | not_interested | treatment_elsewhere
 * The handler (agent) is taken from the LOGIN KEY server-side, never from the page.
 * Escalating outcomes also append a persistent row to Followup_Escalations.
 */
function saveFollowupOutcome(key, payload) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, reason: 'Not authorized.' };
    var info = agentInfoForKey_(key);
    var handler = (info && info.name) ? info.name : (dashRole_(key) === 'full' ? 'Doctor' : 'Staff');
    var ext     = (info && info.ext)  ? info.ext  : '';
    payload = payload || {};
    var code = String(payload.outcome || '').trim().toLowerCase().replace(/[^a-z]+/g, '_');
    if (!code) return { ok: false, reason: 'No outcome chosen.' };

    var ss = fuSheet_();
    if (!ss) return { ok: false, reason: 'Sheet not configured.' };

    var settle = FU_SETTLING[code] ? 'settle'
               : (FU_ESCALATING[code] ? 'escalate' : 'retry');

    var mobile = String(payload.mobile || '').replace(/\D/g, '').slice(-10);
    var tz = Session.getScriptTimeZone();
    var whenStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd HH:mm');

    // 1) always log the outcome (one-writer tab)
    var shO = fuEnsureTab_(ss, FU_TAB_OUTCOMES, FU_OUTCOME_HEADERS);
    shO.appendRow([
      whenStr,
      String(payload.rowKey || '').trim(),
      String(payload.name || '').trim(),
      mobile,
      String(payload.section || '').trim(),
      code,
      String(payload.source || '').trim(),     // here | outside (on_medication)
      String(payload.days || '').trim(),        // days' supply (on_medication, both sources)
      String(payload.expected || '').trim(),    // expected date (coming / out_of_town)
      String(payload.detail || '').trim(),
      handler,
      ext,
      settle
    ]);

    // 2) if escalating, also persist to the doctor's escalations tab
    if (settle === 'escalate') {
      var shE = fuEnsureTab_(ss, FU_TAB_ESCAL, FU_ESCAL_HEADERS);
      var reasonLabel = ({
        dikha_chuke: 'Already visited (dikha chuke)',
        problem: 'Problem / needs attention',
        close_followup: 'Close follow-up - treatment complete',
        not_interested: 'Not interested',
        treatment_elsewhere: 'Treatment elsewhere'
      })[code] || code;
      shE.appendRow([
        whenStr,
        String(payload.rowKey || '').trim(),
        String(payload.name || '').trim(),
        String(payload.clinicId || '').trim(),
        String(payload.diagnosis || '').trim(),
        mobile,
        String(payload.lastVisit || '').trim(),
        reasonLabel,
        String(payload.detail || '').trim(),
        handler,
        'OPEN',
        '',     // Resolution - filled when the doctor resolves
        ''      // Resolved When
      ]);
    }

    return { ok: true, settle: settle, outcome: code };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/* ---------------------------------------------------------------------------
 * INCOMING-CALL OUTCOMES (v17)
 * ---------------------------------------------------------------------------
 * An incoming caller is not on the follow-up ladder, so it has its own outcome
 * model: identity (known / existing-new-number / new-patient / surgery-enquiry /
 * non-patient), a reason or type, and a resolution. It writes to the SAME
 * Followup_Outcomes tab (Source = 'incoming') so the next-day summary and
 * escalations absorb it automatically — no new tabs.
 *
 * Escalation rule: any clinical reason (post-op / new symptom / wants doctor) or
 * an explicit "escalated to doctor" resolution -> Followup_Escalations.
 * Non-settling: "needs callback" and "couldn't communicate" stay actionable
 *   (they are logged but the caller is expected to be re-contacted).
 * ------------------------------------------------------------------------- */

// reasons/resolutions that mean "this needs the doctor"
var IN_ESCALATE_REASON = { post_op: 1, new_symptom: 1, wants_doctor: 1 };
var IN_ESCALATE_RESOLN = { escalated: 1 };
// caller TYPES that always reach the doctor, whatever outcome is logged.
// 'surgery_enquiry' is the Doctor/urgent path (surgery, fracture, accident,
//  severe pain): it always escalates AND fires an instant ntfy push, while the
//  staff still record the outcome (appointment booked / will come / etc.).
var IN_ESCALATE_IDENTITY = { surgery_enquiry: 1 };
// resolutions that DON'T settle (caller still needs action)
var IN_NONSETTLING = { needs_callback: 1, cant_communicate: 1 };

/**
 * saveIncomingOutcome(key, p) — log an outcome for an incoming call.
 * p = { phone, identity, name, clinicId, reason, resolution, expected,
 *       channel, forWhom, surgery(bool), detail, lastVisit }
 *   identity: known | existing_new_number | new_patient | surgery_enquiry | non_patient
 * Handler taken from the login key server-side. Returns { ok, settle }.
 */
function saveIncomingOutcome(key, p) {
  try {
    if (dashRole_(key) === 'none') return { ok: false, reason: 'Not authorized.' };
    var info = agentInfoForKey_(key);
    var handler = (info && info.name) ? info.name : (dashRole_(key) === 'full' ? 'Doctor' : 'Staff');
    var ext     = (info && info.ext)  ? info.ext  : '';
    p = p || {};

    var phone = String(p.phone || '').replace(/\D/g, '').slice(-10);
    if (phone.length !== 10) return { ok: false, reason: 'Bad number.' };

    var identity   = String(p.identity || '').trim().toLowerCase().replace(/[^a-z_]+/g, '_');
    var reason     = String(p.reason || '').trim().toLowerCase().replace(/[^a-z_]+/g, '_');
    var resolution = String(p.resolution || '').trim().toLowerCase().replace(/[^a-z_]+/g, '_');
    if (!resolution && !reason) return { ok: false, reason: 'Nothing to log yet.' };

    var ss = fuSheet_();
    if (!ss) return { ok: false, reason: 'Sheet not configured.' };

    var isUrgent = !!IN_ESCALATE_IDENTITY[identity];
    var escalate = !!(isUrgent || IN_ESCALATE_REASON[reason] || IN_ESCALATE_RESOLN[resolution]);
    var settle = escalate ? 'escalate'
               : (IN_NONSETTLING[resolution] ? 'retry' : 'settle');

    var tz = Session.getScriptTimeZone();
    var whenStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd HH:mm');
    var dayKey  = Utilities.formatDate(new Date(), tz, 'yyyyMMdd');
    var rowKey  = 'IN_' + phone + '_' + dayKey;
    // a readable combined "outcome" code for the summary cross-tab
    var outcomeCode = 'in_' + (resolution || reason || 'logged');

    var shO = fuEnsureTab_(ss, FU_TAB_OUTCOMES, FU_OUTCOME_HEADERS);
    shO.appendRow([
      whenStr,
      rowKey,
      String(p.name || '').trim(),
      phone,
      'Incoming',               // Section
      outcomeCode,              // Outcome (summary groups on this)
      '',                       // Source-on-medication (n/a)
      '',                       // Days (n/a)
      String(p.expected || '').trim(),
      String(p.detail || '').trim(),
      handler,
      ext,
      settle,
      identity,                 // Identity
      reason,                   // Reason
      String(p.channel || '').trim(),   // Channel (how heard) - new patients only
      String(p.forWhom || '').trim(),   // For Whom - self/other
      String(p.clinicId || '').trim()   // Clinic ID
    ]);

    // escalate clinical/flagged incoming calls into the same doctor queue
    if (settle === 'escalate') {
      var shE = fuEnsureTab_(ss, FU_TAB_ESCAL, FU_ESCAL_HEADERS);
      var reasonLabel =
        isUrgent ? 'Incoming: Doctor/urgent (surgery / fracture / accident / severe pain)'
        : ({
            post_op: 'Incoming: post-op / recovery concern',
            new_symptom: 'Incoming: new symptom / problem',
            wants_doctor: 'Incoming: wants to speak to doctor'
          })[reason] || 'Incoming: escalated to doctor';
      shE.appendRow([
        whenStr, rowKey, String(p.name || '').trim(),
        String(p.clinicId || '').trim(), '', phone,
        String(p.lastVisit || '').trim(), reasonLabel,
        String(p.detail || '').trim(), handler, 'OPEN', '', ''
      ]);
    }

    // INSTANT push for the Doctor/urgent path (surgery / fracture / accident /
    // severe pain). Staff are also trained to call the doctor at once; this is
    // the written backup buzz. Best-effort: never let a push failure block the
    // save (the outcome + escalation are already written above).
    if (isUrgent) {
      try { notifyUrgentIncoming_(p, phone, handler); } catch (e) {}
    }

    return { ok: true, settle: settle };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/**
 * notifyUrgentIncoming_ — fire a high-priority ntfy push for a Doctor/urgent
 * incoming call. Option A: posts to the EXISTING ntfy topic (NTFY_TOPIC) so we
 * don't trip the ntfy.sh free-tier second-topic 429. A distinct 🚨 title + high
 * priority + tags make it stand out from the ordinary WhatsApp name alerts.
 *
 * Body content (graduated, per owner decision 28 Jun 2026):
 *   - known patient:        name + short status tag + number + staff
 *   - existing/new number:  name (as given) + number + staff
 *   - new / unknown:        "new patient" + number + staff
 * The patient NUMBER is included (owner wants one-tap call-back from the push).
 * No clinical free-text is ever placed in the push body.
 */
function notifyUrgentIncoming_(p, phone, handler) {
  var topic = (PropertiesService.getScriptProperties().getProperty('NTFY_TOPIC') || '').trim();
  if (!topic) return;                       // no topic configured -> silently skip

  var name = String((p && p.name) || '').trim();
  var identity = String((p && p.identity) || '').trim().toLowerCase().replace(/[^a-z_]+/g, '_');
  var lastVisit = String((p && p.lastVisit) || '').trim();
  var clinicId = String((p && p.clinicId) || '').trim();

  // short status tag from what we know (no VIP flag yet -> derive op/known/new)
  var tag;
  if (identity === 'surgery_enquiry' && !name && !clinicId) tag = 'new patient';
  else if (clinicId || lastVisit)                           tag = 'known patient';
  else if (name)                                            tag = name;          // name itself is the signal
  else                                                       tag = 'new patient';

  // assemble a single readable line. Name leads when we have it.
  var who = name ? name : 'new patient';
  var bits = [who];
  if (tag !== who && tag !== 'new patient') bits.push(tag);
  else if (!name) bits.push(tag);
  if (lastVisit) bits.push('last visit ' + lastVisit);
  bits.push('\uD83D\uDCDE ' + phone);                       // 📞 number (owner-approved)
  if (handler) bits.push('by ' + handler);
  bits.push('open dashboard');
  var body = bits.join('  \u00b7  ');

  var url = 'https://ntfy.sh/' + encodeURIComponent(topic);
  UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'text/plain; charset=utf-8',
    payload: Utilities.newBlob(body).getBytes(),
    headers: {
      'Title': '\uD83D\uDEA8 URGENT incoming call',        // 🚨
      'Priority': 'urgent',                                 // max ntfy priority
      'Tags': 'rotating_light,hospital'
    },
    muteHttpExceptions: true
  });
}

/** getEscalations(key) — DOCTOR ONLY: the open escalations to resolve. */
function getEscalations(key) {
  if (dashRole_(key) !== 'full') return { ok: false, reason: 'Not authorized.' };
  try {
    var ss = fuSheet_();
    if (!ss) return { ok: true, open: [] };
    var sh = ss.getSheetByName(FU_TAB_ESCAL);
    if (!sh) return { ok: true, open: [] };
    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, open: [] };
    var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });
    var col = function (name) { return H.indexOf(name); };
    var tz = Session.getScriptTimeZone();
    var open = [];
    for (var r = 1; r < vals.length; r++) {
      var status = String(vals[r][col('status')] || '').trim().toUpperCase();
      if (status && status !== 'OPEN') continue;          // resolved ones drop off
      open.push({
        rowIndex:  r + 1,                                  // 1-based sheet row (for resolve)
        raised:    fmtDateCell_(vals[r][col('raised')]),
        name:      String(vals[r][col('patient')] || '').trim(),
        clinicId:  String(vals[r][col('clinic id')] || '').trim(),
        diagnosis: String(vals[r][col('diagnosis')] || '').trim(),
        mobile:    String(vals[r][col('mobile')] || '').replace(/\D/g, '').slice(-10),
        lastVisit: String(vals[r][col('last visit')] || '').trim(),
        reason:    String(vals[r][col('reason')] || '').trim(),
        detail:    String(vals[r][col('detail')] || '').trim(),
        by:        String(vals[r][col('raised by')] || '').trim()
      });
    }
    open.reverse();   // newest first
    return { ok: true, open: open };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/** resolveEscalation(key, rowIndex, resolution) — DOCTOR ONLY. Stamps a row resolved. */
function resolveEscalation(key, rowIndex, resolution) {
  if (dashRole_(key) !== 'full') return { ok: false, reason: 'Not authorized.' };
  try {
    var ri = parseInt(rowIndex, 10);
    if (!ri || ri < 2) return { ok: false, reason: 'Bad row.' };
    var res = String(resolution || '').trim();
    if (!res) return { ok: false, reason: 'Pick a resolution.' };
    var ss = fuSheet_();
    var sh = ss && ss.getSheetByName(FU_TAB_ESCAL);
    if (!sh) return { ok: false, reason: 'No escalations tab.' };
    var H = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]
              .map(function (x) { return String(x).trim().toLowerCase(); });
    var iStat = H.indexOf('status'), iResn = H.indexOf('resolution'), iWhen = H.indexOf('resolved when');
    if (iStat < 0) return { ok: false, reason: 'Tab missing Status column.' };
    var when = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
    sh.getRange(ri, iStat + 1).setValue('RESOLVED');
    if (iResn >= 0) sh.getRange(ri, iResn + 1).setValue(res);
    if (iWhen >= 0) sh.getRange(ri, iWhen + 1).setValue(when);
    return { ok: true };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/* ---------------------------------------------------------------------------
 * NEXT-DAY SUMMARY — staff-wise x outcome-wise, emailed + ntfy nudge.
 * ---------------------------------------------------------------------------
 * Set a daily time-driven trigger on sendFollowupSummary (e.g. 8 AM).
 * Reads YESTERDAY's Followup_Outcomes rows, builds the cross-tab, emails a
 * readable HTML table to Script Property SUMMARY_EMAIL, and posts a short
 * companion nudge to ntfy topic in Script Property NTFY_TOPIC.
 * No secrets in this file: both the address and the topic live in Properties.
 * ------------------------------------------------------------------------- */
var FU_OUTCOME_LABEL = {
  coming: 'Coming / will visit',
  out_of_town: 'Out of town',
  on_medication: 'On medication',
  cant_communicate: "Couldn't communicate",
  dikha_chuke: 'Already visited',
  problem: 'Problem / attention',
  close_followup: 'Close follow-up',
  not_interested: 'Not interested',
  treatment_elsewhere: 'Treatment elsewhere',
  in_resolved_on_call: 'In: resolved on call',
  in_appointment_booked: 'In: appointment booked',
  in_info_given: 'In: info given',
  in_info_given_will_act: 'In: info given',
  in_needs_callback: 'In: needs callback',
  in_escalated: 'In: escalated to doctor',
  in_cant_communicate: "In: couldn't communicate",
  in_will_come: 'In: will come / considering',
  in_enquiry_only: 'In: enquiry only',
  in_no_action: 'In: no action',
  in_not_relevant: 'In: not relevant'
};

function sendFollowupSummary() {
  var sp = PropertiesService.getScriptProperties();
  var email = (sp.getProperty('SUMMARY_EMAIL') || '').trim();
  var topic = (sp.getProperty('NTFY_TOPIC') || '').trim();
  var ss = fuSheet_();
  if (!ss) { Logger.log('summary: no sheet'); return; }

  var tz = Session.getScriptTimeZone();
  var yday = new Date(Date.now() - 24 * 3600 * 1000);
  var ydayStr = Utilities.formatDate(yday, tz, 'yyyy-MM-dd');
  var prettyDay = Utilities.formatDate(yday, tz, 'EEE d MMM yyyy');

  var rows = fuReadObjects_(ss, FU_TAB_OUTCOMES).filter(function (o) {
    var t = dateVal_(o['when']);
    return t && Utilities.formatDate(new Date(t), tz, 'yyyy-MM-dd') === ydayStr;
  });

  // cross-tab: staff -> outcomeCode -> count
  var staffSet = {}, outcomeSet = {}, grid = {};
  rows.forEach(function (o) {
    var staff = String(o['handled by'] || 'Unknown').trim() || 'Unknown';
    var code  = String(o['outcome'] || '').trim().toLowerCase().replace(/[^a-z]+/g, '_');
    if (!code) return;
    staffSet[staff] = 1; outcomeSet[code] = 1;
    (grid[staff] || (grid[staff] = {}));
    grid[staff][code] = (grid[staff][code] || 0) + 1;
  });
  var staves = Object.keys(staffSet).sort();
  var codes  = Object.keys(outcomeSet).sort();

  var total = rows.length;
  var subject = 'Clinic follow-ups — ' + prettyDay + ' — ' + total + ' outcome' + (total === 1 ? '' : 's') + ' logged';

  // build a readable HTML table
  var html = '<div style="font-family:Arial,Helvetica,sans-serif;color:#1f2937">';
  html += '<h2 style="margin:0 0 4px">Follow-up call outcomes</h2>';
  html += '<div style="color:#6b7280;margin-bottom:14px">' + prettyDay + ' · ' + total + ' logged</div>';
  if (!total) {
    html += '<p>No follow-up outcomes were logged yesterday.</p>';
  } else {
    html += '<table style="border-collapse:collapse;font-size:14px">';
    html += '<tr><th style="text-align:left;padding:6px 10px;border:1px solid #e5e7eb;background:#f9fafb">Staff</th>';
    codes.forEach(function (c) {
      html += '<th style="padding:6px 10px;border:1px solid #e5e7eb;background:#f9fafb">' +
              (FU_OUTCOME_LABEL[c] || c) + '</th>';
    });
    html += '<th style="padding:6px 10px;border:1px solid #e5e7eb;background:#eef2ff">Total</th></tr>';
    var colTot = {};
    staves.forEach(function (s) {
      var rowTot = 0;
      html += '<tr><td style="padding:6px 10px;border:1px solid #e5e7eb;font-weight:bold">' + s + '</td>';
      codes.forEach(function (c) {
        var n = (grid[s] && grid[s][c]) || 0; rowTot += n; colTot[c] = (colTot[c] || 0) + n;
        html += '<td style="text-align:center;padding:6px 10px;border:1px solid #e5e7eb">' + (n || '') + '</td>';
      });
      html += '<td style="text-align:center;padding:6px 10px;border:1px solid #e5e7eb;font-weight:bold;background:#eef2ff">' + rowTot + '</td></tr>';
    });
    html += '<tr><td style="padding:6px 10px;border:1px solid #e5e7eb;font-weight:bold;background:#f9fafb">Total</td>';
    codes.forEach(function (c) {
      html += '<td style="text-align:center;padding:6px 10px;border:1px solid #e5e7eb;font-weight:bold;background:#f9fafb">' + (colTot[c] || 0) + '</td>';
    });
    html += '<td style="text-align:center;padding:6px 10px;border:1px solid #e5e7eb;font-weight:bold;background:#e0e7ff">' + total + '</td></tr>';
    html += '</table>';
  }
  html += '<p style="color:#9ca3af;font-size:12px;margin-top:16px">Auto-generated by the clinic dashboard. Open the dashboard to action open escalations.</p></div>';

  if (email) {
    MailApp.sendEmail({ to: email, subject: subject, htmlBody: html });
    Logger.log('summary: emailed ' + total + ' rows');
  } else {
    Logger.log('summary: SUMMARY_EMAIL not set — skipped email');
  }

  // short ntfy nudge — OFF by default (ntfy.sh free quota is reserved for the
  // live notifier). Flip Script Property SUMMARY_NTFY = 'on' once a no-quota
  // self-hosted ntfy exists (planned for the VPS brain-migration, rollout #4).
  var ntfyOn = String(sp.getProperty('SUMMARY_NTFY') || '').trim().toLowerCase() === 'on';
  if (topic && ntfyOn) {
    try {
      var line = total
        ? (total + ' follow-up outcomes logged ' + prettyDay + '. Open email for the staff-wise table.')
        : ('No follow-up outcomes logged ' + prettyDay + '.');
      UrlFetchApp.fetch('https://ntfy.sh/' + encodeURIComponent(topic), {
        method: 'post',
        contentType: 'text/plain; charset=utf-8',
        headers: { 'Title': 'Clinic follow-up summary', 'Tags': 'clipboard' },
        payload: line,
        muteHttpExceptions: true
      });
    } catch (e) { Logger.log('summary: ntfy failed ' + e); }
  }
}

/**
 * =====================================================================
 * "WHO IS THIS?" 360 PATIENT LOOKUP  (added Session 14, mobile-first)
 * ---------------------------------------------------------------------
 * A read-only, glance-first patient lookup for use on the phone (rounds,
 * chamber, away from the desk). Answers: who they are, when last seen,
 * sanitised taxonomical diagnosis, and what's pending.
 *
 * Source: the SAME live tabs the dashboard already reads -
 *   - Patient_Master  (mirror of the tracker's patient_master.csv)
 *   - Followups_Today  (the live worklist, for the "pending" line)
 * No new tabs, no new plumbing. Survives the VPS/SQLite migration
 * untouched (it reads the Sheet, which the migration keeps filling).
 *
 * Tiers (server-enforced, never trusted from the page):
 *   - role 'none'  -> refused.
 *   - role 'staff' / 'full' -> may look up patients (clinical context).
 *   Revenue is NOT in Patient_Master, so nothing financial is exposed
 *   here yet; the Doctor-only financial widening comes with the
 *   migration (KB: M6). 'canFinancial' is returned for the page to use
 *   once that lands.
 *
 * Search modes (one of):
 *   mode 'mobile'   -> exact, last-10 digits.
 *   mode 'clinicid' -> exact; tolerant: matches the 4-digit Clinic ID
 *                      column AND the opaque UID column (whichever the
 *                      mirror pushed), so it works regardless.
 *   mode 'name'     -> partial, case-insensitive; returns a short
 *                      pick-list when several match.
 *
 * Returns:
 *   { ok, mode, query, freshness, canFinancial,
 *     matches: [ {name, age, sex, clinicId, uid, mobile, dx,
 *                 lastVisit, lastAgo, pending} ],
 *     tooMany (bool), note }
 * Phone numbers are returned in full ONLY for the one-tap Call action
 * (the dashboard already shows numbers to authorised staff); nothing is
 * logged by this function - it is pure read.
 * =====================================================================
 */
var P360_MAX_NAME_HITS = 25;   // cap a name pick-list (older base: names repeat)

function lookupPatient360(key, mode, query) {
  var role = dashRole_(key);
  if (role === 'none') return { ok: false, error: 'Not authorized. Please sign in again.' };

  mode  = String(mode || '').trim().toLowerCase();
  query = String(query || '').trim();
  if (!query) return { ok: false, error: 'Type something to search.' };

  var canFinancial = (role === 'full');   // for the future revenue widening (M6)

  try {
    var sp = PropertiesService.getScriptProperties();
    var id = sp.getProperty('PATIENT_SHEET_ID') || sp.getProperty(CFG.SHEET_ID_PROP);
    if (!id) return { ok: false, error: 'Patient sheet not configured.' };
    var sh = SpreadsheetApp.openById(id).getSheetByName(PATIENT_TAB);
    if (!sh) return { ok: false, error: 'Patient_Master tab not found.' };

    var vals = sh.getDataRange().getValues();
    if (vals.length < 2) return { ok: true, mode: mode, query: query, matches: [],
                                  freshness: '', canFinancial: canFinancial,
                                  note: 'Patient list is empty.' };

    var H = vals[0].map(function (x) { return String(x).trim().toLowerCase(); });
    var iPhone = findCol_(H, ['mobile', 'phone number', 'mobile number', 'mobile no', 'phone', 'number', 'phone10']);
    var iName  = findCol_(H, ['patient name', 'name', 'first name']);
    var iDx    = findCol_(H, ['diagnosis', 'dx', 'purpose of visit', 'purpose']);
    var iAge   = findCol_(H, ['age']);
    var iSex   = findCol_(H, ['gender', 'sex']);
    var iLast  = findCol_(H, ['last visit', 'consultation date', 'last seen', 'seen']);
    var iUid   = findCol_(H, ['clinic specific id', 'clinic id', 'patient uid', 'uid']);

    // Freshness stamp: when the spreadsheet was last written (best-effort).
    // The mirror replaces Patient_Master on each run, so the file's
    // last-updated time is a good "data as of" proxy.
    var freshness = '';
    try {
      var file = DriveApp.getFileById(id);
      freshness = Utilities.formatDate(file.getLastUpdated(), Session.getScriptTimeZone(), 'd MMM, h:mm a');
    } catch (e) { freshness = ''; }

    var qDigits = query.replace(/\D/g, '');
    var qLower  = query.toLowerCase();
    var hits = [];

    for (var r = 1; r < vals.length && hits.length <= (P360_MAX_NAME_HITS + 1); r++) {
      var phRaw = iPhone >= 0 ? vals[r][iPhone] : '';
      var ph    = last10_(phRaw);
      var name  = iName >= 0 ? String(vals[r][iName] || '').trim() : '';
      var uid   = iUid  >= 0 ? String(vals[r][iUid]  || '').trim() : '';

      var isMatch = false;
      if (mode === 'mobile') {
        if (qDigits.length >= 6 && ph && ph.slice(-10) === qDigits.slice(-10)) isMatch = true;
      } else if (mode === 'clinicid') {
        // tolerant: compare against the id column both as-typed and digits-only
        var uidL = uid.toLowerCase();
        if (uid && (uidL === qLower || uid.replace(/\D/g, '') === qDigits && qDigits !== '')) isMatch = true;
      } else { // name (partial)
        if (name && qLower && name.toLowerCase().indexOf(qLower) >= 0) isMatch = true;
      }
      if (!isMatch) continue;

      var lastStr = iLast >= 0 ? fmtDateCell_(vals[r][iLast]) : '';
      var lastMs  = iLast >= 0 ? dateVal_(vals[r][iLast])     : 0;
      hits.push({
        name:      name,
        age:       iAge >= 0 ? String(vals[r][iAge] || '').trim() : '',
        sex:       iSex >= 0 ? String(vals[r][iSex] || '').trim() : '',
        clinicId:  uid,
        uid:       uid,
        mobile:    ph || '',
        dx:        iDx >= 0 ? String(vals[r][iDx] || '').trim() : '',
        lastVisit: lastStr,
        lastAgo:   agoFromMs_(lastMs),
        _sort:     lastMs,
        pending:   ''
      });
    }

    var tooMany = false;
    if (hits.length > P360_MAX_NAME_HITS) { hits = hits.slice(0, P360_MAX_NAME_HITS); tooMany = true; }

    // Most-recent first (helps tell repeated names apart).
    hits.sort(function (a, b) { return (b._sort || 0) - (a._sort || 0); });

    // Add the "pending" line from Followups_Today (best-effort; never blocks).
    if (hits.length) {
      try {
        var pend = pendingByMobile_();
        hits.forEach(function (h) {
          if (h.mobile && pend[h.mobile]) h.pending = pend[h.mobile];
        });
      } catch (e) { /* pending optional */ }
    }
    hits.forEach(function (h) { delete h._sort; });

    return {
      ok: true, mode: mode, query: query,
      freshness: freshness, canFinancial: canFinancial,
      matches: hits, tooMany: tooMany,
      note: hits.length ? '' : 'No patient matched.'
    };
  } catch (err) {
    return { ok: false, error: String(err && err.message ? err.message : err) };
  }
}

/** "x days/months ago" from a millis timestamp, or '' if unknown. */
function agoFromMs_(ms) {
  if (!ms) return '';
  var days = Math.floor((Date.now() - ms) / 86400000);
  if (days < 0)   return '';
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30)  return days + ' days ago';
  var months = Math.floor(days / 30);
  if (months < 12) return months + (months === 1 ? ' month ago' : ' months ago');
  var years = Math.floor(days / 365);
  return years + (years === 1 ? ' year ago' : ' years ago');
}

/** phone10 -> short pending text, read from Followups_Today (best-effort). */
function pendingByMobile_() {
  var out = {};
  try {
    var ss = fuSheet_();
    if (!ss) return out;
    var rows = fuReadObjects_(ss, FU_TAB_TODAY);
    rows.forEach(function (o) {
      var m = String(o['mobile'] || '').replace(/\D/g, '');
      if (m.length > 10) m = m.slice(-10);
      if (!m) return;
      var sec = String(o['section'] || 'Follow-up').trim();
      var due = fmtDateCell_(o['due date'] || o['due'] || '');
      out[m] = sec + (due ? (' \u00b7 due ' + due) : '');
    });
  } catch (e) { /* optional */ }
  return out;
}
