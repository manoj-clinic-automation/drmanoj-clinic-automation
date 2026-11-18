/** ==========================================================================
 *  Renewal_Nag.gs · v5 · S890 (18-Nov-2026, D1017) · PERSONAL account — lives in the Inbox Janitor project beside Code.gs.
 *
 *  v5 — THE OWNER'S RULING (21:56 18-Nov-2026): the renewals live WHOLLY ON THE CLINIC SERVER. This script holds NO list any
 *  more. It does three things, all through the server's token doors (the token = the Script Property RENEWALS_PUSH_TOKEN,
 *  the same one as before; nothing new to set):
 *    1. nagRenewals()  (the existing daily 08:42 trigger, unchanged): asks the server for today's due list — the server
 *       computes every lead time (passport 365 days; vehicle insurance 30; PUC 7; RC 45; everything else 45) and the
 *       cadence (daily inside 7 days, every 3 inside 21, weekly inside the lead time, a passport monthly before that,
 *       overdue kept 45 days) — and sends the mail the server composed, from this Gmail, as today. Then tells the server
 *       the mail went, so the cadence remembers. Document numbers: last 4 only, everywhere.
 *    2. feedRenewalMail_() (run by nagRenewals right after the mail): looks in this Gmail for renewal-type mails of the
 *       last 2 days and posts each — sender, date, subject, the first part of the text, attachment names, the Gmail link —
 *       to the server's "Found in your mail" box. NOTHING is changed by this: the owner taps Apply / Add as new / Not a
 *       renewal on the page. A posted thread is labelled Renewal-Posted and never posted again.
 *    3. seedServerOnce(): ONE-TIME. Posts the typed RENEWALS + ANNUAL_RENEWALS of Code.gs to the server with every
 *       number cut to its last 4 (the server cuts again). Refused by the server once seeded. After the seed is proven
 *       the typed lists in Code.gs are emptied (var RENEWALS = []; var ANNUAL_RENEWALS = [];).
 *  The old push (pushRenewalsToVPS) is GONE: the server writes the health page's file from the one list itself.
 *  ========================================================================== */

var NAG_TO    = 'drmanojkragarwal@gmail.com';
var S890_BASE = 'https://followup.dr-manoj.in/scanapp/renewals/one/api';
var S890_TOKEN_PROP = 'RENEWALS_PUSH_TOKEN';
var S890_SEEN_LABEL = 'Renewal-Posted';
var S890_FEED_QUERY = 'newer_than:2d -from:me -label:' + S890_SEEN_LABEL + ' ' +
  '(renewed OR renewal OR "policy schedule" OR "policy issued" OR licence OR license OR subscription OR domain OR ' +
  '"valid till" OR "valid upto" OR "valid up to" OR expiry OR expires OR expiring OR "premium receipt" OR membership OR ' +
  '"registration certificate" OR PUC OR "pollution under control")';
var S890_EXCERPT = 1500;

function s890Token_() {
  return PropertiesService.getScriptProperties().getProperty(S890_TOKEN_PROP) || '';
}

function s890Call_(path, method, payload) {
  var token = s890Token_();
  if (!token) return { code: 0, body: 'NO TOKEN: Script Property ' + S890_TOKEN_PROP + ' not set' };
  var opt = { method: method, headers: { 'X-Finance-Renewals': token }, muteHttpExceptions: true };
  if (payload !== undefined) { opt.contentType = 'application/json'; opt.payload = JSON.stringify(payload); }
  var resp = UrlFetchApp.fetch(S890_BASE + path, opt);
  var txt = resp.getContentText();
  var json = null;
  try { json = JSON.parse(txt); } catch (e) { json = null; }
  return { code: resp.getResponseCode(), body: txt.slice(0, 300), json: json };
}

/** Any run of 5+ digits -> '…' + its last 4; a vehicle registration (UP25AB1234) -> '…1234'. The server does the same again. */
function s890Mask_(s) {
  return String(s || '')
    .replace(/\b([A-Z]{2})[ -]?(\d{1,2})[ -]?([A-Z]{1,3})[ -]?(\d{4})\b/g, function (m, a, b, c, d) { return '…' + d; })
    .replace(/\d{5,}/g, function (m) { return '…' + m.slice(-4); });
}

/* ---------------------------------------------------------------- 1. the 08:42 mail, from the server's list */
function nagRenewalsCore() {
  var r = s890Call_('/due', 'get');
  if (r.code !== 200 || !r.json || !r.json.ok) return 'DUE LIST NOT READ: HTTP ' + r.code + ' ' + r.body;
  var d = r.json;
  if (!d.items || !d.items.length) return 'quiet: nothing due on the server list';
  if (!d.nag_now) return 'due items exist (' + d.items.length + ') but none needed a nag today';
  MailApp.sendEmail(NAG_TO, d.subject, d.text);
  var s = s890Call_('/due/sent', 'post', { ids: d.ids_to_mark || [] });
  if (s.code !== 200) { Utilities.sleep(3000); s = s890Call_('/due/sent', 'post', { ids: d.ids_to_mark || [] }); }   // once more, then say so
  if (s.code !== 200) Logger.log('due/sent not marked: HTTP ' + s.code + ' ' + s.body);
  return 'nagged: ' + d.items.length + ' item(s), nearest ' + d.items[0].days + 'd; cadence marked: ' + (s.json && s.json.marked);
}

