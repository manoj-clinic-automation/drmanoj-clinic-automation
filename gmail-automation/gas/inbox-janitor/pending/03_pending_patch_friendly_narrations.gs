/**
 * PENDING PATCH — Accountant-friendly narrations for Payment Register
 * Status 23-Jul-2026: DELIVERED, NOT PASTED. Gated on Hemant's feedback.
 *
 * TO APPLY (in the Inbox Janitor GAS project):
 * 1. Replace the existing registerThread_ function with the one below.
 * 2. Add friendlyNarration_ and rebuildRegister below it.
 * 3. Save, then run rebuildRegister() ONCE — wipes the Payment Register
 *    sheet and re-enters ~2 years of entries with plain-language
 *    descriptions. Daily runs use the same narrations thereafter.
 * 4. Then update process_statements.py narration cleaner to match
 *    (needs 5-6 sample rows from tally_entries.csv for tuning).
 */

function registerThread_(thread) {
  var sheet = registerSheet_();
  var m = thread.getMessages()[0];
  var body = m.getPlainBody().slice(0, 3000);
  var amt = (body.match(/(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)/i) || [])[1] || '';
  sheet.appendRow([
    Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(), 'dd-MM-yyyy'),
    vendorOf_(m.getFrom()),
    friendlyNarration_(m.getFrom(), m.getSubject(), body),
    amt.replace(/,/g, ''),
    m.getAttachments().length ? 'Yes' : 'No',
    'https://mail.google.com/mail/u/0/#all/' + thread.getId()
  ]);
}

/** Plain-language narration the accountant can book directly. */
function friendlyNarration_(from, subject, body) {
  var f = from.toLowerCase(), s = subject;
  if (f.indexOf('razorpay') !== -1 || f.indexOf('cashfree') !== -1) {
    var mch = (s.match(/Payment successful for (.+)/i) || [])[1] || '';
    if (/hostinger/i.test(mch + body)) return 'Website/server hosting charges - Hostinger';
    if (/docterz/i.test(mch + body))   return 'Clinic software (EMR) payment - Docterz';
    return 'Online payment - ' + (mch || 'see email');
  }
  if (f.indexOf('anthropic') !== -1)       return 'AI software subscription - Claude (Anthropic)';
  if (f.indexOf('myoperator') !== -1)      return 'Clinic phone & WhatsApp service - MyOperator';
  if (f.indexOf('googleplay') !== -1)      return 'Mobile app subscription - Google Play';
  if (f.indexOf('apple') !== -1)           return 'Mobile app subscription - Apple';
  if (f.indexOf('samsungcheckout') !== -1) return 'TV app subscription - Samsung';
  if (f.indexOf('airtel') !== -1)          return 'Telephone / internet bill - Airtel';
  if (f.indexOf('gstinvoice') !== -1)      return 'Bank charges GST invoice - ICICI Bank';
  if (f.indexOf('agilus') !== -1)          return 'Lab outsourcing invoice - Agilus (NK Pathology)';
  if (f.indexOf('godaddy') !== -1)         return 'Domain name charges - GoDaddy';
  if (f.indexOf('hostinger') !== -1)       return 'Website/server hosting - Hostinger';
  if (f.indexOf('newindia') !== -1)        return 'Insurance premium - New India Assurance';
  if (f.indexOf('nic.co') !== -1)          return 'Insurance premium - National Insurance';
  if (f.indexOf('geninsindia') !== -1)     return 'Health insurance TPA - GenIns';
  return s;  // fallback: original subject
}

/** ONE-SHOT: wipe and rebuild the whole register with clean narrations. */
function rebuildRegister() {
  var sheet = registerSheet_();
  sheet.clearContents();
  sheet.appendRow(['Date', 'Vendor', 'Description', 'Amount (Rs)',
                   'Attachment in Drive', 'Gmail Link']);
  var threads = GmailApp.search(RULE_PAYMENTS.query + ' newer_than:2y', 0, 200);
  threads.forEach(registerThread_);
  Logger.log('Register rebuilt: ' + threads.length + ' entries.');
}
