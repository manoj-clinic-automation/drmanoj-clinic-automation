/****************************************************************************
 * UPI Reconciliation — logged (Accounting sheet) vs settled (ICICI digest)
 * Dr. Manoj Agarwal Clinic, Bareilly
 *
 * Compares, per day and per entity:
 *   LOGGED UPI  (what staff recorded in the "Accounting details" sheet)
 *   SETTLED UPI (what actually hit the bank, from the ICICI emails already
 *                pulled into the "Daily Clinic Reports" sheet)
 *
 *   Clinic   : OPD UPI + X-Ray UPI + Procedure UPI   <->  ICICI Dr Manoj Agarwal Clinic
 *   Sanjeevni: Medical UPI                            <->  ICICI Sanjeevni Medicos
 *   Lab      : Lab UPI                                <->  ICICI NK Pathology
 *
 * DISPLAY NOTE:
 *   In the email/sheet the columns read "Google Form" (what staff logged)
 *   and "Bank" (what settled), and the pharmacy entity is shown as
 *   "Sanjeevni". The internal entity key stays 'pharmacy' so matching is
 *   unaffected — only the displayed labels changed.
 *
 * FOOLPROOFING:
 *   - SETTLED_FLOOR ignores days before the ICICI ledger existed.
 *   - Open_Exceptions tab: every real gap is recorded and KEEPS being
 *     surfaced every run until the sheet is corrected and the gap clears —
 *     even after it scrolls past the rolling window. Nothing is forgotten.
 *   - Always emails a full daily report (matched + open exceptions).
 ****************************************************************************/

// ===== CONFIG ==============================================================
var ACCOUNTING_SHEET_ID = '1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8';
var REPORTS_SHEET_ID    = '1rwxrqAiLh9xBLezZLe7VqBWeCn3FRf_GZqOAEZi-oWc';
var RECON_TAB           = 'UPI_Reconciliation';
var OPEN_TAB            = 'Open_Exceptions';            // persistent gap ledger
var RECIPIENTS          = 'drmka.ortho@gmail.com';
var TOLERANCE           = 1;        // rupees; ignore differences at or below this
var LOOKBACK_DAYS       = 12;       // rolling window for the "Full grid"
var SETTLED_FIELD       = 'Gross_Amount';
var SETTLED_FLOOR       = '2026-06-06'; // first date the ICICI settled ledger has data
// ===========================================================================

var ENTITIES   = ['clinic', 'pharmacy', 'lab'];
var LABEL       = { clinic: 'Clinic', pharmacy: 'Sanjeevni', lab: 'Lab' };
var KEY_BY_LABEL = { Clinic: 'clinic', Sanjeevni: 'pharmacy', Lab: 'lab' };

function runUpiReconciliation() {
  var logged  = readLoggedUpi_();
  var settled = readSettledUpi_();
  var through = settled.__through;
  delete settled.__through;
  if (!through) { Logger.log('No ICICI data found; nothing to reconcile.'); return; }

  var fromKey = shiftDateKey_(through, -LOOKBACK_DAYS);
  if (fromKey < SETTLED_FLOOR) fromKey = SETTLED_FLOOR;

  // ---- build the windowed grid (for the sheet + email "Full grid") ----
  var rows = [], windowGaps = [];
  var dates = uniqueSortedDates_(logged, settled, fromKey, through);
  dates.forEach(function (d) {
    ENTITIES.forEach(function (e) {
      var ev = evalCell_(logged, settled, d, e);
      rows.push([d, LABEL[e], ev.logged, ev.settled, ev.diff, ev.status, noteFor_(logged, d, e)]);
      if (isGap_(ev.status)) windowGaps.push({ date: d, entity: LABEL[e] });
    });
  });
  writeReconTab_(rows);

  // ---- maintain the persistent open-exceptions ledger ----
  var ex = maintainOpenExceptions_(logged, settled, windowGaps);  // {open, resolved}

  sendReconEmail_(ex.open, ex.resolved, through, fromKey, rows);
  Logger.log('Window ' + fromKey + '..' + through + '; open exceptions: ' + ex.open.length +
             '; resolved this run: ' + ex.resolved.length);
}

