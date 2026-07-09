/**
* Health.gs  v2.2 — daily HEARTBEAT health report (Session 128)
 * -----------------------------------------------------------------------------
 * WHY v2 EXISTS  (v1 shipped 09-Jul 10:23 and was wrong twice)
 *
 *   v1 asked every tab the same question: "how many rows today?"  That question
 *   is meaningless for a tab refreshed once a night. At 09:00 the answer is
 *   always 0 — whether the nightly job ran or died. v1 printed "Clinic health OK"
 *   over a Call_Feed whose refresh trigger could have been dead for a week.
 *   A check that cannot fail is not a check.
 *
 *   v1 also never looked at Call_Durations — the tab the VPS receiver writes in
 *   real time, and the exact tab that went silent for 44 hours on 06-Jul.
 *
 *   v2 asks each tab the question that fits ITS OWN clock:
 *        "how far behind today is your newest row, and is that further than
 *         your schedule allows?"
 *
 * THE FOUR CLOCKS
 *   Followups_Today       pushed from the clinic PC each morning
 *   Followup_Outcomes     written by staff through the day (dashboard)
 *   Call_Durations        VPS receiver, real time -- but ONLY calls placed from
 *                         the dashboard dialler. The receiver writes a row only
 *                         when category=="obd" AND client_ref_id is present;
 *                         everything else (incoming calls, non-OBD legs) is
 *                         raw-logged on the VPS and never reaches this tab.
 *                         Proof, 09-Jul: 66 webhooks accepted, 29 rows written.
 *                         CONSEQUENCE: a clinic day on which nobody uses the
 *                         console dialler looks exactly like a dead receiver.
 *                         maxLag is 1: one dialler-free day is absorbed; two in
 *                         a row raise a flag you dismiss in five seconds. maxLag
 *                         2 was tried and REJECTED -- it delays outage detection
 *                         to the third morning, trading away the whole point to
 *                         buy comfort against a rare event. The reverse also
 *                         holds: an outage on a dialler-free day is invisible
 *                         here. The VPS raw log remains the only complete
 *                         record, and Apps Script cannot read it.
 *   Call_Feed             rebuildCallFeed(), nightly 21:30
 *   Call_Recordings       Stage 1, ~02:00, archives YESTERDAY
 *   Call_Transcripts      Stage 2, ~03:00, archives YESTERDAY
 *   Followup_Escalations  sporadic — informational only, never alarms
 *   Followups_Settled     sporadic — informational only, never alarms
 *
 * WHAT IT DOES NOT DO
 *   - Writes NOTHING to any sheet. One-writer-per-table untouched.
 *   - Does not open, call, or modify WebApp.gs (D34).
 *   - Carries NO patient data. Counts, dates, tab names only.
 *
 * WHAT IT REFUSES TO DO
 *   - Never reports a clean zero for something it could not read. MISSING,
 *     EMPTY, "no dated column" and "no readable dates" each say so. (Category 6.)
 *   - Never treats silence as a pass.
 *   - If it errors, it emails the error.
 *
 * KNOWN, DELIBERATE LIMIT — read this before trusting it
 *   Call_Durations is allowed ONE day of lag, not zero. At 09:00 there may
 *   legitimately be no call yet today, and a zero-lag rule would cry wolf every
 *   morning. Cost: a receiver outage is caught on its SECOND morning, not its
 *   first (~24-36h, versus 44h unaided, versus never with v1). To close the gap,
 *   add a second trigger at 13:00 — by then a clinic day always has calls.
 *   Not built. Ask for it.
 *
 * TO ARM IT (once)
 *   Apps Script editor -> paste over the Health file -> Save
 *     Run -> testHealthReportNow      (sends one mail now)
 *     Run -> installHealthTrigger     (daily 09:00-10:00 IST)
 *   No web-app redeploy. No new OAuth scopes.
 *
 * TO DISARM        Run -> removeHealthTrigger
 * TO ROLL BACK     paste Health_v1_S128.gs.bak over this file. Neither wrote anything.
 * -----------------------------------------------------------------------------
 */

