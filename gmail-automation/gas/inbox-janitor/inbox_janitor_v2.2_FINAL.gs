/**
 * INBOX JANITOR v2.2 FINAL (consolidated 24-Jul-2026) (DEPLOYED STATE: 17-entry verified RENEWALS array) — drmanojkragarwal@gmail.com  (23-Jul-2026)
 *
 * FUNCTIONS & TRIGGERS:
 *   runJanitor            - daily 7-8am  : label/archive/save payment PDFs
 *                                          + append rows to Payment Register
 *   monthlyPaymentDigest  - monthly 1st  : digest email + upcoming renewals
 *   syncRenewalReminders  - monthly 2nd  : calendar events for renewals
 *   cleanupLabels         - RUN ONCE MANUALLY: deletes the approved 50+
 *                                          stale labels (emails untouched)
 *                                          [ALREADY EXECUTED 23-Jul-2026]
 *
 * ACCOUNTANT WORKFLOW: a Google Sheet "Payment Register" is auto-created
 * in My Drive. Every captured payment email becomes a row:
 * Date | Vendor | Description | Amount(Rs) | Attachment saved | Gmail link.
 * Share that sheet + the "Payment Records" Drive folder with your
 * accountant (read-only) and manual forwarding ends.
 */

// =============== CONFIG ===============
var DRIVE_ROOT   = 'Payment Records';
var REGISTER_NAME= 'Payment Register';
var DIGEST_TO    = 'drmanojkragarwal@gmail.com';
var JANITOR_DONE = 'Janitor-Done';

