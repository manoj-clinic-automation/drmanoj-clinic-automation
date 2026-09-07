/**********************************************************************
 * DAILY CLINIC REPORTS — Email -> Google Sheets automation
 * Dr. Manoj Agarwal Clinic, Bareilly
 *
 * v5: adds a per-vehicle TRIPS breakdown (start, end, duration, distance)
 *     below the vehicle summary, read from Trip.csv. Builds on v4
 *     (UTF-16 attendance decode + fixed-width parsing).
 **********************************************************************/

/********************* CONFIG — edit if needed ************************/
var CONFIG = {
  SPREADSHEET_NAME: 'Daily Clinic Reports',

  // Who receives the daily digest. Comma-separate for multiple.
  DIGEST_TO: 'drmanojkragarwal@gmail.com, drmka.ortho@gmail.com',

  LOOKBACK_DAYS: 2,                       // safe buffer for finding emails
  VEHICLE_SUBJECT: 'Manoj find me report',
  ICICI_SUBJECT:   'MerchantStatement',

  // Optional: prettier names for the digest.
  LABEL_OVERRIDES: {
    'DR_MANOJ_AGARWAL_CLINIC': 'Clinic',
    'SANJEEVNI_MEDICOS':       'Medicos',
    'NK_PATHOLOGY':            'NK Pathology'
  },

  // Attendance (ONtime) email subject — shared by the Late-Arrival,
  // Early-Departure and Absent mails, so the code picks the ABSENT csv.
  ATTENDANCE_SUBJECT: 'ONtime Employee Manager Report',

  // Both vehicles are always shown in the digest, with friendly labels.
  VEHICLES: [
    { reg: 'UP25AE0028', label: 'Scooty' },
    { reg: 'UP25Q0997',  label: 'Bike'   }
  ]
};

var VEHICLE_HEADERS = ['Date','Vehicle','Distance_Km','Cumulative_Km',
  'Max_Speed_Kmph','Motion_Time','Idle_Time','Trip_Count','Added_On'];
var ICICI_HEADERS = ['Txn_Date','Settlement_Date','Timestamp','Mode','Scheme',
  'RRN','Transaction_ID','Gross_Amount','MDR_Charges','GST','Net_Settlement',
  'Txn_Type','Terminal_ID','Added_On'];
var VEH_MONTH_HEADERS   = ['Month','Vehicle','Days','Total_Km'];
var ICICI_MONTH_HEADERS = ['Month','Account','Txn_Count','Gross','MDR','GST','Net'];
var REGISTRY_HEADERS = ['MID','Merchant_Name','Label','Tab_Name','First_Seen','Last_Seen'];
var RUNLOG_HEADERS   = ['Run_Time','Date_Covered','Vehicle_Added','ICICI_Added','Notes'];

/********************* ENTRY POINTS **********************************/

// Run ONCE manually to create the spreadsheet + base tabs.
function setup() {
  var ss = getOrCreateSpreadsheet_();
  Logger.log('Spreadsheet ready: ' + ss.getUrl());
}

// What the daily trigger calls.
function runDaily() {
  var ss = getOrCreateSpreadsheet_();
  var notes = [];

  var veh = processVehicle_(ss, notes);
  var ici = processIcici_(ss, notes);
  var att = processAttendance_(ss, notes);

  recomputeVehicleCumulative_(ss);
  recomputeVehicleMonthly_(ss);
  recomputeIciciMonthly_(ss);

  logRun_(ss, veh, ici, notes);
  sendDigest_(ss, veh, ici, notes, att);
}

// Run this ONCE if you already got duplicate vehicle rows or a blank NK tab.
function repairExistingData() {
  var ss = getOrCreateSpreadsheet_();
  dedupeVehicleLog_(ss);
  fixNkPathologyTab_(ss);
  recomputeVehicleCumulative_(ss);
  recomputeVehicleMonthly_(ss);
  recomputeIciciMonthly_(ss);
  Logger.log('Repair complete: duplicate vehicle rows removed; NK blank tab fixed if present.');
}

/********************* VEHICLE STREAM ********************************/

function processVehicle_(ss, notes) {
  var out = { added: 0, rows: [], found: false, trips: [] };
  var msg = findLatestMessageBySubject_(CONFIG.VEHICLE_SUBJECT);
  if (!msg) { notes.push('Vehicle email not found.'); return out; }
  out.found = true;

  var summaryBlob = getAttachmentByName_(msg, 'Summary.csv');
  if (!summaryBlob) { notes.push('Summary.csv missing in vehicle email.'); return out; }

  var tripBlob = getAttachmentByName_(msg, 'Trip.csv');
  out.trips = parseTrips_(tripBlob);                 // for the digest breakdown
  var trips = countTripsByVehicle_(tripBlob);

  var rows = Utilities.parseCsv(summaryBlob.getDataAsString());
  var col = headerIndex_(rows[0]);
  var sheet = getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS);
  var seen = existingVehicleKeySet_(sheet);

  for (var i = 1; i < rows.length; i++) {
    var r = rows[i];
    if (!r[col['Device Name']]) continue;
    var vehicle = String(r[col['Device Name']]).trim();
    var date = normDate_(String(r[col['Start Time']] || '').split(' ')[0]);
    if (!date || !vehicle) continue;
    var key = date + '|' + vehicle;
    if (seen[key]) continue;

    sheet.appendRow([date, vehicle, toNum_(r[col['Distance (Kms)']]), '',
      toNum_(r[col['Max Speed']]), r[col['Motion Time']] || '',
      r[col['Idle Time']] || '', trips[vehicle] || 0, nowStr_()]);
    seen[key] = true;
    out.added++;
    out.rows.push({ vehicle: vehicle, date: date, km: toNum_(r[col['Distance (Kms)']]) });
  }
  return out;
}

