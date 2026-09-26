# Claude Code brief — S412_YESBANK_UNLOCK (the shelf opens Yes Bank's password-locked statements itself; two S411 loose ends)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S412 (follow-up to S408/S411; PARENT-owned, README says so).**
The owner will NOT open PDFs by hand every month (REPORT_S411's suggestion is withdrawn): the server unlocks them. Read REPORT_S411.md first.

## 0 · READ FIRST — the owner's correction (26-Sep, after S411)
Yes Bank statements reach the clinic mailbox TWO ways, both relayed from the owner's personal Gmail with the [STMT] tag and filed by the
S195 filer into Drive Bank Statements/<year>: (a) the bank's own monthly e-statements ("Your YES BANK e-Statement for <MON>' 26 for Customer id
XXXXXXXXnn", one per customer ID, PDF **password-locked**) — the 5 locked files S411 saw; (b) **the branch's statements**, sent by a Yes Bank staff
member (a WRM) with the bare subject "statement", ~600 KB PDFs, **NOT password-locked** — seen 22-Aug and 02-Sep 2026 in the clinic mailbox and
sent on to the accountants by the filer; this month's is late (expected this week). **The branch copies are the PRIMARY Yes Bank source.** First
job: find where those two branch PDFs went on the shelf (S411 counted "all 21 ICICI" + 5 locked — so the branch PDFs were either misidentified
as ICICI, unplaced, or never fetched; read `stmt_file` and the inbox), read them with the Yes Bank reader, and place every account they carry
(a branch PDF may hold several accounts — split by account header if so). The locked e-statements are the FALLBACK for a month the branch is
late: unlock them only when no branch copy for that account-month has arrived by the 10th — so the password card in §2.1 stays, optional, and
its Needs-you line appears only when a month is missing on both routes. When both exist for an account-month, the branch copy is the one on
the shelf and in the pack; the locked one is marked "duplicate of branch copy", never read twice into the tables.

## 1 · What S411 left
- 16 of 21 bank PDFs read (ICICI, six accounts, July + August complete). **5 Yes Bank PDFs are password-locked** (`read_status` says so), untouched.
- Two notes for a later revision: the ICICI anchor moved to 10-Sep on the strength of a text statement's last running balance; ICICI text statements
  carry a degenerate header period that should be widened to the rows.

## 2 · The build
1. **Unlock on the shelf.** Add a `stmt_secret` table (slot_key or bank, secret, set_by, set_at) — **stored only in finance.db, never in the repo,
   never logged, never echoed back to any page** (the page shows only "set on <date>" and a Replace button). On the owner's Month-end packs page,
   a small card **"Statement passwords"**: one masked field per bank that sends locked PDFs (Yes Bank now; ICICI/HDFC cards if their originals
   are ever needed), owner-only, POST over the existing gate, audited as "set/replaced" without the value. Yes Bank commonly uses the customer
   ID or a DOB pattern; the field accepts a list of candidates (one per line) and the shelf tries each. `process_inbox` / `read_file`: when a PDF
   is encrypted (`pdftotext` refuses or `qpdf --is-encrypted` says so), decrypt with `qpdf --password=… --decrypt` (or pikepdf if present; check
   the box, install nothing outside the venv without saying so) into the inbox as `<id>.unlocked.pdf`, then identify and read as normal; keep the
   locked original; `read_status='locked — no password'` (with a Needs-you line "Yes Bank statements need their password on the packs page")
   when no candidate opens it. Re-try locked files on every run until they open.
2. **Yes Bank read path proven on the real files**: once unlocked, the 5 go through `finance_yesbank.ingest_statement` (S360) — Sanjeevni's two
   accounts feed the shared `bank_statement_line` tables as today; **the four non-Sanjeevni Yes Bank accounts (NK Pathology, Clinic, the three
   savings) must NOT enter the shared tables** — S411 found the owner's Bank card and the NEFT checks read those tables with no account filter.
   Put them in the per-account tables S411 created for ICICI (generalise the table to `bank`+`slot_key`), or a Yes Bank twin of them; read-only
   for the shelf and the pack. Prove the reader on each real file (opening + rows = closing, running balances); if the reader refuses a savings
   layout, extend it with the proof intact (anchored, declared — it is the Sanjeevni file).
3. **The two S411 notes:** (a) the ICICI anchor (`bank_anchor`, S377) may move only on a statement whose header period is real and whose closing
   balance is proven — not on a text statement's degenerate header; restore the 31-Aug anchor if the 10-Sep move rested on that, and say so;
   (b) widen the text-statement period to its first and last row dates when the header is degenerate.
4. **Amir's pack** now assembles when both Sanjeevni statements are on the shelf for the previous month — check it fires for August after the
   Yes Bank file reads; the owner's page shows it.

## 3 · Pins — read live (S411 TO pins in REPORT_S411; packs.py, stmt_shelf.py, finance_icici.py; finance_yesbank.py 825016c0 — anchored only;
finance_approvals.html / sanjeevni_approvals.py as S410 left them — the Needs-you line + the passwords card, declared). Restart clinic-finance only.

## 4 · Walk
A crafted encrypted PDF (qpdf-encrypted fixture) opens with the right candidate, fails cleanly with a wrong one and reads `locked — no password`
· the secret never appears in any page body, log line, report or the kit (assert) · a Yes Bank Sanjeevni fixture lands in the shared tables; a
non-Sanjeevni one lands only in the per-account tables and the owner's Bank card figures are byte-identical before/after · anchor rule (3a) on
crafted text and PDF statements · Amir's pack fires only with both · S408–S411 walks re-run green.

## 5 · Done means
Kit `deploy_kits\S412_YESBANK_UNLOCK\` · installed · published · `claude_code_briefs\REPORT_S412.md` — owner lines first: the one thing he does
(type the Yes Bank statement password once on the packs page), how many of the 21 are read after that, what Amir's August pack holds; ending with
`https://followup.dr-manoj.in/finance/packs`. No secret, account number or personal-statement figure in the report.
