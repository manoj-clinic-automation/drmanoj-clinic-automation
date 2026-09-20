/* ============================================================================
 *  VPS_Lab_Files.gs  -  S333 build (session 273, 20-Sep-2026; S332 + the X-ray folders)
 *  Lives in the UPIReconciliation Apps Script project of drmka.ortho@gmail.com, beside
 *  VPS_Push_Lab.gs (which it does NOT change), and uses the SAME script property FINANCE_VPS_TOKEN.
 *
 *  WHAT IT DOES. Every 15 minutes it takes each NK Pathology report e-mail it has not filed yet,
 *  saves the PDF into this account's Google Drive:
 *      Clinic Records / Blood / Sep 2026 / 19-Sep / "2026-09-19 · 8118 · <name> · Blood report.pdf"
 *  and tells the clinic server the file's Drive id (never the file itself). The doctors' patient-record
 *  page then opens it. The folder is shared ONLY with the clinic server's read-only reader account,
 *  quietly (no e-mail); nothing is ever made public. The same PDF sent twice is kept once.
 *
 *  S333: setup also makes Clinic Records / X-ray test, X-ray inbox, X-ray check (inside the same shared
 *  folder) and tells the server their ids. Staff put the pen drive's X-ray files into "X-ray test" for the
 *  read-only test run; nothing is renamed until the doctor has looked.
 *
 *  ONE TIME:  add this as a new file in the project, Save, choose  setupLabFiles  in the function box
 *  and press Run. It makes the folders, shares them with the server, installs the 15-minute trigger,
 *  files every report since 17-Sep, and prints a short check including this Drive's free space.
 *  verifyLabFiles() prints the same check at any time.
 * ========================================================================== */

var REC_BASE     = 'https://followup.dr-manoj.in/finance/records/api/';
var REC_SEARCH   = 'from:nkpathology@gmail.com subject:(Your Report) newer_than:4d';
var REC_FIRST    = 'from:nkpathology@gmail.com subject:(Your Report) after:2026/09/16';
var REC_TIME_MS  = 4.5 * 60 * 1000;
var REC_ROOT     = 'Clinic Records';
var REC_TZ       = 'Asia/Kolkata';

function verifyLabFiles() {
  var props = PropertiesService.getScriptProperties();
  var tok = props.getProperty('FINANCE_VPS_TOKEN');
  var trig = ScriptApp.getProjectTriggers().filter(function (t) { return t.getHandlerFunction() === 'fileLabReports'; });
  var filed = props.getKeys().filter(function (k) { return k.indexOf('lab_filed_') === 0; }).length;
  var used = DriveApp.getStorageUsed(), lim = DriveApp.getStorageLimit();
  var gb = function (b) { return (b / 1073741824).toFixed(1) + ' GB'; };
  var msg = 'FINANCE_VPS_TOKEN : ' + (tok ? 'present' : '*** MISSING ***')
          + '\nfiling trigger    : ' + (trig.length ? 'installed (every 15 min)' : '*** NONE ***')
          + '\nfolder            : ' + (props.getProperty('rec_root_id') ? REC_ROOT + ' (shared with ' + (props.getProperty('rec_reader') || '?') + ')' : '*** NOT MADE ***')
          + '\nX-ray folders     : ' + (props.getProperty('rec_root_id') ? 'X-ray test, X-ray inbox, X-ray check' : '-')
          + '\nreports filed     : ' + filed
          + '\nDrive space       : ' + gb(used) + ' used of ' + (lim > 0 ? gb(lim) : 'unlimited')
          + (lim > 0 ? ' (' + Math.round(100 * used / lim) + '%)' : '');
  Logger.log(msg);
  return msg;
}

function setupLabFiles() {
  var root = _recRoot(true);
  var ids = { root_id: root.getId(), blood_id: _sub(root, 'Blood').getId(),
              xray_test_id: _sub(root, 'X-ray test').getId(), xray_inbox_id: _sub(root, 'X-ray inbox').getId(),
              xray_check_id: _sub(root, 'X-ray check').getId() };
  var f = _call('folders', 'post', ids);
  if (f.getResponseCode() !== 200) throw new Error('the server did not take the folder ids (' + f.getResponseCode() + ')');
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fileLabReports') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('fileLabReports').timeBased().everyMinutes(15).create();
  _fileLab(REC_FIRST);
  return verifyLabFiles();
}

function fileLabReports() { _fileLab(REC_SEARCH); }

function _call(path, method, body) {
  var tok = PropertiesService.getScriptProperties().getProperty('FINANCE_VPS_TOKEN');
  var o = { method: method, headers: { 'X-Finance-Cron': tok }, muteHttpExceptions: true };
  if (body) { o.contentType = 'application/json'; o.payload = JSON.stringify(body); }
  return UrlFetchApp.fetch(REC_BASE + path, o);
}