/* ---------- evaluate one date+entity from the maps (any date) ---------- */
function evalCell_(logged, settled, dateKey, entityKey) {
  var L = logged[dateKey], S = settled[dateKey];
  var hasLogged = L && (entityKey in L);
  var lv = hasLogged ? L[entityKey] : '';
  var sv = (S && (entityKey in S)) ? S[entityKey] : 0;
  if (!hasLogged) return { status: 'NOT LOGGED YET', logged: '', settled: sv, diff: '' };
  var diff = round2_(lv - sv);
  var status = Math.abs(diff) <= TOLERANCE ? 'OK' : (lv > sv ? 'LOGGED > SETTLED' : 'SETTLED > LOGGED');
  return { status: status, logged: lv, settled: sv, diff: diff };
}
function isGap_(status) { return status === 'LOGGED > SETTLED' || status === 'SETTLED > LOGGED'; }
function noteFor_(logged, d, e) {
  var L = logged[d];
  return (L && L.dupNote && L.dupNote[e]) ? L.dupNote[e] : '';
}

/* ---------- persistent open-exceptions ledger ---------- */
function maintainOpenExceptions_(logged, settled, windowGaps) {
  var prev = readOpenExceptions_();          // [{date, entity, firstFlagged}]
  var byKey = {};
  prev.forEach(function (e) { byKey[e.date + '|' + e.entity] = e; });
  var today = todayKey_();

  // fold in any newly-found gaps from this run's window
  windowGaps.forEach(function (g) {
    var k = g.date + '|' + g.entity;
    if (!byKey[k]) byKey[k] = { date: g.date, entity: g.entity, firstFlagged: today };
  });

  // re-evaluate EVERY tracked key against current data (even outside the window)
  var open = [], resolved = [];
  Object.keys(byKey).forEach(function (k) {
    var e = byKey[k];
    var ev = evalCell_(logged, settled, e.date, KEY_BY_LABEL[e.entity]);
    e.logged = ev.logged; e.settled = ev.settled; e.diff = ev.diff; e.lastChecked = today;
    if (ev.status === 'OK') { e.resolvedOn = today; resolved.push(e); }     // fixed in the sheet
    else { e.status = ev.status; open.push(e); }
  });
  open.sort(function (a, b) { return a.date < b.date ? -1 : (a.date > b.date ? 1 : 0); });
  writeOpenExceptions_(open);
  return { open: open, resolved: resolved };
}

function readOpenExceptions_() {
  var ss = SpreadsheetApp.openById(REPORTS_SHEET_ID);
  var sh = ss.getSheetByName(OPEN_TAB);
  if (!sh) return [];
  var data = sh.getDataRange().getValues();
  var out = [];
  for (var r = 1; r < data.length; r++) {
    if (!data[r][0]) continue;
    out.push({ date: String(data[r][0]), entity: String(data[r][1]), firstFlagged: String(data[r][2]) });
  }
  return out;
}

function writeOpenExceptions_(open) {
  var ss = SpreadsheetApp.openById(REPORTS_SHEET_ID);
  var sh = ss.getSheetByName(OPEN_TAB) || ss.insertSheet(OPEN_TAB);
  sh.clearContents();
  var header = ['Date', 'Entity', 'First_Flagged', 'Days_Open', 'Google Form', 'Bank',
                'Diff', 'Status', 'Last_Checked', 'Correct_To (enter this)'];
  sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight('bold').setBackground('#fde8e8');
  var body = open.map(function (e) {
    return [e.date, e.entity, e.firstFlagged, daysBetween_(e.firstFlagged, todayKey_()),
            e.logged, e.settled, e.diff, e.status, e.lastChecked, e.settled];
  });
  if (body.length) sh.getRange(2, 1, body.length, header.length).setValues(body);
  sh.getRange('A:A').setNumberFormat('@');
  sh.getRange('C:C').setNumberFormat('@');
  sh.getRange('I:I').setNumberFormat('@');
  sh.setFrozenRows(1);
}

