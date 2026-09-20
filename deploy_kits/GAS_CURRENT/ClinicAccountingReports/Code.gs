/****************************************************************************************
 * DR. MANOJ AGARWAL CLINIC — ACCOUNTING REPORT AUTOMATION
 * Runs in clinic hub Gmail (drmka.ortho@gmail.com)
 *
 *   • Daily email  @ 14:00 IST  -> new entries since last run + still-missing days + ALL open issues
 *   • Monthly email @ 09:00 IST on the FIRST SUNDAY -> previous-month insights + pending corrections
 *
 * Reads  : "Accounting details"            (source workbook, owned by personal Gmail, shared with hub)
 * Writes : "Monthly Accounting Reports..." (report workbook, owned by hub; tabs already exist)
 *
 * Design principles (per clinic standard): idempotent, self-healing, low-maintenance.
 *  - Source tabs are matched by HEADER SIGNATURE, not by exact tab name (rename-proof).
 *  - The Data_Quality_Audit tab IS the persistent issue ledger. An issue stays "open" and keeps
 *    appearing in the daily email until the underlying source cell is corrected, then it
 *    auto-resolves (the row is kept for audit, marked Resolved = Yes). Manual Resolved = Yes is
 *    respected as a suppression so you can silence a false positive.
 ****************************************************************************************/

const CONFIG = {
  SOURCE_ID : '1AnJWDJsAwtgkfFCQNwLzi6lqPPAfGwd-4TUZkuzrZH8',  // Accounting details
  REPORT_ID : '13eJo58J7G8n846mGlyv-pHpDILQnCrK-8ZZekyi1Hrg',  // Monthly Accounting Reports
  EMAIL_TO  : 'drmanojkragarwal@gmail.com',                    // where you read mail
  TZ        : 'Asia/Kolkata',
  WATCH_DAYS: 40,            // how far back the daily email still chases missing days
  FUTURE_TOL: 2,            // a revenue date this many days AFTER its submission stamp = suspicious
  PAST_TOL  : 75,           // a revenue date this many days BEFORE its submission stamp = suspicious
  START_DATE: '2026-06-01'  // GO-LIVE FLOOR: anything before this date is ignored entirely.
                            // Fixed on purpose (a rolling "current month" would break the
                            // previous-month monthly report). Set once; leave it after that.
};

// Report-tab names (created earlier by the hub). Matched case-insensitively; created if missing.
const TABS = {
  SUMMARY  : 'Monthly_Summary',
  DETAIL   : 'Department_Daily_Detail',
  AUDIT    : 'Data_Quality_Audit',
  PENDING  : 'Correction_Pending'
};

const SEV = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, REVIEW: 1 };
const SEV_NAME = { 4: 'Critical', 3: 'High', 2: 'Medium', 1: 'Review' };

/* =====================================================================================
 * 1. ENTRY POINTS  (these are what the triggers call)
 * ===================================================================================== */

function runDailyReport() {
  const model = buildModel_();
  syncAuditLedger_(model.issues);                 // keep the persistent ledger current
  const openIssues = readOpenIssues_();           // re-read so "age" reflects the ledger

  const props = PropertiesService.getScriptProperties();
  const lastRunIso = props.getProperty('LAST_RUN_TS');
  const now = new Date();
  // First ever run: only treat the last 2 days as "new" instead of the whole history.
  const since = lastRunIso ? new Date(lastRunIso) : addDays_(startOfDay_(now), -2);

  const floor = startFloor_();
  const newEntries = model.records
    .filter(r => r.timestamp instanceof Date && r.timestamp > since)
    .filter(r => !r.revDate || r.revDate >= floor)
    .sort((a, b) => b.timestamp - a.timestamp);

  const missing = computeMissingForWindow_(model, addDays_(startOfDay_(now), -1));

  sendDailyEmail_(newEntries, missing, openIssues, now);
  props.setProperty('LAST_RUN_TS', now.toISOString());
}

/** Weekly Sunday-09:00 trigger lands here; only proceeds on the first Sunday of the month. */
function runMonthlyGate() {
  const dayOfMonth = Number(Utilities.formatDate(new Date(), CONFIG.TZ, 'd'));
  if (dayOfMonth <= 7) runMonthlyReport();
}

function runMonthlyReport() {
  const now = new Date();
  const target = addDays_(startOfDay_(now), -1);   // a day in the previous month
  target.setDate(1); target.setMonth(target.getMonth());  // first of current month...
  const firstOfThisMonth = startOfMonth_(now);
  const prevMonthEnd = addDays_(firstOfThisMonth, -1);
  const prevMonthStart = startOfMonth_(prevMonthEnd);

  const model = buildModel_();
  syncAuditLedger_(model.issues);

  const monthRecords = model.records.filter(r =>
    r.revDate && r.revDate >= prevMonthStart && r.revDate <= prevMonthEnd);

  writeDetailSheet_(monthRecords, prevMonthStart);
  const summary = writeSummarySheet_(monthRecords, model, prevMonthStart, prevMonthEnd, now);
  const pending = writePendingSheet_(model, prevMonthStart, prevMonthEnd);

  sendMonthlyEmail_(summary, pending, prevMonthStart, now);
}

/* =====================================================================================
 * 2. SOURCE PARSING  ->  normalized records + detected issues
 * ===================================================================================== */

