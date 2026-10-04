# GAS_CURRENT/PersonalJanitor — the PERSONAL account's Apps Script project "Janitor" (drmanojkragarwal@)
Living copy (D583 rule: every Apps Script change placed in the owner's browser lands here in the same breath).
- Bank_Statement_Relay.gs — as edited 26-Sep-2026 14:51 IST by the Sanjeevni chat (S283) in the owner's signed-in
  browser pane, on the owner's word: SENDER_QUERY gains `account.statement` (YES savings e-statements: HUF, personal)
  and `(from:vikrant.tayal from:yes)` — the YES BANK branch writes from yes.bank.in, which Gmail's `from:yesbank`
  never matched, so the branch's open statements (5-Aug, 23-Sep) were never relayed. Run once after saving:
  "relayed 7 statement mail(s)" (14:51:52 IST). Code.gs (Inbox Janitor v2.3) and Renewal_Nag.gs not copied here;
  S195_STMT holds the frozen originals.
- 14:56 IST, second edit on the owner's word ("mostly Vikrant sends, sometimes another person"): the branch match is now
  `from:yes.bank.in` -- ANY sender at the Yes Bank branch domain with an attachment is relayed; the locked e-statements
  (customer-ID passwords the owner does not use) stay a fallback only. Saved, run once: "relayed 0" (the 7 were already
  relayed and labelled at 14:51).
- 04-Oct-2026 (S293, the parent), on the owner's ruling that a bank statement never enters the staff-readable clinic mailbox and
  the accountants get statements only inside the month-end pack: Bank_Statement_Relay.gs -> S293 v2 (md5 3fd8564a, 3,601 B),
  placed in the shared Janitor project from the clinic account's browser pane through the editor's own API (byte-exact; sha256
  109b479d... read back after a reload, 08:1x IST). It now SAVES each statement mail's attachments straight into the clinic Drive
  folder Clinic Data Archive / Bank Statements / <YYYY> (folder 1wGzaXnCo... shared to drmanojkragarwal@ as editor the same
  minute, verified by the Drive API) -- no forward, no mail. Same senders, same label, plus a file-name dedupe. The clinic-side
  Bank_Statement_Filer.gs (UPI Reconciliation) is RETIRED the same hour: its daily trigger removed by its own retireStmtFiler()
  ("RETIRED S293: 1 trigger(s) removed", 08:07:01 IST; 7 other triggers untouched). The Janitor and CC saver triggers have failed
  since 1-Oct / 2-Oct with "Authorization is required" -- the owner re-authorises both in his personal account (his hand only);
  the relay's first run after that catches up the last 40 days of unlabelled statement mail.
