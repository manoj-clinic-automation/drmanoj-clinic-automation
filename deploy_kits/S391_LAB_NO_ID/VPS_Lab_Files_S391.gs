/* ============================================================================
 *  VPS_Lab_Files.gs  -  S391 build (session 279, 24-Sep-2026; S332 + S333 X-ray folders + S344 WhatsApp + S345 papers + S373 X-ray filing + S391 no-ID reports)
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
 *  S344: each run also asks the server which photos/PDFs patients sent on the clinic WhatsApp, saves each
 *  into Clinic Records / WhatsApp / <Mon YYYY> / <DD-Mon>, and reports the Drive id. Reception then confirms
 *  the patient and the kind in Check karein; nothing is filed to a patient before that.
 *
 *  S345: each run also carries the papers staff or the doctor added (MRI/CT, discharge, outside reports,
 *  event papers) from the clinic server to Clinic Records / Scans | Papers | Blood outside | X-ray outside,
 *  then tells the server, which files it on the patient and deletes its own copy.
 *
 *  S373: each run also files the X-ray photos in "X-ray test" / "X-ray inbox" as the server's plan says
 *  (Clinic Records / X-ray / <Mon YYYY> / <DD-Mon>, originals to X-ray inbox / _filed, never deleted).
 *
 *  S391: a report whose subject has NO clinic ID ("Your Report  MRS. <name>") used to be skipped for ever. Now the
 *  run asks the clinic server (POST /finance/slips/api/lab-noid, same token) which patient it is; the server answers
 *  when it is certain (the one open blood test of that name) or when reception has picked the patient on Report baaki,
 *  and the PDF is then filed exactly like the others. Until then the e-mail is simply asked about again next run.
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
var REC_NOID_URL = 'https://followup.dr-manoj.in/finance/slips/api/lab-noid';   // S391

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
  _sub(root, 'WhatsApp');
  var f = _call('folders', 'post', ids);
  if (f.getResponseCode() !== 200) throw new Error('the server did not take the folder ids (' + f.getResponseCode() + ')');
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fileLabReports') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('fileLabReports').timeBased().everyMinutes(15).create();
  _fileLab(REC_FIRST);
  return verifyLabFiles();
}

function fileLabReports() {
  _fileLab(REC_SEARCH);
  try { _fileWa(); } catch (e) { Logger.log('WhatsApp step: ' + e); }
  try { _fileUploads(); } catch (e) { Logger.log('Papers step: ' + e); }
  try { _fileXray(); } catch (e) { Logger.log('X-ray step: ' + e); }
}

/* S373 (23-Sep-2026, the owner: "the X-ray upload test period is over"): the X-ray photos staff put in
   "X-ray test" or "X-ray inbox". The SERVER decides (xray-plan); this script only copies, moves and reports.
   file  -> a copy under the new name into Clinic Records / X-ray / Mon YYYY / DD-Mon, and the original moves
            to X-ray inbox / _filed / <today>   (if the move fails the copy is trashed, so nothing is doubled)
   check -> moved to "X-ray check"; the staff type the clinic ID in Check karein and the next run files it
   dup   -> moved to X-ray inbox / _filed / duplicates
   Nothing is ever deleted. A report the server did not take is kept and sent first next run. */
function _fileXray() {
  var props = PropertiesService.getScriptProperties();
  var left = props.getProperty('xray_unreported');
  if (left) {
    var p0 = _call('xray-done', 'post', { files: JSON.parse(left) });
    if (p0.getResponseCode() !== 200) { Logger.log('X-ray: earlier report still not taken (' + p0.getResponseCode() + ')'); return; }
    props.deleteProperty('xray_unreported');
  }
  var r = _call('xray-plan', 'get');
  if (r.getResponseCode() !== 200) { Logger.log('xray-plan said ' + r.getResponseCode()); return; }
  var items = (JSON.parse(r.getContentText() || '{}').items) || [];
  if (!items.length) return;
  var t0 = Date.now(), root = _recRoot(false), inbox = _sub(root, 'X-ray inbox'), filed = _sub(inbox, '_filed');
  var check = _sub(root, 'X-ray check'), today = Utilities.formatDate(new Date(), REC_TZ, 'dd-MMM'), out = [];
  for (var i = 0; i < items.length; i++) {
    if (Date.now() - t0 > 3 * 60 * 1000) break;          // the rest next run
    var it = items[i];
    try {
      var f = DriveApp.getFileById(it.id);
      if (it.action === 'file') {
        var dest = root;
        for (var k = 0; k < it.path.length; k++) dest = _sub(dest, it.path[k]);
        var copy = f.makeCopy(it.name, dest);
        try { f.moveTo(_sub(filed, today)); } catch (e) { copy.setTrashed(true); Logger.log('X-ray not moved, copy withdrawn: ' + e); continue; }
        out.push({ id: it.id, action: 'file', dest_id: copy.getId(), name: it.name });
      } else if (it.action === 'check') {
        f.moveTo(check); out.push({ id: it.id, action: 'check' });
      } else if (it.action === 'dup') {
        f.moveTo(_sub(filed, 'duplicates')); out.push({ id: it.id, action: 'dup' });
      }
    } catch (e) { Logger.log('X-ray not filed: ' + e); }
  }
  if (out.length) {
    var p = _call('xray-done', 'post', { files: out });
    if (p.getResponseCode() !== 200) props.setProperty('xray_unreported', JSON.stringify(out));
    Logger.log('X-ray: ' + out.length + ' done, server said ' + p.getResponseCode());
  }
}