function buildModel_() {
  const ss = SpreadsheetApp.openById(CONFIG.SOURCE_ID);
  const sheets = ss.getSheets();
  const records = [];

  parseTab_(sheets, ['medical total', 'total cash'], 'Medical', records, parseMedicalRow_);
  parseTab_(sheets, ['opd cash', 'procedure cash'], 'OPD/X-Ray/Pro', records, parseOpdRow_);
  parseTab_(sheets, ['lab cash', 'total work'], 'Lab', records, parseLabRow_);

  const issues = detectIssues_(records);
  return { records, issues };
}

/** Find the tab whose header row contains every signature keyword, then parse each data row. */
function parseTab_(sheets, signature, tabKey, out, rowFn) {
  for (const sh of sheets) {
    const values = sh.getDataRange().getValues();
    const headerRow = findHeaderRow_(values, signature);
    if (headerRow < 0) continue;
    const map = headerMap_(values[headerRow]);
    for (let i = headerRow + 1; i < values.length; i++) {
      const row = values[i];
      if (row.every(c => c === '' || c === null)) continue;            // skip blank lines
      const recs = rowFn(row, map, i + 1, tabKey);                      // 1-based source row
      recs.forEach(rec => { if (rec) out.push(rec); });
    }
    return;  // first matching tab wins
  }
  Logger.log('WARNING: no tab matched signature ' + signature.join(' + '));
}

function parseMedicalRow_(row, m, srcRow, tabKey) {
  const ts   = asDate_(row[m['timestamp']]);
  const dRaw = row[m['date']];
  const d    = normalizeDate_(dRaw, ts);
  const gross = parseNum_(row[m['medical total']]);
  const upi   = parseNum_(row[m['medical upi']]);
  const exp   = parseNum_(row[m['expenses']]);
  const bal   = parseNum_(row[m['total cash']]);
  return [{
    dept: 'Medical', tabKey, srcRow, timestamp: ts,
    revDate: d.date, revDateStr: d.str, rawDate: dRaw, dateIssue: d.issue,
    cash: numOr0_(gross) - numOr0_(upi), upi: numOr0_(upi), gross: numOr0_(gross),
    expenses: numOr0_(exp), net: numOr0_(gross) - numOr0_(exp),
    balance: bal.ok ? bal.value : null,
    cells: { 'Medical Total': gross, 'Medical UPI': upi, 'Expenses': exp, 'Total Cash': bal }
  }];
}

function parseOpdRow_(row, m, srcRow, tabKey) {
  const ts   = asDate_(row[m['timestamp']]);
  const dRaw = row[m['date']];
  const d    = normalizeDate_(dRaw, ts);
  const exp  = parseNum_(row[m['expenses']]);
  const subs = [
    { dept: 'OPD',       cash: row[m['opd cash']],       upi: row[m['opd upi']],       carryExp: true },
    { dept: 'X-Ray',     cash: row[m['x-ray cash']],     upi: row[m['x-ray upi']] },
    { dept: 'Procedure', cash: row[m['procedure cash']], upi: row[m['procedure upi']] }
  ];
  return subs.map(s => {
    const c = parseNum_(s.cash), u = parseNum_(s.upi);
    const e = s.carryExp ? exp : { ok: true, value: 0 };  // day expense logged once (under OPD)
    return {
      dept: s.dept, tabKey, srcRow, timestamp: ts,
      revDate: d.date, revDateStr: d.str, rawDate: dRaw, dateIssue: d.issue,
      cash: numOr0_(c), upi: numOr0_(u), gross: numOr0_(c) + numOr0_(u),
      expenses: numOr0_(e), net: numOr0_(c) + numOr0_(u) - numOr0_(e), balance: null,
      cells: s.carryExp
        ? { 'OPD Cash': c, 'OPD UPI': u, 'Expenses': exp }
        : { [s.dept + ' Cash']: c, [s.dept + ' UPI']: u }
    };
  });
}

function parseLabRow_(row, m, srcRow, tabKey) {
  const ts   = asDate_(row[m['timestamp']]);
  const dRaw = row[m['date']];
  const d    = normalizeDate_(dRaw, ts);
  const cash = parseNum_(row[m['lab cash']]);
  const upi  = parseNum_(row[m['upi']]);
  const exp  = parseNum_(row[m['expense']]);
  return [{
    dept: 'Lab', tabKey, srcRow, timestamp: ts,
    revDate: d.date, revDateStr: d.str, rawDate: dRaw, dateIssue: d.issue,
    cash: numOr0_(cash), upi: numOr0_(upi), gross: numOr0_(cash) + numOr0_(upi),
    expenses: numOr0_(exp), net: numOr0_(cash) + numOr0_(upi) - numOr0_(exp), balance: null,
    cells: { 'Lab Cash': cash, 'UPI': upi, 'Expense': exp }
  }];
}

/* =====================================================================================
 * 3. ISSUE DETECTION
 * ===================================================================================== */

