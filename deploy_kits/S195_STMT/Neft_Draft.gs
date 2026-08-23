/** ==========================================================================
 *  Neft_Draft.gs · S195 · CLINIC account (drmka.ortho@)
 *  Paste as a NEW file in the "UPI Reconciliation" GAS project.
 *  Function names are nd_-prefixed; nothing collides with the other files.
 *
 *  THE NEFT MONTHLY RHYTHM (as observed live, 22-Aug-2026):
 *    "NEFT ADVICE <MONTH> <YEAR>.xlsx" in SHAVEZ / SANJEEVNI MEDICOS FILES
 *    is created early in the cycle, refined by Shavez over days, finalised
 *    around the 20th of the FOLLOWING month, and delivered to YES Bank with
 *    the letter and one signed cheque.
 *
 *  WHAT THIS AUTOMATES (owner spec, 23-Aug-2026):
 *    1. nd_makeNextDraft — monthly, 1st: if this month's advice file does
 *       not exist yet, create it as a COPY of the latest one. The vendor
 *       rows (accounts, IFSC, names) carry over; amounts start as last
 *       month's and Shavez refines the few that changed. Cheque no + date
 *       stay manual, by design (D325: a person signs).
 *    2. nd_sendFinalsToAmir — monthly, 25th: copy the latest advice file +
 *       the letter into ToMedical as "<name> (FINAL)", which lands them in
 *       medical D:\SendToClinic\FROM_CLINIC for Amir's monthly records.
 *  NOTHING is ever sent to a bank by this script. It copies files.
 *
 *  SETUP: run nd_setup() once.
 *  ========================================================================== */

var ND_FOLDER = 'SANJEEVNI MEDICOS FILES';       // inside SHAVEZ
var ND_TOMED  = 'ToMedical';                     // inside Clinic Data Archive
var ND_LETTER = 'NEFT ADVICE LETTER.docx';
var ND_MONTHS = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY',
                 'AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];

function nd_setup() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    var f = t.getHandlerFunction();
    if (f === 'nd_makeNextDraft' || f === 'nd_sendFinalsToAmir')
      ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('nd_makeNextDraft').timeBased()
    .onMonthDay(1).atHour(6).create();
  ScriptApp.newTrigger('nd_sendFinalsToAmir').timeBased()
    .onMonthDay(25).atHour(6).create();
  Logger.log('triggers installed (1st: next draft · 25th: finals to Amir). '
           + 'Draft check now: ' + nd_makeNextDraft());
}

function nd_folder_() {
  var it = DriveApp.getFoldersByName(ND_FOLDER);
  if (!it.hasNext()) throw new Error('folder not found: ' + ND_FOLDER);
  return it.next();
}

function nd_latestAdvice_(folder) {
  var it = folder.getFiles(), best = null;
  while (it.hasNext()) {
    var f = it.next();
    if (f.getName().indexOf('NEFT ADVICE') === 0
        && f.getName().indexOf('.xlsx') !== -1
        && (!best || f.getLastUpdated() > best.getLastUpdated())) best = f;
  }
  return best;
}

function nd_makeNextDraft() {
  var folder = nd_folder_();
  var now = new Date();
  var name = 'NEFT ADVICE ' + ND_MONTHS[now.getMonth()] + ' '
           + now.getFullYear() + '.xlsx';
  if (folder.getFilesByName(name).hasNext())
    return 'exists already: ' + name;
  var src = nd_latestAdvice_(folder);
  if (!src) return 'NO SOURCE: no NEFT ADVICE xlsx found to copy from';
  src.makeCopy(name, folder);
  Logger.log('draft created: ' + name + ' (from ' + src.getName() + '). '
           + 'Vendor rows carried over; Shavez refines amounts; cheque no + '
           + 'date manual.');
  return 'draft created: ' + name;
}

function nd_sendFinalsToAmir() {
  var folder = nd_folder_();
  var toMedIt = DriveApp.getFoldersByName(ND_TOMED);
  if (!toMedIt.hasNext()) return 'ToMedical folder not found';
  var toMed = toMedIt.next();
  var out = [];
  var adv = nd_latestAdvice_(folder);
  if (adv) { adv.makeCopy(adv.getName().replace('.xlsx',' (FINAL).xlsx'), toMed);
             out.push(adv.getName()); }
  var let_ = folder.getFilesByName(ND_LETTER);
  if (let_.hasNext()) {
    var stamp = ND_MONTHS[new Date().getMonth()] + ' ' + new Date().getFullYear();
    let_.next().makeCopy('NEFT ADVICE LETTER ' + stamp + ' (FINAL).docx', toMed);
    out.push(ND_LETTER);
  }
  Logger.log('sent to Amir (ToMedical): ' + (out.join(', ') || 'nothing found'));
  return 'sent: ' + (out.join(', ') || 'nothing');
}
