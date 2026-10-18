/**
 * Clinic Portal Watcher — kit S573 (session S319, 17-Oct-2026); self-repair order added by kit S578 (S325, 18-Oct-2026, D734).
 * Checks the clinic portal and the website from OUTSIDE the server every 5 minutes.
 *
 * The order when the portal does not answer:
 *  - website answers (the server is on): the server repairs itself every 5 minutes (clinic-doctor --auto) and tells
 *    the phone itself. The watcher waits 15 minutes, then alerts with step 3 of the guide.
 *  - website down too (the whole server off or stuck), with HOSTINGER_KEY in Script Properties:
 *      Hostinger busy (an action running or the VM locked) -> wait and say so once;
 *      stopped -> start it (after 10 minutes down);  running but not answering -> restart it (after 15 minutes down);
 *      at most one start/restart per hour; then re-check and tell the owner the outcome.
 *    An alert (high) only when the automatic steps failed, naming the one next step and opening the guide at it.
 *  - without HOSTINGER_KEY: the old alert, step 4 of the guide.
 * Every attempt is written to the Script Property 'log' (the newest 30), so the next chat can read what happened.
 * The ntfy topic (NTFY_TOPIC) and the Hostinger key (HOSTINGER_KEY) live only in this project's Script Properties —
 * never in code, a repository, a page, a mail or a log line.
 * To stop it: run stopWatcher(). To start it again: run setup(). To read Hostinger once without acting: run testHostinger().
 */
var PORTAL = 'https://followup.dr-manoj.in/finance/healthz';
var SITE   = 'https://drmanojagarwal.com/robots.txt';
var GUIDE  = 'https://claude.ai/artifact/H5W1T3WPNm85t2peTnNnfP';
var EMAIL  = 'drmanojkragarwal@gmail.com';
var NTFY   = 'https://ntfy.sh/';
var HAPI   = 'https://developers.hostinger.com/api/vps/v1/virtual-machines';
var HOSTNAME = 'srv1746119.hstgr.cloud';   // the clinic server's name at Hostinger
var FAILS_TO_ALERT = 2;     // checks in a row (5 minutes apart) -- the server-off alert when there is no Hostinger key
var FAILS_SERVER_ON = 3;    // server on, portal down: the server's own repair has had two rounds by then
var FAILS_TO_START = 2;     // whole server stopped: start it after 10 minutes
var FAILS_TO_RESTART = 3;   // whole server running but not answering: restart it after 15 minutes
var ACT_EVERY_MIN = 60;     // at most one start/restart per hour
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
  retryPending_();
  var P = PropertiesService.getScriptProperties();
  var now = new Date();
  var portal = probe_(PORTAL);
  if (!portal) { Utilities.sleep(20000); portal = probe_(PORTAL); }   // one retry before counting a failure
  var st = JSON.parse(P.getProperty('state') || '{"fails":0}');
  if (portal) {
    if (st.alertedAt || st.actedAt || st.toldBusy) {
      var did = st.acted ? ' The watcher ' + st.acted + ' the server through Hostinger at ' + fmt_(st.actedAt) + '.' : '';
      notify_('Clinic portal is back',
              'The portal answers again. It was down about ' + mins_(st.downSince, now) + ' minutes, from ' + fmt_(st.downSince) + '.' + did,
              'default', 'white_check_mark');
      log_('back after ' + mins_(st.downSince, now) + ' min' + (st.acted ? ' (watcher ' + st.acted + ' it)' : ''));
    }
    P.setProperty('state', JSON.stringify({ fails: 0, lastActAt: st.lastActAt }));
    P.setProperty('lastOk', now.toISOString());
    return;
  }
  st.fails = (st.fails || 0) + 1;
  if (!st.downSince) st.downSince = now.toISOString();
  var siteOk = probe_(SITE);
  if (siteOk) {
    // The server is on: its own repair (clinic-doctor --auto, every 5 minutes) is working on it and tells the phone itself.
    if (st.fails >= FAILS_SERVER_ON && due_(st, now)) {
      alert_(st, now, 'Clinic portal is DOWN (server is on)',
             'The portal has not answered since ' + fmt_(st.downSince) + ', but your website answers, so the server is on. ' +
             'The server has been trying to repair it by itself.\n' +
             'Do step 3 of the guide: open Termius, type clinic-doctor, and send a photo of the screen to Claude.', '#s3');
    }
  } else {
    hostinger_(st, now);
  }
  P.setProperty('state', JSON.stringify(st));
}