function detectIssues_(records) {
  const floor = startFloor_();
  records = records.filter(r =>
    r.revDate ? r.revDate >= floor : (r.timestamp ? r.timestamp >= floor : true));
  const issues = [];
  const add = (type, dept, dateStr, srcRow, raw, suggested, sev) =>
    issues.push({ type, dept, dateStr: cellToStr_(dateStr) || '(blank)', srcRow,
                  raw: cellToStr_(raw), suggested: suggested || '', sev });

  // --- per-record: numeric/formula + date problems ---------------------------------
  const rowMoney = {};   // total money on each source row (across its sub-departments)
  records.forEach(r => {
    const k = r.tabKey + '|' + r.srcRow;
    rowMoney[k] = (rowMoney[k] || 0) + Math.abs(r.gross || 0) + Math.abs(r.expenses || 0);
  });
  const seenDateIssue = new Set();   // a 3-in-1 OPD row must not raise the same date flag thrice
  for (const r of records) {
    Object.keys(r.cells).forEach(label => {
      const cell = r.cells[label];
      if (cell && cell.ok === false) {
        if (cell.type === 'formula')
          add('Formula error', r.dept, r.revDateStr, r.srcRow, cell.raw,
              'Re-enter a number; remove the broken formula', SEV.CRITICAL);
        else if (cell.type === 'nonnumeric')
          add('Non-numeric value', r.dept, r.revDateStr, r.srcRow, cell.raw,
              'Looks like a typo (e.g. letter "O" for 0) — enter a number', SEV.CRITICAL);
      } else if (cell && cell.leadingZero) {
        add('Suspicious leading zero', r.dept, r.revDateStr, r.srcRow, cell.raw,
            'Read as ' + cell.value + ' — confirm the intended amount', SEV.REVIEW);
      }
    });
    if (r.dateIssue) {
      // A row with no date AND no money is leftover junk (e.g. only a PDF link or a stray
      // space) — not a real entry. Don't nag to "enter the date"; just ignore it.
      const blankAndEmpty = r.dateIssue.type === 'Missing date in row'
        && (rowMoney[r.tabKey + '|' + r.srcRow] || 0) === 0;
      const dk = r.tabKey + '|' + r.srcRow + '|' + r.dateIssue.type;
      if (!blankAndEmpty && !seenDateIssue.has(dk)) {
        seenDateIssue.add(dk);
        add(r.dateIssue.type, r.tabKey, r.revDateStr, r.srcRow, r.rawDate,
            r.dateIssue.suggested, r.dateIssue.sev);
      }
    }
  }

  // --- per tab+date: duplicates -----------------------------------------------------
  const byTabDate = {};
  records.forEach(r => {
    if (!r.revDate) return;
    const k = r.tabKey + '|' + r.revDateStr;
    (byTabDate[k] = byTabDate[k] || []).push(r);
  });
  Object.keys(byTabDate).forEach(k => {
    const grp = byTabDate[k];
    // one row in OPD tab spawns 3 dept records for the same date — that is NOT a duplicate.
    const distinctRows = new Set(grp.map(r => r.srcRow));
    if (distinctRows.size > 1) {
      const r0 = grp[0];
      add('Duplicate date entry', r0.tabKey, r0.revDateStr,
          Array.from(distinctRows).join(', '),
          distinctRows.size + ' separate rows for this date',
          'Keep the correct row, delete the rest (or confirm it is a genuine correction)',
          SEV.MEDIUM);
    }
  });

  // NOTE: "missing days" are intentionally NOT logged as ledger issues. They are operational,
  // not data defects, and are shown (capped at today) in the email's "Days still not entered"
  // section + counted directly in the monthly summary. Logging them here caused duplication and,
  // if a stray future date slipped in, a flood of phantom future "missing" rows.

  // --- Medical running balance sanity ----------------------------------------------
  const med = records.filter(r => r.dept === 'Medical' && r.revDate)
                     .sort((a, b) => a.revDate - b.revDate);
  med.forEach(r => {
    if (r.balance !== null && r.balance < 0)
      add('Negative cash balance', 'Medical', r.revDateStr, r.srcRow, r.balance,
          'Check the day\u2019s deposit / old-balance carry-forward', SEV.HIGH);
  });

  return issues;
}

/* =====================================================================================
 * 4. PERSISTENT AUDIT LEDGER  (Data_Quality_Audit tab)
 * ===================================================================================== */

const AUDIT_HEADERS = ['Issue Type', 'Department', 'Revenue Date', 'Source Row', 'Raw Value',
  'Suggested Correction', 'Severity', 'Resolved?', 'Remarks', 'First Seen', 'Last Seen'];

function issueKey_(type, dept, dateStr, raw) {
  return [type, dept, dateStr, String(raw)].join('||');     // stable across source row drift
}

