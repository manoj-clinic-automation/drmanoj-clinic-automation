/* ============================================================================
 *  VPS_Push_Lab.gs  -  S330 (session 271, 19-Sep-2026)
 *  Lives in the UPIReconciliation Apps Script project of drmka.ortho@gmail.com,
 *  beside VPS_Push_UPI.gs, and uses the SAME script property FINANCE_VPS_TOKEN.
 *
 *  WHAT IT DOES. NK Pathology e-mails every report to this mailbox with the clinic
 *  ID in the subject:  "Your Report   MRS. <name> ( 8118)". Every 15 minutes this
 *  tells the clinic server ONLY: the message id, the clinic ID, the time received.
 *  Never the name, never the file. The server puts the report in reception's
 *  Docterz-upload list and closes the blood-test order for that ID.
 *
 *  ONE TIME:  add this as a new file in the project, Save, choose  setupLabPush
 *  in the function box and press Run (allow access when Google asks).
 *  It installs the 15-minute trigger and sends the reports since 18-Sep.
 *  verifyLabPush() says whether the token and the trigger are in place.
 * ========================================================================== */

var LAB_VPS_URL = 'https://followup.dr-manoj.in/finance/slips/api/lab-report';
var LAB_SEARCH  = 'from:nkpathology@gmail.com subject:(Your Report) newer_than:4d';
var LAB_FIRST   = 'from:nkpathology@gmail.com subject:(Your Report) after:2026/09/17';
var LAB_TIME_MS = 4.5 * 60 * 1000;

function verifyLabPush() {
  var props = PropertiesService.getScriptProperties();
  var tok = props.getProperty('FINANCE_VPS_TOKEN');
  var trig = ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === 'pushLabReports'; });
  var sent = props.getKeys().filter(function (k) { return k.indexOf('lab_pushed_') === 0; }).length;
  var msg = 'FINANCE_VPS_TOKEN : ' + (tok ? ('present, ' + tok.length + ' chars') : '*** MISSING ***')
          + '\nlab trigger       : ' + (trig.length ? 'installed (every 15 min)' : '*** NONE ***')
          + '\nreports sent ever : ' + sent;
  Logger.log(msg);
  return msg;
}

function setupLabPush() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'pushLabReports') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('pushLabReports').timeBased().everyMinutes(15).create();
  _labPush(LAB_FIRST);
  return verifyLabPush();
}

function pushLabReports() { _labPush(LAB_SEARCH); }

function _labPush(query) {
  var started = Date.now();
  var props = PropertiesService.getScriptProperties();
  var tok = props.getProperty('FINANCE_VPS_TOKEN');
  if (!tok) { Logger.log('FINANCE_VPS_TOKEN missing - nothing sent'); return; }
  var tz = 'Asia/Kolkata';
  var batch = [], keys = [];
  var threads = GmailApp.search(query, 0, 200);
  for (var i = 0; i < threads.length && Date.now() - started < LAB_TIME_MS; i++) {
    var msgs = threads[i].getMessages();
    for (var j = 0; j < msgs.length; j++) {
      var m = msgs[j];
      var k = 'lab_pushed_' + m.getId();
      if (props.getProperty(k)) continue;
      var mt = /\(\s*([0-9]{1,8})\s*\)\s*$/.exec(m.getSubject() || '');
      if (!mt || m.getFrom().indexOf('nkpathology@gmail.com') < 0) continue;
      batch.push({ msg_id: m.getId(), clinic_id: mt[1],
                   received_at: Utilities.formatDate(m.getDate(), tz, "yyyy-MM-dd HH:mm:ss") });
      keys.push(k);
    }
  }
  if (!batch.length) return;
  for (var s = 0; s < batch.length; s += 100) {
    var part = batch.slice(s, s + 100);
    var r = UrlFetchApp.fetch(LAB_VPS_URL, { method: 'post', contentType: 'application/json',
      payload: JSON.stringify({ reports: part }), headers: { 'X-Finance-Cron': tok }, muteHttpExceptions: true });
    if (r.getResponseCode() !== 200) { Logger.log('server said ' + r.getResponseCode() + ' - will retry next run'); return; }
    for (var x = s; x < s + part.length; x++) props.setProperty(keys[x], '1');
  }
  Logger.log('sent ' + batch.length + ' report notice(s)');
}
