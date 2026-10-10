/** ==========================================================================
 *  Payments_v24.gs · Inbox Janitor v2.4 · S506 (10-Oct-2026) · PERSONAL account (drmanojkragarwal@)
 *  Lives in the "Janitor" project beside Code.gs (one namespace).
 *
 *  THE OWNER, 10-Oct-2026: the payments sheet "is not updated and up to the mark".
 *  What was wrong (read 10-Oct): any mail from a fixed list of 18 senders became a row -- OTPs, failed and
 *  declined payments, reminders, notices, and Docterz notification mails WITH PATIENT NAMES; only the first
 *  message of a thread was read; nothing stopped the same mail being written twice; the amount was the first
 *  rupee figure in the mail and a dollar receipt (Anthropic) was left blank.
 *
 *  v2.4:
 *   * a mail is a row only when its subject says it is a receipt, an invoice, a bill or a completed payment,
 *     and says nothing of OTP / verification / failed / declined / reminder / appointment / report ...;
 *   * a Docterz mail is a row only when it is an invoice or a receipt -- a patient's name never reaches the
 *     sheet again;
 *   * EVERY message of a thread is read, and each message is written ONCE (its id is kept on the tab
 *     'Janitor-Seen'); a payment arriving in an old thread is still caught (the last 3 days are read again);
 *   * the amount is the labelled one ('Amount paid', 'Total', 'Grand total' ...) before any other figure; a
 *     dollar amount goes into the description ('— USD 23.60') and never into the rupee column;
 *   * Sheet1 keeps its six columns and its row numbers (the VPS reads it every night and refuses a seventh
 *     column or a shorter sheet) -- the Seen tab is a second tab, after Sheet1.
 *  markRegisterV24() -- run ONCE: marks the old rows, never deletes one: '[DUPLICATE of row N]',
 *  '[NOT A PAYMENT]', '[CHECK AMOUNT]' at the front of the description; a blank amount is re-read from its
 *  mail; a Docterz notification row's description is replaced by words without the patient's name.
 *  ========================================================================== */

var PAY_SEEN_TAB = 'Janitor-Seen';
var PAY_NOT = /\b(otp|one[- ]time password|verification|verify|sign[- ]?in|secure link|security alert|password|reset|credentials|declined|failed|unsuccessful|paused|turned off|balance is low|will be charged|expir\w*|reminder|maintenance|days? left|day\(s\) left|changes to|trial|appointment|consultation report|clinical data|meeting|sound was played|cancell?ed|enrol?lment|claim|disbursement|settlement|activated|upgrade request|contact person|statement|policy number\s*:)\b/i;
var PAY_YES = /(receipt|invoice|payment (?:successful|confirmation)|payment (?:is |has been )?(?:successfully )?(?:received|completed?)|purchas|premium|subscription (?:renewal|payment)|subscription is confirmed|bill for your|has been charged|paid)/i;

function payKind_(subject) {
  if (PAY_NOT.test(subject)) return '';
  if (!PAY_YES.test(subject)) return '';
  if (/bill for your/i.test(subject)) return 'bill';
  if (/invoice/i.test(subject)) return 'invoice';
  return 'receipt';
}

function payAmount_(text) {
  var t = String(text || '').replace(/ /g, ' ');
  var lab = /(?:amount paid|total paid|paid amount|grand total|total amount|amount charged|order total|amount due|total)\s*(?:\([^)]*\))?\s*[:\-]?\s*(₹|Rs\.?|INR|US\$|\$|USD)\s*([\d,]+(?:\.\d{1,2})?)/i;
  var m = t.match(lab) || t.match(/(₹|Rs\.?|INR|US\$|\$|USD)\s?([\d,]+(?:\.\d{1,2})?)/i);
  if (!m) return { cur: '', amt: '' };
  return { cur: /\$|USD/i.test(m[1]) ? 'USD' : 'INR', amt: m[2].replace(/,/g, '') };
}

var PAY_SEEN_CACHE_ = null;
function paySeen_() {
  if (PAY_SEEN_CACHE_) return PAY_SEEN_CACHE_;
  var ss = SpreadsheetApp.openById(registerSheet_().getParent().getId());
  var sh = ss.getSheetByName(PAY_SEEN_TAB);
  if (!sh) {
    sh = ss.insertSheet(PAY_SEEN_TAB, ss.getSheets().length);     // always AFTER Sheet1
    sh.appendRow(['Message id', 'Seen at', 'What became of it']);
  }
  var ids = {};
  var n = sh.getLastRow();
  if (n > 1) sh.getRange(2, 1, n - 1, 1).getValues().forEach(function (r) { ids[String(r[0])] = true; });
  PAY_SEEN_CACHE_ = { sheet: sh, ids: ids };
  return PAY_SEEN_CACHE_;
}
function paySeenAdd_(id, what) {
  var s = paySeen_();
  if (s.ids[id]) return;
  s.ids[id] = true;
  s.sheet.appendRow([id, Utilities.formatDate(new Date(), 'Asia/Kolkata', 'dd-MM-yyyy HH:mm'), what]);
}