function syncAuditLedger_(currentIssues) {
  const sh = getTab_(TABS.AUDIT, AUDIT_HEADERS);
  const today = fmt_(new Date());
  const data = sh.getDataRange().getValues();
  const hRow = findHeaderRow_(data, ['issue type', 'resolved?']);
  const idx = headerMap_(data[hRow]);

  // read existing ledger -> map by key (preserve manual Resolved?/Remarks/First Seen)
  const existing = {};
  for (let i = hRow + 1; i < data.length; i++) {
    const row = data[i];
    if (row.every(c => c === '' || c === null)) continue;
    const C = c => cellToStr_(row[idx[c]]);
    const key = issueKey_(C('issue type'), C('department'), C('revenue date'), C('raw value'));
    existing[key] = {
      type: C('issue type'), dept: C('department'),
      dateStr: C('revenue date'), srcRow: C('source row'),
      raw: C('raw value'), suggested: C('suggested correction'),
      sevName: row[idx['severity']],
      resolved: String(row[idx['resolved?']] || '').toLowerCase().startsWith('y'),
      remarks: row[idx['remarks']] || '',
      firstSeen: idx['first seen'] != null ? (row[idx['first seen']] || today) : today,
      manualResolved: String(row[idx['resolved?']] || '').toLowerCase().startsWith('y'),
      stillPresent: false, lastSeen: ''
    };
  }

  const currentKeys = {};
  currentIssues.forEach(ci => {
    const key = issueKey_(ci.type, ci.dept, ci.dateStr, ci.raw);
    currentKeys[key] = ci;
    if (existing[key]) {
      const e = existing[key];
      e.stillPresent = true; e.lastSeen = today;
      e.srcRow = ci.srcRow; e.suggested = ci.suggested; e.sevName = SEV_NAME[ci.sev];
      // Respect a manual "Yes" as suppression; otherwise the still-present issue stays open.
      if (!e.manualResolved) e.resolved = false;
    } else {
      existing[key] = {
        type: ci.type, dept: ci.dept, dateStr: ci.dateStr, srcRow: ci.srcRow,
        raw: ci.raw, suggested: ci.suggested, sevName: SEV_NAME[ci.sev],
        resolved: false, manualResolved: false, remarks: '',
        firstSeen: today, lastSeen: today, stillPresent: true
      };
    }
  });

  // anything previously OPEN but no longer present -> auto-resolve (keep the row for audit)
  Object.keys(existing).forEach(key => {
    const e = existing[key];
    if (!e.stillPresent && !e.resolved) {
      e.resolved = true;
      e.remarks = (e.remarks ? e.remarks + ' | ' : '') + 'auto-resolved ' + today;
    }
  });

  // rewrite the whole table (header + rows), open issues first then by severity
  const rows = Object.keys(existing).map(k => existing[k]).sort((a, b) => {
    if (a.resolved !== b.resolved) return a.resolved ? 1 : -1;
    return (SEV[String(a.sevName).toUpperCase()] || 0) <
           (SEV[String(b.sevName).toUpperCase()] || 0) ? 1 : -1;
  }).map(e => [e.type, e.dept, e.dateStr, e.srcRow, e.raw, e.suggested, e.sevName,
               e.resolved ? 'Yes' : 'No', e.remarks, e.firstSeen, e.lastSeen]);

  sh.clearContents();
  const totalRows = Math.max(rows.length + 1, 1);
  sh.getRange(1, 1, totalRows, AUDIT_HEADERS.length).setNumberFormat('@');  // keep dates as text
  sh.getRange(1, 1, 1, AUDIT_HEADERS.length).setValues([AUDIT_HEADERS]).setFontWeight('bold');
  if (rows.length)
    sh.getRange(2, 1, rows.length, AUDIT_HEADERS.length).setValues(rows);
}

function readOpenIssues_() {
  const sh = getTab_(TABS.AUDIT, AUDIT_HEADERS);
  const data = sh.getDataRange().getValues();
  const hRow = findHeaderRow_(data, ['issue type', 'resolved?']);
  const idx = headerMap_(data[hRow]);
  const today = startOfDay_(new Date());
  const open = [];
  for (let i = hRow + 1; i < data.length; i++) {
    const row = data[i];
    if (row.every(c => c === '' || c === null)) continue;
    if (String(row[idx['resolved?']] || '').toLowerCase().startsWith('y')) continue;
    const C = c => cellToStr_(row[idx[c]]);
    const firstSeen = parseYmd_(row[idx['first seen']]);
    open.push({
      type: C('issue type'), dept: C('department'),
      dateStr: C('revenue date'), srcRow: C('source row'),
      raw: C('raw value'), suggested: C('suggested correction'),
      sevName: C('severity'),
      ageDays: firstSeen ? Math.max(0, Math.round((today - firstSeen) / 86400000)) : 0
    });
  }
  return open.sort((a, b) => {
    const s = (SEV[String(b.sevName).toUpperCase()] || 0) - (SEV[String(a.sevName).toUpperCase()] || 0);
    return s !== 0 ? s : b.ageDays - a.ageDays;
  });
}

/* =====================================================================================
 * 5. MONTHLY SHEET WRITERS
 * ===================================================================================== */

const DETAIL_HEADERS = ['Revenue Date', 'Department', 'Cash', 'UPI', 'Gross', 'Expenses',
  'Net', 'Submitted Timestamp', 'Source Row', 'Status', 'Remarks'];

function writeDetailSheet_(monthRecords, monthStart) {
  const sh = getTab_(TABS.DETAIL, DETAIL_HEADERS);
  sh.clearContents();
  sh.getRange(1, 1, 1, DETAIL_HEADERS.length).setValues([DETAIL_HEADERS]).setFontWeight('bold');
  const rows = monthRecords
    .slice().sort((a, b) => (a.revDate - b.revDate) || a.dept.localeCompare(b.dept))
    .map(r => [r.revDateStr, r.dept, r.cash, r.upi, r.gross, r.expenses, r.net,
               r.timestamp ? fmtDt_(r.timestamp) : '', r.srcRow,
               r.dateIssue ? 'Date flagged' : 'OK', r.dateIssue ? r.dateIssue.type : '']);
  if (rows.length) sh.getRange(2, 1, rows.length, DETAIL_HEADERS.length).setValues(rows);
}

