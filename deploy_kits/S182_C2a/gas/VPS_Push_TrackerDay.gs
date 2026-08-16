/** ===========================================================================
 * VPS_Push_TrackerDay.gs · clinic Gmail account · Session 182 · kit S182_C2
 * ---------------------------------------------------------------------------
 * Pushes ONE day's Docterz / staff-output revenue summary from the
 * Drive-synced revenue_ledger.csv to the finance app:
 *
 *     POST <FINANCE_URL>            (…/finance/api/tracker-feed)
 *     header  X-Finance-Cron: <FINANCE_CRON_TOKEN>
 *     body    { unit:'clinic', date:'YYYY-MM-DD',
 *               summary:{ net, cash, online, consult_n, consult_amt,
 *                         xray_n, xray_amt, proc_n, proc_amt },
 *               lines:[ { clinic_id, source, net }, … ] }
 *
 * Same pattern as VPS_Push_UPI.gs: NO secrets in this file — the URL and
 * token live in Script Properties; a daily time trigger ~21:30; dedupe via a
 * Script Property so re-runs never spam the server with identical payloads
 * (the server upserts anyway — one row per day — so a changed payload may be
 * re-sent safely); mail on FAILURE ONLY, silence when all is well.
 *
 * PRIVACY (enforced twice): the payload carries clinic ids and amounts.
 * NO names, NO phone numbers ever leave this script — and the server refuses
 * a payload that carries them, whole. Nothing needs masking because nothing
 * identifying is sent.
 *
 * SCRIPT PROPERTIES (File → Project properties → Script properties):
 *   FINANCE_URL         e.g. https://<host>/finance/api/tracker-feed
 *   FINANCE_CRON_TOKEN  the same token the systemd unit exports
 *   LEDGER_FILENAME     optional; default 'revenue_ledger.csv'
 *   ALERT_EMAIL         where failure mail goes
 *   (TRACKERDAY_SENT_*  written by the script itself — the dedupe markers)
 *
 * SET-UP: paste, set the four properties, run testTrackerDayNow() once from
 * the editor (authorise Drive + external requests + mail), then run
 * installTrackerDayTrigger() once. Done.
 * =========================================================================== */

var TD_TZ = 'Asia/Kolkata';

/* --------------------------------------------------------------- properties */
function tdProp_(k, dflt) {
  var v = PropertiesService.getScriptProperties().getProperty(k);
  return (v === null || v === '') ? (dflt === undefined ? null : dflt) : v;
}

/* ------------------------------------------------------------ trigger admin */
function installTrackerDayTrigger() {
  removeTrackerDayTrigger();
  ScriptApp.newTrigger('pushTrackerDay')
    .timeBased().everyDays(1).atHour(21).nearMinute(30).create();
  Logger.log('pushTrackerDay trigger installed (~21:30 daily).');
}
function removeTrackerDayTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'pushTrackerDay') ScriptApp.deleteTrigger(t);
  });
}
function testTrackerDayNow() {           // manual runner, same path as the trigger
  pushTrackerDay();
}

/* -------------------------------------------------------------- main runner */
function pushTrackerDay() {
  var today = Utilities.formatDate(new Date(), TD_TZ, 'yyyy-MM-dd');
  try {
    var url = tdProp_('FINANCE_URL');
    var token = tdProp_('FINANCE_CRON_TOKEN');
    if (!url || !token) throw new Error('FINANCE_URL / FINANCE_CRON_TOKEN not set in Script Properties.');

    var payload = buildTrackerPayload_(today);
    if (!payload) {                       // no rows for today — a quiet day, not a fault
      Logger.log('No ledger rows for ' + today + ' — nothing to push.');
      return;
    }

    // dedupe: skip only when THIS exact payload already went for this day.
    // A changed ledger (late entries) produces a new hash and is re-sent;
    // the server upserts one row per day, so that is safe by design.
    var body = JSON.stringify(payload);
    var hash = Utilities.base64Encode(
      Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, body));
    var marker = 'TRACKERDAY_SENT_' + today;
    if (tdProp_(marker) === hash) {
      Logger.log(today + ' already pushed with this exact content — skipped.');
      return;
    }

    var resp = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      payload: body,
      headers: { 'X-Finance-Cron': token },
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code !== 200) {
      throw new Error('server said HTTP ' + code + ': ' +
                      String(resp.getContentText()).slice(0, 300));
    }
    PropertiesService.getScriptProperties().setProperty(marker, hash);
    tdCleanupMarkers_();
    Logger.log('Pushed ' + today + ': ' + payload.lines.length + ' line(s), net ' +
               payload.summary.net + '.');
  } catch (err) {
    tdFail_('tracker-day push failed for ' + today, err);
  }
}