// The whole server is off or stuck: Hostinger first, then the owner -- only if the automatic steps did not work.
function hostinger_(st, now) {
  var key = PropertiesService.getScriptProperties().getProperty('HOSTINGER_KEY');
  if (!key) {
    if (st.fails >= FAILS_TO_ALERT && due_(st, now)) {
      alert_(st, now, 'Clinic server is OFF',
             'Neither the portal nor your website has answered since ' + fmt_(st.downSince) + '.\n' +
             'Do step 4 of the guide: restart the server from the Hostinger panel.', '#s4');
    }
    return;
  }
  if (st.fails < FAILS_TO_START) return;
  var vm = vm_(key);
  if (vm.error) {
    log_('Hostinger not reachable: ' + vm.error);
    if (due_(st, now)) {
      alert_(st, now, 'Clinic server is OFF',
             'Neither the portal nor your website has answered since ' + fmt_(st.downSince) + '. ' +
             'The automatic restart could not reach Hostinger (' + vm.error + ').\n' +
             'Do step 4 of the guide: restart the server from the Hostinger panel.', '#s4');
    }
    return;
  }
  var s = vm.state;
  if (st.actedAt && (now - new Date(st.actedAt)) < 15 * 60000) {   // it was just started/restarted: give it 15 minutes
    log_('waiting after the ' + (st.acted || 'action') + ' (Hostinger: ' + s + ')');
    return;
  }
  if (vm.busy || ['starting', 'stopping', 'creating', 'recreating', 'restoring', 'unsuspending', 'initial'].indexOf(s) >= 0) {
    log_('Hostinger busy: state ' + s + (vm.busy ? ', ' + vm.busy : '') + ' -- waiting');
    if (!st.toldBusy) {
      notify_('Clinic server is OFF -- Hostinger is working on it',
              'The server has not answered since ' + fmt_(st.downSince) + '. Hostinger shows it as "' + s + '"' +
              (vm.busy ? ' (' + vm.busy + ')' : '') + ', so nothing is restarted while it works. ' +
              'Nothing for you to do yet; you will hear when it is back, or if it is not back within an hour.',
              'default', 'hourglass');
      st.toldBusy = now.toISOString();
    } else if ((now - new Date(st.toldBusy)) >= REPEAT_MIN * 60000 && due_(st, now)) {
      alert_(st, now, 'Clinic server still OFF after an hour',
             'Hostinger has shown the server as "' + s + '" since ' + fmt_(st.toldBusy) + '.\n' +
             'Do step 4 of the guide: look at the server in the Hostinger panel.', '#s4');
    }
    return;
  }
  var mayAct = !st.lastActAt || (now - new Date(st.lastActAt)) >= ACT_EVERY_MIN * 60000;
  var verb = null;
  if (s === 'stopped') verb = 'start';
  else if (s === 'running' && st.fails >= FAILS_TO_RESTART) verb = 'restart';
  else if (s === 'running') return;                                  // give it until 15 minutes
  if (!verb) {                                                       // suspended, error, recovery ... : not ours to press
    log_('Hostinger state ' + s + ' -- not acted on');
    if (due_(st, now)) {
      alert_(st, now, 'Clinic server is OFF (Hostinger: ' + s + ')',
             'The server has not answered since ' + fmt_(st.downSince) + ' and Hostinger shows it as "' + s + '", ' +
             'which the watcher does not press buttons for.\nDo step 4 of the guide, and check for a mail from Hostinger.', '#s4');
    }
    return;
  }
  if (!mayAct) {
    if (due_(st, now)) {
      alert_(st, now, 'Clinic server still not answering',
             'The watcher ' + (st.acted || 'restarted') + ' the server through Hostinger at ' + fmt_(st.lastActAt) +
             ', and it still does not answer (Hostinger: "' + s + '").\n' +
             'Do step 4 of the guide: restart it from the Hostinger panel. If that does not help, step 5: send the time to Claude.', '#s4');
    }
    return;
  }
  var res = act_(key, vm.id, verb);
  st.lastActAt = now.toISOString(); st.actedAt = st.lastActAt; st.acted = verb === 'start' ? 'started' : 'restarted';
  log_('Hostinger ' + verb + ' -> ' + res);
  if (res === 'accepted') {
    notify_('Clinic server was ' + (verb === 'start' ? 'OFF' : 'stuck') + ' -- ' + st.acted + ' it automatically',
            'Neither the portal nor your website answered since ' + fmt_(st.downSince) + '. Hostinger showed the server as "' + s +
            '", so the watcher ' + st.acted + ' it at ' + fmt_(st.actedAt) + '. Nothing for you to do; you will hear when it is back.',
            'default', 'arrows_counterclockwise');
  } else {
    alert_(st, now, 'Clinic server is OFF -- the automatic ' + verb + ' was refused',
           'Hostinger did not accept the ' + verb + ' (' + res + ').\nDo step 4 of the guide: ' + verb + ' it from the Hostinger panel.', '#s4');
  }
}

function hreq_(key, method, path) {
  try {
    var r = UrlFetchApp.fetch(HAPI + path, { method: method, muteHttpExceptions: true, contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + key, Accept: 'application/json' } });
    var c = r.getResponseCode(), j = null;
    try { j = JSON.parse(r.getContentText()); } catch (e) { j = null; }
    return { code: c, json: j };
  } catch (e) {
    return { code: 0, json: null };
  }
}