/* ---------- LOGGED side: the Accounting details sheet ---------- */
function readLoggedUpi_() {
  var ss = SpreadsheetApp.openById(ACCOUNTING_SHEET_ID);
  var out = {};
  ss.getSheets().forEach(function (sh) {
    var data = sh.getDataRange().getValues();
    if (data.length < 2) return;
    var hdr = data[0].map(function (h) { return String(h).trim(); });
    var kind = classifyTab_(hdr);
    if (!kind) return;
    var dateCol = idxOf_(hdr, 'Date');
    if (dateCol < 0) return;
    var cols;
    if (kind === 'clinic')   cols = ['OPD UPI', 'X-Ray UPI', 'Procedure UPI'].map(function (n) { return idxOf_(hdr, n); });
    if (kind === 'pharmacy') cols = [idxOf_(hdr, 'Medical UPI')];
    if (kind === 'lab')      cols = [idxOf_(hdr, 'UPI')];
    for (var r = 1; r < data.length; r++) {
      var key = toDateKey_(data[r][dateCol]);
      if (!key) continue;
      var v = 0;
      cols.forEach(function (c) { if (c >= 0) v += num_(data[r][c]); });
      if (!out[key]) out[key] = { dupNote: {} };
      if (kind in out[key]) { out[key][kind] += v; out[key].dupNote[kind] = 'multiple rows summed'; }
      else { out[key][kind] = v; }
    }
  });
  return out;
}

function classifyTab_(hdr) {
  if (hdr.indexOf('OPD UPI') > -1 && hdr.indexOf('Procedure UPI') > -1) return 'clinic';
  if (hdr.indexOf('Medical UPI') > -1) return 'pharmacy';
  if (hdr.indexOf('Lab Cash') > -1 && hdr.indexOf('Total Work') > -1) return 'lab';
  return null;
}

/* ---------- SETTLED side: ICICI tabs in Daily Clinic Reports ---------- */
function readSettledUpi_() {
  var ss = SpreadsheetApp.openById(REPORTS_SHEET_ID);
  var out = {}, through = '';
  ss.getSheets().forEach(function (sh) {
    var name = sh.getName().toUpperCase();
    if (name.indexOf('ICICI') !== 0) return;
    var entity = null;
    if (name.indexOf('PATHOLOGY') > -1) entity = 'lab';
    else if (name.indexOf('MEDICOS') > -1 || name.indexOf('SANJEEVNI') > -1) entity = 'pharmacy';
    else if (name.indexOf('CLINIC') > -1 || name.indexOf('MANOJ') > -1) entity = 'clinic';
    if (!entity) return;
    var data = sh.getDataRange().getValues();
    if (data.length < 2) return;
    var hdr = data[0].map(function (h) { return String(h).trim(); });
    var dCol = idxOf_(hdr, 'Txn_Date'), mCol = idxOf_(hdr, 'Mode'), aCol = idxOf_(hdr, SETTLED_FIELD);
    if (dCol < 0 || aCol < 0) return;
    for (var r = 1; r < data.length; r++) {
      if (mCol > -1 && String(data[r][mCol]).toUpperCase().indexOf('UPI') < 0) continue;
      var key = toDateKey_(data[r][dCol]);
      if (!key) continue;
      if (!out[key]) out[key] = {};
      out[key][entity] = round2_((out[key][entity] || 0) + num_(data[r][aCol]));
      if (key > through) through = key;
    }
  });
  out.__through = through;
  return out;
}

/* ---------- output: main sheet tab ---------- */
function writeReconTab_(rows) {
  var ss = SpreadsheetApp.openById(REPORTS_SHEET_ID);
  var sh = ss.getSheetByName(RECON_TAB) || ss.insertSheet(RECON_TAB);
  sh.clearContents();
  var header = ['Date', 'Entity', 'Google Form UPI', 'Bank UPI', 'Diff (Google Form-Bank)', 'Status', 'Note'];
  sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight('bold');
  if (rows.length) sh.getRange(2, 1, rows.length, header.length).setValues(rows);
  sh.getRange('A:A').setNumberFormat('@');
  sh.setFrozenRows(1);
}