/* The Clinic Records folder, made once and shared (reader, no e-mail) with the server's reader account. */
function _recRoot(share) {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('rec_root_id'), root = null;
  if (id) { try { root = DriveApp.getFolderById(id); if (root.isTrashed()) root = null; } catch (e) { root = null; } }
  if (!root) {
    var it = DriveApp.getRootFolder().getFoldersByName(REC_ROOT);
    root = it.hasNext() ? it.next() : DriveApp.getRootFolder().createFolder(REC_ROOT);
    props.setProperty('rec_root_id', root.getId());
  }
  if (share) {
    var r = _call('reader', 'get');
    var j = JSON.parse(r.getContentText() || '{}');
    if (r.getResponseCode() !== 200 || !j.email) throw new Error('the server did not name its reader account (' + r.getResponseCode() + ')');
    var p = UrlFetchApp.fetch('https://www.googleapis.com/drive/v3/files/' + root.getId() + '/permissions?sendNotificationEmail=false',
      { method: 'post', contentType: 'application/json', muteHttpExceptions: true,
        headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
        payload: JSON.stringify({ role: 'reader', type: 'user', emailAddress: j.email }) });
    if (p.getResponseCode() !== 200) throw new Error('sharing with the server failed (' + p.getResponseCode() + ')');
    props.setProperty('rec_reader', j.email);
  }
  return root;
}

function _sub(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function _dayFolder(d) {
  var root = _recRoot(false);
  var blood = _sub(root, 'Blood');
  var month = _sub(blood, Utilities.formatDate(d, REC_TZ, 'MMM yyyy'));
  return _sub(month, Utilities.formatDate(d, REC_TZ, 'dd-MMM'));
}

function _nameOf(subject) {
  var s = String(subject || '').replace(/^.*?Your\s+Report\s*/i, '').replace(/\(\s*[0-9]{1,8}\s*\)\s*$/, '');
  s = s.replace(/[\\\/:*?"<>|]+/g, ' ').replace(/\s+/g, ' ').trim();
  return s.substring(0, 60);
}

function _fileLab(query) {
  var started = Date.now();
  var props = PropertiesService.getScriptProperties();
  if (!props.getProperty('FINANCE_VPS_TOKEN')) { Logger.log('FINANCE_VPS_TOKEN missing - nothing filed'); return; }
  var batch = [], keys = [];
  var threads = GmailApp.search(query, 0, 200);
  for (var i = 0; i < threads.length && Date.now() - started < REC_TIME_MS; i++) {
    var msgs = threads[i].getMessages();
    for (var j = 0; j < msgs.length && Date.now() - started < REC_TIME_MS; j++) {
      var m = msgs[j];
      var k = 'lab_filed_' + m.getId();
      if (props.getProperty(k)) continue;
      var mt = /\(\s*([0-9]{1,8})\s*\)\s*$/.exec(m.getSubject() || '');
      if (!mt || m.getFrom().indexOf('nkpathology@gmail.com') < 0) continue;
      var cid = mt[1], d = m.getDate();
      var at = Utilities.formatDate(d, REC_TZ, 'yyyy-MM-dd HH:mm:ss');
      var base = Utilities.formatDate(d, REC_TZ, 'yyyy-MM-dd') + ' · ' + cid + ' · ' + _nameOf(m.getSubject()) + ' · Blood report';
      var pdfs = m.getAttachments().filter(function (a) {
        return (a.getContentType() || '').indexOf('pdf') >= 0 || /\.pdf$/i.test(a.getName() || '');
      });
      if (!pdfs.length) {
        batch.push({ msg_id: m.getId(), clinic_id: cid, received_at: at, drive_id: '', file_name: '' });
      }
      for (var a = 0; a < pdfs.length; a++) {
        var blob = pdfs[a].copyBlob();
        var hex = Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, blob.getBytes())
          .map(function (b) { return ('0' + (b & 255).toString(16)).slice(-2); }).join('');
        var fid = props.getProperty('lab_md5_' + hex);
        var name = base + (pdfs.length > 1 ? ' ' + (a + 1) : '') + '.pdf';
        if (!fid) {
          fid = _dayFolder(d).createFile(blob.setName(name)).getId();
          props.setProperty('lab_md5_' + hex, fid);
        }
        batch.push({ msg_id: m.getId(), clinic_id: cid, received_at: at, drive_id: fid, file_name: name,
                     mime: 'application/pdf', bytes: blob.getBytes().length });
      }
      keys.push(k);
    }
  }
  if (!batch.length) return;
  var r = _call('lab-file', 'post', { files: batch });
  if (r.getResponseCode() !== 200) { Logger.log('server said ' + r.getResponseCode() + ' - will retry next run'); return; }
  keys.forEach(function (k) { props.setProperty(k, '1'); });
  Logger.log('filed ' + keys.length + ' report e-mail(s), ' + batch.length + ' line(s)');
}