function countTripsByVehicle_(blob) {
  var counts = {};
  if (!blob) return counts;
  var rows = Utilities.parseCsv(blob.getDataAsString());
  var col = headerIndex_(rows[0]);
  for (var i = 1; i < rows.length; i++) {
    var v = rows[i][col['Device Name']];
    if (v) counts[String(v).trim()] = (counts[String(v).trim()] || 0) + 1;
  }
  return counts;
}

// Parse Trip.csv into per-trip rows for the digest.
// Columns: Device Name, Driver Name, Driver Mobile, Duration, Distance (Kms),
//          Average Speed, Max Speed, Start Time, End Time.
// Start/End look like "14-06-2026 10:04". Duration looks like "0 H 24 M".
function parseTrips_(blob) {
  if (!blob) return [];
  var rows = Utilities.parseCsv(blob.getDataAsString());
  if (!rows.length) return [];
  var col = headerIndex_(rows[0]);
  var iVeh = col['Device Name'], iDur = col['Duration'],
      iDist = col['Distance (Kms)'], iStart = col['Start Time'], iEnd = col['End Time'];
  var out = [];
  for (var i = 1; i < rows.length; i++) {
    var r = rows[i];
    var veh = String(r[iVeh] || '').trim();
    if (!veh) continue;
    out.push({
      vehicle: veh,
      start: tripTime_(r[iStart]),
      end: tripTime_(r[iEnd]),
      dur: prettyDuration_(r[iDur]),
      km: toNum_(r[iDist])
    });
  }
  return out;
}

// "14-06-2026 10:04" -> "10:04"  (keeps just the clock time for readability)
function tripTime_(v) {
  var s = String(v || '').trim();
  var m = s.match(/(\d{1,2}:\d{2})/);
  return m ? m[1] : s;
}

// "0 H 24 M" -> "24 min";  "1 H 5 M" -> "1 h 5 min";  "0 H 0 M" -> "<1 min"
function prettyDuration_(v) {
  var s = String(v || '').trim();
  var m = s.match(/(\d+)\s*H\s*(\d+)\s*M/i);
  if (!m) return s;
  var hrs = parseInt(m[1], 10), mins = parseInt(m[2], 10);
  if (hrs > 0 && mins > 0) return hrs + ' h ' + mins + ' min';
  if (hrs > 0)             return hrs + ' h';
  if (mins > 0)            return mins + ' min';
  return '<1 min';
}

/********************* ATTENDANCE STREAM (ONtime absent list) ********/

function processAttendance_(ss, notes) {
  var out = { found: false, dated: '', absentees: [], note: '' };
  var msgs = findMessagesBySubject_(CONFIG.ATTENDANCE_SUBJECT);
  if (!msgs.length) { notes.push('Attendance (ONtime) email not found.'); return out; }

  // Subject is shared by the Late-Arrival, Early-Departure and Absent mails —
  // pick the one carrying the ABSENT csv.
  var blob = null, picked = null;
  for (var m = 0; m < msgs.length && !blob; m++) {
    var atts = msgs[m].getAttachments({ includeInlineImages: false });
    for (var a = 0; a < atts.length; a++) {
      if (/ABSENT.*\.csv$/i.test(atts[a].getName())) { blob = atts[a].copyBlob(); picked = msgs[m]; break; }
    }
  }
  if (!blob) { notes.push('ONtime email found but ABSENT csv not located.'); return out; }
  out.found = true;

  try {
    var body = picked.getPlainBody() || '';
    var mm = body.match(/On Dated\s*:\s*(\d{2}\/\d{2}\/\d{4})/);
    if (mm) out.dated = mm[1];
  } catch (e) {}

  var parsed = parseAbsentees_(blob);
  out.absentees = parsed.names;
  out.note = parsed.note;
  return out;
}

// Read raw bytes and decode as text, auto-detecting UTF-16 (the ONtime export
// uses UTF-16, which shows up as a null byte between every letter). Falls back
// to UTF-8 if it isn't UTF-16.
function readBlobSmart_(blob) {
  var bytes = blob.getBytes();
  // UTF-16 byte-order marks: FF FE (LE) or FE FF (BE).
  if (bytes.length >= 2) {
    var b0 = bytes[0] & 0xFF, b1 = bytes[1] & 0xFF;
    if (b0 === 0xFF && b1 === 0xFE) return blob.getDataAsString('UTF-16LE');
    if (b0 === 0xFE && b1 === 0xFF) return blob.getDataAsString('UTF-16BE');
  }
  // No BOM: detect interleaved null bytes (classic UTF-16 without a BOM).
  var nulls = 0, checked = Math.min(bytes.length, 200);
  for (var i = 0; i < checked; i++) if (bytes[i] === 0) nulls++;
  if (checked > 0 && nulls > checked / 4) {
    // Lots of zero bytes -> UTF-16. Guess endianness from where the zeros fall.
    return (bytes[0] === 0) ? blob.getDataAsString('UTF-16BE')
                            : blob.getDataAsString('UTF-16LE');
  }
  return blob.getDataAsString();   // normal UTF-8 / ASCII
}

