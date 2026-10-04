/** ==========================================================================
 *  Bank_Statement_Relay.gs · S293 v2 (04-Oct-2026) · PERSONAL account (drmanojkragarwal@)
 *  Lives in the "Janitor" project. Daily 07:00 IST.
 *
 *  THE ROAD (owner's ruling, 04-Oct-2026): a bank statement never enters the
 *  clinic mailbox (staff can read it) and never goes to the accountants one by
 *  one. Each statement mail's attachments are saved STRAIGHT from this account
 *  into the clinic Drive folder the statement shelf reads:
 *      Clinic Data Archive / Bank Statements / <YYYY> / <YYYY-MM-DD>_<original name>
 *  (the folder is shared to this account as editor). The shelf fetches it at
 *  05:40 and 07:30 and identifies the file by its own content. The accountants
 *  receive statements only inside the month-end pack (/finance/packs). The
 *  clinic-side Bank_Statement_Filer is retired the same day.
 *
 *  Senders CONFIRMED by the 22-Aug survey + owner (unchanged from FINAL+1):
 *    corp.stmnts@icici.bank.in   estatement@icici.bank.in   account.statement@
 *    estatement@yes.bank.in      shadab.khan2@icici.bank.in (ICICI RM)
 *    any sender at yes.bank.in (the YES BANK branch; "mostly Vikrant, sometimes
 *    another person" -- owner, 26-Sep)
 *  EXCLUDED: credit_cards@ (CC Saver). Self-sent "Fwd:" copies skipped.
 *
 *  Dedupe twice: the thread label STMT-Relayed, and the file name in the year
 *  folder (a mail re-read after a failure never saves a second copy).
 *  ========================================================================== */

var BANK_STATEMENTS_FOLDER_ID = '1wGzaXnCoKcILw1VSv3UGYfQlVTl78UgT';   // clinic Drive: Clinic Data Archive / Bank Statements
var SENDER_QUERY = '(from:(corp.stmnts OR estatement OR shadab.khan2 OR account.statement) '
                 + 'OR from:yes.bank.in)';
var DONE_LABEL   = 'STMT-Relayed';

function setupBankRelay() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'relayBankStatements') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('relayBankStatements').timeBased().atHour(7).everyDays(1).create();
  Logger.log('daily trigger installed; first run: ' + relayBankStatements());
}

function relayBankStatements() {
  var done = GmailApp.getUserLabelByName(DONE_LABEL) || GmailApp.createLabel(DONE_LABEL);
  var root = DriveApp.getFolderById(BANK_STATEMENTS_FOLDER_ID);
  var q = SENDER_QUERY + ' has:attachment newer_than:40d -label:'
        + DONE_LABEL.toLowerCase();
  var saved = 0, skipped = 0, log = [];
  GmailApp.search(q, 0, 30).forEach(function (th) {
    th.getMessages().forEach(function (m) {
      if (m.getFrom().toLowerCase().indexOf('drmanojkragarwal') !== -1) return;
      var atts = m.getAttachments({includeInlineImages: false});
      if (!atts.length) return;
      var ymd   = Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'yyyy-MM-dd');
      var yearF = _folder_(root, Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'yyyy'));
      atts.forEach(function (a) {
        var name = ymd + '_' + a.getName();
        if (yearF.getFilesByName(name).hasNext()) { skipped++; return; }
        yearF.createFile(a.copyBlob().setName(name));
        saved++;
        log.push(name);
      });
    });
    th.addLabel(done);
  });
  var msg = 'saved ' + saved + ' file(s) to Drive, ' + skipped + ' already there'
          + (log.length ? '\n' + log.join('\n') : '');
  Logger.log(msg);
  return msg;
}

function _folder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
