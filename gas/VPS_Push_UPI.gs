/** ==========================================================================
 *  VPS_Push_UPI.gs  ·  Session 179 · B5
 *  Dr. Manoj Agarwal Clinic — pushes the daily ICICI Merchant (MPR) statements
 *  from the clinic Gmail to the VPS finance app.
 *
 *  WHAT IT IS
 *    A NEW, self-contained script file. It reads Gmail and POSTs files out.
 *    It does not touch, call, or depend on any existing function in this
 *    account — Daily Clinic Reports and UPI Reconciliation keep running
 *    exactly as they do today, in parallel.
 *
 *  WHAT IT DOES, EACH MORNING
 *    1. Finds recent mails from merchantsolutions@icici.bank.in.
 *    2. Takes every *_ICICI_POS_CD.xlsx attachment for the three known
 *       merchant IDs (Sanjeevni / Clinic / NK Pathology). The .zip duplicate
 *       that arrives an hour later is ignored.
 *    3. POSTs each file, once, to the VPS:
 *          POST https://followup.dr-manoj.in/finance/api/upi-statement
 *          header  X-Finance-Cron: <token>
 *       The VPS parses it, verifies it against the file's own Grand Total,
 *       stores settled UPI per unit per day, and flags any day whose entered
 *       UPI disagrees with the bank.
 *    4. Remembers each pushed file in Script Properties so nothing is ever
 *       sent twice, and emails the doctor ONLY if a push fails.
 *
 *  FAILURE DIRECTION (deliberate): if this script breaks, statements simply
 *  stop arriving and days stay UNRECONCILED AND FLAGGED on the doctor's
 *  screen. Nothing is ever wrongly cleared by silence.
 *
 *  ONE-TIME SETUP (in this GAS project):
 *    1. Paste this file as a new script file.
 *    2. Project Settings -> Script Properties -> add:
 *         FINANCE_VPS_TOKEN = <the token printed by the VPS installer>
 *       (The token lives HERE, never in this code, never in git — F-31.)
 *    3. Run setupUpiPush() once. It installs the daily 09:30 trigger and does
 *       a first push immediately so you see it work.
 *  ========================================================================== */

var UPI_VPS_URL = 'https://followup.dr-manoj.in/finance/api/upi-statement';
var UPI_MIDS = ['100000000312505', '100000000306941', '100000000319164'];
var UPI_SEARCH = 'from:merchantsolutions@icici.bank.in newer_than:3d';
var UPI_ALERT_TO = 'drmanojkragarwal@gmail.com';

function setupUpiPush() {
  // remove any older trigger of ours, then install 09:30 daily
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'pushUpiStatements') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('pushUpiStatements').timeBased().atHour(9).nearMinute(30)
    .everyDays(1).create();
  var out = pushUpiStatements();
  Logger.log('setup done; first run: ' + JSON.stringify(out));
}

function pushUpiStatements() {
  var token = PropertiesService.getScriptProperties().getProperty('FINANCE_VPS_TOKEN');
  if (!token) {
    _upiAlert('UPI push NOT configured',
              'FINANCE_VPS_TOKEN is missing from Script Properties. No statement was pushed.');
    return { ok: false, error: 'no token' };
  }

  var props = PropertiesService.getScriptProperties();
  var pushed = 0, skipped = 0, failed = [];

  var threads = GmailApp.search(UPI_SEARCH, 0, 30);
  threads.forEach(function (th) {
    th.getMessages().forEach(function (msg) {
      msg.getAttachments({ includeInlineImages: false }).forEach(function (att) {
        var name = att.getName() || '';
        if (!/_ICICI_POS_CD\.xlsx$/i.test(name)) return;        // skip the .zip twin etc.
        var mid = (name.match(/^(\d{15})_/) || [])[1];
        if (!mid || UPI_MIDS.indexOf(mid) === -1) return;

        var doneKey = 'upi_pushed_' + name;                     // name carries MID + date
        if (props.getProperty(doneKey)) { skipped++; return; }

        try {
          var resp = UrlFetchApp.fetch(UPI_VPS_URL, {
            method: 'post',
            headers: { 'X-Finance-Cron': token, 'X-Msg-Id': msg.getId() },
            payload: { file: att.copyBlob().setName(name) },
            muteHttpExceptions: true
          });
          var code = resp.getResponseCode();
          if (code === 200) {
            props.setProperty(doneKey, new Date().toISOString());
            pushed++;
          } else if (code === 422) {
            // the VPS rejected the file against its own Grand Total — that is a
            // REAL data problem, not a plumbing one. Mark done (retrying cannot
            // fix the file) and tell the doctor.
            props.setProperty(doneKey, 'REJECTED ' + new Date().toISOString());
            failed.push(name + ' -> rejected by parser: ' + resp.getContentText().slice(0, 200));
          } else {
            failed.push(name + ' -> HTTP ' + code);             // NOT marked done; retried tomorrow
          }
        } catch (e) {
          failed.push(name + ' -> ' + e);                        // network etc.; retried tomorrow
        }
      });
    });
  });

  if (failed.length) {
    _upiAlert('UPI statement push: ' + failed.length + ' failure(s)',
              'Pushed OK: ' + pushed + '\nSkipped (already sent): ' + skipped +
              '\n\nFailures:\n- ' + failed.join('\n- ') +
              '\n\nHTTP failures retry automatically tomorrow. Parser rejections need a look.');
  }
  return { ok: failed.length === 0, pushed: pushed, skipped: skipped, failed: failed };
}

function _upiAlert(subject, body) {
  try {
    MailApp.sendEmail(UPI_ALERT_TO, '[Clinic Finance] ' + subject, body);
  } catch (e) { /* alerting must never crash the push */ }
}
