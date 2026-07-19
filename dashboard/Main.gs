/**
 * Main.gs — entry points and triggers.
 *
 * Functions you call by name:
 *   probeApi()            (MyOperator.gs) — verify the API response once
 *   testIntradayNow()     — run today's digest + rebuild the monitor now
 *   testMonitorNow()      (Monitor.gs)    — rebuild only the monitor tab now
 *   testSummaryEmailNow() (Monitor.gs)    — send ONE summary email now
 *   testMorningNow()      — run yesterday's report now
 *   setupTriggers()       — install all time triggers (run once)
 *   removeTriggers()      — uninstall ONLY Main's three (D206; never touches other files' triggers)
 *
 * Triggers call: runIntradayDigest(), runSummaryEmail(), runMorningReport()
 */

/** Start/end Date for a given local calendar day offset (0 = today, -1 = yesterday). */
function dayBounds_(offsetDays) {
  var tz = Session.getScriptTimeZone();
  var now = new Date();
  var ymd = Utilities.formatDate(
    new Date(now.getTime() + offsetDays * 24 * 3600 * 1000), tz, 'yyyy/MM/dd');
  var start = new Date(ymd + ' 00:00:00');
  var end = new Date(start.getTime() + 24 * 3600 * 1000 - 1000);
  return { start: start, end: end, label: Utilities.formatDate(start, tz, 'yyyy-MM-dd') };
}

/** TRIGGER: refresh today's live callback list AND the monitor. Self-skips outside the schedule. */
function runIntradayDigest() {
  var now = new Date();
  if (now.getDay() === 0 && now.getHours() > CFG.SUNDAY_LAST_HOUR) return; // Sunday closes at 2 pm

  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  upsertCallbacksToday_(result.entries);
  buildMonitorTab_(raw, result);
}

/** TRIGGER: send the summary email (fires at each hour in CFG.EMAIL_HOURS). */
function runSummaryEmail() {
  var now = new Date();
  if (now.getDay() === 0 && now.getHours() > CFG.SUNDAY_LAST_HOUR) return; // skip late Sunday
  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  var label = Utilities.formatDate(now, Session.getScriptTimeZone(), 'd MMM, h:mm a');
  sendSummaryEmail_(raw, result, label);
}

/** TRIGGER: write the complete prior-day report, then reset the live tab. */
function runMorningReport() {
  var b = dayBounds_(-1);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  writeDailyReport_(b.label, result);
  archiveAndResetCallbacks_();
}

/** Manual: run today's digest + monitor now (no schedule gate). */
function testIntradayNow() {
  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  var n = upsertCallbacksToday_(result.entries);
  buildMonitorTab_(raw, result);
  Logger.log('Today: %s calls, %s incoming, %s net-missed, %s resolved. Wrote %s callback rows + rebuilt monitor.',
             result.stats.totalCalls, result.stats.incomingCount,
             result.stats.netMissed, result.stats.resolved, n);
}

/** Manual: run yesterday's report now. */
function testMorningNow() {
  var b = dayBounds_(-1);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  writeDailyReport_(b.label, result);
  Logger.log('%s report: %s net-missed of %s incoming (%s total calls).',
             b.label, result.stats.netMissed, result.stats.incomingCount, result.stats.totalCalls);
}

/** Install all time triggers. Safe to re-run (clears old ones first). */
function setupTriggers() {
  removeTriggers();
  CFG.INTRADAY_HOURS.forEach(function (h) {
    ScriptApp.newTrigger('runIntradayDigest').timeBased().atHour(h).everyDays(1).create();
  });
  CFG.EMAIL_HOURS.forEach(function (h) {
    ScriptApp.newTrigger('runSummaryEmail').timeBased().atHour(h).everyDays(1).create();
  });
  ScriptApp.newTrigger('runMorningReport').timeBased()
           .atHour(CFG.MORNING_REPORT_HOUR).nearMinute(30).everyDays(1).create();
  Logger.log('Installed %s intraday + %s email + 1 morning trigger (TZ %s).',
             CFG.INTRADAY_HOURS.length, CFG.EMAIL_HOURS.length, Session.getScriptTimeZone());
}

/** Remove ONLY the triggers Main.gs owns (D206). Other files' triggers
 *  (dailyHealthReport, rebuildCallFeed, sendFollowupSummary, checkFollowupListFresh)
 *  are NEVER touched — each file cleans up after itself, like removeHealthTrigger. */
function removeTriggers() {
  var MINE = { runIntradayDigest: 1, runSummaryEmail: 1, runMorningReport: 1 };
  var all = ScriptApp.getProjectTriggers(), n = 0;
  for (var i = 0; i < all.length; i++) {
    if (MINE[all[i].getHandlerFunction()] === 1) { ScriptApp.deleteTrigger(all[i]); n++; }
  }
  Logger.log('removeTriggers: removed %s of Main\'s own trigger(s); all others untouched.', n);
  return 'removed ' + n + ' trigger(s) (Main.gs owns runIntradayDigest / runSummaryEmail / runMorningReport only)';
}