/**
 * Tabs we report on.
 *   maxLag = how many days behind today the newest row may be before it is a
 *            PROBLEM.  null = informational only, never alarms.
 */
var HEALTH_TABS = [
  { tab: 'Followups_Today',      maxLag: 0,    sched: 'pushed each morning' },
  { tab: 'Followup_Outcomes',    maxLag: 2,    sched: 'staff, through the day' },
  { tab: 'Call_Durations',       maxLag: 1,    sched: 'VPS receiver \u2014 console-dialled calls ONLY' },
  { tab: 'Call_Feed',            maxLag: 1,    sched: 'rebuilt nightly 21:30' },
  { tab: 'Call_Recordings',      maxLag: 1,    sched: 'Stage 1, ~02:00' },
  { tab: 'Call_Transcripts',     maxLag: 1,    sched: 'Stage 2, ~03:00' },
  { tab: 'Followup_Escalations', maxLag: null, sched: 'sporadic' },
  { tab: 'Followups_Settled',    maxLag: null, sched: 'sporadic' }
];

/** Header names that may carry a row's timestamp. FIRST match wins, and the
 *  winner is NAMED in the email, so a wrong pick is visible, not silent.
 *  captured_at_ist / ended_at_ist come from the VPS receiver's Call_Durations. */
var HEALTH_DATE_HEADERS = [
  'captured_at_ist', 'ended_at_ist',
  'when', 'timestamp', 'logged when', 'called when', 'call time', 'start time',
  'created', 'raised', 'due date', 'date'
];

var HEALTH_LAST_RUN_PROP = 'HEALTH_LAST_RUN';
var HEALTH_MS_DAY = 24 * 60 * 60 * 1000;

/* ========================================================================== */
/*  THE REPORT                                                                */
/* ========================================================================== */

