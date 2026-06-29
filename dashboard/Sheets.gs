/**
 * Sheets.gs — all spreadsheet I/O.
 * The intraday digest UPSERTs the callback tab so it never wipes staff notes.
 */

function getSpreadsheet_() {
  var id = PropertiesService.getScriptProperties().getProperty(CFG.SHEET_ID_PROP);
  if (id) return SpreadsheetApp.openById(id);
  var active = SpreadsheetApp.getActiveSpreadsheet();
  if (active) return active;
  throw new Error('No spreadsheet. Either bind this script to your Sheet, or set the "' +
                  CFG.SHEET_ID_PROP + '" Script Property to the Sheet ID.');
}

function getOrCreateTab_(name, headers) {
  var ss = getSpreadsheet_();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    if (headers) {
      sh.getRange(1, 1, 1, headers.length).setValues([headers])
        .setFontWeight('bold').setBackground('#1565C0').setFontColor('#FFFFFF');
      sh.setFrozenRows(1);
    }
  }
  return sh;
}

/** Format one net-missed entry into the non-staff columns (A..H). */
function entryToAutoRow_(e) {
  return [
    'DUE',
    e.priority ? '★' : '',
    "'" + e.number,                 // leading quote keeps the leading-digit format intact
    e.name,
    e.attempts,
    fmtTime_(e.firstTs),
    fmtTime_(e.lastTs),
    e.afterHours ? 'Yes' : ''
  ];
}

/**
 * UPSERT today's callbacks. Preserves the staff columns (Staff Status, Staff
 * Notes) for numbers already on the sheet, marks now-resolved numbers as
 * "Resolved", and re-sorts DUE-first.
 */
function upsertCallbacksToday_(entries) {
  var sh = getOrCreateTab_(CFG.TAB_CALLBACKS, CFG.CALLBACK_HEADERS);
  var nCols = CFG.CALLBACK_HEADERS.length;
  var staffN = CFG.STAFF_COL_COUNT;
  var autoN = nCols - staffN;

  // Read existing data rows.
  var existing = {}; // number -> {auto:[..A..H], staff:[..I,J..]}
  var lastRow = sh.getLastRow();
  if (lastRow > 1) {
    var vals = sh.getRange(2, 1, lastRow - 1, nCols).getValues();
    vals.forEach(function (row) {
      var num = String(row[2]).replace(/\D/g, '');
      if (!num) return;
      existing[num] = { auto: row.slice(0, autoN), staff: row.slice(autoN) };
    });
  }

  var newByNum = {};
  entries.forEach(function (e) { newByNum[e.number] = e; });

  var out = [];

  // 1) DUE rows (from this run), carrying over any staff edits.
  entries.forEach(function (e) {
    var staff = existing[e.number] ? existing[e.number].staff : new Array(staffN).fill('');
    out.push(entryToAutoRow_(e).concat(staff));
  });

  // 2) Rows that were on the sheet but are no longer net-missed -> Resolved,
  //    keeping their staff notes for the day's record.
  Object.keys(existing).forEach(function (num) {
    if (newByNum[num]) return;
    var prev = existing[num];
    var auto = prev.auto.slice();
    auto[0] = 'Resolved';           // Auto-Status
    out.push(auto.concat(prev.staff));
  });

  // Clear old body and write fresh (header row stays).
  if (lastRow > 1) sh.getRange(2, 1, lastRow - 1, nCols).clearContent();
  if (out.length) sh.getRange(2, 1, out.length, nCols).setValues(out);

  return out.length;
}

/** Append yesterday's final net-missed list + stats to the running logs. */
function writeDailyReport_(dateStr, result) {
  // Per-call rows.
  var logSh = getOrCreateTab_(CFG.TAB_REPORT_LOG,
    ['Report Date', 'Priority', 'Phone', 'Caller Name', 'Attempts',
     'First Call', 'Last Call', 'After-Hours']);
  if (result.entries.length) {
    var rows = result.entries.map(function (e) {
      return [dateStr, e.priority ? '★' : '', "'" + e.number, e.name, e.attempts,
              fmtTime_(e.firstTs), fmtTime_(e.lastTs), e.afterHours ? 'Yes' : ''];
    });
    logSh.getRange(logSh.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
  }

  // One summary row for the day.
  var sumSh = getOrCreateTab_(CFG.TAB_SUMMARY,
    ['Date', 'Total Calls', 'Incoming', 'Net-Missed', 'Resolved', 'Net-Missed %']);
  var s = result.stats;
  var pct = s.incomingCount ? Math.round((s.netMissed / s.incomingCount) * 100) + '%' : '0%';
  sumSh.getRange(sumSh.getLastRow() + 1, 1, 1, 6)
       .setValues([[dateStr, s.totalCalls, s.incomingCount, s.netMissed, s.resolved, pct]]);
}

/** Snapshot the current callback tab into the archive, then clear it for a new day. */
function archiveAndResetCallbacks_() {
  var sh = getSpreadsheet_().getSheetByName(CFG.TAB_CALLBACKS);
  if (!sh) return;
  var lastRow = sh.getLastRow();
  var nCols = CFG.CALLBACK_HEADERS.length;
  if (lastRow > 1) {
    var arch = getOrCreateTab_(CFG.TAB_ARCHIVE, ['Archived Date'].concat(CFG.CALLBACK_HEADERS));
    var stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
    var vals = sh.getRange(2, 1, lastRow - 1, nCols).getValues()
                 .map(function (r) { return [stamp].concat(r); });
    arch.getRange(arch.getLastRow() + 1, 1, vals.length, vals[0].length).setValues(vals);
    sh.getRange(2, 1, lastRow - 1, nCols).clearContent();
  }
}
