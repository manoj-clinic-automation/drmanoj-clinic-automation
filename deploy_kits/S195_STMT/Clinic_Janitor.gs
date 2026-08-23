/** ==========================================================================
 *  Clinic_Janitor.gs · S195 · CLINIC account (drmka.ortho@)
 *  Paste as a NEW file in the "UPI Reconciliation" GAS project, beside
 *  VPS_Push_UPI and Bank_Statement_Filer. Names are cj_-prefixed so nothing
 *  collides with those files (GAS merges all files into one namespace).
 *
 *  WHY: the clinic inbox holds 200+ threads, dominated by ICICI merchant
 *  statements (5/day to three addresses). Every consumer of that mail reads
 *  by SEARCH, not by inbox: VPS_Push_UPI (newer_than:10d, any folder) and
 *  Bank_Statement_Filer (label-excluded, any folder). So archiving cleans
 *  the inbox and breaks NOTHING — verified against both scripts' queries.
 *
 *  DELIBERATELY CONSERVATIVE: this janitor NEVER trashes anything, and it
 *  never touches a mail that is not in a class it positively recognises.
 *  [Clinic Finance] ALERTS are deliberately NOT handled — an alert should
 *  sit in the inbox until a human sees it.
 *
 *  SETUP: run cjSetup() once (installs the daily 08-09 trigger).
 *  Backlog: run cjSweepBacklogOnce() repeatedly until every count is 0.
 *  Composition report (to tune future rules): cjSurveyInbox().
 *  ========================================================================== */

var CJ_DONE = 'Clinic-Janitor-Done';

var CJ_RULES = [
  { name: 'ICICI merchant statements',
    // consumed by VPS_Push_UPI via search — archiving is safe (see header)
    query: 'from:merchantsolutions', label: 'ICICI-MPR',
    markRead: true, archiveAfterDays: 2 },
  { name: 'bank statements already filed',
    // only ones Bank_Statement_Filer has ALREADY processed (its own label)
    query: 'label:stmt-filed subject:"[STMT]"', label: null,
    markRead: true, archiveAfterDays: 3 },
  { name: 'UPI reconciliation daily reports',
    query: 'subject:"UPI reconciliation" from:me', label: 'Reports',
    markRead: true, archiveAfterDays: 7 },
  { name: 'google security alerts',
    query: 'from:no-reply@accounts.google.com subject:"security alert"',
    label: null, markRead: true, archiveAfterDays: 7 }
];

function cjSetup() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'cjRun') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('cjRun').timeBased().atHour(8).everyDays(1).create();
  Logger.log('daily trigger installed; first run: ' + cjRun());
}

function cjRun() {
  var done = GmailApp.getUserLabelByName(CJ_DONE) || GmailApp.createLabel(CJ_DONE);
  var totals = [];
  CJ_RULES.forEach(function (rule) {
    var label = rule.label ? (GmailApp.getUserLabelByName(rule.label)
                              || GmailApp.createLabel(rule.label)) : null;
    // pass 1: label/mark new arrivals (never archives fresh mail)
    var fresh = GmailApp.search(rule.query + ' -label:'
                                + CJ_DONE.toLowerCase(), 0, 100);
    fresh.forEach(function (th) {
      if (label) th.addLabel(label);
      if (rule.markRead) th.markRead();
      th.addLabel(done);
    });
    // pass 2: age out of the inbox once old enough
    var aged = GmailApp.search(rule.query + ' in:inbox older_than:'
                               + rule.archiveAfterDays + 'd', 0, 100);
    aged.forEach(function (th) { th.moveToArchive(); });
    totals.push(rule.name + ': ' + fresh.length + ' new, ' + aged.length + ' archived');
  });
  var msg = totals.join(' | ');
  Logger.log(msg);
  return msg;
}

/** Run repeatedly until every 'archived' count is 0 — drains the backlog. */
function cjSweepBacklogOnce() {
  return cjRun();
}

/** Who actually fills this inbox — top senders of the last 200 inbox threads.
 *  Read-only; use it to decide the next rule instead of guessing. */
function cjSurveyInbox() {
  var counts = {};
  GmailApp.search('in:inbox', 0, 200).forEach(function (th) {
    var m = th.getMessages()[0];
    var f = (m.getFrom().match(/@([a-z0-9.-]+)/i) || [, '?'])[1].toLowerCase();
    counts[f] = (counts[f] || 0) + 1;
  });
  var rows = Object.keys(counts).map(function (k) { return [counts[k], k]; })
    .sort(function (a, b) { return b[0] - a[0]; })
    .map(function (r) { return r[0] + '  ' + r[1]; });
  Logger.log('inbox senders (top of last 200 threads):\n' + rows.join('\n'));
  return rows.join('\n');
}
