/** ==========================================================================
 *  Bank_Statement_Filer.gs · S195 v3 · CLINIC account (drmka.ortho@)
 *  Lives in the "UPI Reconciliation" GAS project. Daily 07-08.
 *
 *  THE FLOW (owner spec, 22/23-Aug-2026):
 *    [STMT] mails forwarded by the personal account's Bank_Statement_Relay:
 *      1. ARCHIVE every attachment:
 *           Drive / Clinic Data Archive / Bank Statements / <YYYY> /
 *           <YYYY-MM-DD>_<original name>
 *      2. EMAIL every statement to BOTH accountants (one mail per statement,
 *         attachments included, [STMT] stripped).
 *      3. SANJEEVNI files ALSO to Amir: copy into Clinic Data Archive /
 *         ToMedical -> manojz -> medical D:\SendToClinic\FROM_CLINIC (~10 min).
 *    Dedupe by label -- a mail is never filed or mailed twice.
 *
 *  ACCOUNTANTS (owner, 22-Aug-2026): Hemant Mourya + Shyam Agarwal.
 *  The refuse-if-empty gate stays in case the list is ever cleared:
 *  archiving without forwarding would look like success and deliver nothing.
 *  ========================================================================== */

var STMT_MARKER      = '[STMT]';
var ARCHIVE_ROOT     = 'Clinic Data Archive';
var ARCHIVE_SUB      = 'Bank Statements';
var TOMEDICAL_SUB    = 'ToMedical';
var STMT_DONE        = 'STMT-Filed';
var ACCOUNTANT_EMAILS = ['hemantmourya47@gmail.com',    // Hemant Mourya
                         'shyamagarwalbly@gmail.com'];  // Shyam Agarwal

// Sanjeevni accounts (owner, 23-Aug-2026): YES a/c ...1923, ICICI ...9819.
// Matching is PER ATTACHMENT: the ICICI RM's monthly mail carries all six
// accounts in one message, and Amir gets only his. The subject is a fallback
// for single-statement mails whose filename lacks the number (estatement@).
// KNOWN GAP, logged loudly below: official YES e-statements show a CUSTOMER
// ID (...63/...38), not the account number -- until one is mapped to 1923,
// a YES statement that matches nothing is reported in the log, not dropped.
var SANJEEVNI_MATCH  = ['sanjeevni', '1923', '9819'];

function setupStmtFiler() {
  if (!ACCOUNTANT_EMAILS.length) {
    Logger.log('REFUSED: ACCOUNTANT_EMAILS is empty.');
    return;
  }
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fileBankStatements') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('fileBankStatements').timeBased().atHour(7).everyDays(1).create();
  Logger.log('daily trigger installed; first run: ' + fileBankStatements());
}

function fileBankStatements() {
  if (!ACCOUNTANT_EMAILS.length) return 'REFUSED: accountant emails not set';
  var done  = GmailApp.getUserLabelByName(STMT_DONE) || GmailApp.createLabel(STMT_DONE);
  var root  = _folder_(DriveApp.getRootFolder(), ARCHIVE_ROOT);
  var toMed = _folder_(root, TOMEDICAL_SUB);
  var log = [], n = 0;

  GmailApp.search('subject:"' + STMT_MARKER + '" has:attachment newer_than:60d '
                  + '-label:' + STMT_DONE.toLowerCase(), 0, 20)
    .forEach(function (th) {
      th.getMessages().forEach(function (m) {
        var atts = m.getAttachments({includeInlineImages: false});
        if (!atts.length) return;
        var subj = m.getSubject().replace(STMT_MARKER, '').trim();
        var ymd  = Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'yyyy-MM-dd');
        var yearF = _folder_(_folder_(root, ARCHIVE_SUB),
                             Utilities.formatDate(m.getDate(), 'Asia/Kolkata', 'yyyy'));

        var subjHit = SANJEEVNI_MATCH.some(function (p) {
          return subj.toLowerCase().indexOf(p) !== -1;
        });
        var sentToAmir = 0;
        atts.forEach(function (a) {
          var name = ymd + '_' + a.getName();
          var fileHit = SANJEEVNI_MATCH.some(function (p) {
            return a.getName().toLowerCase().indexOf(p) !== -1;
          });
          yearF.createFile(a.copyBlob().setName(name));            // 1. archive
          if (fileHit || subjHit) {                                // 3. Amir
            toMed.createFile(a.copyBlob().setName(name));
            sentToAmir++;
          }
          n++;
        });
        // the YES mapping gap, said out loud instead of silently dropped:
        var hay = (subj + ' ' + atts.map(function (a) { return a.getName(); })
                   .join(' ')).toLowerCase();
        if (!sentToAmir && (hay.indexOf('yes bank') !== -1
                            || hay.indexOf('_yfb_') !== -1)) {
          log.push('NOTE: a YES BANK statement matched no Sanjeevni pattern — '
                   + 'if this is a/c ...1923, tell Cowork which customer id '
                   + '(...63 or ...38) it is: ' + subj);
        }

        GmailApp.sendEmail(ACCOUNTANT_EMAILS.join(','), subj,     // 2. accountants
          'Bank statement attached (' + ymd + ').\n'
          + 'Sent automatically from the clinic system — Dr. Manoj Agarwal.',
          { attachments: atts.map(function (a) { return a.copyBlob(); }),
            name: 'Dr Manoj Agarwal Clinic' });
        log.push(ymd + ' | ' + subj + ' | '
                 + (sentToAmir ? 'SANJEEVNI (' + sentToAmir + ' file(s)) -> '
                                 + 'archive + accountants + Amir'
                               : 'archive + accountants'));
      });
      th.addLabel(done);
    });
  var msg = 'filed ' + n + ' attachment(s)\n' + (log.join('\n') || '(nothing new)');
  Logger.log(msg);
  return msg;
}

function _folder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
