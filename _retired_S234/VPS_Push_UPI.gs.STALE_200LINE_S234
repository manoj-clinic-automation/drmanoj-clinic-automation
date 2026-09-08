/** ==========================================================================
 *  VPS_Push_UPI.gs  ·  v2  (Session 195)   — supersedes the S179 v1
 *  Dr. Manoj Agarwal Clinic — pushes the daily ICICI Merchant (MPR) statements
 *  from the clinic Gmail to the VPS finance app.
 *
 *  WHY v2
 *    v1 worked, but it only ever looked back THREE DAYS. It first ran on
 *    15-Aug-2026 (and that first run failed: FINANCE_VPS_TOKEN was not set
 *    yet). So the VPS holds statements from about 14-Aug onward and NOTHING
 *    before it — while Gmail still holds every statement back to at least
 *    18-Jul. Eight days of bank truth against eighty days of books, and the
 *    cash/UPI checks can only see the days the bank can witness.
 *
 *    Two changes, both about not losing days:
 *      1. The daily window is now 10 days, not 3. A long weekend, a failed
 *         run, a holiday — any of these used to push a day out of reach
 *         forever. Ten days gives the retry room to work.
 *      2. backfillUpiStatements() walks the whole history once. It searches
 *         in:anywhere, so statements sitting in TRASH are picked up too
 *         without anyone having to restore them by hand.
 *
 *    Nothing else changed. Same URL, same token, same filter, same
 *    "remember what was pushed" dedupe — so re-running is always safe.
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
 *  HOW TO USE THIS FILE
 *    1. Open the GAS project, select the existing VPS_Push_UPI file, select
 *       all, and paste this over it. Save.
 *    2. Run  verifyUpiPush()  — it says whether the token and the daily
 *       trigger are in place, without printing the token.
 *    3. If it says the token is MISSING: Project Settings -> Script
 *       Properties -> FINANCE_VPS_TOKEN = <the VPS cron token>. Then run
 *       setupUpiPush() once.
 *    4. Run  backfillUpiStatements()  — once. It may hit the 6-minute limit;
 *       if it says MORE TO DO, just run it again. It resumes where it stopped
 *       and never re-sends what it already sent.
 *  ========================================================================== */

var UPI_VPS_URL   = 'https://followup.dr-manoj.in/finance/api/upi-statement';
var UPI_MIDS      = ['100000000312505', '100000000306941', '100000000319164'];
var UPI_SEARCH    = 'from:merchantsolutions@icici.bank.in newer_than:10d';
var UPI_BACKFILL  = 'in:anywhere from:merchantsolutions@icici.bank.in newer_than:150d';
var UPI_ALERT_TO  = 'drmanojkragarwal@gmail.com';
var UPI_TIME_MS   = 4.5 * 60 * 1000;   // stop before GAS kills the run at 6 min


/** Say what state this is in, without ever printing the token. */
function verifyUpiPush() {
  var props = PropertiesService.getScriptProperties();
  var tok = props.getProperty('FINANCE_VPS_TOKEN');
  var trig = ScriptApp.getProjectTriggers().filter(function (t) {
    return t.getHandlerFunction() === 'pushUpiStatements';
  });
  var done = 0;
  var keys = props.getKeys();
  for (var i = 0; i < keys.length; i++) {
    if (keys[i].indexOf('upi_pushed_') === 0) done++;
  }
  var msg = 'FINANCE_VPS_TOKEN : ' + (tok ? ('present, ' + tok.length + ' chars') : '*** MISSING ***')
          + '\ndaily trigger     : ' + (trig.length ? (trig.length + ' installed') : '*** NONE ***')
          + '\nfiles pushed ever : ' + done
          + '\ndaily search      : ' + UPI_SEARCH;
  Logger.log(msg);
  return msg;
}


function setupUpiPush() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'pushUpiStatements') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('pushUpiStatements').timeBased().atHour(9).nearMinute(30)
    .everyDays(1).create();
  var out = pushUpiStatements();
  Logger.log('setup done; first run: ' + JSON.stringify(out));
  return out;
}


