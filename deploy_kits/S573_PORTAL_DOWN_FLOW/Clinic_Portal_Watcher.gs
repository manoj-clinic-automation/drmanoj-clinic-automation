/**
 * Clinic Portal Watcher — kit S573 (session S319, 17-Oct-2026).
 * Checks the clinic portal and the website from OUTSIDE the server every 5 minutes.
 * Two failed checks in a row -> one alert to the owner's phone (ntfy, system-health topic) and e-mail,
 * naming the step of the guide to do. Repeats once an hour while still down. One "back" message when it recovers.
 * The ntfy topic lives only in this project's Script Properties (NTFY_TOPIC) — never in code, a repository or a page.
 * To stop it: run stopWatcher(). To start it again: run setup().
 */
var PORTAL = 'https://followup.dr-manoj.in/finance/healthz';
var SITE   = 'https://drmanojagarwal.com/robots.txt';
var GUIDE  = 'https://claude.ai/artifact/H5W1T3WPNm85t2peTnNnfP';
var EMAIL  = 'drmanojkragarwal@gmail.com';
var NTFY   = 'https://ntfy.sh/';
var FAILS_TO_ALERT = 2;     // checks in a row (5 minutes apart)
var REPEAT_MIN     = 60;    // while still down, remind once an hour

function setup() {
  var P = PropertiesService.getScriptProperties();
  var once = '__TOPIC_ONCE__';                       // removed from the code after the first run
  if (once.indexOf('__') !== 0) P.setProperty('NTFY_TOPIC', once);
  if (!P.getProperty('NTFY_TOPIC')) throw new Error('No NTFY_TOPIC in Script Properties.');
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'check') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('check').timeBased().everyMinutes(5).create();
  P.setProperty('state', JSON.stringify({ fails: 0 }));
  var ok = probe_(PORTAL);
  notify_('Portal watcher is ON',
          'This is a test. From now on your phone gets an alert if the clinic portal stops answering, with the step to do.\n' +
          'Portal right now: ' + (ok ? 'answering' : 'NOT answering') + '.\nGuide: ' + GUIDE, 'default', 'white_check_mark');
}

function stopWatcher() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'check') ScriptApp.deleteTrigger(t); });
}

function check() {
  var P = PropertiesService.getScriptProperties();
  var now = new Date();
  var portal = probe_(PORTAL);
  if (!portal) { Utilities.sleep(20000); portal = probe_(PORTAL); }   // one retry before counting a failure
  var st = JSON.parse(P.getProperty('state') || '{"fails":0}');
  if (portal) {
    if (st.alertedAt) {
      notify_('Clinic portal is back',
              'The portal answers again. It was down about ' + mins_(st.downSince, now) + ' minutes, from ' + fmt_(st.downSince) + '.',
              'default', 'white_check_mark');
    }
    P.setProperty('state', JSON.stringify({ fails: 0 }));
    P.setProperty('lastOk', now.toISOString());
    return;
  }
  st.fails = (st.fails || 0) + 1;
  if (!st.downSince) st.downSince = now.toISOString();
  var due = st.fails >= FAILS_TO_ALERT && (!st.alertedAt || (now - new Date(st.alertedAt)) >= REPEAT_MIN * 60000);
  if (due) {
    var siteOk = probe_(SITE);
    var title = siteOk ? 'Clinic portal is DOWN (server is on)' : 'Clinic server is OFF';
    var body = siteOk
      ? 'The portal has not answered since ' + fmt_(st.downSince) + ', but your website answers, so the server is on.\n' +
        'Do step 2 of the guide: open Termius and type clinic-doctor.'
      : 'Neither the portal nor your website has answered since ' + fmt_(st.downSince) + '.\n' +
        'Do step 4 of the guide: restart the server from the Hostinger panel.';
    notify_(title, body + '\nGuide: ' + GUIDE, 'high', 'rotating_light');
    st.alertedAt = now.toISOString();
  }
  P.setProperty('state', JSON.stringify(st));
}

function probe_(url) {
  try {
    var r = UrlFetchApp.fetch(url, { muteHttpExceptions: true, followRedirects: false });
    var c = r.getResponseCode();
    return c > 0 && [502, 503, 504].indexOf(c) < 0;   // any reply is alive; a gateway error is not
  } catch (e) {
    return false;
  }
}

function notify_(title, body, priority, tags) {
  var topic = PropertiesService.getScriptProperties().getProperty('NTFY_TOPIC');
  if (topic) {
    try {
      UrlFetchApp.fetch(NTFY + topic, {
        method: 'post', payload: body, muteHttpExceptions: true,
        headers: { Title: title, Priority: priority || 'high', Tags: tags || 'warning', Click: GUIDE }
      });
    } catch (e) { /* the e-mail below still goes */ }
  }
  MailApp.sendEmail(EMAIL, title, body);
}

function fmt_(iso) { return Utilities.formatDate(new Date(iso), 'Asia/Kolkata', 'dd-MMM HH:mm') + ' IST'; }
function mins_(iso, now) { return Math.max(1, Math.round((now - new Date(iso)) / 60000)); }