/* ---------------------------------------------------------------- 2. the feeder: renewal-type mails -> the page's box */
function feedRenewalMail_() {
  var label = GmailApp.getUserLabelByName(S890_SEEN_LABEL) || GmailApp.createLabel(S890_SEEN_LABEL);
  var threads = GmailApp.search(S890_FEED_QUERY, 0, 25);
  var mails = [], thr = [];
  threads.forEach(function (t) {
    var msgs = t.getMessages();
    var m = msgs[msgs.length - 1];
    var subj = String(m.getSubject() || '');
    if (/^(OVERDUE RENEWAL|RENEWAL DUE):/.test(subj)) return;              // our own nag
    var body = '';
    try { body = m.getPlainBody() || ''; } catch (e) { body = ''; }
    body = body.replace(/\r/g, '').replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();
    var att = [];
    try { m.getAttachments({ includeInlineImages: false }).forEach(function (a) { att.push(String(a.getName() || '').slice(0, 80)); }); } catch (e) {}
    mails.push({
      mail_key: 'gmail:' + m.getId(),
      received_at: Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'yyyy-MM-dd HH:mm'),
      sender: s890Mask_(String(m.getFrom() || '').slice(0, 160)),
      subject: s890Mask_(subj.slice(0, 200)),
      excerpt: s890Mask_(body.slice(0, S890_EXCERPT)),
      attachments: att.slice(0, 10),
      link: 'https://mail.google.com/mail/u/0/#all/' + m.getId()
    });
    thr.push(t);
  });
  if (!mails.length) return 'feed: nothing new';
  var r = s890Call_('/mail', 'post', { mails: mails });
  if (r.code !== 200) return 'FEED NOT POSTED: HTTP ' + r.code + ' ' + r.body;
  thr.forEach(function (t) { t.addLabel(label); });
  return 'feed: ' + mails.length + ' mail(s) posted (' + (r.json && r.json.stored) + ' new, ' + (r.json && r.json.already) + ' already)';
}

/* The trigger target (the daily 08:42 trigger stays as it is). */
function nagRenewals() {
  var out = nagRenewalsCore();
  var fed = '';
  try { fed = feedRenewalMail_(); } catch (e) { fed = 'FEED ERROR: ' + e; }
  return out + ' | ' + fed;
}

/* ---------------------------------------------------------------- 3. the one-time seed from the typed lists of Code.gs */
function s890Last4_(s) { var d = String(s || '').replace(/\D/g, ''); return d ? d.slice(-4) : ''; }

function seedServerOnce() {
  var rows = [];
  (typeof RENEWALS !== 'undefined' ? RENEWALS : []).forEach(function (r) {
    var br = String(r.vendor || '').match(/\(([^)]*\d[^)]*)\)/);
    rows.push({
      what: s890Mask_(String(r.vendor || '').replace(/\s*\([^)]*\d[^)]*\)/g, '').trim()),
      number: br ? s890Last4_(br[1]) : '',
      dateISO: r.dateISO || '', expiryISO: r.expiryISO || '', cycleMonths: r.cycleMonths || 12,
      note: s890Mask_(r.note || '')
    });
  });
  (typeof ANNUAL_RENEWALS !== 'undefined' ? ANNUAL_RENEWALS : []).forEach(function (r) {
    rows.push({ what: s890Mask_(String(r.title || '').replace(/^ANNUAL:\s*/, '')), number: '', dateISO: r.firstISO || '',
                cycleMonths: 12, note: s890Mask_(r.note || '') });
  });
  var r = s890Call_('/seed', 'post', { rows: rows });
  var msg = 'seed: ' + rows.length + ' rows sent -> HTTP ' + r.code + ' ' + r.body;
  Logger.log(msg);
  return msg;
}

/* A dry look at what the seed WOULD send (numbers already cut) — nothing posted. Safe from the editor. */
function seedPreview() {
  var out = [];
  (typeof RENEWALS !== 'undefined' ? RENEWALS : []).forEach(function (r) {
    out.push((r.expiryISO || r.dateISO) + '  ' + s890Mask_(String(r.vendor || '').replace(/\s*\([^)]*\d[^)]*\)/g, '')));
  });
  (typeof ANNUAL_RENEWALS !== 'undefined' ? ANNUAL_RENEWALS : []).forEach(function (r) { out.push(r.firstISO + '  ' + s890Mask_(r.title)); });
  var msg = out.join('\n');
  Logger.log(msg);
  return msg;
}