// The ONtime "Absent" CSV is UTF-16 encoded and laid out in fixed-width / tab
// columns with a "----" divider row. Decode first, then split columns
// (tab, else 2+ spaces, else comma) and find the column whose header has "name".
function parseAbsentees_(blob) {
  var out = { names: [], note: '' };

  var raw = readBlobSmart_(blob);
  if (!raw) return out;

  // Strip any leftover BOM / stray null characters defensively.
  raw = raw.replace(/^\uFEFF/, '').replace(/\u0000/g, '');

  var lines = raw.split(/\r\n|\r|\n/).filter(function (ln) { return ln.trim() !== ''; });
  if (!lines.length) return out;

  var rows = lines.map(function (ln) {
    var parts;
    if (ln.indexOf('\t') >= 0)       parts = ln.split('\t');
    else if (/\s{2,}/.test(ln))      parts = ln.split(/\s{2,}/);
    else                             parts = ln.split(',');
    return parts.map(function (c) { return String(c).trim(); });
  });

  var hdr = -1, nameCol = -1;
  for (var i = 0; i < Math.min(rows.length, 10) && hdr < 0; i++) {
    for (var j = 0; j < rows[i].length; j++) {
      if (/name/i.test(rows[i][j])) { hdr = i; nameCol = j; break; }
    }
  }
  if (hdr < 0) { out.note = 'name column not found'; return out; }

  for (var r = hdr + 1; r < rows.length; r++) {
    var v = (rows[r][nameCol] || '').trim();
    if (!v) continue;
    if (/^[-\s]+$/.test(v)) continue;                          // skip the "----" divider row
    if (/^(total|grand total|page|generated|report|sno|s\.?\s*no|sr\.?|count)\b/i.test(v)) continue;
    out.names.push(v);
  }

  var seen = {}, dd = [];
  out.names.forEach(function (n) { if (!seen[n]) { seen[n] = 1; dd.push(n); } });
  out.names = dd;
  return out;
}

/********************* ICICI STREAM (auto-discovery) ****************/

function processIcici_(ss, notes) {
  var out = { byAccount: {}, totalAdded: 0 };
  var msgs = findMessagesBySubject_(CONFIG.ICICI_SUBJECT);
  if (!msgs.length) { notes.push('No ICICI MerchantStatement email found.'); return out; }

  var handled = {};                        // one (latest) file per MID per run
  for (var m = 0; m < msgs.length; m++) {
    var atts = msgs[m].getAttachments();
    for (var a = 0; a < atts.length; a++) {
      var name = atts[a].getName();
      var lower = name.toLowerCase();
      var isXlsx = lower.indexOf('.xlsx') >= 0;
      var isCsv  = lower.indexOf('.csv')  >= 0;
      if (!isXlsx && !isCsv) continue;        // ignore the .zip / .pdf copies
      var meta = parseIciciFilename_(name);
      if (!meta) continue;
      if (handled[meta.mid]) continue;        // one statement per MID per run
      handled[meta.mid] = true;

      var acct = registerIciciAccount_(ss, meta.mid, meta.rawName);
      var res = out.byAccount[acct.label] ||
        (out.byAccount[acct.label] = { added:0, gross:0, net:0, mdr:0, gst:0, count:0 });
      var values = isXlsx
        ? xlsxToValues_(atts[a].copyBlob())
        : Utilities.parseCsv(atts[a].copyBlob().getDataAsString());
      ingestIcici_(ss, acct, values, res);
    }
  }
  for (var lbl in out.byAccount) out.totalAdded += out.byAccount[lbl].added;
  if (out.totalAdded === 0 && !Object.keys(out.byAccount).length)
    notes.push('ICICI emails found but no .xlsx statements parsed.');
  return out;
}

function ingestIcici_(ss, acct, values, res) {
  if (!values || values.length < 2) return;
  var ci = {};
  values[0].forEach(function (h, i) { ci[String(h).trim()] = i; });
  var sheet = getSheet_(ss, acct.tab, ICICI_HEADERS);
  var seen = existingKeySet_(sheet, [6]);   // Transaction_ID

  for (var i = 1; i < values.length; i++) {
    var r = values[i];
    var txid = r[ci['Transaction ID']];
    var ttype = r[ci['Transaction Type']];
    if (!txid || !ttype) continue;          // skip subtotal / grand-total rows
    txid = String(txid).trim();
    if (seen[txid]) continue;

    var ts = r[ci['Transaction Date']];
    sheet.appendRow([
      normDate_(ts) || normDate_(r[ci['TXN DT']]),
      normDate_(r[ci['Date of Settlement Initiation']]),
      ts || '', r[ci['Mode of Payment']] || '', r[ci['Scheme Name']] || '',
      r[ci['RRN']] || '', txid,
      toNum_(r[ci['Transaction Amount']]), toNum_(r[ci['Transaction Charges']]),
      toNum_(r[ci['GST']]), toNum_(r[ci['Net Settlement Amount']]),
      ttype, r[ci['Terminal ID']] || '', nowStr_()
    ]);
    seen[txid] = true;
    res.added++; res.count++;
    res.gross += toNum_(r[ci['Transaction Amount']]);
    res.mdr   += toNum_(r[ci['Transaction Charges']]);
    res.gst   += toNum_(r[ci['GST']]);
    res.net   += toNum_(r[ci['Net Settlement Amount']]);
  }
}

// Filename: {MID}_MS{MERCHANT}_{DDMMYYYY}_ICICI_POS_CD.xlsx
function parseIciciFilename_(name) {
  var m = name.match(/^(\d{6,})_MS(.+?)_(\d{8})_ICICI/i);
  if (!m) return null;
  return { mid: m[1], rawName: m[2], date: m[3] };
}

