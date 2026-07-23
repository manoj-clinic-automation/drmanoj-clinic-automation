/**
 * Auto-save credit card statement PDFs from Gmail to Google Drive,
 * organized into one folder per card.
 * Tailored for drmanojkragarwal@gmail.com — audited 23-Jul-2026.
 *
 * Drive structure created:
 *   Credit Card Statements/
 *     HDFC Business Regalia/   2025-03-16_<original>.pdf ...
 *     ICICI Amazon Pay/        2025-03-13_<original>.pdf ...
 *     ICICI Card 5007/         2026-06-03_<original>.pdf ...
 *     Other Cards/             (safety net for any future new card)
 *
 * DOMAIN-PROOF: matches sender usernames only (credit_cards,
 * emailstatements), so the 2026 hdfcbank.net->hdfcbank.bank.in and
 * icicibank.com->icici.bank.in migrations — and any future ones —
 * cannot break it. No Gmail filters needed.
 *
 * SETUP (one time, ~3 minutes):
 * 1. script.google.com -> New project -> paste this file -> Save.
 * 2. Run saveStatements from the toolbar -> authorize with
 *    drmanojkragarwal@gmail.com. Backfills from Mar 2025.
 *    Re-run until the log says "Saved 0 new".
 * 3. Triggers (clock icon) -> Add Trigger:
 *    saveStatements | Time-driven | Day timer | 6am-7am -> Save.
 *    Future statements then file themselves automatically.
 *
 * NOTE: if you already ran the earlier month-folder version, first
 * delete the old "Credit Card Statements" folder in Drive AND the
 * "CC-Saved" label in Gmail (Settings -> Labels -> remove), then run
 * this fresh so everything lands once, in the new per-card layout.
 */

// ===== CONFIG =====
var SENDERS      = '(credit_cards OR emailstatements OR emailstatements.cc)';
var SUBJECT      = '"credit card statement"';   // excludes MerchantStatements
var START_DATE   = '2025/03/01';
var DRIVE_FOLDER = 'Credit Card Statements';
var SORT_LABEL   = 'banks/credit card';         // kept current automatically
var DONE_LABEL   = 'CC-Saved';                  // script bookkeeping only
// ==================

function saveStatements() {
  var doneLabel = GmailApp.getUserLabelByName(DONE_LABEL) ||
                  GmailApp.createLabel(DONE_LABEL);
  var sortLabel = GmailApp.getUserLabelByName(SORT_LABEL);
  var rootFolder = getOrCreateFolder_(DriveApp.getRootFolder(), DRIVE_FOLDER);

  var query = 'from:' + SENDERS +
              ' subject:' + SUBJECT +
              ' after:' + START_DATE +
              ' -label:' + DONE_LABEL.toLowerCase() +
              ' has:attachment';

  var threads = GmailApp.search(query, 0, 100);
  var savedCount = 0;

  threads.forEach(function (thread) {
    thread.getMessages().forEach(function (msg) {
      var cardFolderName = detectCard_(msg.getSubject(), msg.getFrom());
      msg.getAttachments().forEach(function (att) {
        var name = att.getName();
        var isPdf = att.getContentType() === 'application/pdf' ||
                    name.toLowerCase().slice(-4) === '.pdf';
        if (!isPdf) return;

        var cardFolder = getOrCreateFolder_(rootFolder, cardFolderName);
        var stamp = Utilities.formatDate(msg.getDate(),
                      Session.getScriptTimeZone(), 'yyyy-MM-dd');
        var fileName = stamp + '_' + name;

        if (!cardFolder.getFilesByName(fileName).hasNext()) {
          cardFolder.createFile(att.copyBlob()).setName(fileName);
          savedCount++;
        }
      });
    });
    thread.addLabel(doneLabel);
    if (sortLabel) thread.addLabel(sortLabel);
  });

  Logger.log('Saved ' + savedCount + ' new statement PDF(s) from ' +
             threads.length + ' thread(s).');
}

/** Map a statement email to its card folder (verified against mailbox). */
function detectCard_(subject, from) {
  var s = subject.toLowerCase();
  if (s.indexOf('regalia') !== -1 || /hdfc/i.test(from)) {
    return 'HDFC Business Regalia';
  }
  if (s.indexOf('amazon pay') !== -1) {
    return 'ICICI Amazon Pay';
  }
  if (/icici/i.test(from) || s.indexOf('icici') !== -1) {
    return 'ICICI Card 5007';   // the non-Amazon ICICI card
  }
  return 'Other Cards';          // future/unrecognized card safety net
}

function getOrCreateFolder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}