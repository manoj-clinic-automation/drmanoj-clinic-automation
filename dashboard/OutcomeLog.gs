/* ===========================================================================
 * OutcomeLog.gs — DOCTOR'S OUTCOME REVIEW CONSOLE (server layer) · v2.0
 * ---------------------------------------------------------------------------
 * Session 25: read-only staff outcome log.
 * Session 36 (v2.0): upgraded to the UNIFIED REVIEW CONSOLE per the doctor's
 *   Session-34/35 direction — every outcome staff file flows here for the
 *   doctor's final glance. The doctor can:
 *     · see everything about the call in one place: the actual call's time +
 *       duration, patient + Clinic ID, the outcome EXACTLY as staff filed it,
 *       🎧 recording (same-day via MyOperator, next-day via the Drive archive),
 *       transcript (expandable, Stage 2), and a free-text note line;
 *     · APPROVE (row leaves the pending view, permanently logged), or
 *     · SEND BACK to staff (recorded now; drives list suppression when the
 *       loop-closing build lands — Session 35 finding).
 *   Today | Yesterday views. Grouped by follow-up band (frozen at save-time).
 *
 * DESIGN (matches CallConsole.gs, D34):
 *   - STANDALONE file. Never modifies WebApp.gs.
 *   - Reuses shared helpers (same project = one global namespace):
 *       dashRole_(), fuSheet_()                       — WebApp.gs
 *       fetchCallsBetween_()                          — MyOperator.gs
 *       cc_todayBounds_(), cc_patientMap_(), cc_pick_(),
 *       cc_last10_(), cc_int_(), cc_mmss_(), CC_TZ    — CallConsole.gs
 *   - WRITES: only the three NEW review columns it owns at the far end of
 *     Followup_Outcomes ('Doctor Review' | 'Doctor Note' | 'Reviewed When').
 *     WebApp.gs only APPENDS whole new rows and never touches these columns,
 *     so the one-writer-per-column discipline holds.
 *
 * ACCESS: FULL (doctor) key ONLY for everything in this file.
 * ========================================================================= */

var OL_TAB        = 'Followup_Outcomes';
var OL_TAB_REC    = 'Call_Recordings';
var OL_TAB_TX     = 'Call_Transcripts';
var OL_REVIEW_COLS = ['Doctor Review', 'Doctor Note', 'Reviewed When'];
var OL_TX_MAXCHARS = 20000;   // safety cap for very long transcripts

/* ----------------------------- small helpers ---------------------------- */

function OL_lc_(arr) {
  var o = [];
  for (var i = 0; i < arr.length; i++) o.push(String(arr[i] || '').trim().toLowerCase());
  return o;
}
function OL_col_(H, names) {
  for (var i = 0; i < names.length; i++) {
    var ix = H.indexOf(names[i]);
    if (ix >= 0) return ix;
  }
  return -1;
}
/** True when the "Handled By" value is a generic placeholder rather than a real
 *  agent's name. Used at the outcome-row build step: if the outcome was filed
 *  under a generic label AND we matched a real call, we borrow the real caller
 *  name from the call log. Blank counts as generic. (S94 fix — this helper was
 *  referenced on line ~333 but never defined, which broke the Today outcome view.) */
function isGenericAgent_(name) {
  var n = String(name || '').trim().toLowerCase();
  if (!n) return true;
  return (n === 'staff' || n === 'doctor' || n === 'unknown' || n === 'agent' || n === 'system');
}
/** 'When' cells may come back as Date objects OR strings — normalise both. */
function OL_whenParts_(v) {
  if (v instanceof Date) {
    return {
      date: Utilities.formatDate(v, CC_TZ, 'yyyy-MM-dd'),
      time: Utilities.formatDate(v, CC_TZ, 'HH:mm'),
      epoch: Math.floor(v.getTime() / 1000)
    };
  }
  var s = String(v || '').trim();                       // 'yyyy-MM-dd HH:mm'
  var m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})/);
  if (!m) return { date: s.slice(0, 10), time: s.slice(11, 16), epoch: 0 };
  var d = new Date(m[1] + '-' + m[2] + '-' + m[3] + 'T' +
                   ('0' + m[4]).slice(-2) + ':' + m[5] + ':00+05:30');
  return { date: m[1] + '-' + m[2] + '-' + m[3],
           time: ('0' + m[4]).slice(-2) + ':' + m[5],
           epoch: Math.floor(d.getTime() / 1000) };
}
function OL_last4_(v) {
  var s = String(v || '').replace(/\D/g, '');
  return s.length >= 4 ? s.slice(-4) : '';
}