// Renewal registry — verified against invoices/emails 23-Jul-2026.
// dateISO = next renewal/action date 'yyyy-MM-dd'. cycleMonths 60 = 5-yearly.
var RENEWALS = [
  { vendor: 'ACTION: Transfer drmanojagarwal.in JustDial->Hostinger',
    dateISO: '2026-08-12', cycleMonths: 12,
    note: 'Lock ends 11-Aug; EPP code from JustDial; adds ~1yr validity' },
  { vendor: 'GoDaddy dr-manoj.in', dateISO: '2026-08-29', cycleMonths: 12,
    note: 'Short-link infra depends on this domain' },
  { vendor: 'Marg ERP licence 141167', dateISO: '2026-12-03', cycleMonths: 12,
    note: 'Sanjeevni Medicos pharmacy ERP; feeds revenue pipeline' },
  { vendor: 'KIA Carnival insurance', dateISO: '2027-02-28', cycleMonths: 12,
    note: 'CoverYou/ICICI Lombard ...540601; Rs 29,160 last year' },
  { vendor: 'VW Vento insurance', dateISO: '2027-03-03', cycleMonths: 12,
    note: 'ICICI Lombard ...541720' },
  { vendor: 'Biomedical waste authorization x2 (Clinic + NK Pathology)',
    dateISO: '2027-04-01', cycleMonths: 12,
    note: 'UPPCB; both valid 1-Apr to 31-Mar; renew before 1st April' },
  { vendor: 'Fire extinguisher cylinder refill', dateISO: '2027-04-01',
    cycleMonths: 12, note: 'Annual refill due in April' },
  { vendor: 'Professional Indemnity - Dr. Manoj', dateISO: '2027-04-27',
    cycleMonths: 12,
    note: 'New India 3222...0162 via HICL; Rs 3,805 paid 27-Apr-2026' },
  { vendor: 'Professional Indemnity - Bhawna', dateISO: '2027-04-27',
    cycleMonths: 12, note: 'National Insurance 461300492610000004' },
  { vendor: 'drmanojagarwal.in domain', dateISO: '2027-06-01', cycleMonths: 12,
    note: 'Update after Hostinger transfer extends expiry' },
  { vendor: 'Health insurance - Gauri + Manoj (NIC Mediclaim)',
    dateISO: '2027-07-15', cycleMonths: 12,
    note: 'Policies ...091/...092; TPA GenIns' },
  { vendor: 'MyOperator (IVR+WABA)', dateISO: '2027-09-03', cycleMonths: 15,
    note: 'Rs 2,12,400 incl GST; negotiate before renewal' },
  { vendor: 'Docterz EMR 5-year plan', dateISO: '2027-09-25', cycleMonths: 60,
    note: 'Rs 29,500; strategic: renew vs migrate; Bharat 9833620035' },
  { vendor: 'CHECK: Webuzo licence auto-renew is OFF', dateISO: '2028-05-10',
    cycleMonths: 24, note: 'Parked upsell Rs 4,296; must not renew 10-Jun-2028' },
  { vendor: 'Hostinger KVM2 VPS (2-year)', dateISO: '2028-06-10', cycleMonths: 24,
    note: 'Rs 28,776/2yr; confirm Webuzo not re-added at renewal' },
  { vendor: 'drmanojagarwal.com domain', dateISO: '2029-06-10', cycleMonths: 12,
    note: 'Primary website domain; Rs 4,497' },
  { vendor: 'Clinic registration CMO/UPMC (5-yearly)', dateISO: '2030-03-31',
    cycleMonths: 60, note: 'Valid 01-Apr-2025 to 31-Mar-2030; start Jan-2030' }
  ,
  // ---- Personal identity documents (merged 23-Jul-2026) ----
  { vendor: 'Arms licence renewal - Manoj (LN33013A7C39319/1028/2007)',
    dateISO: '2026-09-27', cycleMonths: 60,
    note: 'Expiry 26-12-2026 (user-confirmed). 90-day lead. UIN 330130012051232015.' },
  { vendor: 'Manoj DL renewal (UP25 20040006175)',
    dateISO: '2027-11-26', cycleMonths: 60,
    note: 'DL valid to 26-Dec-2027 (user-confirmed). 30-day lead. Renew via Parivahan.' },
  { vendor: 'Bhawna passport renewal (T7363710)',
    dateISO: '2028-08-13', cycleMonths: 120,
    note: 'Expires 13-Aug-2029. 12-month lead for reissue processing.' },
  { vendor: 'Manoj passport renewal (T2864619)',
    dateISO: '2028-08-15', cycleMonths: 120,
    note: 'Expires 15-Aug-2029. 12-month lead.' },
  { vendor: 'Gauri passport renewal (U2373491)',
    dateISO: '2029-01-02', cycleMonths: 120,
    note: 'Expires 02-Jan-2030 (MRZ-verified from PDF). 12-month lead.' },
  { vendor: 'Raghav passport renewal (Z7420519)',
    dateISO: '2032-08-22', cycleMonths: 120,
    note: 'Expires 22-Aug-2033. 12-month lead.' },
  { vendor: 'Raghav DL renewal (UP25 20130009667)',
    dateISO: '2033-05-06', cycleMonths: 240,
    note: 'DL valid to 05-Jun-2033. 30-day lead. Via Parivahan.' },
  { vendor: 'VW Vento registration (RC) renewal', dateISO: '2028-05-01',
    cycleMonths: 60,
    note: 'RC renewal due Jun-2028. 30-day lead; re-registration may need fitness inspection - start early via Parivahan.' },
  { vendor: 'Bhawna DL renewal (UP25 20040001711)',
    dateISO: 'TODO-enter-expiry-minus-30d', cycleMonths: 60,
    note: 'Renewed 2026 (confirmed, date pending). When known: set dateISO = new expiry minus 30 days, update Personal Docs sheet row 2, run syncRenewalReminders().' }
  // Gauri DL (valid to 16-Jul-2043) optional - add nearer the time.
  // Bhawna DL EXPIRED 30-Aug-2024: immediate Parivahan task, not a reminder.
];

// Recurring ANNUAL civic renewals -> yearly calendar series (synced below)
var ANNUAL_RENEWALS = [
  { title: 'ANNUAL: Nagar Nigam renewal - Clinic',        firstISO: '2027-01-01',
    note: 'Renew every January. Nagar Nigam Bareilly.' },
  { title: 'ANNUAL: Nagar Nigam renewal - NK Pathology',  firstISO: '2027-01-01',
    note: 'Renew every January. Nagar Nigam Bareilly.' },
  { title: 'ANNUAL: Nagar Nigam municipal taxes',         firstISO: '2027-05-01',
    note: 'Pay during May each year.' },
  { title: 'ANNUAL: Bareilly Club membership',            firstISO: '2027-06-01',
    note: 'Renew each June.' },
  { title: 'ANNUAL: TVS Star City UP-25-Q-0997 insurance renewal',
    firstISO: '2026-12-05',
    note: 'Renewed offline via agent every year; fixed anniversary. Owner Bhawna. Last known: National Insurance 461300312310001832.' },
  { title: 'ANNUAL: Honda Aviator UP-25-AE-0028 insurance renewal',
    firstISO: '2027-01-19',
    note: 'Renewed offline via agent every year; fixed anniversary. Owner Manoj. Last known: National Insurance 461300312310002129.' }

];

