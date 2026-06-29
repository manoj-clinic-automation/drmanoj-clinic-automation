/**
 * Monitor.gs — the Daily_Monitor dashboard tab + the summary emails.
 *
 * Computes its own at-a-glance view over the raw call records (independent of
 * the callback engine in Netting.gs), writes a single monitor tab, and sends a
 * summary email at the hours in CFG.EMAIL_HOURS.
 *
 * Reuses globals already defined elsewhere:
 *   last10_, hhmmssToSeconds_   (MyOperator.gs)
 *   getSpreadsheet_, getOrCreateTab_ (Sheets.gs)
 *   fetchCallsBetween_, computeNetMissed_, dayBounds_ (MyOperator.gs / Netting.gs / Main.gs)
 *
 * "Resolved" and "Awaiting callback" are taken from the SAME engine that builds
 * Callbacks_Today (netResult), so the numbers always agree with that tab.
 */

/* ---------- small format helpers ---------- */
function secsToMS_(sec) {
  sec = Math.max(0, Math.round(sec || 0));
  var m = Math.floor(sec / 60), s = sec % 60;
  return m + ':' + (s < 10 ? '0' : '') + s;
}
function pad2_(n) { return (n < 10 ? '0' : '') + n; }
function objLen_(o) { return Object.keys(o).length; }
function repeatChar_(ch, n) { n = Math.round(n || 0); return n > 0 ? new Array(n + 1).join(ch) : ''; }
function fmtClock_(d) { return d ? Utilities.formatDate(d, Session.getScriptTimeZone(), 'h:mm a') : ''; }
/** Comma-list of attempt times for one callback entry, e.g. "10:14 AM, 8:15 PM". */
function attemptTimesStr_(e) {
  return (e.attemptTimes || []).map(fmtClock_).filter(String).join(', ');
}

/* ---------- per-call agent / wait extraction ---------- */
/** From one record's log_details, get the answering agent, talk seconds, and
 *  how long the caller rang before pickup (ringWait). */
function callAgentInfo_(r) {
  var agent = '', talkSec = 0, ringWait = null;
  var startSec = Number(r.start_time) || 0;
  var lds = (r.log_details && r.log_details.length) ? r.log_details : [];
  var recv = null, anyName = '';
  for (var i = 0; i < lds.length; i++) {
    var ld = lds[i];
    var nm = (ld.received_by && ld.received_by[0] && ld.received_by[0].name) ? ld.received_by[0].name : '';
    if (!anyName && nm) anyName = nm;
    if (ld.action === 'received') { recv = ld; if (nm) agent = nm; break; }
  }
  if (!agent) agent = anyName;
  if (recv) {
    talkSec = hhmmssToSeconds_(recv.duration);
    var ls = Number(recv.start_time) || 0;
    if (ls >= startSec && startSec > 0) ringWait = ls - startSec;
  }
  return { agent: agent, talkSec: talkSec, ringWait: ringWait };
}