/* ---------- output: email ---------- */
function sendReconEmail_(open, resolved, through, fromKey, rows) {
  var COLOR = { 'OK': '#137333', 'LOGGED > SETTLED': '#b00020', 'SETTLED > LOGGED': '#b06000', 'NOT LOGGED YET': '#888888' };
  var matched = rows.filter(function (r) { return r[5] === 'OK'; }).length;

  var h = [];
  h.push('<div style="font-family:Arial,sans-serif;font-size:14px;color:#222">');
  h.push('<h2 style="margin:0 0 4px">UPI Reconciliation</h2>');
  h.push('<p style="margin:0 0 14px;color:#666">Window ' + fromKey + ' to ' + through +
         ' &middot; ' + matched + ' matched &middot; <b style="color:#b00020">' + open.length +
         '</b> open exception' + (open.length === 1 ? '' : 's') + '</p>');

  // OPEN EXCEPTIONS — persists until fixed, regardless of window
  if (open.length) {
    h.push('<h3 style="margin:12px 0 6px;color:#b00020">&#9888; Open exceptions — fix in the sheet</h3>');
    h.push('<table style="border-collapse:collapse;font-size:14px">');
    h.push('<tr style="background:#f7e8e8">' +
           ['Date', 'Entity', 'Open', 'Google Form', 'Bank', 'Set UPI to'].map(function (c, i) {
             return '<th style="text-align:' + (i < 2 ? 'left' : 'right') + ';padding:4px 12px">' + c + '</th>';
           }).join('') + '</tr>');
    open.forEach(function (e) {
      var age = daysBetween_(e.firstFlagged, todayKey_());
      h.push('<tr>' +
        '<td style="padding:3px 12px">' + e.date + '</td>' +
        '<td style="padding:3px 12px">' + e.entity + '</td>' +
        '<td style="text-align:right;padding:3px 12px' + (age >= 3 ? ';color:#b00020;font-weight:bold' : '') + '">' + age + 'd</td>' +
        '<td style="text-align:right;padding:3px 12px">' + inr_(e.logged) + '</td>' +
        '<td style="text-align:right;padding:3px 12px">' + inr_(e.settled) + '</td>' +
        '<td style="text-align:right;padding:3px 12px;font-weight:bold">' + inr_(e.settled) + '</td></tr>');
    });
    h.push('</table>');
    h.push('<p style="margin:8px 0 0;color:#666;font-size:12.5px">' +
           'The bank settlement is the source of truth — set each day\u2019s UPI cell to the <b>Set UPI to</b> figure. ' +
           'Rows stay here every day until the gap clears.</p>');
  } else {
    h.push('<p style="color:#137333;font-weight:bold;margin:10px 0">&#10003; No open exceptions. Everything reconciles.</p>');
  }

  if (resolved.length) {
    h.push('<p style="color:#137333;margin:10px 0">&#10003; Cleared since last run: ' +
           resolved.map(function (e) { return e.date + ' ' + e.entity; }).join(', ') + '</p>');
  }

  // Full grid (windowed)
  h.push('<h3 style="margin:18px 0 6px">Full grid (' + fromKey + ' to ' + through + ')</h3>');
  h.push('<table style="border-collapse:collapse;font-size:13.5px">');
  h.push('<tr style="background:#f2f2f2">' +
         ['Date', 'Entity', 'Google Form', 'Bank', 'Diff', 'Status'].map(function (c, i) {
           return '<th style="text-align:' + (i < 2 ? 'left' : (i === 5 ? 'left' : 'right')) + ';padding:4px 12px">' + c + '</th>';
         }).join('') + '</tr>');
  rows.forEach(function (r) {
    var c = COLOR[r[5]] || '#222';
    h.push('<tr>' +
      '<td style="padding:2px 12px">' + r[0] + '</td>' +
      '<td style="padding:2px 12px">' + r[1] + '</td>' +
      '<td style="text-align:right;padding:2px 12px">' + (r[2] === '' ? '\u2014' : inr_(r[2])) + '</td>' +
      '<td style="text-align:right;padding:2px 12px">' + inr_(r[3]) + '</td>' +
      '<td style="text-align:right;padding:2px 12px">' + (r[4] === '' ? '' : inr_(r[4])) + '</td>' +
      '<td style="padding:2px 12px;color:' + c + '">' + r[5] + '</td></tr>');
  });
  h.push('</table>');
  h.push('<p style="margin-top:16px"><a href="https://docs.google.com/spreadsheets/d/' + REPORTS_SHEET_ID +
         '/edit">Open spreadsheet</a> &middot; tabs: ' + RECON_TAB + ', ' + OPEN_TAB + '</p></div>');

  var text = [];
  if (open.length) {
    text.push('UPI reconciliation — ' + open.length + ' open exception(s):', '');
    open.forEach(function (e) {
      text.push('  ' + e.date + '  ' + e.entity + ' — Google Form Rs' + e.logged + ' vs Bank Rs' + e.settled +
                ' (set UPI to Rs' + e.settled + ', open ' + daysBetween_(e.firstFlagged, todayKey_()) + 'd)');
    });
  } else { text.push('UPI reconciliation: no open exceptions through ' + through + '.'); }
  text.push('', 'Sheet: https://docs.google.com/spreadsheets/d/' + REPORTS_SHEET_ID + '/edit');

  MailApp.sendEmail({
    to: RECIPIENTS,
    subject: 'UPI reconciliation — ' + (open.length ? (open.length + ' open') : 'all clear') + ' (through ' + through + ')',
    body: text.join('\n'), htmlBody: h.join(''), name: 'Clinic Reconciliation'
  });
}