/** Ensure the three review columns exist on the header row.
 *  Returns their 1-based column numbers {rev, note, when}. */
function OL_ensureReviewCols_(sh) {
  var lastCol = Math.max(sh.getLastColumn(), 1);
  var head = sh.getRange(1, 1, 1, lastCol).getValues()[0];
  var H = OL_lc_(head);
  var pos = {};
  var names = ['doctor review', 'doctor note', 'reviewed when'];
  var missing = [];
  for (var i = 0; i < names.length; i++) {
    var ix = H.indexOf(names[i]);
    if (ix >= 0) pos[names[i]] = ix + 1; else missing.push(i);
  }
  if (missing.length) {
    var startCol = lastCol + 1;
    var add = [];
    for (var j = 0; j < missing.length; j++) add.push(OL_REVIEW_COLS[missing[j]]);
    sh.getRange(1, startCol, 1, add.length).setValues([add]);
    for (var k = 0; k < missing.length; k++) pos[names[missing[k]]] = startCol + k;
  }
  return { rev: pos['doctor review'], note: pos['doctor note'], when: pos['reviewed when'] };
}

/* ------------------- call matching (today / yesterday) ------------------- */

/** TODAY: phone10 -> [ {epoch, durSec, filename} ] connected calls, live feed. */
function OL_todayCallsByPhone_() {
  var m = {};
  try {
    var b = cc_todayBounds_();
    var raw = fetchCallsBetween_(b.start, b.end) || [];
    var amap = {};
    try { amap = cc_agentMap_() || {}; } catch (eA) {}
    for (var i = 0; i < raw.length; i++) {
      var s = raw[i] || {};
      var missed = (typeof s.is_missed === 'boolean')
        ? s.is_missed
        : (String(cc_pick_(s, ['status', 'call_status'])) === '2');
      if (missed) continue;                              // only connected calls have audio
      var ph = cc_last10_(cc_pick_(s, ['phone10', 'caller_number_raw', 'caller_number', 'number']));
      if (!ph) continue;
      var epoch = cc_int_(cc_pick_(s, ['start_time', 'synced_time', 'time']));
      if (!epoch) continue;
      (m[ph] || (m[ph] = [])).push({
        epoch: epoch,
        durSec: cc_int_(cc_pick_(s, ['duration_seconds', 'duration', 'seconds'])),
        filename: String(cc_pick_(s, ['filename', 'recording_filename']) || ''),
        agent: cc_agentName_(s, amap)                    // v18.7: who handled the call
      });
    }
  } catch (e) { /* feed unavailable -> rows simply show no call match */ }
  return m;
}

/** TODAY: connected calls by phone (with agent) AND the set of phones that had a
 *  missed call today — computed in one feed pass. Lets the escalation card show the
 *  call, or state clearly that it was a missed call / no call. */
function OL_todayCallsAndMissed_() {
  var connected = {}, missed = {};
  try {
    var b = cc_todayBounds_();
    var raw = fetchCallsBetween_(b.start, b.end) || [];
    var amap = {};
    try { amap = cc_agentMap_() || {}; } catch (eA) {}
    for (var i = 0; i < raw.length; i++) {
      var s = raw[i] || {};
      var ph = cc_last10_(cc_pick_(s, ['phone10', 'caller_number_raw', 'caller_number', 'number']));
      if (!ph) continue;
      var isMissed = (typeof s.is_missed === 'boolean')
        ? s.is_missed
        : (String(cc_pick_(s, ['status', 'call_status'])) === '2');
      if (isMissed) { missed[ph] = true; continue; }
      var epoch = cc_int_(cc_pick_(s, ['start_time', 'synced_time', 'time']));
      if (!epoch) continue;
      (connected[ph] || (connected[ph] = [])).push({
        epoch: epoch,
        durSec: cc_int_(cc_pick_(s, ['duration_seconds', 'duration', 'seconds'])),
        filename: String(cc_pick_(s, ['filename', 'recording_filename']) || ''),
        agent: cc_agentName_(s, amap)
      });
    }
  } catch (e) { /* feed unavailable -> escalation cards say "no call" */ }
  return { connected: connected, missed: missed };
}