/* ---------- one-pass stats over the day's raw records ---------- */
function computeMonitorStats_(raw) {
  var tz = Session.getScriptTimeZone();
  var s = {
    total: 0, incoming: 0, outgoing: 0, incomingMissed: 0, incomingAnswered: 0,
    afterHoursMissed: 0, uniqueCallers: {}, byHour: {}, agents: {}, perNumber: {},
    longestWaitSec: -1, longestWaitNum: ''
  };

  raw.forEach(function (r) {
    s.total++;
    var num = r.phone10 || last10_(r.caller_number_raw || r.caller_number || '');
    if (num) s.uniqueCallers[num] = true;
    var isOut = (String(r.direction) === 'outgoing') || (String(r.event) === '2');
    var missed = (r.is_missed === true) || String(r.status) === '2';
    var startSec = Number(r.start_time) || 0;
    var ts = startSec ? new Date(startSec * 1000) : null;
    var info = callAgentInfo_(r);

    var pn = num ? (s.perNumber[num] || (s.perNumber[num] = { attempts: 0, resolved: false, how: '', handledBy: '' })) : null;

    if (isOut) {
      s.outgoing++;
      if (info.agent) {
        var ao = s.agents[info.agent] || (s.agents[info.agent] = { answered: 0, talkSec: 0, outMade: 0, outConnected: 0 });
        ao.outMade++;
        if (!missed) ao.outConnected++;
      }
      if (pn && !missed) { pn.resolved = true; if (!pn.how) pn.how = 'Called back'; if (info.agent) pn.handledBy = info.agent; }
    } else {
      s.incoming++;
      var hh = ts ? Number(Utilities.formatDate(ts, tz, 'H')) : 0;
      var hb = s.byHour[hh] || (s.byHour[hh] = { answered: 0, missed: 0 });
      if (missed) {
        s.incomingMissed++; hb.missed++;
        if (ts && (ts.getHours() < CFG.WORKDAY_START_HOUR || ts.getHours() >= CFG.WORKDAY_END_HOUR)) s.afterHoursMissed++;
        if (pn) pn.attempts++;
      } else {
        s.incomingAnswered++; hb.answered++;
        if (info.agent) {
          var ai = s.agents[info.agent] || (s.agents[info.agent] = { answered: 0, talkSec: 0, outMade: 0, outConnected: 0 });
          ai.answered++; ai.talkSec += info.talkSec;
        }
        if (info.ringWait != null && info.ringWait > s.longestWaitSec) {
          s.longestWaitSec = info.ringWait; s.longestWaitNum = num;
        }
        if (pn) { pn.resolved = true; if (!pn.how) pn.how = 'Got through'; if (info.agent) pn.handledBy = info.agent; }
      }
    }
  });
  return s;
}

/** Agent rows sorted by calls answered (busiest first). */
function agentRows_(s) {
  var out = [];
  Object.keys(s.agents).forEach(function (name) {
    var a = s.agents[name];
    out.push({
      name: name, answered: a.answered, talkMin: Math.round(a.talkSec / 60),
      avg: a.answered ? secsToMS_(a.talkSec / a.answered) : '—',
      outMade: a.outMade, outConnected: a.outConnected
    });
  });
  out.sort(function (x, y) { return y.answered - x.answered; });
  return out;
}

/** Numbers that tried 2+ times (high-intent), with how they resolved. */
function repeatRows_(s) {
  var out = [];
  Object.keys(s.perNumber).forEach(function (num) {
    var p = s.perNumber[num];
    if (p.attempts >= 2) out.push({ number: num, attempts: p.attempts, resolved: p.resolved, how: p.how, handledBy: p.handledBy });
  });
  out.sort(function (x, y) { return y.attempts - x.attempts; });
  return out;
}

/** Last up-to-7 daily callback-miss rates, read from Daily_Summary. */
function sevenDayTrend_() {
  var out = [];
  var ss = getSpreadsheet_();
  var sh = ss.getSheetByName(CFG.TAB_SUMMARY);
  if (!sh) return out;
  var last = sh.getLastRow();
  if (last < 2) return out;
  var n = Math.min(7, last - 1);
  // cols: Date, Total Calls, Incoming, Net-Missed, Resolved, Net-Missed %
  var vals = sh.getRange(last - n + 1, 1, n, 6).getValues();
  vals.forEach(function (row) {
    var incoming = Number(row[2]) || 0;
    var netMissed = Number(row[3]) || 0;
    out.push({ date: row[0], rate: incoming ? Math.round((netMissed / incoming) * 100) : 0 });
  });
  return out;
}