var RULE_PAYMENTS = {
  name: 'payments',
  query: 'from:(razorpay.com OR mail.anthropic.com OR alert.myoperator.info OR ' +
         'googleplay-noreply OR email.apple.com OR samsungcheckout.com OR ' +
         'update@airtel.com OR ebill@airtel.com OR cashfreemail.com OR ' +
         'godaddy.com OR hostinger.com OR sarvam OR docterz OR ' +
         'gstinvoice@icici.bank.in OR sales.accounts@agilus.in OR ' +
         'newindia.co.in OR nic.co.in OR geninsindia.com) ' +
         '-subject:"credit card statement" -subject:"verification" ' +
         '-subject:"sign in" -subject:"security alert"',
  label: 'PAYMENT RECORDS',
  saveAttachments: true, register: true, archiveAfterDays: 30
};
var RULE_BANK_ALERTS = {
  name: 'bank alerts',
  query: 'from:(cards@icici.bank.in OR credit_cards OR custcomm.icici OR ' +
         'alerts.sbi.bank.in OR corp.stmnts) -subject:"credit card statement"',
  label: 'banks', saveAttachments: false, register: false, archiveAfterDays: 7
};
var RULE_NEWSLETTERS = {
  name: 'newsletters',
  query: 'from:(medscape.com OR mail.clickup.com OR shopifyemail.com OR ' +
         'justdial.com OR policybazaar.com OR cred.club OR ' +
         'mapmygenome.in OR maildesq.com OR onboarding.deepstash.com OR ' +
         'mail.instagram.com)',
  label: null, saveAttachments: false, register: false, archiveAfterDays: 3
};
var RULE_REPORTS = {
  name: 'auto reports',
  // ONtime -> migrated to VPS attendance system; track360 -> processed by GAS
  // in clinic account (drmka.ortho); merchant MPR + NSDL/BSE/NSE -> records only.
  query: '(from:(MERCHANTSOLUTIONS@icicibank.com OR mail.track360.co.in OR ' +
         'NSDL-CAS@nsdl.co.in OR info@bseindia.in OR nse-direct@nse.co.in) OR ' +
         'subject:"ONtime Employee Manager Report")',
  label: 'Reports', saveAttachments: false, register: false,
  markRead: true, archiveAfterDays: 2
};
var RULE_VENDOR_PROMOS = {
  name: 'vendor promos',
  query: 'from:(arrowmarketing360.com OR pepperfry.com OR omronbrandshop.com OR ' +
         'tatatelebusiness.com OR atreyainnovations.com OR hs-send.com OR ' +
         'satvicmovement.org OR artofliving.org OR em-s.dropbox.com OR ' +
         'iascon2026.com OR ioacon2024bengaluru.com OR citadelarch.com OR ' +
         'extensionerp.com OR custcom.yes.bank.in OR shiprocket OR ' +
         'business-noreply@google.com)',
  label: 'Vendor-Archive', saveAttachments: false, register: false,
  markRead: true, archiveAfterDays: 1
};
var RULES = [RULE_PAYMENTS, RULE_BANK_ALERTS, RULE_NEWSLETTERS,
             RULE_REPORTS, RULE_VENDOR_PROMOS];

var VENDOR_MAP = {
  'razorpay': 'Hostinger & Razorpay', 'anthropic': 'Anthropic Claude',
  'myoperator': 'MyOperator', 'googleplay': 'Google Play', 'apple': 'Apple',
  'samsungcheckout': 'Samsung', 'airtel': 'Airtel', 'cashfree': 'Cashfree',
  'godaddy': 'GoDaddy', 'hostinger': 'Hostinger & Razorpay',
  'sarvam': 'Sarvam AI', 'docterz': 'Docterz EMR',
  'gstinvoice': 'GST Invoices', 'agilus': 'Agilus (NK Pathology)',
  'newindia': 'Insurance', 'nic.co': 'Insurance', 'geninsindia': 'Insurance'
};
// ======================================