/** v2.4: replaces registerThread_ -- every message of the thread, each once, payments only. */
function registerPayments_(thread) {
  var sheet = registerSheet_();
  var seen = paySeen_();
  var written = 0;
  thread.getMessages().forEach(function (m) {
    var id = m.getId();
    if (seen.ids[id]) return;
    var from = m.getFrom().toLowerCase();
    var subject = m.getSubject() || '';
    if (from.indexOf('drmanojkragarwal') !== -1 || from.indexOf('drmka.ortho') !== -1) { paySeenAdd_(id, 'own mail'); return; }
    if (from.indexOf('docterz') !== -1 && !/invoice|receipt/i.test(subject)) { paySeenAdd_(id, 'Docterz notification (not a payment)'); return; }
    var kind = payKind_(subject);
    if (!kind) { paySeenAdd_(id, 'not a payment'); return; }
    var a = payAmount_(m.getPlainBody().slice(0, 6000));
    var desc = subject + (a.cur === 'USD' && a.amt ? ' — USD ' + a.amt : '');
    sheet.appendRow([
      Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'dd-MM-yyyy'),
      vendorOf_(m.getFrom()),
      desc,
      a.cur === 'INR' ? a.amt : '',
      m.getAttachments().length ? 'Yes' : 'No',
      'https://mail.google.com/mail/u/0/#all/' + id
    ]);
    paySeenAdd_(id, 'written (' + kind + ')');
    written++;
  });
  return written;
}

/** v2.4: the last 3 days are read again, so a payment arriving in an old (already labelled) thread is caught. */
function registerRecentPayments_() {
  var n = 0;
  GmailApp.search(RULE_PAYMENTS.query + ' newer_than:3d', 0, 50).forEach(function (t) { n += registerPayments_(t); });
  return n;
}

/** ONE-SHOT (run once by hand; safe to run again -- a marked row is skipped). Marks, never deletes. */
function markRegisterV24() {
  var sheet = registerSheet_();
  var n = sheet.getLastRow();
  if (n < 2) return 'empty';
  var vals = sheet.getRange(2, 1, n - 1, 6).getValues();
  var firstOf = {}, out = { duplicate: 0, notPayment: 0, docterz: 0, amountRead: 0, usd: 0, checkAmount: 0, ok: 0, alreadyMarked: 0 };
  vals.forEach(function (r, i) {
    var row = i + 2;
    var date = String(r[0]), vendor = String(r[1]), desc = String(r[2]), amt = String(r[3]), link = String(r[5]);
    var tid = (link.match(/#all\/([0-9a-f]+)/) || [])[1];
    if (tid) paySeenAdd_(tid, 'row ' + row + ' (before v2.4)');
    if (/^\[(DUPLICATE|NOT A PAYMENT|CHECK AMOUNT)/.test(desc) || / — USD [\d.]+$/.test(desc)) { out.alreadyMarked++; return; }
    var key = [date, vendor, desc, amt].join('|');
    if (firstOf[key]) { sheet.getRange(row, 3).setValue('[DUPLICATE of row ' + firstOf[key] + '] ' + desc); out.duplicate++; return; }
    firstOf[key] = row;
    if (/docterz/i.test(vendor) && !/invoice|receipt/i.test(desc)) {
      sheet.getRange(row, 3).setValue('[NOT A PAYMENT] Docterz notification — patient details removed'); out.docterz++; return;
    }
    if (!payKind_(desc)) { sheet.getRange(row, 3).setValue('[NOT A PAYMENT] ' + desc); out.notPayment++; return; }
    if (!amt && tid) {
      try {
        var th = GmailApp.getThreadById(tid);
        var a = th ? payAmount_(th.getMessages()[0].getPlainBody().slice(0, 6000)) : { cur: '', amt: '' };
        if (a.cur === 'INR' && a.amt) { sheet.getRange(row, 4).setValue(a.amt); out.amountRead++; return; }
        if (a.cur === 'USD' && a.amt) { sheet.getRange(row, 3).setValue(desc + ' — USD ' + a.amt); out.usd++; return; }
      } catch (e) { /* the mail is gone: marked below */ }
    }
    if (!amt) { sheet.getRange(row, 3).setValue('[CHECK AMOUNT] ' + desc); out.checkAmount++; return; }
    out.ok++;
  });
  var msg = 'v2.4 marking: ' + JSON.stringify(out);
  Logger.log(msg);
  return msg;
}