/* ---------- build the Daily_Monitor tab ---------- */
function buildMonitorTab_(raw, netResult) {
  var tz = Session.getScriptTimeZone();
  var s = computeMonitorStats_(raw);
  var sh = getOrCreateTab_(CFG.TAB_MONITOR, null);
  sh.clear();

  var W = 6, rows = [], sectionRows = [], boldRows = [];
  function push(arr) { while (arr.length < W) arr.push(''); rows.push(arr.slice(0, W)); }
  function section(title) { push([title, '', '', '', '', '']); sectionRows.push(rows.length); }
  function colhead(arr) { push(arr); boldRows.push(rows.length); }
  function blank() { push(['', '', '', '', '', '']); }

  // Title
  push(['Clinic call monitor', '', '', '', '', '']); boldRows.push(1);
  push(['Updated ' + Utilities.formatDate(new Date(), tz, 'EEE d MMM yyyy, h:mm a') + '  ·  refreshes 8am–8pm', '', '', '', '', '']);
  blank();

  // Today at a glance
  section('Today at a glance');
  var rate = s.incoming ? Math.round((s.incomingMissed / s.incoming) * 100) : 0;
  var lw = (s.longestWaitSec >= 0)
    ? secsToMS_(s.longestWaitSec) + (s.longestWaitNum ? ('  (' + s.longestWaitNum + ')') : '')
    : '—';
  push(['Total calls', s.total, '', 'Incoming', s.incoming, '']);
  push(['Incoming missed', s.incomingMissed, '', 'Missed rate', rate + '%', '']);
  push(['Resolved', netResult.stats.resolved, '', 'Awaiting callback', netResult.entries.length, '']);
  push(['Longest wait to answer', lw, '', 'Unique callers', objLen_(s.uniqueCallers), '']);
  blank();

  // Awaiting callback — with the time of each attempt
  section('Awaiting callback — attempt times');
  colhead(['Phone', 'Attempts', 'Attempt times', 'Priority', 'After-hrs', '']);
  if (!netResult.entries.length) push(['(none right now)', '', '', '', '', '']);
  netResult.entries.forEach(function (e) {
    push(["'" + e.number, e.attempts, attemptTimesStr_(e), e.priority ? '★' : '', e.afterHours ? 'Yes' : '', '']);
  });
  blank();

  // Agent activity
  section('Agent activity (today)');
  colhead(['Agent', 'Answered', 'Talk (min)', 'Avg call', 'Callbacks made', 'Connected']);
  var agents = agentRows_(s);
  if (!agents.length) push(['(no agent activity yet)', '', '', '', '', '']);
  agents.forEach(function (a) { push([a.name, a.answered, a.talkMin, a.avg, a.outMade, a.outConnected]); });
  blank();

  // Repeat callers
  section('Repeat callers (2+ attempts)');
  colhead(['Phone', 'Attempts', 'Resolved?', 'How', 'Handled by', '']);
  var reps = repeatRows_(s);
  if (!reps.length) push(['(none today)', '', '', '', '', '']);
  reps.forEach(function (r) {
    push(["'" + r.number, r.attempts, r.resolved ? 'Yes' : 'No', r.resolved ? r.how : 'Pending', r.handledBy || '', '']);
  });
  blank();

  // Busiest hours
  section('Busiest hours — incoming  (■ answered  □ missed)');
  for (var h = CFG.WORKDAY_START_HOUR; h <= CFG.WORKDAY_END_HOUR; h++) {
    var hb = s.byHour[h] || { answered: 0, missed: 0 };
    var tot = hb.answered + hb.missed;
    push([pad2_(h) + ':00', repeatChar_('■', hb.answered) + repeatChar_('□', hb.missed), tot || '', '', '', '']);
  }
  blank();

  // 7-day trend
  section('7-day callback-miss rate');
  var trend = sevenDayTrend_();
  if (!trend.length) push(['(builds up over the coming days)', '', '', '', '', '']);
  trend.forEach(function (t) {
    var d = (t.date instanceof Date) ? Utilities.formatDate(t.date, tz, 'dd MMM') : String(t.date);
    push([d, t.rate + '%', repeatChar_('█', t.rate / 5), '', '', '']);
  });
  blank();

  // Escalate
  section('Escalate to doctor');
  var prio = 0;
  netResult.entries.forEach(function (e) { if (e.priority) prio++; });
  push(['Pending callbacks', netResult.entries.length, '', '', '', '']);
  push(['High-intent (3+ attempts, unresolved)', prio, '', '', '', '']);
  push(['After-hours missed', s.afterHoursMissed, '', '', '', '']);

  // write + format
  sh.getRange(1, 1, rows.length, W).setValues(rows);
  sh.setColumnWidth(1, 230); sh.setColumnWidth(2, 95); sh.setColumnWidth(3, 160);
  sh.setColumnWidth(4, 120); sh.setColumnWidth(5, 120); sh.setColumnWidth(6, 90);
  sh.getRange(1, 1, 1, W).setFontSize(14).setFontWeight('bold');
  sectionRows.forEach(function (rn) { sh.getRange(rn, 1, 1, W).setFontWeight('bold').setBackground('#E6F1FB'); });
  boldRows.forEach(function (rn) { sh.getRange(rn, 1, 1, W).setFontWeight('bold'); });
  sh.setFrozenRows(2);
  return s;
}

