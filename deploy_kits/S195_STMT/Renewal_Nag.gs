/** ==========================================================================
 *  Renewal_Nag.gs · S195 · PERSONAL account — paste as a NEW file in the
 *  Inbox Janitor project (beside Code.gs; it reads the RENEWALS array from
 *  there — GAS merges files into one namespace).
 *
 *  WHY: one calendar reminder at 30 days and one at 7 gets swept away in a
 *  working day and forgotten — the owner said so, and the estate almost
 *  proved it (dr-manoj.in was inside its 7-day window before anyone moved).
 *  A reminder system's job is not to have reminded; it is to be IMPOSSIBLE
 *  to ignore in the last stretch while staying silent the rest of the year.
 *
 *  WHAT IT DOES (daily 08-09, but emails only when something is CLOSE):
 *    - nothing due within 21 days  -> no email at all, ever
 *    - something within 21 days    -> ONE consolidated email, repeated every
 *                                     3 days; inside 7 days, repeated DAILY
 *    - overdue (up to 45 days)     -> stays in the email, marked OVERDUE,
 *                                     until the date in RENEWALS is advanced
 *  The email dies only when the RENEWALS row is updated — which is exactly
 *  the action the nag exists to force. Per-item pacing is kept in Script
 *  Properties so the quiet items never generate noise.
 *
 *  SETUP: run setupRenewalNag() once.
 *  ========================================================================== */

var NAG_WINDOW_DAYS  = 21;    // start nagging this far ahead
var NAG_URGENT_DAYS  = 7;     // inside this: daily
var NAG_EVERY_DAYS   = 3;     // outside urgent: every N days
var NAG_OVERDUE_KEEP = 45;    // keep shouting this long past due
var NAG_TO           = 'drmanojkragarwal@gmail.com';

function setupRenewalNag() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'nagRenewals') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('nagRenewals').timeBased().atHour(8).everyDays(1).create();
  Logger.log('daily nag trigger installed; first run: ' + nagRenewals());
}

function nagRenewals() {
  var now = new Date();
  var props = PropertiesService.getScriptProperties();
  var due = [], nagNow = false;

  RENEWALS.forEach(function (r) {
    if (!r.dateISO || r.dateISO.indexOf('TODO') === 0) return;
    var d = new Date(r.dateISO + 'T09:00:00');
    var days = Math.floor((d - now) / 864e5);
    if (days > NAG_WINDOW_DAYS || days < -NAG_OVERDUE_KEEP) return;

    var key = 'nag_' + r.dateISO + '_' + r.vendor.slice(0, 40);
    var last = props.getProperty(key);
    var gapNeeded = (days <= NAG_URGENT_DAYS) ? 1 : NAG_EVERY_DAYS;
    var lastD = last ? new Date(last) : null;
    var since = lastD ? Math.floor((now - lastD) / 864e5) : 999;
    if (since >= gapNeeded) { nagNow = true; props.setProperty(key, now.toISOString()); }

    due.push({ days: days, vendor: r.vendor, note: r.note || '' });
  });

  if (!due.length) return 'quiet: nothing within ' + NAG_WINDOW_DAYS + ' days';
  if (!nagNow)     return 'due items exist but none needed a nag today';

  due.sort(function (a, b) { return a.days - b.days; });
  var lines = due.map(function (x) {
    var when = x.days < 0 ? 'OVERDUE by ' + (-x.days) + ' day(s)'
             : x.days === 0 ? 'DUE TODAY'
             : 'due in ' + x.days + ' day(s)';
    return '• ' + when + ' — ' + x.vendor + (x.note ? '\n    ' + x.note : '');
  });
  var worst = due[0];
  var subject = (worst.days < 0 ? 'OVERDUE RENEWAL: ' : 'RENEWAL DUE: ')
              + worst.vendor.slice(0, 60)
              + (due.length > 1 ? ' (+' + (due.length - 1) + ' more)' : '');
  MailApp.sendEmail(NAG_TO, subject,
    'These will keep arriving until the RENEWALS entry is updated:\n\n'
    + lines.join('\n') + '\n\n— Renewal nag (Inbox Janitor project). '
    + 'After renewing, advance the item\'s dateISO in Code.gs.');
  return 'nagged: ' + due.length + ' item(s), nearest ' + worst.days + 'd';
}
