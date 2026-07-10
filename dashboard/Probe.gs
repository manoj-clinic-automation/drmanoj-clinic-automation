/**
 * Probe.gs — ONE-TIME, READ-ONLY checks for the call-recording feature.
 *
 * SAFE TO PASTE BACK: these log only field names, HTTP status, content-type,
 * size, and MASKED hosts (host + file-type + query-key NAMES). They never log
 * a full URL, a token value, audio bytes, or a phone number.
 *
 * Two functions:
 *   probeRecordingField()    — confirms which field holds the recording link.
 *   probeRecordingPlayback() — tests HOW that link plays (open? redirect? login?).
 *
 * HOW TO RUN: pick the function in the dropdown next to ▶ Run, click Run, then
 * open "Execution log" and copy what it prints.
 */

/* ===== 1. Which field is the recording? (already run — field is "fileurl") ===== */
function probeRecordingField() {
  var end = new Date();
  var start = new Date(end.getTime() - 48 * 3600 * 1000);   // last 48h

  var savedPage = CFG.PAGE_SIZE, savedMax = CFG.MAX_PAGES;
  CFG.PAGE_SIZE = 3; CFG.MAX_PAGES = 1;
  var recs;
  try { recs = fetchCallsBetween_(start, end); }
  finally { CFG.PAGE_SIZE = savedPage; CFG.MAX_PAGES = savedMax; }

  if (!recs.length) { Logger.log('No calls in the last 48 hours — widen the window and run again.'); return; }

  Logger.log('Top-level field names on a call record:');
  Logger.log('  %s', Object.keys(recs[0]).join(', '));

  var found = {};
  recs.forEach(function (r) { scanUrls_(r, '', found, 0); });
  var keys = Object.keys(found);
  if (!keys.length) {
    Logger.log('RESULT: no web link found. Paste me the field-names line above.');
  } else {
    Logger.log('RESULT: found %s link field(s) (masked):', keys.length);
    keys.forEach(function (k) { Logger.log('  %s   ->   %s', k, found[k]); });
  }
}

/* ===== 2. How does the recording link actually play? ===== */
function probeRecordingPlayback() {
  var end = new Date();
  var start = new Date(end.getTime() - 72 * 3600 * 1000);   // last 72h
  var savedPage = CFG.PAGE_SIZE, savedMax = CFG.MAX_PAGES;
  CFG.PAGE_SIZE = 15; CFG.MAX_PAGES = 1;
  var recs;
  try { recs = fetchCallsBetween_(start, end); }
  finally { CFG.PAGE_SIZE = savedPage; CFG.MAX_PAGES = savedMax; }
  if (!recs.length) { Logger.log('No calls in the last 72 hours.'); return; }

  // Prefer an answered call (status==1) — most likely to have real audio.
  var url = '';
  for (var i = 0; i < recs.length; i++) {
    var fu = recs[i].fileurl;
    if (fu && /^https?:/i.test(String(fu))) { url = String(fu); if (String(recs[i].status) === '1') break; }
  }
  if (!url) { Logger.log('No fileurl on the sampled records. Try widening the window.'); return; }

  Logger.log('Testing the recording link 4 ways (the link itself is NOT printed):');
  tryFetch_('1) plain, no-follow', url, false);
  tryFetch_('2) plain, follow',    url, true);

  var token = '';
  try { token = getToken_(); } catch (e) {}
  if (token) {
    var sep = (url.indexOf('?') >= 0) ? '&' : '?';
    var withTok = url + sep + 'token=' + encodeURIComponent(token);
    tryFetch_('3) with ?token=, no-follow', withTok, false);
    tryFetch_('4) with ?token=, follow',    withTok, true);
  } else {
    Logger.log('  (no MYOP_TOKEN found, so token variants were skipped)');
  }
  Logger.log('Done. Copy these lines — no URLs or tokens are printed.');
}