/** The daily job. Unchanged in behaviour; wider window. */
function pushUpiStatements() {
  return _pushSearch(UPI_SEARCH, 60, true);
}


/**
 * ONE-TIME (repeatable) history walk. Safe to run as many times as you like:
 * every file already sent is skipped, so a second run only picks up what the
 * first run ran out of time for. Searches in:anywhere, so a statement that was
 * deleted is still found in Trash and pushed before Gmail purges it.
 */
function backfillUpiStatements() {
  var out = _pushSearch(UPI_BACKFILL, 400, false);
  var msg = 'backfill: pushed ' + out.pushed + ', already had ' + out.skipped
          + ', failed ' + out.failed.length
          + (out.more ? '\n\n*** MORE TO DO — run backfillUpiStatements() again. ***'
                      : '\n\nComplete: nothing left to send.');
  if (out.failed.length) msg += '\n\nFailures:\n- ' + out.failed.join('\n- ');
  Logger.log(msg);
  return msg;
}


/** Shared engine. alertOnFail=false for the backfill (its result is the log). */
function _pushSearch(query, maxThreads, alertOnFail) {
  var started = new Date().getTime();
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('FINANCE_VPS_TOKEN');
  if (!token) {
    _upiAlert('UPI push NOT configured',
              'FINANCE_VPS_TOKEN is missing from Script Properties. No statement was pushed.');
    return { ok: false, error: 'no token', pushed: 0, skipped: 0, failed: [], more: false };
  }

  var pushed = 0, skipped = 0, failed = [], more = false;

  for (var start = 0; start < maxThreads; start += 50) {
    if (new Date().getTime() - started > UPI_TIME_MS) { more = true; break; }
    var threads = GmailApp.search(query, start, 50);
    if (!threads.length) break;

    for (var ti = 0; ti < threads.length; ti++) {
      if (new Date().getTime() - started > UPI_TIME_MS) { more = true; break; }
      var msgs = threads[ti].getMessages();

      for (var mi = 0; mi < msgs.length; mi++) {
        var msg = msgs[mi];
        var atts = msg.getAttachments({ includeInlineImages: false });

        for (var ai = 0; ai < atts.length; ai++) {
          var att = atts[ai];
          var name = att.getName() || '';
          if (!/_ICICI_POS_CD\.xlsx$/i.test(name)) continue;     // skip the .zip twin etc.
          var mid = (name.match(/^(\d{15})_/) || [])[1];
          if (!mid || UPI_MIDS.indexOf(mid) === -1) continue;

          var doneKey = 'upi_pushed_' + name;                    // name carries MID + date
          if (props.getProperty(doneKey)) { skipped++; continue; }

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
              // the VPS rejected the file against its own Grand Total — a REAL
              // data problem, not a plumbing one. Mark done (retrying cannot
              // fix the file) and report it.
              props.setProperty(doneKey, 'REJECTED ' + new Date().toISOString());
              failed.push(name + ' -> rejected by parser: ' + resp.getContentText().slice(0, 200));
            } else {
              failed.push(name + ' -> HTTP ' + code);            // NOT marked done; retried later
            }
          } catch (e) {
            failed.push(name + ' -> ' + e);                      // network etc.; retried later
          }
        }
      }
    }
  }

  if (alertOnFail && failed.length) {
    _upiAlert('UPI statement push: ' + failed.length + ' failure(s)',
              'Pushed OK: ' + pushed + '\nSkipped (already sent): ' + skipped +
              '\n\nFailures:\n- ' + failed.join('\n- ') +
              '\n\nHTTP failures retry automatically tomorrow. Parser rejections need a look.');
  }
  return { ok: failed.length === 0, pushed: pushed, skipped: skipped,
           failed: failed, more: more };
}


function _upiAlert(subject, body) {
  try {
    MailApp.sendEmail(UPI_ALERT_TO, '[Clinic Finance] ' + subject, body);
  } catch (e) { /* alerting must never crash the push */ }
}