function registerIciciAccount_(ss, mid, rawName) {
  var reg = getSheet_(ss, 'ICICI_Accounts', REGISTRY_HEADERS);
  var data = reg.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(mid)) {
      reg.getRange(i + 1, 6).setValue(nowStr_());     // Last_Seen
      return { mid: mid, label: data[i][2], tab: data[i][3] };
    }
  }
  var label = CONFIG.LABEL_OVERRIDES[rawName] || prettyLabel_(rawName);
  var baseTab = 'ICICI_' + sanitizeTab_(rawName);
  var existingBase = ss.getSheetByName(baseTab);
  var tab = existingBase && isSheetEmptyOrHeaderOnly_(existingBase, ICICI_HEADERS)
    ? baseTab
    : uniqueTabName_(ss, baseTab);
  getSheet_(ss, tab, ICICI_HEADERS);
  reg.appendRow([mid, rawName, label, tab, nowStr_(), nowStr_()]);
  return { mid: mid, label: label, tab: tab };
}

/********************* MONTHLY ROLLUPS ******************************/

function recomputeVehicleMonthly_(ss) {
  var data = getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS).getDataRange().getValues();
  var agg = {};
  for (var i = 1; i < data.length; i++) {
    var d = normDate_(data[i][0]), v = data[i][1];
    if (!d || !v) continue;
    var k = d.substring(0, 7) + '|' + v;
    agg[k] = agg[k] || { days: 0, km: 0 };
    agg[k].days++; agg[k].km += toNum_(data[i][2]);
  }
  writeAggSheet_(ss, 'Vehicle_Monthly', VEH_MONTH_HEADERS, agg, function (k, a) {
    var p = k.split('|'); return [p[0], p[1], a.days, round2_(a.km)];
  });
}

function recomputeIciciMonthly_(ss) {
  var reg = getSheet_(ss, 'ICICI_Accounts', REGISTRY_HEADERS).getDataRange().getValues();
  var agg = {};
  for (var ri = 1; ri < reg.length; ri++) {
    var label = reg[ri][2], tab = reg[ri][3];
    if (!tab) continue;
    var sh = ss.getSheetByName(tab);
    if (!sh) continue;
    var data = sh.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      var d = normDate_(data[i][0]); if (!d) continue;
      var k = d.substring(0, 7) + '|' + label;
      agg[k] = agg[k] || { count:0, gross:0, mdr:0, gst:0, net:0 };
      agg[k].count++;
      agg[k].gross += toNum_(data[i][7]); agg[k].mdr += toNum_(data[i][8]);
      agg[k].gst   += toNum_(data[i][9]); agg[k].net += toNum_(data[i][10]);
    }
  }
  writeAggSheet_(ss, 'ICICI_Monthly', ICICI_MONTH_HEADERS, agg, function (k, a) {
    var p = k.split('|');
    return [p[0], p[1], a.count, round2_(a.gross), round2_(a.mdr), round2_(a.gst), round2_(a.net)];
  });
}

function recomputeVehicleCumulative_(ss) {
  var sheet = getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS);
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return;
  var body = data.slice(1).filter(function (r) { return r[0] && r[1]; });
  body.sort(function (a, b) {
    if (a[1] === b[1]) return String(a[0]) < String(b[0]) ? -1 : 1;
    return a[1] < b[1] ? -1 : 1;
  });
  var run = {};
  body.forEach(function (r) { run[r[1]] = (run[r[1]] || 0) + toNum_(r[2]); r[3] = round2_(run[r[1]]); });
  sheet.getRange(2, 1, body.length, VEHICLE_HEADERS.length).setValues(body);
}

/********************* DIGEST EMAIL ********************************/