/** Fetch once and log status / type / size / masked redirect only. */
function tryFetch_(label, url, follow) {
  try {
    var resp = UrlFetchApp.fetch(url, { method: 'get', muteHttpExceptions: true, followRedirects: !!follow });
    var code = resp.getResponseCode();
    var hdrs = resp.getHeaders() || {};
    var ct = hdrs['Content-Type'] || hdrs['content-type'] || '(none)';
    var loc = hdrs['Location'] || hdrs['location'] || '';
    var bytes = resp.getContent() ? resp.getContent().length : 0;
    var kb = Math.round(bytes / 1024);
    Logger.log('  %s -> HTTP %s | type=%s | size=%sKB%s',
      label, code, ct, kb, loc ? (' | redirect-> ' + maskUrl_(loc)) : '');
  } catch (e) {
    Logger.log('  %s -> ERROR %s', label, (e && e.message) ? e.message : e);
  }
}

/* ===== shared helpers ===== */
/** Walk an object/array; record dotted PATH + masked URL for any http(s) string. */
function scanUrls_(obj, path, out, depth) {
  if (obj == null || depth > 4) return;
  if (typeof obj === 'string') {
    if (/^https?:\/\//i.test(obj)) out[path || '(root)'] = maskUrl_(obj);
    return;
  }
  if (Object.prototype.toString.call(obj) === '[object Array]') {
    for (var i = 0; i < obj.length && i < 3; i++) scanUrls_(obj[i], path + '[]', out, depth + 1);
    return;
  }
  if (typeof obj === 'object') {
    Object.keys(obj).forEach(function (k) { scanUrls_(obj[k], path ? path + '.' + k : k, out, depth + 1); });
  }
}

/** Show host + file-type + query-param NAMES only — never token values. */
function maskUrl_(u) {
  try {
    var noScheme = u.replace(/^https?:\/\//i, '');
    var host = noScheme.split('/')[0];
    var afterHost = noScheme.slice(host.length);
    var path = afterHost.split('?')[0];
    var q = (afterHost.indexOf('?') >= 0) ? afterHost.split('?')[1] : '';
    var qkeys = q ? q.split('&').map(function (p) { return p.split('=')[0]; }).join(',') : '(none)';
    var ext = (path.match(/\.[a-z0-9]{2,4}$/i) || ['(no file extension)'])[0];
    return 'host=' + host + ' | file-type=' + ext + ' | query-keys=' + qkeys;
  } catch (e) { return '(could not parse)'; }
}
function dumpAllProjectFiles_() {
  var id = ScriptApp.getScriptId();
  var url = 'https://script.googleapis.com/v1/projects/' + id + '/content';
  var token = ScriptApp.getOAuthToken();
  var res = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token },
    muteHttpExceptions: true
  });
  var files = JSON.parse(res.getContentText()).files || [];
  var doc = DocumentApp.create('PROJECT_DUMP_' + new Date().getTime());
  var body = doc.getBody();
  files.forEach(function (f) {
    body.appendParagraph('===== FILE: ' + f.name + ' . ' + f.type + ' =====');
    body.appendParagraph(f.source || '(empty)');
  });
  Logger.log('DONE. Open this Doc and share the link: ' + doc.getUrl());
}
/** READ-ONLY diagnostic — Session 16. Logs what getDashboardData returns.
 *  Touches nothing live; prints no secrets. Delete after use. */
function probeDashboardData_() {
  var sp = PropertiesService.getScriptProperties();
  var key = (sp.getProperty('DASH_KEY') || sp.getProperty('SECRET_KEY') || '').trim();
  Logger.log('Key present: %s (role=%s)', key ? 'yes' : 'NO', dashRole_(key));

  var d = getDashboardData(key, true);   // force=true bypasses the 90s cache
  if (d && d.error) { Logger.log('RETURNED ERROR: %s', d.error); return; }

  Logger.log('updated=%s  build=%s', d.updated, d.build);
  Logger.log('kpis: %s', JSON.stringify(d.kpis));
  Logger.log('COUNTS -> pending:%s  resolved:%s  handled:%s  recentWA:%s  agents:%s',
    (d.pending||[]).length, (d.resolved||[]).length, (d.handled||[]).length,
    (d.recentWA||[]).length, (d.agents||[]).length);

  if ((d.agents||[]).length)  Logger.log('first agent: %s', JSON.stringify(d.agents[0]));
  if ((d.pending||[]).length) Logger.log('first pending: %s', JSON.stringify(d.pending[0]));
}
function RUN_DASH_PROBE() {
  probeDashboardData_();
}