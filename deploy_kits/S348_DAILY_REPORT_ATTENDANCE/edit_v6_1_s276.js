var S276B_ANCHOR_START = "function processAttendanceSummary_(notes) {\n";
var S276B_ANCHOR_END = "// v6 (S276): read-only proof. Logs what the attendance section would say. Sends nothing.\n";
var S276B_NEW = "function processAttendanceSummary_(notes) {\n" +
"  var msgs = findMessagesBySubject_(CONFIG.ATTENDANCE_SUMMARY_SUBJECT);\n" +
"  if (!msgs.length) { notes.push('Attendance day-summary email not found; trying the ONtime path.'); return null; }\n" +
"  var m = msgs[0];\n" +
"  // v6.1: the mail is HTML-only, so read the HTML first (its structure is fixed);\n" +
"  // the tag-stripped plain rendering is the fallback. The first live run proved\n" +
"  // that getPlainBody() alone does not carry the shape the parser expected.\n" +
"  var p = null;\n" +
"  try { p = parseAttendanceSummary_(m.getBody() || ''); } catch (e) {}\n" +
"  if (!p) { try { p = parseAttendanceSummary_(m.getPlainBody() || ''); } catch (e2) {} }\n" +
"  if (!p) { notes.push('Attendance day-summary email found but could not be read.'); return null; }\n" +
"  p.found = true;\n" +
"  p.source = 'summary';\n" +
"  var sub = m.getSubject() || '';\n" +
"  var d = sub.match(/\\((\\d{1,2} \\w{3})\\)/);\n" +
"  p.dated = d ? d[1] : Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'dd MMM');\n" +
"  return p;\n" +
"}\n" +
"\n" +
"// Reads either the HTML body (three count boxes, the PRESENT table whose Name\n" +
"// cell carries <b>(late Nm)</b>, and the ABSENT heading followed by one div of\n" +
"// names or 'None') or the tag-stripped plain rendering of the same mail.\n" +
"function parseAttendanceSummary_(body) {\n" +
"  var out = { found: false, dated: '', absentees: [], note: '', present: -1, late: -1, lateList: [], source: '' };\n" +
"  var t = String(body || '').replace(/\\r/g, '');\n" +
"  var isHtml = /<\\/?(div|td|h3|table)\\b/i.test(t);\n" +
"  var c, absentCount, a, re, mm, names;\n" +
"  if (isHtml) {\n" +
"    var cp = t.match(/>\\s*(\\d+)\\s*<\\/div>\\s*<div[^>]*>\\s*PRESENT\\s*</i);\n" +
"    var ca = t.match(/>\\s*(\\d+)\\s*<\\/div>\\s*<div[^>]*>\\s*ABSENT\\s*</i);\n" +
"    var cl = t.match(/>\\s*(\\d+)\\s*<\\/div>\\s*<div[^>]*>\\s*LATE\\s*</i);\n" +
"    if (!cp || !ca || !cl) return null;\n" +
"    out.present = parseInt(cp[1], 10); absentCount = parseInt(ca[1], 10); out.late = parseInt(cl[1], 10);\n" +
"    a = t.match(/ABSENT\\s*\\((\\d+)\\)\\s*<\\/h3>\\s*<div[^>]*>([^<]*)<\\/div>/i);\n" +
"    names = a ? a[2] : '';\n" +
"    re = /<td[^>]*>\\s*([^<]+?)\\s*<b[^>]*>\\(late (\\d+)m\\)<\\/b>/gi;\n" +
"  } else {\n" +
"    c = t.match(/(\\d+)\\s*PRESENT\\s*\\|?\\s*(\\d+)\\s*ABSENT\\s*\\|?\\s*(\\d+)\\s*LATE/i);\n" +
"    if (!c) return null;\n" +
"    out.present = parseInt(c[1], 10); absentCount = parseInt(c[2], 10); out.late = parseInt(c[3], 10);\n" +
"    a = t.match(/ABSENT\\s*\\((\\d+)\\)\\s*\\n?\\s*([^\\n]*?)\\s*(?:\\n|Late\\/early|$)/i);\n" +
"    names = a ? a[2] : '';\n" +
"    re = /(\\S+)\\s*\\(late (\\d+)m\\)/g;   \/\/ fallback only: the word before (late Nm)\n" +
"  }\n" +
"  names = String(names).replace(/&[a-z]+;/g, ' ').trim();\n" +
"  if (absentCount > 0 && names && !/^none$/i.test(names)) {\n" +
"    out.absentees = names.split(',').map(function (s) { return s.trim(); })\n" +
"      .filter(function (s) { return s && s !== '\\u2014' && s !== '-'; });\n" +
"  }\n" +
"  while ((mm = re.exec(t)) !== null) out.lateList.push(mm[1].replace(/\\s+/g, ' ').trim() + ' ' + mm[2] + 'm');\n" +
"  if (absentCount > 0 && out.absentees.length !== absentCount)\n" +
"    out.note = 'absent count ' + absentCount + ' but ' + out.absentees.length + ' name(s) read';\n" +
"  return out;\n" +
"}\n\n";
function s276bApply(text) {
  if (text.indexOf("v6.1: the mail is HTML-only") >= 0) return { text: text, msgs: ["ALREADY"], ok: true };
  var i = text.indexOf(S276B_ANCHOR_START), j = text.indexOf(S276B_ANCHOR_END);
  if (i < 0 || j < 0 || j < i || text.split(S276B_ANCHOR_START).length !== 2 || text.split(S276B_ANCHOR_END).length !== 2)
    return { text: null, msgs: ["anchors not found exactly once -- refusing"], ok: false };
  return { text: text.slice(0, i) + S276B_NEW + text.slice(j), msgs: ["v6.1 applied"], ok: true };
}
if (typeof module !== "undefined") module.exports = { s276bApply: s276bApply };