function writeSummarySheet_(monthRecords, model, monthStart, monthEnd, now) {
  const sh = getTab_(TABS.SUMMARY, null);
  sh.clearContents();
  const monthLabel = Utilities.formatDate(monthStart, CONFIG.TZ, 'MMMM yyyy');
  sh.getRange(1, 1, 1, 5).setValues([['MONTHLY ACCOUNTING REPORT', 'Report Month',
    'Generated On', 'Source Sheet', 'Status']]);
  sh.getRange(2, 1, 1, 5).setValues([['', monthLabel, fmtDt_(now), 'Accounting details',
    'Auto-generated']]);
  const tableHeader = ['Department', 'Gross', 'Cash', 'UPI', 'Expenses', 'Net', 'Missing Dates',
    'Duplicate Dates', 'Date Errors', 'Numeric/Formula Errors', 'Balance Issues', 'Remarks'];
  sh.getRange(4, 1, 1, tableHeader.length).setValues([tableHeader]).setFontWeight('bold');

  const depts = ['Medical', 'OPD', 'X-Ray', 'Procedure', 'Lab'];
  const issuesInMonth = model.issues.filter(i => inMonthStr_(i.dateStr, monthStart, monthEnd));
  const tabOf = { Medical: 'Medical', OPD: 'OPD/X-Ray/Pro', 'X-Ray': 'OPD/X-Ray/Pro',
                  Procedure: 'OPD/X-Ray/Pro', Lab: 'Lab' };

  const summary = depts.map(dep => {
    const recs = monthRecords.filter(r => r.dept === dep);
    const t = recs.reduce((a, r) => {
      a.gross += r.gross; a.cash += r.cash; a.upi += r.upi; a.exp += r.expenses; a.net += r.net;
      return a;
    }, { gross: 0, cash: 0, upi: 0, exp: 0, net: 0 });
    const di = issuesInMonth.filter(i => i.dept === dep || i.dept === tabOf[dep]);
    const cnt = type => di.filter(i => i.type.indexOf(type) === 0).length;
    return {
      dept: dep, gross: t.gross, cash: t.cash, upi: t.upi, exp: t.exp, net: t.net,
      missing: countMissingInRange_(model, tabOf[dep], monthStart, monthEnd),
      dup: cnt('Duplicate'), dateErr: cnt('Date') + cnt('Year') + cnt('Impossible') + cnt('Transposed') + cnt('Unreadable'),
      numErr: cnt('Formula') + cnt('Non-numeric'), balErr: cnt('Negative'),
      remark: di.length ? di.length + ' flagged' : ''
    };
  });

  const rows = summary.map(s => [s.dept, s.gross, s.cash, s.upi, s.exp, s.net,
    s.missing, s.dup, s.dateErr, s.numErr, s.balErr, s.remark]);
  const grand = summary.reduce((a, s) => {
    a.gross += s.gross; a.cash += s.cash; a.upi += s.upi; a.exp += s.exp; a.net += s.net; return a;
  }, { gross: 0, cash: 0, upi: 0, exp: 0, net: 0 });
  rows.push(['TOTAL', grand.gross, grand.cash, grand.upi, grand.exp, grand.net, '', '', '', '', '', '']);
  sh.getRange(5, 1, rows.length, tableHeader.length).setValues(rows);
  sh.getRange(5 + rows.length - 1, 1, 1, tableHeader.length).setFontWeight('bold');

  return { monthLabel, summary, grand };
}

const PENDING_HEADERS = ['Department', 'Revenue Date', 'Pending Item', 'Responsible',
  'Action Required', 'Resolved?', 'Remarks'];

function writePendingSheet_(model, monthStart, monthEnd) {
  const sh = getTab_(TABS.PENDING, PENDING_HEADERS);
  sh.clearContents();
  sh.getRange(1, 1, 1, PENDING_HEADERS.length).setValues([PENDING_HEADERS]).setFontWeight('bold');
  const open = readOpenIssues_().filter(i => inMonthStr_(i.dateStr, monthStart, monthEnd)
                                          || i.dateStr === '(blank)');
  const rows = open.map(i => [i.dept, i.dateStr, i.type + (i.raw ? ' (' + i.raw + ')' : ''),
    'Reception', i.suggested, 'No', i.sevName + ' \u00b7 open ' + i.ageDays + 'd']);
  if (rows.length) sh.getRange(2, 1, rows.length, PENDING_HEADERS.length).setValues(rows);
  return open;
}

/* =====================================================================================
 * 6. EMAIL
 * ===================================================================================== */