function runJanitor() {
  var done = GmailApp.getUserLabelByName(JANITOR_DONE) ||
             GmailApp.createLabel(JANITOR_DONE);
  var totals = [];

  RULES.forEach(function (rule) {
    var label = rule.label ?
        (GmailApp.getUserLabelByName(rule.label) ||
         GmailApp.createLabel(rule.label)) : null;
    var threads = GmailApp.search(
      rule.query + ' -label:' + JANITOR_DONE.toLowerCase() + ' newer_than:2y',
      0, 100);

    threads.forEach(function (thread) {
      if (label) thread.addLabel(label);
      if (rule.saveAttachments) saveThreadAttachments_(thread);
      if (rule.markRead) thread.markRead();
      if (rule.register) registerThread_(thread);
      thread.addLabel(done);
      var ageDays = (Date.now() - thread.getLastMessageDate().getTime()) / 864e5;
      if (rule.archiveAfterDays !== null && ageDays > rule.archiveAfterDays &&
          thread.isInInbox()) thread.moveToArchive();
    });
    totals.push(rule.name + ': ' + threads.length);
  });

  RULES.forEach(function (rule) {          // age-out pass
    if (rule.archiveAfterDays === null) return;
    GmailApp.search(rule.query + ' label:' + JANITOR_DONE.toLowerCase() +
      ' in:inbox older_than:' + rule.archiveAfterDays + 'd', 0, 100)
      .forEach(function (t) { t.moveToArchive(); });
  });
  Logger.log('Processed -> ' + totals.join(' | '));
  runSweeps_();   // v2.2 trash + special sweeps
}

// ---------- Payment Register (Google Sheet) ----------
function registerSheet_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('REGISTER_ID');
  var ss;
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (e) {} }
  if (!ss) {
    ss = SpreadsheetApp.create(REGISTER_NAME);
    ss.getActiveSheet().appendRow(
      ['Date', 'Vendor', 'Description', 'Amount (Rs)',
       'Attachment in Drive', 'Gmail Link']);
    props.setProperty('REGISTER_ID', ss.getId());
  }
  return ss.getActiveSheet();
}

function registerThread_(thread) {
  var sheet = registerSheet_();
  var m = thread.getMessages()[0];
  var body = m.getPlainBody().slice(0, 3000);
  var amt = (body.match(/(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)/i) || [])[1] || '';
  sheet.appendRow([
    Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(), 'dd-MM-yyyy'),
    vendorOf_(m.getFrom()),
    m.getSubject(),
    amt.replace(/,/g, ''),
    m.getAttachments().length ? 'Yes' : 'No',
    'https://mail.google.com/mail/u/0/#all/' + thread.getId()
  ]);
}

// ---------- Renewal reminders ----------
function syncRenewalReminders() {
  var cal = CalendarApp.getDefaultCalendar();
  RENEWALS.forEach(function (r) {
    if (r.dateISO.indexOf('TODO') === 0) return;
    var due = new Date(r.dateISO + 'T09:00:00');
    if (due < new Date()) return;
    var title = 'RENEWAL DUE: ' + r.vendor;
    var existing = cal.getEventsForDay(due).some(function (e) {
      return e.getTitle() === title;
    });
    if (!existing) {
      var ev = cal.createAllDayEvent(title, due, { description: r.note });
      ev.addEmailReminder(30 * 24 * 60); // 30 days before
      ev.addEmailReminder(7 * 24 * 60);  // 7 days before
    }
  });
  // yearly recurring civic series (dedup by title on first occurrence day)
  ANNUAL_RENEWALS.forEach(function (a) {
    var first = new Date(a.firstISO + 'T09:00:00');
    var exists = cal.getEventsForDay(first).some(function (e) {
      return e.getTitle() === a.title;
    });
    if (!exists) {
      var series = cal.createAllDayEventSeries(a.title, first,
        CalendarApp.newRecurrence().addYearlyRule(),
        { description: a.note });
      series.addEmailReminder(30 * 24 * 60);
      series.addEmailReminder(7 * 24 * 60);
    }
  });
  Logger.log('Renewal reminders synced (incl. annual series).');
}

