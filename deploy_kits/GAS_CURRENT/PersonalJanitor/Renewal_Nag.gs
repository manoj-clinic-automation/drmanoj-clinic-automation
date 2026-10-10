/** ==========================================================================
 *  Renewal_Nag.gs · v3 · S513 (10-Oct-2026) · PERSONAL account — lives in the
 *  Inbox Janitor project beside Code.gs (it reads the RENEWALS array from
 *  there — GAS merges files into one namespace).
 *
 *  v3 — THE OWNER'S RULING (D689; closes F-775): a renewal comes up 45 days
 *  before its REAL EXPIRY and is red only AFTER the expiry. Until v3 the
 *  row's dateISO — an EARLY-ALERT day (the arms licence: 27-Sep for an
 *  expiry of 26-Dec) — was read as the deadline, and the health page called
 *  the arms licence OVERDUE from 27-Sep. An alert day and a deadline are two
 *  fields:
 *    - the expiry is r.expiryISO when a row carries one; otherwise the date
 *      written in the row's own note ("Expiry 26-12-2026", "valid to
 *      26-Dec-2027", "Expires 13-Aug-2029", "Valid 01-Apr-2025 to
 *      31-Mar-2030"); otherwise dateISO itself (the insurance and licence
 *      rows, whose date IS the renewal day). A note's date EARLIER than the
 *      row's dateISO is an old note left behind after a renewal — then
 *      dateISO wins.
 *    - the email: from 45 days before the expiry weekly, inside 21 days
 *      every 3 days, inside 7 days daily; OVERDUE only after the expiry,
 *      and kept for 45 days after it.
 *    - the VPS push carries expiryISO beside dateISO, for every row whose
 *      expiry is inside 50 days or up to 45 days past. The push NEVER
 *      carries the note, and a bracket holding a number is taken out of the
 *      name — an identity-document number does not leave this account.
 *
 *  SETUP: unchanged — the daily nagRenewals trigger (setupRenewalNag() once).
 *  ========================================================================== */

var NAG_WINDOW_DAYS  = 45;    // start nagging this far before the REAL expiry (D689)
var NAG_CLOSE_DAYS   = 21;    // inside this: every NAG_EVERY_DAYS
var NAG_URGENT_DAYS  = 7;     // inside this: daily
var NAG_EVERY_DAYS   = 3;
var NAG_WEEKLY_DAYS  = 7;     // between NAG_WINDOW_DAYS and NAG_CLOSE_DAYS: weekly
var NAG_OVERDUE_KEEP = 45;    // keep shouting this long past the expiry
var NAG_TO           = 'drmanojkragarwal@gmail.com';

function setupRenewalNag() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'nagRenewals') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('nagRenewals').timeBased().atHour(8).everyDays(1).create();
  Logger.log('daily nag trigger installed; first run: ' + nagRenewals());
}

var RN_MONTHS_ = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
                   jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };

function rnIso_(y, m, d) {
  var dt = new Date(Date.UTC(y, m - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) return '';
  return y + '-' + (m < 10 ? '0' : '') + m + '-' + (d < 10 ? '0' : '') + d;
}

/** The date written in a note after "Expiry/Expires/Expired" or "valid (…) to", as yyyy-MM-dd, or ''. */
function noteExpiry_(note) {
  var m = String(note || '').match(
    /(?:expir\w*|valid\s+(?:[\w-]+\s+)?to)\s*:?\s*(\d{1,2})[-\/. ]([A-Za-z]{3,9}|\d{1,2})[-\/. ](\d{4})/i);
  if (!m) return '';
  var mon = /^\d+$/.test(m[2]) ? parseInt(m[2], 10) : RN_MONTHS_[m[2].slice(0, 3).toLowerCase()];
  if (!mon) return '';
  return rnIso_(parseInt(m[3], 10), mon, parseInt(m[1], 10));
}

/** The REAL expiry of a RENEWALS row (see the header), or '' for an undated row. */
function expiryOf_(r) {
  if (!r.dateISO || !/^\d{4}-\d{2}-\d{2}$/.test(r.dateISO)) return '';
  if (r.expiryISO && /^\d{4}-\d{2}-\d{2}$/.test(r.expiryISO)) return r.expiryISO;
  var n = noteExpiry_(r.note);
  return (n && n >= r.dateISO) ? n : r.dateISO;
}

/** Whole days from TODAY IN IST to iso (0 = today, negative = past) — the same answer at any hour. */
function daysTo_(iso, now) {
  var t = Utilities.formatDate(now, 'Asia/Kolkata', 'yyyy-MM-dd');
  return Math.round((Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10))
                   - Date.UTC(+t.slice(0, 4), +t.slice(5, 7) - 1, +t.slice(8, 10))) / 864e5);
}