function sendDigest_(ss, veh, ici, notes, att) {
  var to = CONFIG.DIGEST_TO || Session.getActiveUser().getEmail();
  var dateCovered = guessDateCovered_(veh);
  var vehList = buildVehicleList_(ss, dateCovered, veh);

  var h = [];
  h.push('<div style="font-family:Arial,sans-serif;font-size:14px;color:#222">');
  h.push('<h2 style="color:#0b5;margin:0 0 8px">Daily Clinic Report</h2>');
  h.push('<p style="margin:0 0 16px;color:#666">Data for <b>' + dateCovered + '</b></p>');

  // --- Staff attendance (ABOVE vehicles) ---
  h.push('<h3 style="margin:14px 0 6px">&#128101; Staff Attendance' +
    (att && att.dated ? (' &mdash; ' + att.dated) : '') + '</h3>');
  if (!att || !att.found) {
    h.push('<p style="margin:2px 0;color:#a00">Attendance report not received.</p>');
  } else if (att.note) {
    h.push('<p style="margin:2px 0;color:#a60">Absent list received but could not be read (' + att.note + ').</p>');
  } else if (!att.absentees.length) {
    h.push('<p style="margin:2px 0;color:#137333;font-weight:bold">&#10003; All present.</p>');
  } else {
    h.push('<p style="margin:2px 0"><b style="color:#b00020">Absent (' + att.absentees.length + '):</b> ' +
      att.absentees.join(', ') + '</p>');
  }

  // --- Vehicles: always both, labelled, 0 km if idle ---
  h.push('<h3 style="margin:18px 0 6px">&#128663; Vehicles</h3>');
  h.push('<table style="border-collapse:collapse">');
  vehList.forEach(function (v) {
    var zero = !v.km;
    h.push('<tr><td style="padding:2px 14px 2px 0"><b>' + v.label + '</b> (' + v.reg + ')</td>' +
      '<td style="padding:2px 0' + (zero ? ';color:#888' : '') + '">' + (v.km || 0) + ' km' +
      (zero ? ' (did not run)' : '') + '</td></tr>');
  });
  h.push('</table>');

  // --- Trips breakdown, grouped by vehicle ---
  h.push(tripsHtml_(veh));

  // --- Collections ---
  h.push('<h3 style="margin:18px 0 6px">&#128179; UPI / Card Collections</h3>');
  h.push('<table style="border-collapse:collapse;font-size:14px">');
  h.push('<tr style="background:#f2f2f2"><th style="text-align:left;padding:4px 14px">Account</th>' +
    '<th style="text-align:right;padding:4px 14px">Txns</th>' +
    '<th style="text-align:right;padding:4px 14px">Gross</th>' +
    '<th style="text-align:right;padding:4px 14px">Net</th></tr>');
  var gG = 0, gN = 0, gC = 0, labels = Object.keys(ici.byAccount);
  if (!labels.length) {
    h.push('<tr><td colspan="4" style="padding:4px 14px;color:#a00">No statements parsed today.</td></tr>');
  }
  labels.forEach(function (lbl) {
    var a = ici.byAccount[lbl]; gG += a.gross; gN += a.net; gC += a.count;
    h.push('<tr><td style="padding:4px 14px">' + lbl + '</td>' +
      '<td style="text-align:right;padding:4px 14px">' + a.count + '</td>' +
      '<td style="text-align:right;padding:4px 14px">' + inr_(a.gross) + '</td>' +
      '<td style="text-align:right;padding:4px 14px">' + inr_(a.net) + '</td></tr>');
  });
  if (labels.length > 1)
    h.push('<tr style="border-top:2px solid #ccc;font-weight:bold">' +
      '<td style="padding:4px 14px">Total</td>' +
      '<td style="text-align:right;padding:4px 14px">' + gC + '</td>' +
      '<td style="text-align:right;padding:4px 14px">' + inr_(gG) + '</td>' +
      '<td style="text-align:right;padding:4px 14px">' + inr_(gN) + '</td></tr>');
  h.push('</table>');

  h.push(monthToDateHtml_(ss, dateCovered));

  if (notes.length) {
    h.push('<h3 style="margin:18px 0 6px;color:#a60">&#9888; Notes</h3><ul>');
    notes.forEach(function (n) { h.push('<li>' + n + '</li>'); });
    h.push('</ul>');
  }
  h.push('<p style="margin-top:18px"><a href="' + ss.getUrl() + '">Open full spreadsheet &raquo;</a></p></div>');

  MailApp.sendEmail({ to: to, subject: 'Daily Clinic Report — ' + dateCovered,
    htmlBody: h.join('') });

  // Optional WhatsApp export through MyOperator WABA API.
  try {
    sendWhatsAppDigest_(ss, dateCovered, veh, ici, notes);
  } catch (e) {
    logWhatsAppError_(ss, e);
  }
}

// Per-vehicle trip tables (start, end, duration, distance), in CONFIG order.
function tripsHtml_(veh) {
  var trips = (veh && veh.trips) ? veh.trips : [];
  if (!trips.length) return '';

  // Group trips by vehicle registration.
  var byReg = {};
  trips.forEach(function (t) {
    (byReg[t.vehicle] = byReg[t.vehicle] || []).push(t);
  });

  var h = ['<h3 style="margin:18px 0 6px">&#128205; Trips</h3>'];
  CONFIG.VEHICLES.forEach(function (v) {
    var list = byReg[v.reg] || [];
    var totalKm = 0;
    list.forEach(function (t) { totalKm += toNum_(t.km); });

    h.push('<p style="margin:10px 0 4px"><b>' + v.label + '</b> (' + v.reg + ') &mdash; ' +
      list.length + ' trip' + (list.length === 1 ? '' : 's') +
      (list.length ? ', ' + round2_(totalKm) + ' km' : '') + '</p>');

    if (!list.length) {
      h.push('<p style="margin:0 0 6px;color:#888">No trips.</p>');
      return;
    }

    h.push('<table style="border-collapse:collapse;font-size:13px;margin-bottom:4px">');
    h.push('<tr style="background:#f2f2f2">' +
      '<th style="text-align:left;padding:3px 12px">Start</th>' +
      '<th style="text-align:left;padding:3px 12px">End</th>' +
      '<th style="text-align:left;padding:3px 12px">Duration</th>' +
      '<th style="text-align:right;padding:3px 12px">Distance</th></tr>');
    list.forEach(function (t) {
      h.push('<tr>' +
        '<td style="padding:3px 12px">' + t.start + '</td>' +
        '<td style="padding:3px 12px">' + t.end + '</td>' +
        '<td style="padding:3px 12px">' + t.dur + '</td>' +
        '<td style="text-align:right;padding:3px 12px">' + round2_(t.km) + ' km</td></tr>');
    });
    h.push('</table>');
  });
  return h.join('');
}