// ---------- Monthly digest ----------
function monthlyPaymentDigest() {
  var now = new Date();
  var first = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  var last  = new Date(now.getFullYear(), now.getMonth(), 1);
  var fmt = function (d) { return Utilities.formatDate(d,
      Session.getScriptTimeZone(), 'yyyy/MM/dd'); };
  var threads = GmailApp.search(RULE_PAYMENTS.query +
      ' after:' + fmt(first) + ' before:' + fmt(last), 0, 100);

  var lines = threads.map(function (t) {
    var m = t.getMessages()[0];
    return Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(),
      'dd MMM') + '  |  ' + vendorOf_(m.getFrom()) + '  |  ' + m.getSubject();
  });

  var horizon = new Date(now.getTime() + 60 * 864e5);
  var upcoming = RENEWALS.filter(function (r) {
    if (r.dateISO.indexOf('TODO') === 0) return true;
    var d = new Date(r.dateISO);
    return d >= now && d <= horizon;
  }).map(function (r) {
    return r.dateISO + '  |  ' + r.vendor + '  |  ' + r.note;
  });

  MailApp.sendEmail(DIGEST_TO,
    'Payment Digest — ' + Utilities.formatDate(first,
      Session.getScriptTimeZone(), 'MMMM yyyy') +
      ' (' + threads.length + ' items)',
    'Payments captured last month:\n\n' + (lines.join('\n') || '(none)') +
    '\n\nRENEWALS in next 60 days / missing dates:\n' +
    (upcoming.join('\n') || '(none)') +
    '\n\nRegister sheet + PDFs: Drive > "' + REGISTER_NAME +
    '" and "' + DRIVE_ROOT + '".');
}

// ---------- One-shot: approved stale-label cleanup ----------
// [ALREADY EXECUTED 23-Jul-2026 — kept for reference; safe to re-run]
function cleanupLabels() {
  var names = [
    'orth societies conferences/IOACON 2011',
    'orth societies conferences/midterm symposium gkp 15 9 13',
    'RENOVATION 2017', 'HOME RENOVATION/Architect', 'HOME RENOVATION/indiamart',
    'HOME RENOVATION', 'house renovation', 'construction 2020', 'spine 2018',
    'IMA 19-20', 'IMA 2020', 'usa trip', 'north east trip', 'camp material',
    'pathology/upgrade 2016/knowlarity', 'pathology/upgrade 2016',
    'mutual funds/2015-16',
    'mutual funds/mutual funds 2017/dsp opportunities mka',
    'mutual funds/mutual funds 2017/bsl equity ba',
    'mutual funds/mutual funds 2017/franklin BA',
    'mutual funds/mutual funds 2017/dsp taxsaver huf',
    'mutual funds/mutual funds 2017/bsl equity mka',
    'mutual funds/mutual funds 2017/SBI BLUE CHIP MKA',
    'mutual funds/mutual funds 2017/icici mutual ba',
    'mutual funds/mutual funds 2017/franklin MKA',
    'mutual funds/mutual funds 2017/icici mutual MKA',
    'mutual funds/mutual funds 2017/bsl huf',
    'mutual funds/mutual funds 2017/mfu',
    'mutual funds/mutual funds 2017',
    'mutual funds/mutual funds organise', 'mutual funds/to be followed',
    'dsp opportunities ba', 'Reliance Mutual', 'Franklin',
    'tata sky', 'vodafone', 'Idea', 'bsnl', 'NYMGO', 'yodlee', 'dyndns',
    'blinklist', 'easy clinin', 'knowledge genie',
    'Boomerang-Outbox/Cancelled', 'Boomerang-Outbox', 'Boomerang-Returned',
    'Boomerang', 'teamviewer', 'medscape', 'quora', 'darpan', 'SAT',
    'sintex', 'upsrtc', 'irctc'
  ];
  var deleted = 0;
  names.forEach(function (n) {
    var l = GmailApp.getUserLabelByName(n);
    if (l) { GmailApp.deleteLabel(l); deleted++; }
  });
  Logger.log('Deleted ' + deleted + ' labels. Emails are untouched.');
}

// ---------- shared helpers ----------
function saveThreadAttachments_(thread) {
  var root = getOrCreateFolder_(DriveApp.getRootFolder(), DRIVE_ROOT);
  thread.getMessages().forEach(function (msg) {
    var atts = msg.getAttachments();
    if (!atts.length) return;
    var folder = getOrCreateFolder_(root, vendorOf_(msg.getFrom()));
    var stamp = Utilities.formatDate(msg.getDate(),
      Session.getScriptTimeZone(), 'yyyy-MM-dd');
    atts.forEach(function (att) {
      var fileName = stamp + '_' + att.getName();
      if (!folder.getFilesByName(fileName).hasNext()) {
        folder.createFile(att.copyBlob()).setName(fileName);
      }
    });
  });
}
function vendorOf_(from) {
  var f = from.toLowerCase();
  for (var k in VENDOR_MAP) if (f.indexOf(k) !== -1) return VENDOR_MAP[k];
  var m = f.match(/@([a-z0-9.-]+)/);
  return m ? m[1] : 'Other';
}
function getOrCreateFolder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

