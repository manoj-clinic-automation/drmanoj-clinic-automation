/** ==========================================================================
 *  Bank_Statement_Relay.gs · S195 · PERSONAL account (drmanojkragarwal@)
 *  Paste as a NEW file in the personal GAS project (next to CC Statement
 *  Saver). Purpose: the monthly ICICI + YES BANK account statements land in
 *  this inbox; the clinic side (Amir, the accountant flow) needs them.
 *  This relay forwards each statement mail ONCE to the clinic account.
 *
 *  BUILT SURVEY-FIRST, deliberately. The exact sender addresses were not
 *  guessed (guessed shapes caused five rollbacks in S195):
 *    1. Run  surveyBankStatements()  once. It saves NOTHING and forwards
 *       NOTHING — it prints every candidate statement mail of the last 120
 *       days: sender, subject, attachment names. ~30 seconds.
 *    2. Paste the log to Cowork (or read it yourself) and put the real
 *       sender usernames into CONFIRMED_SENDERS below.
 *    3. Run  setupBankRelay()  once — installs the daily 07-08 trigger.
 *  Until CONFIRMED_SENDERS is filled, the relay REFUSES to run, loudly.
 *  ========================================================================== */

var RELAY_TO          = 'drmka.ortho@gmail.com';
var RELAY_MARKER      = '[STMT]';                  // clinic filer keys on this
var CONFIRMED_SENDERS = '';   // e.g. '(estatement OR estatements)' — from the survey
// 'corp.stmnts' comes from the Inbox Janitor's bank-alerts rule -- almost
// certainly the YES BANK account-statement sender. Still survey-first: it is
// a CANDIDATE the survey must confirm, not a confirmed sender.
var SURVEY_QUERY      = '(from:corp.stmnts OR from:estatement OR from:icici.bank.in '
                      + 'OR from:icicibank.com OR from:yesbank.in) '
                      + 'subject:statement has:attachment newer_than:120d';
var DONE_LABEL        = 'STMT-Relayed';

function surveyBankStatements() {
  var out = ['SURVEY — nothing forwarded, nothing changed. Candidates:'];
  GmailApp.search(SURVEY_QUERY, 0, 60).forEach(function (th) {
    th.getMessages().forEach(function (m) {
      var atts = m.getAttachments({includeInlineImages: false})
                  .map(function (a) { return a.getName(); }).join(', ');
      if (atts) out.push(m.getDate() + ' | ' + m.getFrom() + ' | ' +
                         m.getSubject() + ' | ' + atts);
    });
  });
  if (out.length === 1) out.push('(none found — widen SURVEY_QUERY and rerun)');
  Logger.log(out.join('\n'));
  return out.join('\n');
}

function setupBankRelay() {
  if (!CONFIRMED_SENDERS) {
    Logger.log('REFUSED: CONFIRMED_SENDERS is empty. Run surveyBankStatements() '
             + 'first and fill it from what the survey actually saw.');
    return;
  }
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'relayBankStatements') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('relayBankStatements').timeBased().atHour(7).everyDays(1).create();
  Logger.log('daily trigger installed; first run: ' + relayBankStatements());
}

function relayBankStatements() {
  if (!CONFIRMED_SENDERS) return 'REFUSED: senders not confirmed';
  var done = GmailApp.getUserLabelByName(DONE_LABEL) || GmailApp.createLabel(DONE_LABEL);
  var q = 'from:' + CONFIRMED_SENDERS + ' subject:statement has:attachment '
        + 'newer_than:40d -label:' + DONE_LABEL.toLowerCase();
  var n = 0;
  GmailApp.search(q, 0, 20).forEach(function (th) {
    th.getMessages().forEach(function (m) {
      if (!m.getAttachments({includeInlineImages: false}).length) return;
      m.forward(RELAY_TO, {subject: RELAY_MARKER + ' ' + m.getSubject()});
      n++;
    });
    th.addLabel(done);        // per-thread: a statement mail is single-message
  });
  Logger.log('relayed ' + n + ' statement mail(s)');
  return 'relayed ' + n;
}