function sendDailyEmail_(newEntries, missing, openIssues, now) {
  const dateLabel = fmt_(now);
  const subject = 'Clinic Accounts \u2014 Daily ' + dateLabel +
    ' \u00b7 ' + newEntries.length + ' new \u00b7 ' + openIssues.length + ' open issue' +
    (openIssues.length === 1 ? '' : 's');

  let h = emailHead_('Daily Accounting Report', Utilities.formatDate(now, CONFIG.TZ, 'EEEE, dd MMM yyyy'));

  // new entries
  h += section_('New entries submitted since yesterday');
  if (newEntries.length) {
    h += table_(['Revenue Date', 'Department', 'Cash', 'UPI', 'Gross', 'Expenses', 'Net', 'Filed'],
      newEntries.map(r => [r.revDateStr, r.dept, money_(r.cash), money_(r.upi), money_(r.gross),
        money_(r.expenses), money_(r.net), r.timestamp ? fmtDt_(r.timestamp) : '']));
  } else {
    h += note_('No new entries were submitted since the last report.');
  }

  // still-missing days
  h += section_('Days still not entered (within the last ' + CONFIG.WATCH_DAYS + ' days)');
  const missKeys = Object.keys(missing);
  if (missKeys.length) {
    h += table_(['Department', 'Missing dates'],
      missKeys.map(k => [k, missing[k].join(', ')]));
  } else {
    h += note_('All days are entered \u2014 nothing missing.');
  }

  // open issues
  h += section_('Open data-quality issues (carried forward until corrected)');
  if (openIssues.length) {
    h += table_(['Age', 'Severity', 'Department', 'Row', 'Date', 'Issue', 'Value', 'Suggested fix'],
      openIssues.map(i => [i.ageDays + 'd', sevBadge_(i.sevName), i.dept, i.srcRow || '', i.dateStr,
        i.type, esc_(i.raw), esc_(i.suggested)]));
  } else {
    h += note_('No open issues. Everything reconciles.');
  }

  h += emailFoot_();
  MailApp.sendEmail({ to: CONFIG.EMAIL_TO, subject: subject, htmlBody: h });
}

function sendMonthlyEmail_(summary, pending, monthStart, now) {
  const subject = 'Clinic Accounts \u2014 Monthly Summary: ' + summary.monthLabel;
  let h = emailHead_('Monthly Accounting Summary', summary.monthLabel);

  h += section_('Revenue by department');
  h += table_(['Department', 'Gross', 'Cash', 'UPI', 'Expenses', 'Net'],
    summary.summary.map(s => [s.dept, money_(s.gross), money_(s.cash), money_(s.upi),
      money_(s.exp), money_(s.net)])
    .concat([['<b>TOTAL</b>', '<b>' + money_(summary.grand.gross) + '</b>',
      '<b>' + money_(summary.grand.cash) + '</b>', '<b>' + money_(summary.grand.upi) + '</b>',
      '<b>' + money_(summary.grand.exp) + '</b>', '<b>' + money_(summary.grand.net) + '</b>']]), true);

  h += section_('Data quality this month');
  h += table_(['Department', 'Missing', 'Duplicates', 'Date errors', 'Numeric/Formula', 'Balance'],
    summary.summary.map(s => [s.dept, s.missing, s.dup, s.dateErr, s.numErr, s.balErr]));

  h += section_('Pending corrections (' + pending.length + ' open)');
  if (pending.length) {
    h += table_(['Severity', 'Department', 'Date', 'Item', 'Action'],
      pending.map(i => [sevBadge_(i.sevName), i.dept, i.dateStr, i.type, esc_(i.suggested)]));
  } else {
    h += note_('No pending corrections \u2014 the month is clean.');
  }

  h += emailFoot_();
  MailApp.sendEmail({ to: CONFIG.EMAIL_TO, subject: subject, htmlBody: h });
}

/* ---- email building blocks ---- */
function emailHead_(title, sub) {
  const url = 'https://docs.google.com/spreadsheets/d/' + CONFIG.REPORT_ID + '/edit';
  return '<div style="font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;max-width:680px">' +
    '<div style="border-bottom:3px solid #0b6e4f;padding-bottom:8px;margin-bottom:4px">' +
    '<div style="font-size:18px;font-weight:bold">Dr. Manoj Agarwal Clinic</div>' +
    '<div style="font-size:15px;color:#0b6e4f;font-weight:bold">' + title + '</div>' +
    '<div style="font-size:12px;color:#666">' + sub + '</div></div>' +
    '<div style="font-size:11px;margin:6px 0 14px"><a href="' + url + '" style="color:#0b6e4f">Open the report workbook \u2192</a></div>';
}
function emailFoot_() {
  return '<div style="font-size:11px;color:#888;margin-top:18px;border-top:1px solid #ddd;padding-top:8px">' +
    'Open issues keep appearing here every day until the source cell is corrected in <i>Accounting details</i>. ' +
    'To silence a false alarm, set <b>Resolved?</b> = Yes for that row in the Data_Quality_Audit tab.' +
    '</div></div>';
}
function section_(t) {
  return '<div style="font-size:13px;font-weight:bold;color:#0b6e4f;margin:16px 0 6px">' + t + '</div>';
}
function note_(t) {
  return '<div style="font-size:12px;color:#555;background:#f3f6f4;border-radius:6px;padding:8px 10px">' + t + '</div>';
}
function table_(headers, rows, rawCells) {
  let t = '<table style="border-collapse:collapse;width:100%;font-size:12px">';
  t += '<tr>' + headers.map(h => '<th style="text-align:left;background:#0b6e4f;color:#fff;' +
    'padding:5px 7px;border:1px solid #0b6e4f">' + h + '</th>').join('') + '</tr>';
  rows.forEach((r, i) => {
    const bg = i % 2 ? '#f7faf9' : '#ffffff';
    t += '<tr>' + r.map(c => '<td style="padding:5px 7px;border:1px solid #dde5e2;background:' + bg + '">' +
      (rawCells ? c : (c === null || c === undefined ? '' : c)) + '</td>').join('') + '</tr>';
  });
  return t + '</table>';
}
function sevBadge_(name) {
  const colors = { Critical: '#c0392b', High: '#d35400', Medium: '#b7950b', Review: '#7f8c8d' };
  const c = colors[name] || '#7f8c8d';
  return '<span style="background:' + c + ';color:#fff;border-radius:4px;padding:1px 6px;font-size:11px">' + name + '</span>';
}

