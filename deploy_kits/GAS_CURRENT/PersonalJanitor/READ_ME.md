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