// Always returns BOTH configured vehicles, with the day's km (0 if it did not run).
function buildVehicleList_(ss, dateCovered, veh) {
  var kmByReg = {};
  (veh && veh.rows ? veh.rows : []).forEach(function (r) { kmByReg[r.vehicle] = r.km; });

  var missing = CONFIG.VEHICLES.some(function (v) { return !(v.reg in kmByReg); });
  if (missing) {
    var data = getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS).getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (normDate_(data[i][0]) === dateCovered) {
        var reg = String(data[i][1] || '').trim();
        if (reg && !(reg in kmByReg)) kmByReg[reg] = toNum_(data[i][2]);
      }
    }
  }
  return CONFIG.VEHICLES.map(function (v) {
    return { label: v.label, reg: v.reg, km: (v.reg in kmByReg) ? kmByReg[v.reg] : 0 };
  });
}


/********************* OPTIONAL WHATSAPP EXPORT — MYOPERATOR WABA *****/

var MYOP_DEFAULTS = {
  BASE_URL: 'https://publicapi.myoperator.co',
  API_KEY: '«MASKED-S230»',
  COMPANY_ID: '«MASKED-S230»',
  PHONE_NUMBER_ID: '«MASKED-S230»',
  WA_TO_NUMBERS: '«MASKED-PHONE»',
  WA_TEMPLATE: 'daily_account_summary',
  WA_LANGUAGE: 'en',
  WA_ENABLED_DEFAULT: 'NO'
};

function sendWhatsAppDigest_(ss, dateCovered, veh, ici, notes) {
  var props = PropertiesService.getScriptProperties();
  var waEnabled = props.getProperty('MYOP_WA_ENABLED') || MYOP_DEFAULTS.WA_ENABLED_DEFAULT;
  if (waEnabled !== 'YES') return;

  var apiKey = props.getProperty('MYOP_API_KEY') || MYOP_DEFAULTS.API_KEY;
  var companyId = props.getProperty('MYOP_COMPANY_ID') || MYOP_DEFAULTS.COMPANY_ID;
  var phoneNumberId = props.getProperty('MYOP_PHONE_NUMBER_ID') || MYOP_DEFAULTS.PHONE_NUMBER_ID;
  var toNumbers = (props.getProperty('MYOP_WA_TO_NUMBERS') || MYOP_DEFAULTS.WA_TO_NUMBERS)
    .split(',')
    .map(function (s) { return String(s).replace(/\D/g, ''); })
    .filter(Boolean);

  var templateName = props.getProperty('MYOP_WA_TEMPLATE') || MYOP_DEFAULTS.WA_TEMPLATE;
  var language = props.getProperty('MYOP_WA_LANGUAGE') || MYOP_DEFAULTS.WA_LANGUAGE;

  var text = buildWhatsAppDigestText_(ss, dateCovered, veh, ici, notes);
  toNumbers.forEach(function (mobile) {
    sendMyOperatorTemplate_(apiKey, companyId, phoneNumberId, mobile, templateName, language, text);
  });
}

function buildWhatsAppDigestText_(ss, dateCovered, veh, ici, notes) {
  var vehList = buildVehicleList_(ss, dateCovered, veh);
  var vehicles = vehList.map(function (v) {
    return v.label + ' (' + v.reg + '): ' + (v.km || 0) + ' km';
  }).join('\n');

  var labels = Object.keys(ici.byAccount || {});
  var gN = 0, gC = 0, collections = '';
  if (labels.length) {
    collections = labels.map(function (lbl) {
      var a = ici.byAccount[lbl]; gN += a.net; gC += a.count;
      return lbl + ': ' + a.count + ' txns, Net ' + inr_(a.net);
    }).join('\n');
  } else {
    collections = 'No ICICI statements parsed today';
  }

  return {
    date: String(dateCovered),
    vehicle_summary: truncateWa_(vehicles, 900),
    collection_summary: truncateWa_(collections, 900),
    total_amount: labels.length ? (gC + ' txns, Net ' + inr_(gN)) : 'Nil'
  };
}

function sendMyOperatorTemplate_(apiKey, companyId, phoneNumberId, mobile, templateName, language, text) {
  var url = MYOP_DEFAULTS.BASE_URL + '/chat/messages';

  var payload = {
    phone_number_id: phoneNumberId,
    customer_country_code: '91',
    customer_number: mobile,
    data: {
      type: 'template',
      context: {
        template_name: templateName,
        language: language,
        body: {
          date: text.date,
          vehicle_summary: text.vehicle_summary,
          collection_summary: text.collection_summary,
          total_amount: text.total_amount
        }
      }
    },
    reply_to: null,
    myop_ref_id: null,
    trail: { name: null }
  };

  var res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Accept: 'application/json',
      Authorization: 'Bearer ' + apiKey,
      'X-MYOP-COMPANY-ID': companyId
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  var body = res.getContentText();
  Logger.log('MyOperator WhatsApp response ' + code + ': ' + body);

  if (code < 200 || code >= 300) {
    throw new Error('MyOperator WhatsApp failed: HTTP ' + code + ' — ' + body);
  }
}

function requiredProp_(key) {
  var v = PropertiesService.getScriptProperties().getProperty(key);
  if (!v) throw new Error('Missing Script Property: ' + key);
  return v;
}

function truncateWa_(s, maxLen) {
  s = String(s || '');
  return s.length <= maxLen ? s : s.substring(0, maxLen - 20) + '... [truncated]';
}

function logWhatsAppError_(ss, e) {
  try {
    var sh = getSheet_(ss, 'Run_Log', RUNLOG_HEADERS);
    sh.appendRow([nowStr_(), '', 0, 0, 'WhatsApp error: ' + (e && e.message ? e.message : e)]);
  } catch (ignore) {
    Logger.log(e);
  }
}