/* S344: photos and PDFs patients sent on the clinic WhatsApp. The server gives the message id, MyOperator's
   copy of the file, its type and time -- never the phone number. Saved once; the server remembers it. */
function _fileWa() {
  var r = _call('wa-pending', 'get');
  if (r.getResponseCode() !== 200) { Logger.log('wa-pending said ' + r.getResponseCode()); return; }
  var items = (JSON.parse(r.getContentText() || '{}').items) || [];
  if (!items.length) return;
  var wa = _sub(_recRoot(false), 'WhatsApp'), out = [];
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    try {
      var resp = UrlFetchApp.fetch(it.link, { muteHttpExceptions: true, followRedirects: true });
      var code = resp.getResponseCode();
      if (code === 403 || code === 404) { out.push({ msg_id: it.msg_id, drive_id: '' }); continue; }
      if (code !== 200) continue;                         // try again next run
      var blob = resp.getBlob(), ct = String(blob.getContentType() || '');
      var ext = ct.indexOf('pdf') >= 0 ? '.pdf' : ct.indexOf('png') >= 0 ? '.png' : (ct.indexOf('jpeg') >= 0 || ct.indexOf('jpg') >= 0) ? '.jpg' : '';
      var d = new Date(String(it.received_at).replace(' ', 'T') + '+05:30');
      if (isNaN(d.getTime())) d = new Date();
      var folder = _sub(_sub(wa, Utilities.formatDate(d, REC_TZ, 'MMM yyyy')), Utilities.formatDate(d, REC_TZ, 'dd-MMM'));
      var name = Utilities.formatDate(d, REC_TZ, 'yyyy-MM-dd HHmm') + ' · WhatsApp · ' + String(it.msg_id).slice(-8) + ext;
      var f = folder.createFile(blob.setName(name));
      out.push({ msg_id: it.msg_id, drive_id: f.getId(), file_name: name, mime: ct, bytes: blob.getBytes().length });
    } catch (e) { Logger.log('WhatsApp file not saved: ' + e); }
  }
  if (out.length) {
    var p = _call('wa-file', 'post', { files: out });
    Logger.log('WhatsApp: saved ' + out.length + ', server said ' + p.getResponseCode());
  }
}

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
      if (m.getFrom().indexOf('nkpathology@gmail.com') < 0) continue;
      var mt = /\(\s*([0-9]{1,8})\s*\)\s*$/.exec(m.getSubject() || '');
      var cid = mt ? mt[1] : _noidCid(m);                                   // S391
      if (!cid) continue;
      var d = m.getDate();
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

/* S391: the clinic ID for a report e-mailed without one -- '' while the server is not certain (asked again next run). */
function _noidCid(m) {
  var tok = PropertiesService.getScriptProperties().getProperty('FINANCE_VPS_TOKEN');
  var body = { reports: [{ msg_id: m.getId(), name: _nameOf(m.getSubject()),
                           received_at: Utilities.formatDate(m.getDate(), REC_TZ, 'yyyy-MM-dd HH:mm:ss') }] };
  try {
    var r = UrlFetchApp.fetch(REC_NOID_URL, { method: 'post', contentType: 'application/json', payload: JSON.stringify(body),
                                              headers: { 'X-Finance-Cron': tok }, muteHttpExceptions: true });
    if (r.getResponseCode() !== 200) return '';
    var x = (JSON.parse(r.getContentText() || '{}').reports || [])[0] || {};
    return /^[0-9A-Za-z\-\/]{1,12}$/.test(String(x.clinic_id || '')) ? String(x.clinic_id) : '';
  } catch (e) { return ''; }
}

/* S345: papers added on the clinic server (it keeps them only until they are in Drive). */
function _fileUploads() {
  var r = _call('upload-pending', 'get');
  if (r.getResponseCode() !== 200) { Logger.log('upload-pending said ' + r.getResponseCode()); return; }
  var items = (JSON.parse(r.getContentText() || '{}').items) || [];
  if (!items.length) return;
  var root = _recRoot(false), out = [];
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    try {
      var f = _call('upload-file/' + it.id, 'get');
      if (f.getResponseCode() !== 200) continue;
      var d = new Date(String(it.day) + 'T12:00:00+05:30');
      var folder = _sub(_sub(_sub(root, it.folder), Utilities.formatDate(d, REC_TZ, 'MMM yyyy')), Utilities.formatDate(d, REC_TZ, 'dd-MMM'));
      var blob = f.getBlob().setName(it.file_name);
      if (it.mime) blob.setContentType(it.mime);
      out.push({ id: it.id, drive_id: folder.createFile(blob).getId(), file_name: it.file_name });
    } catch (e) { Logger.log('paper not saved: ' + e); }
  }
  if (out.length) {
    var p = _call('upload-done', 'post', { files: out });
    Logger.log('Papers: saved ' + out.length + ', server said ' + p.getResponseCode());
  }
}