function dailyHealthReport() {
  var tz = Session.getScriptTimeZone();
  var today = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  var problems = [];
  var lines = [];

  try {
    var ss = fuSheet_();
    if (!ss) {
      healthAlert_(true, '\u26A0\uFE0F Clinic health: CANNOT READ THE SHEET \u2014 ' + today,
        'fuSheet_() returned nothing. The tracker could not be opened at all.\n' +
        'NOTHING below was checked. Every tab is UNKNOWN. This is not a pass.\n');
      return { ok: false, reason: 'no-sheet' };
    }

    // --- 1. Did yesterday's heartbeat happen? -------------------------------
    var sp = PropertiesService.getScriptProperties();
    var lastRun = (sp.getProperty(HEALTH_LAST_RUN_PROP) || '').trim();
    var gapNote;
    if (!lastRun) {
      gapNote = 'First run \u2014 no previous heartbeat recorded.';
    } else if (lastRun !== hrYesterday_(tz) && lastRun !== today) {
      gapNote = 'GAP: last heartbeat was ' + lastRun + '. Days were missed.';
      problems.push('heartbeat gap since ' + lastRun);
    } else {
      gapNote = 'Previous heartbeat: ' + lastRun + '.';
    }

    // --- 2. Per-tab census, each against its own clock ----------------------
    for (var i = 0; i < HEALTH_TABS.length; i++) {
      var spec = HEALTH_TABS[i];
      var info = hrTabInfo_(ss, spec.tab, today, tz);
      var verdict = hrVerdict_(spec, info);
      lines.push(hrRender_(spec, info, verdict));
      if (verdict.problem) problems.push(spec.tab + ' ' + verdict.tag);
    }

    // --- 3. Is today's call list actually today's? --------------------------
    var fresh = hrFreshness_(ss, today, tz);
    lines.push('');
    lines.push("TODAY'S LIST");
    if (fresh.state === 'FRESH') {
      lines.push('  OK \u2014 newest due date on the board is ' + fresh.newest + '.');
    } else if (fresh.state === 'STALE') {
      lines.push('  STALE \u2014 the board shows ' + fresh.newest + ', not ' + today + '.');
      lines.push('  Fix on the laptop:  python push_followups_today.py --push');
      problems.push("today's list is stale");
    } else {
      lines.push('  UNKNOWN \u2014 ' + fresh.note + '. Not treated as a pass.');
      problems.push("today's list freshness UNKNOWN");
    }

    // --- 4. Doctor review backlog -------------------------------------------
    lines.push('');
    lines.push('AWAITING YOUR REVIEW');
    var rev = hrAwaitingReview_(ss, today, tz);
    if (rev.state === 'NO_COLUMNS') {
      lines.push('  Review columns do not exist yet \u2014 created the first time you');
      lines.push('  review an outcome. This is NOT the same as "zero waiting".');
    } else if (rev.state === 'NO_WHEN') {
      lines.push('  UNKNOWN \u2014 no "when" column; the queue cannot be dated.');
    } else if (rev.state === 'MISSING') {
      lines.push('  UNKNOWN \u2014 Followup_Outcomes is missing.');
    } else {
      lines.push('  Today      ' + rev.today + '   <- this is the work. Dashboard \u2192 Outcome Log.');
      lines.push('  Yesterday  ' + rev.yesterday + '   (still reachable in the dashboard)');
      lines.push('  Older      ' + rev.older + '   aged out of the review UI. NOT a queue.');
      if (rev.undated) lines.push('  Undated    ' + rev.undated + '   unreadable "when" \u2014 not counted above.');
    }

    // --- 5. Send -------------------------------------------------------------
    var bad = problems.length > 0;
    var subject = (bad ? '\u26A0\uFE0F Clinic health: ' + problems.length + ' problem(s)'
                       : '\u2705 Clinic health OK') + ' \u2014 ' + today;

    var body = ''
      + 'Daily health report \u00B7 Dr Manoj Agarwal Clinic\n'
      + 'Generated ' + Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd HH:mm') + ' IST\n'
      + gapNote + '\n'
      + '\n' + (bad ? 'PROBLEMS: ' + problems.join(' \u00B7 ') : 'No problems found.') + '\n'
      + '\n----------------------------------------------------------\n'
      + 'TABS   (lag = days behind today; each tab judged on its own schedule)\n'
      + lines.join('\n')
      + '\n----------------------------------------------------------\n'
      + '\nThis mail arrives every day. If it does not arrive, THAT is the fault:\n'
      + 'the trigger has stopped, not the clinic. Check Apps Script -> Triggers.\n'
      + '\nRead-only check. Nothing was written. No patient data appears above.\n';

    healthAlert_(bad, subject, body);
    sp.setProperty(HEALTH_LAST_RUN_PROP, today);
    Logger.log(subject + '\n' + body);
    return { ok: true, problems: problems.length };

  } catch (err) {
    var em = (err && err.message) ? err.message : String(err);
    try {
      healthAlert_(true, '\u26A0\uFE0F Clinic health check ERRORED \u2014 ' + today,
        'The daily health report could not complete.\n\nError: ' + em +
        '\n\nNothing was written. Nothing is known about the tabs today.\n');
    } catch (e2) {}
    Logger.log('dailyHealthReport ERROR: ' + em);
    return { ok: false, error: em };
  }
}

/* ========================================================================== */
/*  READERS — MISSING / EMPTY / NO-DATE-COLUMN are never rendered as zero     */
/* ========================================================================== */

function hrTabInfo_(ss, tabName, today, tz) {
  var sh = ss.getSheetByName(tabName);
  if (!sh) return { state: 'MISSING' };

  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { state: 'EMPTY', rows: 0,
                            note: (lastRow < 1 ? 'no header row' : 'header only') };

  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]
               .map(function (x) { return String(x).trim().toLowerCase(); });

  var dcol = -1, dname = '';
  for (var h = 0; h < HEALTH_DATE_HEADERS.length && dcol < 0; h++) {
    var idx = head.indexOf(HEALTH_DATE_HEADERS[h]);
    if (idx >= 0) { dcol = idx; dname = HEALTH_DATE_HEADERS[h]; }
  }

  var rows = lastRow - 1;
  if (dcol < 0) return { state: 'NO_DATE_COL', rows: rows };

  var col = sh.getRange(2, dcol + 1, rows, 1).getValues();
  var todayRows = 0, newest = '';
  for (var r = 0; r < col.length; r++) {
    var ds = hrDayString_(col[r][0], tz);
    if (!ds) continue;
    if (ds === today) todayRows++;
    if (!newest || ds > newest) newest = ds;
  }
  if (!newest) return { state: 'NO_DATES', rows: rows, dateCol: dname };

  return { state: 'OK', rows: rows, todayRows: todayRows, newest: newest,
           dateCol: dname, lag: hrLagDays_(today, newest) };
}