/* =====================================================================================
 * 7. HELPERS
 * ===================================================================================== */

/** Count days in [start, min(end, today)] with no row for the given source tab. */
function countMissingInRange_(model, tabKey, start, end) {
  const today = startOfDay_(new Date());
  let stop = end < today ? end : today;
  const floor = startFloor_();
  let from = start < floor ? floor : start;
  const present = new Set(model.records.filter(r => r.tabKey === tabKey && r.revDate)
                                       .map(r => r.revDateStr));
  let c = 0;
  for (let d = new Date(from); d <= stop; d = addDays_(d, 1))
    if (!present.has(fmt_(d))) c++;
  return c;
}

function computeMissingForWindow_(model, upTo) {
  const floor = startFloor_();
  let start = addDays_(startOfDay_(upTo), -(CONFIG.WATCH_DAYS - 1));
  if (start < floor) start = floor;
  const tabs = { Medical: 'Medical', 'OPD / X-Ray / Procedure': 'OPD/X-Ray/Pro', Lab: 'Lab' };
  const out = {};
  Object.keys(tabs).forEach(label => {
    const tk = tabs[label];
    const present = new Set(model.records.filter(r => r.tabKey === tk && r.revDate)
                                         .map(r => r.revDateStr));
    const miss = [];
    for (let d = new Date(start); d <= upTo; d = addDays_(d, 1)) {
      if (!present.has(fmt_(d))) miss.push(fmt_(d));
    }
    if (miss.length) out[label] = miss;
  });
  return out;
}

function getTab_(name, headersIfNew) {
  const ss = SpreadsheetApp.openById(CONFIG.REPORT_ID);
  let sh = ss.getSheets().filter(s => s.getName().toLowerCase() === name.toLowerCase())[0];
  if (!sh) {
    sh = ss.insertSheet(name);
    if (headersIfNew)
      sh.getRange(1, 1, 1, headersIfNew.length).setValues([headersIfNew]).setFontWeight('bold');
  }
  return sh;
}

function findHeaderRow_(values, signature) {
  const limit = Math.min(values.length, 6);
  for (let i = 0; i < limit; i++) {
    const joined = values[i].map(c => String(c).toLowerCase().trim()).join('|');
    if (signature.every(sig => joined.indexOf(sig) >= 0)) return i;
  }
  return -1;
}
function headerMap_(headerRow) {
  const m = {};
  headerRow.forEach((h, i) => {
    const key = String(h).toLowerCase().trim();
    if (key && !(key in m)) m[key] = i;   // first occurrence wins (handles duplicate "Expenses")
  });
  return m;
}

function parseNum_(raw) {
  if (raw === '' || raw === null || raw === undefined) return { ok: true, value: 0, blank: true };
  if (typeof raw === 'number') return { ok: true, value: raw };
  const s = String(raw).trim();
  if (s.charAt(0) === '#') return { ok: false, type: 'formula', raw: s };
  const cleaned = s.replace(/[,\s\u20b9]/g, '');
  if (/^-?\d+(\.\d+)?$/.test(cleaned)) {
    const leadingZero = /^0\d+/.test(cleaned);
    return { ok: true, value: Number(cleaned), leadingZero: leadingZero, raw: s };
  }
  return { ok: false, type: 'nonnumeric', raw: s };
}
function numOr0_(n) { return (n && n.ok) ? n.value : 0; }

