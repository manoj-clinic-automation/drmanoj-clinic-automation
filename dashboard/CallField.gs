/**
 * CallFeed.gs — Dr. Manoj Agarwal Clinic
 * ---------------------------------------------------------------------------
 * ONE name-free feed for the Follow-Up Tracker, serving both call features:
 *   • outgoing calls   -> telephony reconciliation (Call Audit)
 *   • incoming MISSED  -> "Called In & Due" worklist
 *
 * Emits a "Call_Feed" tab, one row per call:
 *   Date · Time · Phone10 · Direction · Agent · Duration_s · Status · Start_Unix
 * No patient names, no diagnosis — just phone + agent + status. The tracker joins
 * this to patient identity LOCALLY, so PHI never leaves the clinic.
 *
 * This SUPERSEDES OutboundLog.gs. After installing this, delete OutboundLog.gs (or
 * at least remove its trigger). installCallFeedTrigger() removes the old
 * rebuildOutboundLog trigger automatically so you don't get two refreshes.
 *
 * Reuses the project's existing helpers: fetchCallsBetween_, callAgentInfo_,
 * getOrCreateTab_, last10_, hhmmssToSeconds_. Changes nothing else.
 *
 * HOW TO USE
 *   1. Add this file to the call-logs Apps Script project (＋ → Script → paste).
 *   2. Run rebuildCallFeed once (authorise if prompted) → confirm the Call_Feed tab.
 *   3. installCallFeedTrigger() once → refreshes ~21:30 daily (after the 9 PM close).
 *   4. Publish JUST this tab: File → Share → Publish to web → "Call_Feed" → CSV →
 *      copy the link. Paste that link into the tracker file  data\feed_url.txt .
 *      After that the tracker pulls it automatically — no download, no upload.
 */

var TAB_CALLFEED   = 'Call_Feed';
var CALLFEED_HEADERS = ['Date', 'Time', 'Phone10', 'Direction', 'Agent',
                        'Duration_s', 'Status', 'Start_Unix'];
var CALLFEED_DEFAULT_DAYS = 14;

/** Build feed rows: all OUTGOING calls + INCOMING calls that were MISSED. */
function callFeedRows_(raw) {
  var tz = Session.getScriptTimeZone();
  var rows = [];
  raw.forEach(function (r) {
    var isOut = (String(r.direction) === 'outgoing') || (String(r.event) === '2');
    var isIn  = (String(r.direction) === 'incoming') || (String(r.event) === '1');
    var missed = (r.is_missed === true) || String(r.status) === '2';
    if (!isOut && !(isIn && missed)) return;        // keep outgoing(all) + incoming(missed)

    var num = r.phone10 || last10_(r.caller_number_raw || r.caller_number || '');
    if (!num) return;
    var startSec = Number(r.start_time) || 0;
    var ts = startSec ? new Date(startSec * 1000) : null;
    var info = callAgentInfo_(r);
    var dur = (r.duration_seconds != null) ? r.duration_seconds : hhmmssToSeconds_(r.duration);
    rows.push([
      ts ? Utilities.formatDate(ts, tz, 'yyyy-MM-dd') : '',
      ts ? Utilities.formatDate(ts, tz, 'HH:mm') : '',
      "'" + num,
      isOut ? 'outgoing' : 'incoming',
      info.agent || '',
      dur,
      missed ? 'missed' : 'connected',
      startSec
    ]);
  });
  rows.sort(function (a, b) { return Number(b[7]) - Number(a[7]); });   // newest first
  return rows;
}

/** Clear + rewrite Call_Feed for [startDate, endDate]. Returns row count. */
function writeCallFeed_(startDate, endDate) {
  var raw = fetchCallsBetween_(startDate, endDate);
  var rows = callFeedRows_(raw);
  var sh = getOrCreateTab_(TAB_CALLFEED, CALLFEED_HEADERS);
  var last = sh.getLastRow();
  if (last > 1) sh.getRange(2, 1, last - 1, CALLFEED_HEADERS.length).clearContent();
  if (rows.length) sh.getRange(2, 1, rows.length, CALLFEED_HEADERS.length).setValues(rows);
  return rows.length;
}

/** PUBLIC — rebuild Call_Feed for the last N days (default 14). Idempotent. */
function rebuildCallFeed(daysBack) {
  daysBack = daysBack || CALLFEED_DEFAULT_DAYS;
  var tz = Session.getScriptTimeZone();
  var now = new Date();
  var end = new Date(Utilities.formatDate(now, tz, 'yyyy/MM/dd') + ' 23:59:59');
  var startYmd = Utilities.formatDate(
    new Date(end.getTime() - (daysBack - 1) * 24 * 3600 * 1000), tz, 'yyyy/MM/dd');
  var start = new Date(startYmd + ' 00:00:00');
  var n = writeCallFeed_(start, end);
  Logger.log('Call_Feed rebuilt: %s row(s) over the last %s day(s).', n, daysBack);
  return n;
}

/** Manual: rebuild now and log the count. */
function testCallFeedNow() {
  var n = rebuildCallFeed(CALLFEED_DEFAULT_DAYS);
  Logger.log('Done. Open the "%s" tab — %s rows.', TAB_CALLFEED, n);
}

/** Optional: daily END-OF-DAY refresh (~21:30). Removes any old rebuildOutboundLog
 *  trigger and any existing rebuildCallFeed trigger first, so you never double up. */
function installCallFeedTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    var h = t.getHandlerFunction();
    if (h === 'rebuildCallFeed' || h === 'rebuildOutboundLog') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('rebuildCallFeed').timeBased().atHour(21).nearMinute(30).everyDays(1).create();
  Logger.log('Installed daily Call_Feed refresh (~21:30 %s).', Session.getScriptTimeZone());
}