/** YESTERDAY(+ any archived day): phone10 -> [ {epoch, timeStr, durStr, fileId, joinKey} ]
 *  from the permanent Call_Recordings archive, restricted to dateStr. */
function OL_archivedCallsByPhone_(ss, dateStr) {
  var m = {};
  var sh = ss.getSheetByName(OL_TAB_REC);
  if (!sh) return m;
  var vals = sh.getDataRange().getValues();
  if (vals.length < 2) return m;
  var H = OL_lc_(vals[0]);
  var iDate = OL_col_(H, ['date']);
  var iTime = OL_col_(H, ['time']);
  var iDur  = OL_col_(H, ['duration']);
  var iKey  = OL_col_(H, ['join key', 'joinkey']);
  var iFile = OL_col_(H, ['drive file id', 'file id']);
  if (iKey < 0 || iFile < 0) return m;
  for (var r = 1; r < vals.length; r++) {
    var row = vals[r];
    var dRaw = row[iDate];
    var d = (dRaw instanceof Date)
      ? Utilities.formatDate(dRaw, CC_TZ, 'yyyy-MM-dd')
      : String(dRaw || '').slice(0, 10);
    if (d !== dateStr) continue;
    var key = String(row[iKey] || '').trim();            // phone10_startUnix
    var us  = key.indexOf('_');
    if (us < 10) continue;
    var ph  = key.slice(0, us);
    var epoch = parseInt(key.slice(us + 1), 10) || 0;
    var fileId = String(row[iFile] || '').trim();
    if (!ph || !fileId) continue;
    var tRaw = row[iTime];
    var tStr = (tRaw instanceof Date)
      ? Utilities.formatDate(tRaw, CC_TZ, 'HH:mm')
      : String(tRaw || '').slice(0, 5);
    (m[ph] || (m[ph] = [])).push({
      epoch: epoch, timeStr: tStr,
      durStr: String(row[iDur] || ''),
      fileId: fileId, joinKey: key
    });
  }
  return m;
}

/** joinKey -> transcript Drive file ID (only where a transcript exists). */
function OL_transcriptsByKey_(ss) {
  var m = {};
  var sh = ss.getSheetByName(OL_TAB_TX);
  if (!sh) return m;
  var vals = sh.getDataRange().getValues();
  if (vals.length < 2) return m;
  var H = OL_lc_(vals[0]);
  var iKey  = OL_col_(H, ['join key', 'joinkey']);
  var iFile = OL_col_(H, ['transcript drive file id', 'transcript file id']);
  if (iKey < 0 || iFile < 0) return m;
  for (var r = 1; r < vals.length; r++) {
    var key = String(vals[r][iKey] || '').trim();
    var fid = String(vals[r][iFile] || '').trim();
    if (key && fid && fid.toLowerCase() !== 'none') m[key] = fid;
  }
  return m;
}

/** Pick the connected call nearest BEFORE the outcome save time (staff call,
 *  then save). Falls back to the nearest same-day call after it. */
function OL_nearestCall_(list, saveEpoch) {
  if (!list || !list.length) return null;
  var before = null, after = null;
  for (var i = 0; i < list.length; i++) {
    var c = list[i];
    if (!saveEpoch) { if (!before || c.epoch > before.epoch) before = c; continue; }
    if (c.epoch <= saveEpoch) { if (!before || c.epoch > before.epoch) before = c; }
    else                      { if (!after  || c.epoch < after.epoch)  after  = c; }
  }
  return before || after;
}

/* ------------------------------ main reads ------------------------------ */