/* ---------------------------------------------------- read + shape the day */
function buildTrackerPayload_(dayIso) {
  var name = tdProp_('LEDGER_FILENAME', 'revenue_ledger.csv');
  var files = DriveApp.getFilesByName(name);
  if (!files.hasNext()) throw new Error("Drive file '" + name + "' not found.");
  var file = files.next();
  if (files.hasNext()) {
    // two files with the same name is an accident worth hearing about
    throw new Error("More than one Drive file is called '" + name + "' — fix the sync folder.");
  }

  var rows = Utilities.parseCsv(file.getBlob().getDataAsString());
  if (!rows || rows.length < 2) throw new Error("'" + name + "' is empty or has no data rows.");
  var hdr = rows[0].map(function (h) { return String(h || '').trim().toLowerCase(); });

  // tolerant header lookup — the ledger's headings must be FOUND, never guessed
  function col(cands) {
    for (var i = 0; i < cands.length; i++) {
      var at = hdr.indexOf(cands[i]);
      if (at >= 0) return at;
    }
    return -1;
  }
  var cDate = col(['date', 'bill_date', 'visit_date', 'day']);
  var cId = col(['clinic_id', 'patient_id', 'clinicid', 'id']);
  var cSrc = col(['source', 'service', 'head', 'type', 'category']);
  var cNet = col(['net', 'net_amount', 'amount', 'net amt', 'total']);
  var cMode = col(['mode', 'payment_mode', 'payment', 'tender']);
  if (cDate < 0 || cNet < 0) {
    throw new Error("'" + name + "' is missing a date or net column — header was: " +
                    rows[0].join(', '));
  }

  var sum = { net: 0, cash: 0, online: 0,
              consult_n: 0, consult_amt: 0,
              xray_n: 0, xray_amt: 0,
              proc_n: 0, proc_amt: 0 };
  var lines = [];
  for (var r = 1; r < rows.length; r++) {
    var row = rows[r];
    if (tdRowDate_(row[cDate]) !== dayIso) continue;
    var net = Number(String(row[cNet] || '').replace(/[₹, ]/g, '')) || 0;
    var src = String(cSrc >= 0 ? row[cSrc] : '').trim().toLowerCase();
    var mode = String(cMode >= 0 ? row[cMode] : '').trim().toLowerCase();
    // PRIVACY: the id is kept to its digits; nothing else from the row leaves
    var cid = String(cId >= 0 ? row[cId] : '').replace(/\D/g, '');

    sum.net += net;
    if (mode === 'cash') sum.cash += net; else sum.online += net;
    if (src.indexOf('consult') >= 0 || src.indexOf('opd') >= 0) {
      sum.consult_n += 1; sum.consult_amt += net;
    } else if (src.indexOf('xray') >= 0 || src.indexOf('x-ray') >= 0) {
      sum.xray_n += 1; sum.xray_amt += net;
    } else if (src.indexOf('proc') >= 0) {
      sum.proc_n += 1; sum.proc_amt += net;
    }
    lines.push({ clinic_id: cid, source: src || 'other', net: net });
  }
  if (!lines.length) return null;
  return { unit: 'clinic', date: dayIso, summary: sum, lines: lines };
}

function tdRowDate_(v) {
  var s = String(v || '').trim();
  var m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);           // 2026-08-16[…]
  if (m) return m[1] + '-' + m[2] + '-' + m[3];
  m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/); // 16/08/2026 (dd first)
  if (m) return m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
  var d = new Date(s);                                    // sheet Date objects etc.
  if (!isNaN(d.getTime())) return Utilities.formatDate(d, TD_TZ, 'yyyy-MM-dd');
  return null;
}

/* ---------------------------------------------------------------- plumbing */
function tdCleanupMarkers_() {          // keep only ~14 days of dedupe markers
  var props = PropertiesService.getScriptProperties();
  var all = props.getKeys().filter(function (k) {
    return k.indexOf('TRACKERDAY_SENT_') === 0;
  }).sort();
  while (all.length > 14) props.deleteProperty(all.shift());
}

function tdFail_(subject, err) {        // mail on failure ONLY — success is silent
  var msg = String(err && err.message ? err.message : err);
  Logger.log('FAIL: ' + subject + ' — ' + msg);
  var to = tdProp_('ALERT_EMAIL');
  if (!to) return;
  MailApp.sendEmail({
    to: to,
    subject: '[clinic finance] ' + subject,
    body: subject + '\n\n' + msg +
          '\n\nRun testTrackerDayNow() in the Apps Script editor to retry and ' +
          'see the log. The server keeps one row per day, so a retry is always safe.'
  });
}