function vm_(key) {
  var P = PropertiesService.getScriptProperties();
  var id = P.getProperty('HOSTINGER_VM');
  if (!id) {
    var L = hreq_(key, 'get', '');
    if (L.code !== 200) return { error: L.code === 401 ? 'the key was refused (401)' : 'answer ' + L.code };
    var list = Array.isArray(L.json) ? L.json : ((L.json && L.json.data) || []);
    var mine = list.filter(function (v) { return v.hostname === HOSTNAME; });
    if (!mine.length && list.length === 1) mine = list;
    if (mine.length !== 1) return { error: 'the clinic server was not found in the account' };
    id = String(mine[0].id); P.setProperty('HOSTINGER_VM', id);
  }
  var V = hreq_(key, 'get', '/' + id);
  if (V.code !== 200 || !V.json) return { error: V.code === 401 ? 'the key was refused (401)' : 'answer ' + V.code };
  var vm = V.json.data && !V.json.state ? V.json.data : V.json;
  var lock = vm.actions_lock || vm.actionsLock;
  var busy = lock === 'locked' ? 'an action is running' : '';
  if (!busy) {
    var A = hreq_(key, 'get', '/' + id + '/actions');
    var acts = A.code === 200 ? (Array.isArray(A.json) ? A.json : ((A.json && A.json.data) || [])) : [];
    var open = acts.filter(function (a) { return ['created', 'sent', 'delayed'].indexOf(a.state) >= 0; });
    if (open.length) busy = 'Hostinger action "' + (open[0].name || 'unknown') + '" is ' + open[0].state;
  }
  return { id: id, state: String(vm.state || 'unknown'), busy: busy };
}

function act_(key, id, verb) {
  var r = hreq_(key, 'post', '/' + id + '/' + verb);
  return (r.code >= 200 && r.code < 300) ? 'accepted' : (r.code === 401 ? 'the key was refused (401)' : 'answer ' + r.code);
}

function testHostinger() {        // reads only: is the key good, which server, what state -- presses nothing
  var key = PropertiesService.getScriptProperties().getProperty('HOSTINGER_KEY');
  if (!key) { log_('test: no HOSTINGER_KEY'); return 'no HOSTINGER_KEY'; }
  var vm = vm_(key);
  var line = vm.error ? 'test: ' + vm.error : 'test: key good, server ' + vm.id + ', state ' + vm.state + (vm.busy ? ', ' + vm.busy : ', not busy');
  log_(line);
  return line;
}

function due_(st, now) { return !st.alertedAt || (now - new Date(st.alertedAt)) >= REPEAT_MIN * 60000; }

function alert_(st, now, title, body, anchor) {
  notify_(title, body + '\nGuide: ' + GUIDE + anchor, 'high', 'rotating_light', anchor);
  st.alertedAt = now.toISOString();
  log_('ALERT ' + title);
}

function log_(what) {
  var P = PropertiesService.getScriptProperties();
  var L = JSON.parse(P.getProperty('log') || '[]');
  L.push(Utilities.formatDate(new Date(), 'Asia/Kolkata', 'dd-MMM HH:mm') + ' ' + what);
  P.setProperty('log', JSON.stringify(L.slice(-30)));
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

function notify_(title, body, priority, tags, anchor) {
  MailApp.sendEmail(EMAIL, title, body);                       // the e-mail always goes first
  var item = { title: title, body: body, priority: priority || 'high', tags: tags || 'warning', since: new Date().toISOString(),
               click: GUIDE + (anchor || '') };
  if (!push_(item, 3)) {                                       // ntfy.sh refuses when Google's shared address is over its daily quota
    var P = PropertiesService.getScriptProperties();
    var q = JSON.parse(P.getProperty('pendingPush') || '[]'); q.push(item); P.setProperty('pendingPush', JSON.stringify(q.slice(-5)));
  }
}

function push_(item, tries) {
  var P = PropertiesService.getScriptProperties();
  var topic = P.getProperty('NTFY_TOPIC');
  if (!topic) return false;
  for (var i = 0; i < tries; i++) {
    try {
      var res = UrlFetchApp.fetch(NTFY + topic, {
        method: 'post', payload: item.body, muteHttpExceptions: true,
        headers: { Title: item.title, Priority: item.priority, Tags: item.tags, Click: item.click || GUIDE }
      });
      P.setProperty('lastPush', new Date().toISOString() + ' ' + res.getResponseCode() + ' ' + item.title);
      if (res.getResponseCode() === 200) return true;
    } catch (e) {
      P.setProperty('lastPush', new Date().toISOString() + ' ERROR ' + String(e).slice(0, 120));
    }
    if (i < tries - 1) Utilities.sleep(15000);
  }
  return false;
}

function retryPending_() {                                     // every check: send what the phone has not had yet (for up to 3 hours)
  var P = PropertiesService.getScriptProperties();
  var q = JSON.parse(P.getProperty('pendingPush') || '[]');
  if (!q.length) return;
  var keep = [];
  q.forEach(function (item) {
    if (new Date() - new Date(item.since) > 3 * 3600000) return;
    if (!push_(item, 1)) keep.push(item);
  });
  P.setProperty('pendingPush', JSON.stringify(keep));
}

function fmt_(iso) { return Utilities.formatDate(new Date(iso), 'Asia/Kolkata', 'dd-MMM HH:mm') + ' IST'; }
function mins_(iso, now) { return Math.max(1, Math.round((now - new Date(iso)) / 60000)); }
