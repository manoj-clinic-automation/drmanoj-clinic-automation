/**
 * Diagnostics.gs  —  clinic-automation self-checks (Session 53)
 * -----------------------------------------------------------------------------
 * FIRST CHECK: the follow-up "stale list" guard — the exact protection for the
 * morning incident that has now recurred twice (today's list generated overnight
 * but never reaching the dashboard, so staff would call yesterday's patients).
 *
 * WHAT IT ANSWERS (once a day, before the 3 PM calling window):
 *   "Did TODAY'S follow-up list actually reach the dashboard?"
 * It separates the two real failure modes we have seen:
 *   1) GENERATION MISSING — today's Staff_Action_Today_<date>.xlsx was never
 *      produced (the tracker/laptop didn't run).
 *   2) NOT PUSHED — the file exists, but the live Followups_Today tab still shows
 *      an older day (the watcher/push didn't run). Fix: python push_followups_today.py --push
 *
 * SAFETY: strictly READ-ONLY. No sheet is written, no writer is touched. It reuses
 * existing helpers (fuSheet_, fuReadObjects_, dateVal_, FU_TAB_TODAY, CFG). If the
 * check itself errors, it ALERTS about that too — a silent guard is worse than none.
 * No patient data ever leaves this file: alerts carry counts and dates only.
 *
 * ALERTS: email always (CFG.EMAIL_TO, or a SENTINEL_ALERT_EMAIL Script Property);
 * plus an ntfy phone-push if a Script Property NTFY_TOPIC_URL is set (optional).
 *
 * TO ARM IT (owner, once — no web-app redeploy needed):
 *   Apps Script editor -> Triggers (clock icon) -> Add Trigger
 *     function: checkFollowupListFresh
 *     event source: Time-driven -> Day timer -> 2pm to 3pm
 *   (First run will ask you to authorize Mail + Drive access — approve once.)
 *   Test the alert first: Run -> testSentinelAlert -> check your phone.
 * -----------------------------------------------------------------------------
 */

var SENTINEL_FILE_PREFIX = 'Staff_Action_Today_';   // + yyyy-MM-dd + '.xlsx'
var SENTINEL_MONTHS = { jan:0, feb:1, mar:2, apr:3, may:4, jun:5,
                        jul:6, aug:7, sep:8, oct:9, nov:10, dec:11 };

/** Parse a due-date cell to epoch ms. The push writes "DD-Mon-YYYY" (e.g.
 *  "03-Jul-2026"); this also handles a real Date object or an ISO string,
 *  and returns 0 on anything unparseable. */
function sentParseDate_(v) {
  if (v instanceof Date) return v.getTime();
  var s = String(v == null ? '' : v).trim();
  if (!s) return 0;
  var m = s.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);   // 03-Jul-2026
  if (m) {
    var mon = SENTINEL_MONTHS[m[2].toLowerCase()];
    if (mon != null) return new Date(parseInt(m[3], 10), mon, parseInt(m[1], 10)).getTime();
  }
  try { return dateVal_(s); } catch (e) { return 0; }     // ISO / other parseable
}

function sentDateStr_(epoch, tz) {
  return epoch ? Utilities.formatDate(new Date(epoch), tz, 'yyyy-MM-dd') : '';
}

/**
 * The guard itself. Returns a small status object (for the editor log) and fires
 * an alert only when something is wrong.
 */
function checkFollowupListFresh() {
  var tz = Session.getScriptTimeZone();
  var todayStr = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  var res = { ok: false, today: todayStr, fileFound: null, rows: 0,
              newestDue: '', fresh: false, alerted: false, note: '' };
  try {
    // 1) Was today's list GENERATED?  (search Drive by the day's exact filename)
    var wantName = SENTINEL_FILE_PREFIX + todayStr + '.xlsx';
    try {
      res.fileFound = DriveApp.getFilesByName(wantName).hasNext();
    } catch (eDrive) {
      res.fileFound = null;                 // Drive not authorized yet -> "unknown", never false-alarm
      res.note += 'drive-skipped ';
    }

    // 2) Does the live Followups_Today tab REFLECT today?  (newest Due Date)
    var ss = fuSheet_();
    var newestEpoch = 0;
    if (ss) {
      var rows = fuReadObjects_(ss, FU_TAB_TODAY);
      res.rows = rows.length;
      for (var i = 0; i < rows.length; i++) {
        var t = sentParseDate_(rows[i]['due date'] || rows[i]['due'] || '');
        if (t && t > newestEpoch) newestEpoch = t;
      }
    } else {
      res.note += 'no-sheet ';
    }
    var newestStr = sentDateStr_(newestEpoch, tz);
    res.newestDue = newestStr;
    res.fresh = !!newestStr && (newestStr >= todayStr);   // yyyy-MM-dd strings sort chronologically

    // 3) Decide + alert (only on a problem)
    var msg = '';
    if (res.fileFound === false) {
      msg = 'GENERATION MISSING: today\'s follow-up list (' + todayStr + ') was not generated.\n'
          + 'Check the tracker on the laptop, then run the push.';
    } else if (!res.fresh) {
      msg = 'LIST STALE: today\'s list (' + todayStr + ') has NOT reached the dashboard.\n'
          + 'The board still shows ' + (newestStr || 'no dated rows') + '.\n'
          + 'Fix on the laptop:  python push_followups_today.py --push';
    }
    if (msg) {
      sentinelAlert_('\u26A0\uFE0F Follow-up list check', msg);
      res.alerted = true; res.note += 'ALERT';
    } else {
      res.note += 'fresh-ok';
    }
    res.ok = true;
    Logger.log(JSON.stringify(res));
    return res;
  } catch (err) {
    // a broken guard must not fail silently
    var em = (err && err.message) ? err.message : String(err);
    try { sentinelAlert_('\u26A0\uFE0F Sentinel could not run', 'The follow-up list check errored: ' + em); } catch (e2) {}
    res.note += 'ERROR:' + em;
    Logger.log(JSON.stringify(res));
    return res;
  }
}

/** Send the alert by email (always) + ntfy phone-push (if configured).
 *  No patient data — counts and dates only. */
function sentinelAlert_(subject, body) {
  var sp = PropertiesService.getScriptProperties();
  var to = (sp.getProperty('SENTINEL_ALERT_EMAIL')
            || ((typeof CFG !== 'undefined' && CFG.EMAIL_TO) ? CFG.EMAIL_TO : '')).trim();
  var full = body + '\n\n(Automated check \u00B7 Dr Manoj Agarwal Clinic)';
  if (to) { try { MailApp.sendEmail(to, subject, full); } catch (e) {} }

  var ntfy = (sp.getProperty('NTFY_TOPIC_URL') || '').trim();
  if (ntfy) {
    try {
      UrlFetchApp.fetch(ntfy, {
        method: 'post',
        payload: body,
        headers: {
          'Title':    subject.replace(/[^\x20-\x7E]/g, '').trim() || 'Clinic alert',
          'Priority': 'high',
          'Tags':     'warning'
        },
        muteHttpExceptions: true
      });
    } catch (e) {}
  }
}

/** One-tap test: Run this from the editor to confirm the alert reaches your phone. */
function testSentinelAlert() {
  sentinelAlert_('\u2705 Sentinel test',
    'This is a test alert. If you can read this on your phone, the follow-up list guard is wired correctly.');
  var hasNtfy = !!(PropertiesService.getScriptProperties().getProperty('NTFY_TOPIC_URL') || '').trim();
  return 'test sent (email' + (hasNtfy ? ' + ntfy' : ' only \u2014 set NTFY_TOPIC_URL for phone push') + ')';
}