/* ---------- helpers ---------- */
function uniqueSortedDates_(logged, settled, fromKey, through) {
  var all = Object.keys(logged).concat(Object.keys(settled)), seen = {}, out = [];
  all.forEach(function (d) {
    if (seen[d]) return; seen[d] = 1;
    if (d >= fromKey && d <= through) out.push(d);
  });
  return out.sort();
}
function idxOf_(hdr, name) { for (var i = 0; i < hdr.length; i++) if (hdr[i] === name) return i; return -1; }
function num_(v) {
  if (v === null || v === '' || v === undefined) return 0;
  var n = parseFloat(String(v).replace(/[^0-9.\-]/g, ''));
  return isNaN(n) ? 0 : n;
}
function round2_(n) { return Math.round(n * 100) / 100; }
function inr_(n) { var x = (typeof n === 'number') ? n : num_(n); return '\u20B9' + round2_(x).toLocaleString('en-IN'); }
function toDateKey_(v) {
  if (v instanceof Date && !isNaN(v)) {
    var y = v.getFullYear(); if (y < 100) y += 2000;
    return y + '-' + pad_(v.getMonth() + 1) + '-' + pad_(v.getDate());
  }
  var s = String(v).trim(); if (!s) return '';
  var iso = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (iso) return iso[1] + '-' + pad_(iso[2]) + '-' + pad_(iso[3]);
  var m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{1,4})/);
  if (m) { var yy = parseInt(m[3], 10); if (yy < 100) yy += 2000; return yy + '-' + pad_(m[1]) + '-' + pad_(m[2]); }
  return '';
}
function pad_(n) { n = String(n); return n.length < 2 ? '0' + n : n; }
function shiftDateKey_(key, deltaDays) {
  var p = key.split('-'), d = new Date(parseInt(p[0], 10), parseInt(p[1], 10) - 1, parseInt(p[2], 10));
  d.setDate(d.getDate() + deltaDays);
  return d.getFullYear() + '-' + pad_(d.getMonth() + 1) + '-' + pad_(d.getDate());
}
function daysBetween_(a, b) {
  var pa = a.split('-'), pb = b.split('-');
  var da = new Date(pa[0], pa[1] - 1, pa[2]), db = new Date(pb[0], pb[1] - 1, pb[2]);
  return Math.round((db - da) / 86400000);
}
function todayKey_() { return Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd'); }