function nagRenewalsCore() {
  var now = new Date();
  var props = PropertiesService.getScriptProperties();
  var due = [], nagNow = false;

  RENEWALS.forEach(function (r) {
    var exp = expiryOf_(r);
    if (!exp) return;
    var days = daysTo_(exp, now);
    if (days > NAG_WINDOW_DAYS || days < -NAG_OVERDUE_KEEP) return;

    var key = 'nag_' + exp + '_' + r.vendor.slice(0, 40);
    var last = props.getProperty(key);
    var gapNeeded = (days <= NAG_URGENT_DAYS) ? 1
                  : (days <= NAG_CLOSE_DAYS) ? NAG_EVERY_DAYS : NAG_WEEKLY_DAYS;
    var lastD = last ? new Date(last) : null;
    var since = lastD ? Math.floor((now - lastD) / 864e5) : 999;
    if (since >= gapNeeded) { nagNow = true; props.setProperty(key, now.toISOString()); }

    due.push({ days: days, vendor: r.vendor, note: r.note || '', exp: exp });
  });

  if (!due.length) return 'quiet: nothing expires within ' + NAG_WINDOW_DAYS + ' days';
  if (!nagNow)     return 'due items exist but none needed a nag today';

  due.sort(function (a, b) { return a.days - b.days; });
  var lines = due.map(function (x) {
    var when = x.days < 0 ? 'OVERDUE — expired ' + (-x.days) + ' day(s) ago (' + x.exp + ')'
             : x.days === 0 ? 'EXPIRES TODAY (' + x.exp + ')'
             : 'expires in ' + x.days + ' day(s) (' + x.exp + ')';
    return '• ' + when + ' — ' + x.vendor + (x.note ? '\n    ' + x.note : '');
  });
  var worst = due[0];
  var subject = (worst.days < 0 ? 'OVERDUE RENEWAL: ' : 'RENEWAL DUE: ')
              + worst.vendor.slice(0, 60)
              + (due.length > 1 ? ' (+' + (due.length - 1) + ' more)' : '');
  MailApp.sendEmail(NAG_TO, subject,
    'These will keep arriving until the RENEWALS entry is updated:\n\n'
    + lines.join('\n') + '\n\n— Renewal nag (Inbox Janitor project). '
    + 'After renewing, advance the item\'s dateISO in Code.gs and write the '
    + 'new expiry in its note.');
  return 'nagged: ' + due.length + ' item(s), nearest ' + worst.days + 'd';
}

/** ==========================================================================
 *  The push to the clinic VPS (v2, S196; v3 above). It runs every day, quiet
 *  or not, so the health card can also say "feed stale" the day this script
 *  stops running. The token is the Script Property RENEWALS_PUSH_TOKEN.
 *  ========================================================================== */

var PUSH_URL         = 'https://followup.dr-manoj.in/finance/api/renewals-push';
var PUSH_WINDOW_DAYS = 50;    // a little beyond the card's 45-day window
var PUSH_OVERDUE_KEEP= 45;    // and everything past expiry the nag still tracks

function pushName_(vendor) {
  return String(vendor || '').replace(/\s*\([^)]*\d[^)]*\)/g, '').trim();
}

function pushRenewalsToVPS() {
  var now = new Date(), items = [];
  RENEWALS.forEach(function (r) {
    var exp = expiryOf_(r);
    if (!exp) return;
    var days = daysTo_(exp, now);
    if (days > PUSH_WINDOW_DAYS || days < -PUSH_OVERDUE_KEEP) return;
    items.push({ vendor: pushName_(r.vendor), dateISO: r.dateISO, expiryISO: exp, note: '' });
  });
  var token = PropertiesService.getScriptProperties()
                .getProperty('RENEWALS_PUSH_TOKEN');
  if (!token) return 'NOT PUSHED: RENEWALS_PUSH_TOKEN script property not set';
  try {
    var resp = UrlFetchApp.fetch(PUSH_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: { 'X-Finance-Renewals': token },
      payload: JSON.stringify({ window_days: NAG_WINDOW_DAYS, items: items }),
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    PropertiesService.getScriptProperties().setProperty(
      'renewals_last_push', code + ' @ ' + now.toISOString());
    return code === 200 ? 'pushed: ' + items.length + ' item(s)'
                        : 'PUSH FAILED: HTTP ' + code + ' ' +
                          String(resp.getContentText()).slice(0, 120);
  } catch (e) {
    return 'PUSH FAILED: ' + e;
  }
}

/* The trigger target. The push happens on EVERY daily run, quiet days included. */
function nagRenewals() {
  var out = nagRenewalsCore();
  var pushed = pushRenewalsToVPS();
  return out + ' | ' + pushed;
}

/* v3: a dry run, nothing sent and nothing stored — each dated row's alert day, its expiry and where the
   expiry came from. Safe to run any time from the editor. */
function renewalsExpiryCheck() {
  var now = new Date();
  var out = RENEWALS.map(function (r) {
    var exp = expiryOf_(r);
    if (!exp) return 'undated   ' + pushName_(r.vendor);
    var src = (r.expiryISO && exp === r.expiryISO) ? 'expiryISO'
            : (exp !== r.dateISO) ? 'note' : 'dateISO';
    return exp + ' (' + src + ', ' + daysTo_(exp, now) + 'd)  alert ' + r.dateISO + '  ' + pushName_(r.vendor);
  });
  var msg = out.join('\n');
  Logger.log(msg);
  return msg;
}
