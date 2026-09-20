// S276 — anchored edits for DailyClinicReports/Code.gs (v5 -> v6). Runs in the page
// (the Apps Script editor) so the live text never leaves the browser; also runs in
// node for the offline test. Each anchor must occur exactly once or nothing changes.
var S276_EDITS = [
  ["v5: adds a per-vehicle TRIPS breakdown (start, end, duration, distance)\n *     below the vehicle summary, read from Trip.csv. Builds on v4\n *     (UTF-16 attendance decode + fixed-width parsing).\n",
   "v5: adds a per-vehicle TRIPS breakdown (start, end, duration, distance)\n *     below the vehicle summary, read from Trip.csv. Builds on v4\n *     (UTF-16 attendance decode + fixed-width parsing).\n * v6 (S276, 20-Sep-2026): the attendance section reads the clinic server's own\n *     \"Attendance — day summary\" mail (21:00 IST). The ONtime machine's mail\n *     stopped on 01-Aug-2026 and the digest had said \"Attendance report not\n *     received\" every day since. The ONtime path stays as the fallback.\n"],
  ["  ATTENDANCE_SUBJECT: 'ONtime Employee Manager Report',\n",
   "  ATTENDANCE_SUBJECT: 'ONtime Employee Manager Report',\n  // v6 (S276): the clinic server's own day summary, read FIRST; ONtime is the fallback.\n  ATTENDANCE_SUMMARY_SUBJECT: 'Attendance — day summary',\n"],
  ["function processAttendance_(ss, notes) {\n  var out = { found: false, dated: '', absentees: [], note: '' };\n  var msgs = findMessagesBySubject_(CONFIG.ATTENDANCE_SUBJECT);\n",
   "function processAttendance_(ss, notes) {\n  var out = { found: false, dated: '', absentees: [], note: '', present: -1, late: -1, lateList: [], source: '' };\n  // v6 (S276): the clinic server's own day summary first; the ONtime path below is the fallback.\n  var sum = processAttendanceSummary_(notes);\n  if (sum) return sum;\n  var msgs = findMessagesBySubject_(CONFIG.ATTENDANCE_SUBJECT);\n"],
  ["// Read raw bytes and decode as text, auto-detecting UTF-16 (the ONtime export\n",
   "// v6 (S276, 20-Sep-2026). The clinic server mails \"Attendance — day summary\n// (DD Mon): N present, M absent\" at 21:00 IST every day. Its plain body carries\n// \"| N PRESENT | M ABSENT | K LATE |\", a PRESENT table whose Name column reads\n// \"Name (late 14m)\" for a late arrival, and \"### ABSENT (M)\" followed by the\n// comma-separated names. Newest such mail = yesterday's, which is the day the\n// digest covers.\nfunction processAttendanceSummary_(notes) {\n  var msgs = findMessagesBySubject_(CONFIG.ATTENDANCE_SUMMARY_SUBJECT);\n  if (!msgs.length) { notes.push('Attendance day-summary email not found; trying the ONtime path.'); return null; }\n  var m = msgs[0];\n  var body = '';\n  try { body = m.getPlainBody() || ''; } catch (e) {}\n  var p = parseAttendanceSummary_(body);\n  if (!p) { notes.push('Attendance day-summary email found but could not be read.'); return null; }\n  p.found = true;\n  p.source = 'summary';\n  var sub = m.getSubject() || '';\n  var d = sub.match(/\\((\\d{1,2} \\w{3})\\)/);\n  p.dated = d ? d[1] : Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'dd MMM');\n  return p;\n}\n\nfunction parseAttendanceSummary_(body) {\n  var out = { found: false, dated: '', absentees: [], note: '', present: -1, late: -1, lateList: [], source: '' };\n  var t = String(body || '').replace(/\\r/g, '');\n  var c = t.match(/\\|\\s*(\\d+)\\s*PRESENT\\s*\\|\\s*(\\d+)\\s*ABSENT\\s*\\|\\s*(\\d+)\\s*LATE\\s*\\|/i);\n  if (!c) return null;\n  out.present = parseInt(c[1], 10);\n  var absentCount = parseInt(c[2], 10);\n  out.late = parseInt(c[3], 10);\n  var a = t.match(/###\\s*ABSENT\\s*\\((\\d+)\\)\\s*\\n([^\\n]*)/i);\n  if (a && absentCount > 0) {\n    out.absentees = a[2].split(',').map(function (s) { return s.trim(); })\n      .filter(function (s) { return s && s !== '—' && s !== '-'; });\n  }\n  var re = /^\\|\\s*([^|]+?)\\s*\\(late (\\d+)m\\)\\s*\\|/gmi, mm;\n  while ((mm = re.exec(t)) !== null) out.lateList.push(mm[1].trim() + ' ' + mm[2] + 'm');\n  if (absentCount > 0 && out.absentees.length !== absentCount)\n    out.note = 'absent count ' + absentCount + ' but ' + out.absentees.length + ' name(s) read';\n  return out;\n}\n\n// v6 (S276): read-only proof. Logs what the attendance section would say. Sends nothing.\nfunction previewAttendance() {\n  var notes = [];\n  var att = processAttendance_(null, notes);\n  Logger.log(JSON.stringify({ att: att, notes: notes }));\n}\n\n// Read raw bytes and decode as text, auto-detecting UTF-16 (the ONtime export\n"],
  ["  if (!att || !att.found) {\n    h.push('<p style=\"margin:2px 0;color:#a00\">Attendance report not received.</p>');\n  } else if (att.note) {\n",
   "  if (!att || !att.found) {\n    h.push('<p style=\"margin:2px 0;color:#a00\">Attendance report not received.</p>');\n  } else if (att.source === 'summary') {\n    // v6 (S276): the clinic server's own day summary.\n    h.push('<p style=\"margin:2px 0\"><b>' + att.present + ' present</b> &middot; ' +\n      (att.absentees.length\n        ? '<b style=\"color:#b00020\">' + att.absentees.length + ' absent</b>: ' + att.absentees.join(', ')\n        : '<span style=\"color:#137333\">0 absent</span>') +\n      ' &middot; ' + att.late + ' late' +\n      (att.lateList.length ? ' <span style=\"color:#666\">(' + att.lateList.join(', ') + ')</span>' : '') + '</p>');\n    if (att.note) h.push('<p style=\"margin:2px 0;color:#a60\">' + att.note + '</p>');\n  } else if (att.note) {\n"]
];
var S276_MARK = "v6 (S276, 20-Sep-2026)";

function s276Apply(text) {
  if (text.indexOf(S276_MARK) >= 0) return { text: text, msgs: ["ALREADY"], ok: true };
  var msgs = [];
  for (var i = 0; i < S276_EDITS.length; i++) {
    var n = text.split(S276_EDITS[i][0]).length - 1;
    if (n !== 1) return { text: null, msgs: ["edit " + (i + 1) + ": anchor found " + n + " time(s), not once -- refusing"], ok: false };
  }
  for (var j = 0; j < S276_EDITS.length; j++) {
    text = text.replace(S276_EDITS[j][0], function () { return S276_EDITS[j][1]; });
    msgs.push("edit " + (j + 1) + " applied");
  }
  return { text: text, msgs: msgs, ok: true };
}
if (typeof module !== "undefined") module.exports = { s276Apply: s276Apply, S276_EDITS: S276_EDITS };