function asDate_(v) {
  if (v instanceof Date) return v;
  if (v === '' || v === null || v === undefined) return null;
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

/** Returns {date: Date|null, str: 'yyyy-MM-dd'|'', issue: {type,suggested,sev}|null}. */
function normalizeDate_(raw, ts) {
  if (raw === '' || raw === null || raw === undefined)
    return { date: null, str: '', issue: { type: 'Missing date in row', suggested: 'Enter the revenue date', sev: SEV.HIGH } };

  let y, mo, da, issue = null;

  if (raw instanceof Date) {
    let yy = raw.getFullYear(), mm = raw.getMonth() + 1, dd = raw.getDate();
    const ancient = yy < 100;                 // a 2-digit year coerced into year 00xx
    if (ancient) yy += 2000;
    y = yy; mo = mm; da = dd;                  // as Sheets stored it
    let corrected = false;

    if (ancient && dd >= 1 && dd <= 12) {
      // An ancient date can only come from a typed M/D/Y string the D/M/Y-locale sheet
      // coerced — day and month are swapped vs intent. Recover by swapping them back.
      mo = dd; da = mm; corrected = true;
    } else if (!ancient && ts instanceof Date && dd >= 1 && dd <= 12 && mm >= 1 && mm <= 12) {
      // Non-ancient date-typed cell: only swap if the stored date is impossibly in the
      // future AND swapping makes it plausible — never corrupt an already-valid date.
      const tsDay = startOfDay_(ts);
      const storedFuture = (startOfDay_(new Date(y, mm - 1, dd)) - tsDay) / 86400000 > CONFIG.FUTURE_TOL;
      const swapPlausible = (startOfDay_(new Date(y, dd - 1, mm)) - tsDay) / 86400000 <= CONFIG.FUTURE_TOL;
      if (storedFuture && swapPlausible) { mo = dd; da = mm; corrected = true; }
    }

    if (ancient || corrected) {
      issue = { type: 'Coerced date auto-corrected',
        suggested: 'Read as ' + pad_(da) + '/' + pad_(mo) + '/' + y +
                   '. This Date column is not plain text, so Sheets transposed/aged the entry \u2014 ' +
                   'set the column format to plain text and re-enter to fix permanently.',
        sev: SEV.MEDIUM };
    }
  } else {
    const parts = String(raw).trim().split(/[\/\-.]/);
    if (parts.length !== 3) return { date: null, str: '',
      issue: { type: 'Unreadable date', suggested: 'Use DD/MM/YYYY', sev: SEV.HIGH } };
    mo = Number(parts[0]); da = Number(parts[1]); y = Number(parts[2]);   // source is M/D/Y
    if (y < 100) { const fixed = 2000 + y;
      issue = { type: 'Year typo', suggested: 'Year ' + parts[2] + ' \u2192 ' + fixed, sev: SEV.HIGH }; y = fixed; }
    if (mo > 12 && da <= 12) {                  // clearly written D/M/Y instead of M/D/Y
      const t = mo; mo = da; da = t;
      issue = { type: 'Transposed day/month', suggested: 'Read as ' + pad_(da) + '/' + pad_(mo) + '/' + y, sev: SEV.HIGH };
    }
    if (mo < 1 || mo > 12 || da < 1 || da > 31)
      return { date: null, str: '', issue: { type: 'Impossible date', suggested: 'Check this date', sev: SEV.HIGH } };
  }

  const d = new Date(y, mo - 1, da);
  if (ts instanceof Date && !issue) {
    const diff = (startOfDay_(d) - startOfDay_(ts)) / 86400000;
    if (diff > CONFIG.FUTURE_TOL)
      issue = { type: 'Date after submission', suggested: 'Revenue date is later than the day it was filed', sev: SEV.MEDIUM };
    else if (diff < -CONFIG.PAST_TOL)
      issue = { type: 'Date long before submission', suggested: 'Confirm this old date is correct', sev: SEV.REVIEW };
  }
  return { date: d, str: fmt_(d), issue: issue };
}


function inMonthStr_(dateStr, monthStart, monthEnd) {
  const d = parseYmd_(dateStr);
  return d && d >= monthStart && d <= monthEnd;
}

/* date utils (all in script TZ via formatDate where it matters) */
function fmt_(d)   { return Utilities.formatDate(d, CONFIG.TZ, 'yyyy-MM-dd'); }
function fmtDt_(d) { return Utilities.formatDate(d, CONFIG.TZ, 'yyyy-MM-dd HH:mm'); }
function pad_(n)   { return (n < 10 ? '0' : '') + n; }
function parseYmd_(s) {
  if (!s) return null;
  if (s instanceof Date) return startOfDay_(s);
  const m = String(s).match(/(\d{4})-(\d{2})-(\d{2})/);
  return m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null;
}
/** A Sheets cell may come back as a Date even when we wrote a string; render it cleanly.
 *  Built from the date's own components (not Utilities.formatDate) so ancient year-typo
 *  values like "0026" don't get shifted by the Julian-calendar cutover. */
function cellToStr_(v) {
  if (v instanceof Date) {
    const y = ('000' + v.getFullYear()).slice(-4);
    return y + '-' + pad_(v.getMonth() + 1) + '-' + pad_(v.getDate());
  }
  return v === null || v === undefined ? '' : String(v);
}
function startFloor_() {
  const d = parseYmd_(CONFIG.START_DATE);
  return d || new Date(2000, 0, 1);
}
function startOfDay_(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
function startOfMonth_(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
function addDays_(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function money_(n) { return '\u20b9' + Number(n || 0).toLocaleString('en-IN'); }
function esc_(s) { return String(s === null || s === undefined ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

/* =====================================================================================
 * 8. ONE-TIME SETUP  (run setupTriggers once, then authorize)
 * ===================================================================================== */

function setupTriggers() {
  removeTriggers_();
  ScriptApp.newTrigger('runDailyReport').timeBased()
    .everyDays(1).atHour(14).nearMinute(0).inTimezone(CONFIG.TZ).create();
  ScriptApp.newTrigger('runMonthlyGate').timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY).atHour(9).nearMinute(0).inTimezone(CONFIG.TZ).create();
  Logger.log('Triggers installed: daily 14:00 IST, monthly gate Sun 09:00 IST.');
}
function removeTriggers_() {
  ScriptApp.getProjectTriggers().forEach(t => {
    const fn = t.getHandlerFunction();
    if (fn === 'runDailyReport' || fn === 'runMonthlyGate') ScriptApp.deleteTrigger(t);
  });
}

/** Safe to run by hand any time to preview today's daily email without waiting for 2 PM. */
function testDailyNow()   { runDailyReport(); }
/** Run by hand to preview last month's summary without waiting for the first Sunday. */
function testMonthlyNow() { runMonthlyReport(); }