/**
 * getOutcomeLog(key, day) — DOCTOR ONLY. day: 'today' (default) | 'yesterday'.
 * Returns the PENDING (un-reviewed) outcomes of that day, fully enriched:
 *   { ok, day, dateLabel, count, reviewedCount, tally, sheetUrl,
 *     rows: [ { rowIndex, fp, time, patient, last4, clinicId, section,
 *               code, source, days, expected, detail, by, settle, note,
 *               callTime, callDur, rec:{kind:'myop'|'drive', ref}, tx } ] }
 */
function getOutcomeLog(key, day) {
  try {
    if (dashRole_(key) !== 'full') return { error: 'Not authorized.' };
    var ss = fuSheet_();
    if (!ss) return { error: 'Sheet not configured.' };

    day = (String(day || '').toLowerCase() === 'yesterday') ? 'yesterday' : 'today';
    var now = new Date();
    var ref = (day === 'yesterday') ? new Date(now.getTime() - 24 * 3600 * 1000) : now;
    var dateStr = Utilities.formatDate(ref, CC_TZ, 'yyyy-MM-dd');

    var sh = ss.getSheetByName(OL_TAB);
    if (!sh || sh.getLastRow() < 2) {
      return { ok: true, day: day, count: 0, reviewedCount: 0, tally: [], rows: [],
               dateLabel: Utilities.formatDate(ref, CC_TZ, 'EEE d MMM') };
    }
    var vals = sh.getDataRange().getValues();
    var H = OL_lc_(vals[0]);
    var ix = {
      when:    OL_col_(H, ['when']),
      patient: OL_col_(H, ['patient']),
      mobile:  OL_col_(H, ['mobile']),
      section: OL_col_(H, ['section']),
      outcome: OL_col_(H, ['outcome']),
      source:  OL_col_(H, ['source']),
      days:    OL_col_(H, ['days']),
      expect:  OL_col_(H, ['expected date']),
      detail:  OL_col_(H, ['detail']),
      by:      OL_col_(H, ['handled by']),
      settle:  OL_col_(H, ['settle']),
      cid:     OL_col_(H, ['clinic id']),
      rev:     OL_col_(H, ['doctor review']),
      note:    OL_col_(H, ['doctor note'])
    };
    if (ix.when < 0) return { error: 'Outcome tab has no When column.' };

    // enrichment sources for the chosen day
    var callMap, missedToday = {};
    if (day === 'today') {
      var _tcOL = OL_todayCallsAndMissed_();
      callMap = _tcOL.connected || {};
      missedToday = _tcOL.missed || {};
    } else {
      callMap = OL_archivedCallsByPhone_(ss, dateStr);
    }
    var txMap   = (day === 'today') ? {} : OL_transcriptsByKey_(ss);
    var pmap    = {};
    try { pmap = cc_patientMap_() || {}; } catch (e) {}

    function cell(row, i) { return (i >= 0 && i < row.length && row[i] != null) ? row[i] : ''; }

    var rows = [], byStaff = {}, reviewedCount = 0;
    for (var r = 1; r < vals.length; r++) {
      var row = vals[r];
      var wp = OL_whenParts_(cell(row, ix.when));
      if (wp.date !== dateStr) continue;

      var reviewed = String(cell(row, ix.rev) || '').trim();
      if (reviewed) { reviewedCount++; continue; }        // approved/sent-back rows leave the view

      var mob = String(cell(row, ix.mobile) || '').replace(/\D/g, '');
      var ph  = mob.length >= 10 ? mob.slice(-10) : '';
      var by  = String(cell(row, ix.by) || '').trim() || 'Unknown';

      var cid = String(cell(row, ix.cid) || '').trim();
      if (!cid && ph && pmap[ph]) cid = String(pmap[ph].clinicId || '');

      var match = ph ? OL_nearestCall_(callMap[ph], wp.epoch) : null;
      var rec = null, callTime = '', callDur = '', callDate = '', tx = '';
      var callState = 'nocall';
      if (match) {
        callState = 'connected';
        if (day === 'today') {
          callTime = match.epoch ? Utilities.formatDate(new Date(match.epoch * 1000), CC_TZ, 'HH:mm') : '';
          callDate = match.epoch ? Utilities.formatDate(new Date(match.epoch * 1000), CC_TZ, 'd MMM') : '';
          callDur  = cc_mmss_(match.durSec || 0);
          if (match.filename) rec = { kind: 'myop', ref: match.filename };
        } else {
          callTime = match.timeStr || '';
          callDate = Utilities.formatDate(ref, CC_TZ, 'd MMM');
          callDur  = String(match.durStr || '');
          rec = { kind: 'drive', ref: match.fileId };
          tx  = txMap[match.joinKey] || '';
        }
      } else if (day === 'today' && ph && missedToday[ph]) {
        callState = 'missed';
      }

      if (match && match.agent && isGenericAgent_(by)) by = match.agent;   // borrow real caller from the call log
      byStaff[by] = (byStaff[by] || 0) + 1;

      rows.push({
        rowIndex: r + 1,                                  // 1-based sheet row
        fp:       wp.date + '|' + OL_last4_(mob),         // write-safety fingerprint
        time:     wp.time,
        date:     Utilities.formatDate(ref, CC_TZ, 'd MMM'),
        patient:  String(cell(row, ix.patient) || '').trim(),
        last4:    OL_last4_(mob),
        clinicId: cid,
        lastVisit:(ph && pmap[ph]) ? String(pmap[ph].lastVisit || '') : '',   // v18.3: last-visit on console
        section:  String(cell(row, ix.section) || '').trim() || 'Other',
        code:     String(cell(row, ix.outcome) || '').trim(),
        source:   String(cell(row, ix.source) || '').trim(),
        days:     String(cell(row, ix.days) || '').trim(),
        expected: String(cell(row, ix.expect) || '').trim(),
        detail:   String(cell(row, ix.detail) || '').trim(),
        by:       by,
        settle:   String(cell(row, ix.settle) || '').trim().toLowerCase(),
        note:     String(cell(row, ix.note) || '').trim(),
        callTime: callTime, callDur: callDur, callDate: callDate, callState: callState,
        rec: rec, tx: tx
      });
    }

    rows.sort(function (a, b) { return b.time < a.time ? -1 : (b.time > a.time ? 1 : 0); });

    var tally = Object.keys(byStaff).map(function (k) { return { by: k, n: byStaff[k] }; })
                  .sort(function (a, b) { return b.n - a.n; });

    var url = ss.getUrl();
    var shO = ss.getSheetByName(OL_TAB);
    if (shO) url += '#gid=' + shO.getSheetId();

    return {
      ok: true, day: day, count: rows.length, reviewedCount: reviewedCount,
      dateLabel: Utilities.formatDate(ref, CC_TZ, 'EEE d MMM'),
      sheetUrl: url, tally: tally, rows: rows
    };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

/**
 * getTranscriptText(key, fileId) — DOCTOR ONLY. Fetches one transcript's text
 * from the permanent Drive archive, on demand (nothing pre-loaded).
 */
function getTranscriptText(key, fileId) {
  try {
    if (dashRole_(key) !== 'full') return { error: 'Not authorized.' };
    fileId = String(fileId || '').trim();
    if (!fileId) return { error: 'No transcript.' };
    var txt = DriveApp.getFileById(fileId).getBlob().getDataAsString('UTF-8');
    if (!txt) return { error: 'Empty transcript file.' };
    if (txt.length > OL_TX_MAXCHARS) txt = txt.slice(0, OL_TX_MAXCHARS) + '\n… (truncated)';
    return { ok: true, text: txt };
  } catch (err) {
    return { error: String(err && err.message ? err.message : err) };
  }
}

/**
 * reviewOutcome(key, payload) — DOCTOR ONLY. One review action on one row.
 *   payload: { rowIndex, fp, action: 'approve' | 'sendback' | 'note', note }
 * approve  -> Doctor Review = 'APPROVED',  Reviewed When = now, note saved
 * sendback -> Doctor Review = 'SEND BACK', Reviewed When = now, note saved
 * note     -> only the Doctor Note cell is written (row stays pending)
 * The fp (date|last4) must match the row — protects against writing a wrong
 * row if the sheet changed between the doctor's read and click.
 */
function reviewOutcome(key, payload) {
  try {
    if (dashRole_(key) !== 'full') return { ok: false, reason: 'Not authorized.' };
    payload = payload || {};
    var rowIndex = parseInt(payload.rowIndex, 10);
    var action = String(payload.action || '').toLowerCase();
    if (!rowIndex || rowIndex < 2) return { ok: false, reason: 'Bad row.' };
    if (action !== 'approve' && action !== 'sendback' && action !== 'note') {
      return { ok: false, reason: 'Bad action.' };
    }
    var ss = fuSheet_();
    if (!ss) return { ok: false, reason: 'Sheet not configured.' };
    var sh = ss.getSheetByName(OL_TAB);
    if (!sh || rowIndex > sh.getLastRow()) return { ok: false, reason: 'Row not found.' };

    // fingerprint check
    var head = OL_lc_(sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]);
    var iWhen = OL_col_(head, ['when']);
    var iMob  = OL_col_(head, ['mobile']);
    var rowV = sh.getRange(rowIndex, 1, 1, sh.getLastColumn()).getValues()[0];
    var wp = OL_whenParts_(iWhen >= 0 ? rowV[iWhen] : '');
    var fpNow = wp.date + '|' + OL_last4_(iMob >= 0 ? rowV[iMob] : '');
    if (String(payload.fp || '') !== fpNow) {
      return { ok: false, reason: 'Row changed since it was loaded — refresh and retry.' };
    }

    var cols = OL_ensureReviewCols_(sh);
    var note = String(payload.note || '').trim();
    var tz = Session.getScriptTimeZone();
    if (note || action === 'note') sh.getRange(rowIndex, cols.note).setValue(note);
    if (action === 'approve' || action === 'sendback') {
      sh.getRange(rowIndex, cols.rev).setValue(action === 'approve' ? 'APPROVED' : 'SEND BACK');
      sh.getRange(rowIndex, cols.when).setValue(
        Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd HH:mm'));
    }
    return { ok: true, action: action };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/**
 * reviewOutcomeBatch(key, items) — DOCTOR ONLY. Approve-all for one band.
 *   items: [ { rowIndex, fp }, ... ]  (approve only; notes are per-row)
 */
function reviewOutcomeBatch(key, items) {
  try {
    if (dashRole_(key) !== 'full') return { ok: false, reason: 'Not authorized.' };
    items = items || [];
    var done = 0, failed = 0;
    for (var i = 0; i < items.length; i++) {
      var r = reviewOutcome(key, { rowIndex: items[i].rowIndex, fp: items[i].fp,
                                   action: 'approve', note: '' });
      if (r && r.ok) done++; else failed++;
    }
    return { ok: true, done: done, failed: failed };
  } catch (err) {
    return { ok: false, reason: String(err && err.message ? err.message : err) };
  }
}

/** OL_SELFTEST — run from the editor; sanity without the UI (no writes). */
function OL_SELFTEST() {
  var ss = fuSheet_();
  Logger.log('sheet: ' + (ss ? ss.getName() : 'NONE'));
  var sh = ss ? ss.getSheetByName(OL_TAB) : null;
  Logger.log('rows in ' + OL_TAB + ': ' + (sh ? sh.getLastRow() - 1 : 'NO TAB'));
  if (sh) {
    var H = OL_lc_(sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]);
    Logger.log('headers: ' + JSON.stringify(H));
    Logger.log('review cols present: ' +
      (H.indexOf('doctor review') >= 0) + '/' + (H.indexOf('doctor note') >= 0) +
      '/' + (H.indexOf('reviewed when') >= 0) + ' (created on first review click)');
  }
  var rec = ss ? ss.getSheetByName(OL_TAB_REC) : null;
  var tx  = ss ? ss.getSheetByName(OL_TAB_TX)  : null;
  Logger.log('Call_Recordings rows: ' + (rec ? rec.getLastRow() - 1 : 'NO TAB'));
  Logger.log('Call_Transcripts rows: ' + (tx ? tx.getLastRow() - 1 : 'NO TAB'));
}