function enableWhatsAppExport() {
  PropertiesService.getScriptProperties().setProperty('MYOP_WA_ENABLED', 'YES');
  Logger.log('WhatsApp daily export ENABLED. Now run testWhatsAppDailyReport once.');
}

function disableWhatsAppExport() {
  PropertiesService.getScriptProperties().setProperty('MYOP_WA_ENABLED', 'NO');
  Logger.log('WhatsApp daily export DISABLED. Email and spreadsheet automation remain active.');
}

function showWhatsAppStatus() {
  var props = PropertiesService.getScriptProperties();
  var waEnabled = props.getProperty('MYOP_WA_ENABLED') || MYOP_DEFAULTS.WA_ENABLED_DEFAULT;
  Logger.log('MYOP_WA_ENABLED = ' + waEnabled);
  Logger.log('Recipient = ' + MYOP_DEFAULTS.WA_TO_NUMBERS);
  Logger.log('Template = ' + MYOP_DEFAULTS.WA_TEMPLATE);
}

function testWhatsAppDailyReport() {
  var ss = getOrCreateSpreadsheet_();
  var veh = {
    rows: [
      { vehicle: 'UP25AE0028', km: 7.7 },
      { vehicle: 'UP25Q0997', km: 6.7 }
    ]
  };
  var ici = {
    byAccount: {
      'NK Pathology': { count: 2, gross: 1750, net: 1750 },
      'Clinic': { count: 10, gross: 5300, net: 5300 },
      'Medicos': { count: 10, gross: 9805, net: 9805 }
    }
  };
  sendWhatsAppDigest_(ss, Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd'), veh, ici, []);
}


function monthToDateHtml_(ss, dateCovered) {
  var month = String(dateCovered).substring(0, 7);
  var data = getSheet_(ss, 'ICICI_Monthly', ICICI_MONTH_HEADERS).getDataRange().getValues();
  var rows = data.filter(function (r) { return String(r[0]) === month; });
  if (!rows.length) return '';
  var h = ['<h3 style="margin:18px 0 6px">&#128197; Month-to-date (' + month + ')</h3>'];
  h.push('<table style="border-collapse:collapse;font-size:14px">');
  rows.forEach(function (r) {
    h.push('<tr><td style="padding:2px 14px 2px 0"><b>' + r[1] + '</b></td>' +
      '<td style="padding:2px 14px">' + r[2] + ' txns</td>' +
      '<td style="padding:2px 0">Net ' + inr_(r[6]) + '</td></tr>');
  });
  h.push('</table>'); return h.join('');
}

/********************* HELPERS *************************************/

function getOrCreateSpreadsheet_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('SS_ID');
  if (id) { try { return SpreadsheetApp.openById(id); } catch (e) {} }
  var ss = SpreadsheetApp.create(CONFIG.SPREADSHEET_NAME);
  props.setProperty('SS_ID', ss.getId());
  getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS);
  getSheet_(ss, 'Vehicle_Monthly', VEH_MONTH_HEADERS);
  getSheet_(ss, 'ICICI_Monthly', ICICI_MONTH_HEADERS);
  getSheet_(ss, 'ICICI_Accounts', REGISTRY_HEADERS);
  getSheet_(ss, 'Run_Log', RUNLOG_HEADERS);
  var def = ss.getSheetByName('Sheet1'); if (def) ss.deleteSheet(def);
  return ss;
}

function getSheet_(ss, name, headers) {
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.getRange(1, 1, 1, headers.length).setValues([headers])
      .setFontWeight('bold').setBackground('#e8eef7');
    sh.setFrozenRows(1);
  }
  return sh;
}

function xlsxToValues_(blob) {
  blob.setName('tmp_mpr_' + Date.now() + '.xlsx');

  var resource = {
    name: blob.getName(),
    mimeType: 'application/vnd.google-apps.spreadsheet'
  };

  var file = Drive.Files.create(resource, blob, {
    convert: true
  });

  var values = SpreadsheetApp.openById(file.id)
    .getSheets()[0]
    .getDataRange()
    .getValues();

  DriveApp.getFileById(file.id).setTrashed(true);

  return values;
}

function findMessagesBySubject_(subject) {
  var q = 'subject:("' + subject + '") newer_than:' + CONFIG.LOOKBACK_DAYS + 'd';
  var threads = GmailApp.search(q, 0, 30);
  var msgs = [];
  threads.forEach(function (t) {
    t.getMessages().forEach(function (m) {
      if (m.getSubject().indexOf(subject) >= 0) msgs.push(m);
    });
  });
  msgs.sort(function (a, b) { return b.getDate() - a.getDate(); });
  return msgs;
}
function findLatestMessageBySubject_(s) { var m = findMessagesBySubject_(s); return m.length ? m[0] : null; }

function getAttachmentByName_(msg, name) {
  var atts = msg.getAttachments({ includeInlineImages: false });
  for (var i = 0; i < atts.length; i++)
    if (atts[i].getName() === name) return atts[i].copyBlob();
  return null;
}

function existingVehicleKeySet_(sheet) {
  var set = {}, data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    var d = normDate_(data[i][0]);
    var v = String(data[i][1] || '').trim();
    if (d && v) set[d + '|' + v] = true;
  }
  return set;
}

