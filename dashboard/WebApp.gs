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

/** Optional one-time helper: set the dashboard access key from the editor. */
function setDashboardKey(k) {
  PropertiesService.getScriptProperties().setProperty('DASH_KEY', String(k || ''));
  Logger.log('DASH_KEY set. Open the dashboard at <url>?k=%s', k);
}

/** Serve the dashboard page. */
function doGet(e) {
  var key = PropertiesService.getScriptProperties().getProperty('DASH_KEY');
  if (key) {
    var given = (e && e.parameter) ? e.parameter.k : '';
    if (given !== key) {
      return HtmlService.createHtmlOutput(
        '<div style="font-family:Arial;padding:48px;color:#9b1c1c;font-size:18px;">' +
        'Access key required. Open this page with <b>?k=YOUR_KEY</b> in the address.</div>')
        .setTitle('Clinic Callbacks');
    }
  }
  return HtmlService.createHtmlOutputFromFile('Dashboard')
    .setTitle('Clinic Callbacks — Live')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/**
 * Called by the page via google.script.run. Returns a plain object
 * (strings / numbers / arrays only). force=true (Refresh button) bypasses cache.
 */
function getDashboardData(force) {
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
    return { number: m.ph, name: p ? p.name : '', time: m.time, dir: m.dir, text: m.text };
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
    build: 'v7 \u00b7 clinic team',
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
function getRecordingAudio(filename) {
  try {
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
      var text = iText >= 0 ? String(vals[r][iText] || '').trim() : '';
      if (!text) text = '[' + (type || 'message') + ']';
      if (text.length > WA_SNIPPET_MAX) text = text.slice(0, WA_SNIPPET_MAX - 1) + '…';
      rows.push({
        ph: ph, t: t,
        time: t ? Utilities.formatDate(new Date(t), tz, 'd MMM h:mm a') : '',
        dir: iDir >= 0 ? (String(vals[r][iDir] || '').toLowerCase().indexOf('out') >= 0 ? 'out' : 'in') : 'in',
        text: text
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