/* ---------- summary email ---------- */
function row2_(k, v) {
  return '<tr><td style="color:#666;padding:4px 12px 4px 0;">' + k +
         '</td><td align="right" style="padding:4px 0;"><b>' + v + '</b></td></tr>';
}

function buildEmailHtml_(s, netResult, label) {
  var rate = s.incoming ? Math.round((s.incomingMissed / s.incoming) * 100) : 0;
  var h = '';
  h += '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;max-width:560px;">';
  h += '<h2 style="margin:0 0 2px;">Clinic call summary</h2>';
  h += '<div style="color:#777;margin-bottom:12px;">' + label + '</div>';
  h += '<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;">';
  h += row2_('Total calls', s.total);
  h += row2_('Incoming', s.incoming);
  h += row2_('Incoming missed', s.incomingMissed + ' (' + rate + '%)');
  h += row2_('Resolved', netResult.stats.resolved);
  h += row2_('Awaiting callback', netResult.entries.length);
  h += row2_('Longest wait to answer', (s.longestWaitSec >= 0 ? secsToMS_(s.longestWaitSec) : '—'));
  h += '</table>';

  if (netResult.entries.length) {
    h += '<h3 style="margin:16px 0 4px;">Awaiting callback</h3><ul style="margin:0;padding-left:18px;">';
    netResult.entries.forEach(function (e) {
      var times = attemptTimesStr_(e);
      h += '<li>' + e.number + ' — ' + e.attempts + ' attempt' + (e.attempts > 1 ? 's' : '') +
           (times ? ' <span style="color:#555;">at ' + times + '</span>' : '') +
           (e.priority ? ' <b>(priority)</b>' : '') + (e.afterHours ? ' · after-hours' : '') + '</li>';
    });
    h += '</ul>';
  } else {
    h += '<p style="color:#1d7a51;margin:16px 0 0;">No pending callbacks right now.</p>';
  }

  var agents = agentRows_(s);
  if (agents.length) {
    h += '<h3 style="margin:16px 0 4px;">Agent activity</h3>';
    h += '<table cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">';
    h += '<tr style="background:#eef2fb;"><th align="left">Agent</th><th>Answered</th><th>Talk (min)</th><th>Callbacks</th></tr>';
    agents.forEach(function (a) {
      h += '<tr style="border-top:1px solid #eee;"><td>' + a.name + '</td><td align="center">' + a.answered +
           '</td><td align="center">' + a.talkMin + '</td><td align="center">' + a.outMade + '</td></tr>';
    });
    h += '</table>';
  }
  h += '<p style="color:#999;font-size:12px;margin-top:18px;">Auto-generated from the clinic IVR logs. Full detail is in the Daily_Monitor sheet.</p>';
  h += '</div>';
  return h;
}

/** Compute over the day's raw records and send the summary email. */
function sendSummaryEmail_(raw, netResult, label) {
  if (!CFG.EMAIL_TO) { Logger.log('No EMAIL_TO set in Config — skipping email.'); return; }
  var s = computeMonitorStats_(raw);
  var subject = 'Clinic call summary — ' + label + ' · ' + netResult.entries.length + ' awaiting callback';
  MailApp.sendEmail({ to: CFG.EMAIL_TO, subject: subject, htmlBody: buildEmailHtml_(s, netResult, label) });
  Logger.log('Summary email sent to %s (%s awaiting callback).', CFG.EMAIL_TO, netResult.entries.length);
}

/* ---------- manual tests ---------- */
/** Rebuild the Daily_Monitor tab now (no schedule gate). */
function testMonitorNow() {
  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  buildMonitorTab_(raw, result);
  Logger.log('Daily_Monitor rebuilt for %s — open the tab to view it.', b.label);
}

/** Send ONE summary email now, to confirm delivery + formatting. */
function testSummaryEmailNow() {
  var b = dayBounds_(0);
  var raw = fetchCallsBetween_(b.start, b.end);
  var result = computeNetMissed_(raw);
  var label = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'd MMM, h:mm a');
  sendSummaryEmail_(raw, result, label);
}