/** Judge one tab against its own schedule. Informational tabs never alarm. */
function hrVerdict_(spec, info) {
  if (info.state === 'MISSING')     return { problem: true, tag: 'MISSING' };
  if (info.state === 'EMPTY')       return { problem: spec.maxLag !== null, tag: 'EMPTY' };
  if (info.state === 'NO_DATE_COL') return { problem: spec.maxLag !== null,
                                             tag: 'UNREADABLE (no dated column)' };
  if (info.state === 'NO_DATES')    return { problem: spec.maxLag !== null,
                                             tag: 'UNREADABLE (no parseable dates)' };
  if (spec.maxLag === null)         return { problem: false, tag: 'info' };
  if (info.lag > spec.maxLag)       return { problem: true, tag: 'STALE by ' + info.lag + 'd' };
  return { problem: false, tag: 'ok' };
}

function hrRender_(spec, info, verdict) {
  var pad = function (s, n) { s = String(s); while (s.length < n) s += ' '; return s; };
  var name = '  ' + pad(spec.tab, 22);
  var sched = '   (' + spec.sched + ')';

  if (info.state === 'MISSING')     return name + 'MISSING \u2014 the tab is not there.' + sched;
  if (info.state === 'EMPTY')       return name + 'EMPTY (' + info.note + ')' + sched;
  if (info.state === 'NO_DATE_COL') return name + 'rows=' + info.rows +
      '  \u2014 no dated column; freshness CANNOT be judged' + sched;
  if (info.state === 'NO_DATES')    return name + 'rows=' + info.rows +
      '  \u2014 column "' + info.dateCol + '" has no readable dates' + sched;

  var mark = verdict.problem ? 'STALE by ' + info.lag + 'd  <<<'
           : (spec.maxLag === null ? 'info' : 'lag=' + info.lag + 'd ok');
  return name + pad('rows=' + info.rows, 12) + pad('today=' + info.todayRows, 10) +
         pad('newest=' + info.newest, 18) + pad(mark, 20) +
         '[by "' + info.dateCol + '"]' + sched;
}

/** Whole days between two yyyy-MM-dd strings. Future rows count as lag 0. */
function hrLagDays_(today, newest) {
  var a = new Date(today + 'T00:00:00');
  var b = new Date(newest + 'T00:00:00');
  var d = Math.round((a.getTime() - b.getTime()) / HEALTH_MS_DAY);
  return d > 0 ? d : 0;
}

function hrFreshness_(ss, today, tz) {
  var sh = ss.getSheetByName(FU_TAB_TODAY);
  if (!sh) return { state: 'UNKNOWN', note: FU_TAB_TODAY + ' is missing' };
  var rows = fuReadObjects_(ss, FU_TAB_TODAY);
  if (!rows.length) return { state: 'UNKNOWN', note: FU_TAB_TODAY + ' has no rows' };

  var newestEpoch = 0;
  for (var i = 0; i < rows.length; i++) {
    var t = sentParseDate_(rows[i]['due date'] || rows[i]['due'] || '');
    if (t && t > newestEpoch) newestEpoch = t;
  }
  if (!newestEpoch) return { state: 'UNKNOWN', note: 'no parseable due dates' };
  var newest = Utilities.formatDate(new Date(newestEpoch), tz, 'yyyy-MM-dd');
  return { state: (newest >= today) ? 'FRESH' : 'STALE', newest: newest };
}

/** Outcomes logged but not yet reviewed, split by what the dashboard can REACH.
 *  getOutcomeLog(key, day) only ever serves 'today' or 'yesterday'. Older
 *  un-reviewed rows are not a backlog you can work -- they aged out of the UI.
 *  Reporting one lump total invites the doctor to fight a queue that does not
 *  exist. Absent columns are NOT zero. */
