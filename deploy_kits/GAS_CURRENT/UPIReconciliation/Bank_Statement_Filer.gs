/** ==========================================================================
 *  Bank_Statement_Filer.gs · RETIRED at S293 (04-Oct-2026) · CLINIC account (drmka.ortho@)
 *  Lives in the "UPI Reconciliation" GAS project.
 *
 *  The owner's ruling, 04-Oct-2026: bank statements never pass through the
 *  clinic mailbox (staff can read it) and never go to the accountants one by
 *  one. The personal account's Bank_Statement_Relay (S293 v2) now saves each
 *  statement straight into Clinic Data Archive / Bank Statements / <YYYY>;
 *  the accountants receive statements only inside the month-end pack
 *  (/finance/packs); Amir's pack is on his board (S408) -- the ToMedical copy
 *  is not needed. Nothing is forwarded, archived or mailed from here any more.
 *
 *  fileBankStatements is kept as a name so a stale trigger cannot fail: it
 *  removes its own trigger and returns. retireStmtFiler() does the same on demand.
 *  The S195 v3 original is frozen in deploy_kits/S195_STMT/.
 *  ========================================================================== */

function retireStmtFiler() {
  var n = 0;
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'fileBankStatements') { ScriptApp.deleteTrigger(t); n++; }
  });
  Logger.log('RETIRED S293: ' + n + ' trigger(s) removed');
  return 'RETIRED S293: ' + n + ' trigger(s) removed';
}

function fileBankStatements() {
  return retireStmtFiler();
}
