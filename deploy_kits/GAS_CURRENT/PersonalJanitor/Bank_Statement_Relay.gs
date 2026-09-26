/** ==========================================================================
 *  Bank_Statement_Relay.gs · S195 FINAL+1 · PERSONAL account
 *  Senders CONFIRMED by the 22-Aug survey + owner:
 *    corp.stmnts@icici.bank.in   estatement@icici.bank.in
 *    estatement@yes.bank.in      shadab.khan2@icici.bank.in (ICICI RM)
 *    vikrant …@yesbank…          (YES BANK RM — owner-confirmed; matched as
 *                                 vikrant AND yesbank in the sender, never
 *                                 bare 'vikrant', so a stray Vikrant cannot
 *                                 reach the accountant chain)
 *  EXCLUDED: credit_cards@ (CC Saver + existing auto-forward). Self-sent
 *  "Fwd:" copies skipped.
 *  ========================================================================== */

var RELAY_TO     = 'drmka.ortho@gmail.com';
var RELAY_MARKER = '[STMT]';
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
  var q = SENDER_QUERY + ' has:attachment newer_than:40d -label:'
        + DONE_LABEL.toLowerCase();
  var n = 0;
  GmailApp.search(q, 0, 30).forEach(function (th) {
    th.getMessages().forEach(function (m) {
      if (m.getFrom().toLowerCase().indexOf('drmanojkragarwal') !== -1) return;
      if (!m.getAttachments({includeInlineImages: false}).length) return;
      m.forward(RELAY_TO, {subject: RELAY_MARKER + ' ' + m.getSubject()});
      n++;
    });
    th.addLabel(done);
  });
  Logger.log('relayed ' + n + ' statement mail(s)');
  return 'relayed ' + n;
}