/* ================= v2.2 SWEEP MODULE ================= */

var SWEEP_NEWSLETTER_TRASH = [    // trashed 1d after arrival (Gmail purges 30d)
  'myclaw.ai', 'aisecret.us', 'mail.medscape.com', 'recommends@ted.com',
  'm.servicespace.org', 'beehiiv.com', 'mail@ifttt.com', 'rosebud.app',
  'today.getpocket.com', 'onboarding.deepstash.com', 'mail.instagram.com'
];

function runSweeps_() {
  // OTPs / verification codes -> trash after 1 day (never starred mail)
  GmailApp.search('in:inbox older_than:1d -is:starred ' +
    'subject:(OTP OR "one time password" OR "verification code" OR "login code")',
    0, 100).forEach(function (t) { t.markRead().moveToTrash(); });

  // MyOperator (non-payment) -> label + archive after 7d. NEVER trashed.
  var mLabel = GmailApp.getUserLabelByName('MyOperator') ||
               GmailApp.createLabel('MyOperator');
  GmailApp.search('in:inbox older_than:7d from:myoperator -from:alert.myoperator.info',
    0, 100).forEach(function (t) { t.addLabel(mLabel).markRead().moveToArchive(); });

  // Content newsletters -> trash after 1d
  // (JustDial deliberately NOT here - domain-transfer EPP mail must survive;
  //  it stays on the archive-only newsletter rule.)
  GmailApp.search('-in:trash -is:starred older_than:1d from:(' +
    SWEEP_NEWSLETTER_TRASH.join(' OR ') + ')', 0, 100)
    .forEach(function (t) { t.moveToTrash(); });

  // CC statements already filed to Drive -> mark read + archive after 30d
  GmailApp.search('in:inbox label:cc-saved older_than:30d', 0, 100)
    .forEach(function (t) { t.markRead().moveToArchive(); });
}

/** ONE-SHOT backlog cleaner - run manually, repeat until log shows all zeros. */
function sweepBacklogOnce() {
  var counts = {};
  function apply_(q, fn, key) {
    var ts = GmailApp.search(q, 0, 100); ts.forEach(fn); counts[key] = ts.length;
  }
  var rLabel = GmailApp.getUserLabelByName('Reports') || GmailApp.createLabel('Reports');
  var vLabel = GmailApp.getUserLabelByName('Vendor-Archive') || GmailApp.createLabel('Vendor-Archive');
  var mLabel = GmailApp.getUserLabelByName('MyOperator') || GmailApp.createLabel('MyOperator');
  apply_(RULE_REPORTS.query + ' in:inbox',
    function (t) { t.addLabel(rLabel).markRead().moveToArchive(); }, 'reports');
  apply_(RULE_VENDOR_PROMOS.query + ' in:inbox',
    function (t) { t.addLabel(vLabel).markRead().moveToArchive(); }, 'vendors');
  apply_('in:inbox from:myoperator -from:alert.myoperator.info',
    function (t) { t.addLabel(mLabel).markRead().moveToArchive(); }, 'myoperator');
  apply_('in:inbox -is:starred subject:(OTP OR "one time password" OR "verification code")',
    function (t) { t.markRead().moveToTrash(); }, 'otps');
  apply_('in:inbox older_than:7d from:no-reply@accounts.google.com subject:"security alert"',
    function (t) { t.markRead().moveToArchive(); }, 'security');
  apply_('in:inbox label:cc-saved older_than:30d',
    function (t) { t.markRead().moveToArchive(); }, 'cc-saved');
  apply_('in:inbox older_than:30d (from:yesbank subject:welcome OR from:donotreply@gst.gov.in)',
    function (t) { t.markRead().moveToArchive(); }, 'misc');
  Logger.log(JSON.stringify(counts));  // repeat run until all values are 0
}

/* ============ ONE-SHOT sheet fixers (run each once) ============ */