function hrAwaitingReview_(ss, today, tz) {
  var sh = ss.getSheetByName(FU_TAB_OUTCOMES);
  if (!sh) return { state: 'MISSING' };
  var lastRow = sh.getLastRow();
  if (lastRow < 2) return { state: 'OK', today: 0, yesterday: 0, older: 0 };

  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0]
               .map(function (x) { return String(x).trim().toLowerCase(); });
  var rc = head.indexOf('doctor review');
  if (rc < 0) return { state: 'NO_COLUMNS' };
  var wc = head.indexOf('when');
  if (wc < 0) return { state: 'NO_WHEN' };

  var yday = hrYesterday_(tz);
  var vals = sh.getRange(2, 1, lastRow - 1, sh.getLastColumn()).getValues();
  var t = 0, y = 0, o = 0, undated = 0;
  for (var r = 0; r < vals.length; r++) {
    if (String(vals[r][rc]).trim() !== '') continue;      // already reviewed
    var ds = hrDayString_(vals[r][wc], tz);
    if (!ds) { undated++; continue; }
    if (ds === today) t++; else if (ds === yday) y++; else o++;
  }
  return { state: 'OK', today: t, yesterday: y, older: o, undated: undated };
}

/* ========================================================================== */
/*  HELPERS                                                                   */
/* ========================================================================== */

/** A cell -> 'yyyy-MM-dd', or '' if unreadable as a date. */
function hrDayString_(v, tz) {
  if (v instanceof Date) return Utilities.formatDate(v, tz, 'yyyy-MM-dd');
  var s = String(v == null ? '' : v).trim();
  if (!s) return '';
  var m = s.match(/^(\d{4}-\d{2}-\d{2})/);       // ISO, with or without a time
  if (m) return m[1];
  var t = sentParseDate_(s);                      // 09-Jul-2026 etc (Diagnostics.gs)
  return t ? Utilities.formatDate(new Date(t), tz, 'yyyy-MM-dd') : '';
}

function hrYesterday_(tz) {
  var d = new Date(); d.setDate(d.getDate() - 1);
  return Utilities.formatDate(d, tz, 'yyyy-MM-dd');
}

/** Email always. ntfy phone-push only on a problem, so green never buzzes. */
function healthAlert_(isProblem, subject, body) {
  var sp = PropertiesService.getScriptProperties();
  var to = (sp.getProperty('SENTINEL_ALERT_EMAIL')
            || ((typeof CFG !== 'undefined' && CFG.EMAIL_TO) ? CFG.EMAIL_TO : '')).trim();
  if (to) { try { MailApp.sendEmail(to, subject, body); } catch (e) {} }

  if (!isProblem) return;
  var ntfy = (sp.getProperty('NTFY_TOPIC_URL') || '').trim();
  if (!ntfy) return;
  try {
    UrlFetchApp.fetch(ntfy, {
      method: 'post',
      payload: body.slice(0, 800),
      headers: { 'Title': subject.replace(/[^\x20-\x7E]/g, '').trim() || 'Clinic health',
                 'Priority': 'default', 'Tags': 'hospital' },
      muteHttpExceptions: true
    });
  } catch (e) {}
}

/* ========================================================================== */
/*  ARM / DISARM / TEST                                                       */
/* ========================================================================== */

function testHealthReportNow() {
  return 'sent \u2014 ' + JSON.stringify(dailyHealthReport());
}

function installHealthTrigger() {
  removeHealthTrigger();
  ScriptApp.newTrigger('dailyHealthReport')
    .timeBased().atHour(9).everyDays(1)
    .inTimezone(Session.getScriptTimeZone())
    .create();
  return 'installed: dailyHealthReport, daily 09:00-10:00 IST';
}

function removeHealthTrigger() {
  var all = ScriptApp.getProjectTriggers(), n = 0;
  for (var i = 0; i < all.length; i++) {
    if (all[i].getHandlerFunction() === 'dailyHealthReport') {
      ScriptApp.deleteTrigger(all[i]); n++;
    }
  }
  return 'removed ' + n + ' trigger(s)';
}