function dedupeVehicleLog_(ss) {
  var sheet = getSheet_(ss, 'Vehicle_Log', VEHICLE_HEADERS);
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return;
  var seen = {}, kept = [];
  for (var i = 1; i < data.length; i++) {
    var r = data[i];
    var d = normDate_(r[0]);
    var v = String(r[1] || '').trim();
    if (!d || !v) continue;
    var key = d + '|' + v;
    if (seen[key]) continue;
    seen[key] = true;
    r[0] = d;
    kept.push(r.slice(0, VEHICLE_HEADERS.length));
  }
  if (sheet.getLastRow() > 1) sheet.getRange(2, 1, sheet.getLastRow() - 1, VEHICLE_HEADERS.length).clearContent();
  if (kept.length) sheet.getRange(2, 1, kept.length, VEHICLE_HEADERS.length).setValues(kept);
}

function fixNkPathologyTab_(ss) {
  var base = ss.getSheetByName('ICICI_NK_PATHOLOGY');
  var dup = ss.getSheetByName('ICICI_NK_PATHOLOGY_2');
  if (base && dup && isSheetEmptyOrHeaderOnly_(base, ICICI_HEADERS) && dup.getLastRow() > 1) {
    ss.deleteSheet(base);
    dup.setName('ICICI_NK_PATHOLOGY');
    updateRegistryTab_(ss, 'NK_PATHOLOGY', 'ICICI_NK_PATHOLOGY');
  }
}

function updateRegistryTab_(ss, rawName, tabName) {
  var reg = getSheet_(ss, 'ICICI_Accounts', REGISTRY_HEADERS);
  var data = reg.getDataRange().getValues();
  for (var i = 1; i < data.length; i++) {
    if (String(data[i][1]) === rawName) {
      reg.getRange(i + 1, 4).setValue(tabName);
      reg.getRange(i + 1, 6).setValue(nowStr_());
    }
  }
}

function isSheetEmptyOrHeaderOnly_(sh, headers) {
  if (!sh) return true;
  if (sh.getLastRow() === 0) return true;
  if (sh.getLastRow() === 1) return true;
  var values = sh.getRange(2, 1, sh.getLastRow() - 1, Math.min(headers.length, sh.getLastColumn())).getValues();
  for (var i = 0; i < values.length; i++)
    for (var j = 0; j < values[i].length; j++)
      if (values[i][j] !== '' && values[i][j] !== null) return false;
  return true;
}

function existingKeySet_(sheet, colIdxs) {
  var set = {}, data = sheet.getDataRange().getValues();
  for (var i = 1; i < data.length; i++)
    set[colIdxs.map(function (c) { return String(data[i][c]).trim(); }).join('|')] = true;
  return set;
}
function headerIndex_(row) { var idx = {}; row.forEach(function (h, i) { idx[String(h).trim()] = i; }); return idx; }

function writeAggSheet_(ss, name, headers, agg, rowFn) {
  var sh = getSheet_(ss, name, headers);
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, headers.length).clearContent();
  var keys = Object.keys(agg).sort(); if (!keys.length) return;
  sh.getRange(2, 1, keys.length, headers.length)
    .setValues(keys.map(function (k) { return rowFn(k, agg[k]); }));
}

function logRun_(ss, veh, ici, notes) {
  getSheet_(ss, 'Run_Log', RUNLOG_HEADERS)
    .appendRow([nowStr_(), guessDateCovered_(veh), veh.added, ici.totalAdded, notes.join(' | ')]);
}

function guessDateCovered_(veh) {
  if (veh.rows.length) return veh.rows[0].date;
  return Utilities.formatDate(new Date(Date.now() - 864e5), 'Asia/Kolkata', 'yyyy-MM-dd');
}

function prettyLabel_(raw) {
  return String(raw).split('_').map(function (w) {
    return w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w;
  }).join(' ').trim();
}
function sanitizeTab_(raw) { return String(raw).replace(/[\\\/\?\*\[\]:]/g, '_').substring(0, 60); }
function uniqueTabName_(ss, base) {
  var name = base, n = 2;
  while (ss.getSheetByName(name)) name = base + '_' + (n++);
  return name;
}

function normDate_(v) {
  if (!v) return '';

  if (Object.prototype.toString.call(v) === '[object Date]' && !isNaN(v)) {
    return Utilities.formatDate(v, 'Asia/Kolkata', 'yyyy-MM-dd');
  }

  var s = String(v).trim(), m;

  m = s.match(/^(\d{2})-(\d{2})-(\d{4})/);
  if (m) return m[3] + '-' + m[2] + '-' + m[1];

  m = s.match(/^(\d{2})-([A-Za-z]{3})-(\d{2,4})$/);
  if (m) {
    var mo = {
      JAN:'01', FEB:'02', MAR:'03', APR:'04', MAY:'05', JUN:'06',
      JUL:'07', AUG:'08', SEP:'09', OCT:'10', NOV:'11', DEC:'12'
    }[m[2].toUpperCase()];
    var y = m[3].length === 2 ? '20' + m[3] : m[3];
    if (mo) return y + '-' + mo + '-' + m[1];
  }

  m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return m[1] + '-' + m[2] + '-' + m[3];

  return s;
}
function toNum_(v) { if (v===null||v===undefined||v==='') return 0; var n=parseFloat(String(v).replace(/,/g,'')); return isNaN(n)?0:n; }
function round2_(n) { return Math.round(n * 100) / 100; }
function inr_(n) { return '\u20B9' + round2_(n).toLocaleString('en-IN'); }
function nowStr_() { return Utilities.formatDate(new Date(), 'Asia/Kolkata', 'yyyy-MM-dd HH:mm'); }