var MASTER_V2_ID    = '1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E';
var PERSONAL_DOCS_ID = '1NqVH0Eb8625P9_twFybayA-30Y0z30X-B-4BdBYW8L8';

/** IDEMPOTENT sheet updater - safe to run any number of times.
 *  Applies only missing changes; skips anything already present. */
function applySheetUpdatesOnce() {
  // --- A. Personal Documents sheet ---
  var pd = SpreadsheetApp.openById(PERSONAL_DOCS_ID).getSheets()[0];
  var d = pd.getDataRange().getValues();
  for (var i = 0; i < d.length; i++) {
    var num = String(d[i][2]);
    if (num.indexOf('20040006175') !== -1 && String(d[i][4]) !== '26-12-2027') {
      pd.getRange(i + 1, 5).setValue('26-12-2027');
      pd.getRange(i + 1, 6).setValue('26-11-2027');
      pd.getRange(i + 1, 7).setValue('User-confirmed 26-12-2027. 30-day lead. Renew via Parivahan.');
      Logger.log('Manoj DL row updated.');
    }
    if (num.indexOf('LN33013A7C39319') !== -1 && String(d[i][4]) !== '26-12-2026') {
      pd.getRange(i + 1, 5).setValue('26-12-2026');
      pd.getRange(i + 1, 6).setValue('27-09-2026');
      pd.getRange(i + 1, 7).setValue('User-confirmed expiry 26-12-2026. 90-day lead. UIN 330130012051232015.');
      Logger.log('Arms licence row updated.');
    }
    if (num.indexOf('20040001711') !== -1 && String(d[i][5]) === 'IMMEDIATE') {
      pd.getRange(i + 1, 6).setValue('TBD - renewed 2026');
      pd.getRange(i + 1, 7).setValue('RENEWED 2026 (confirmed). Expiry date pending - update this row + RENEWALS entry when known.');
      Logger.log('Bhawna DL row updated to renewed-pending.');
    }
  }

  // --- B. Renewals Master v2: append rows only if absent ---
  var mv = SpreadsheetApp.openById(MASTER_V2_ID).getSheets()[0];
  var items = mv.getDataRange().getValues().map(function (r) { return String(r[1]); }).join('|');
  var want = [
    ['COMPLIANCE', 'Nagar Nigam annual renewal - Clinic', 'Nagar Nigam Bareilly',
     'Dr. Manoj Agarwal', '01-Jan-2027', 'Annual', '', 'Renew every January', 'User provided'],
    ['COMPLIANCE', 'Nagar Nigam annual renewal - NK Pathology', 'Nagar Nigam Bareilly',
     'NK Pathology', '01-Jan-2027', 'Annual', '', 'Renew every January', 'User provided'],
    ['TAX', 'Nagar Nigam municipal taxes', 'Nagar Nigam Bareilly',
     'Dr. Manoj Agarwal', '01-May-2027', 'Annual', '', 'Pay during May each year', 'User provided'],
    ['MEMBERSHIP', 'Bareilly Club membership', 'Bareilly Club',
     'Dr. Manoj Agarwal', '01-Jun-2027', 'Annual', '', 'Renew each June', 'User provided'],
    ['VEHICLE', 'VW Vento registration (RC) renewal', 'RTO Bareilly / Parivahan',
     'Manoj Kumar Agarwal', '01-Jun-2028', '5 years', '',
     'Re-registration may need fitness inspection - start by May-2028', 'User provided'],
    ['VEHICLE', 'TVS Star City UP-25-Q-0997 insurance',
     'Offline agent / National Insurance (last doc 461300312310001832)', 'Bhawna Agarwal',
     '05-Dec-2026', 'Annual', '1191',
     'Renewed offline yearly, fixed anniversary; no email trail - calendar series reminds', 'User confirmed'],
    ['VEHICLE', 'Honda Aviator UP-25-AE-0028 insurance',
     'Offline agent / National Insurance (last doc 461300312310002129)', 'Manoj Kumar Agarwal',
     '19-Jan-2027', 'Annual', '1191',
     'Renewed offline yearly, fixed anniversary; no email trail - calendar series reminds', 'User confirmed']
  ];
  var added = 0;
  want.forEach(function (r) {
    if (items.indexOf(r[1]) === -1) { mv.appendRow(r); added++; }
  });
  Logger.log('Master v2: ' + added + ' new rows appended (existing rows skipped).');
}