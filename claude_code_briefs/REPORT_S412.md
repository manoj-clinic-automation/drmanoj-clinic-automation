# REPORT_S412 — the shelf opens Yes Bank's password-locked statements itself (S412_YESBANK_UNLOCK)

Installed on srv1746119 on 26-Sep-2026, 14:04–14:09 IST (installer's own clock). Kit `deploy_kits\S412_YESBANK_UNLOCK\`.

## For the owner
- **The one thing you do, once:** open the Month-end packs page, find the card **"Statement passwords"**, type the password Yes Bank
  puts on its e-statements into the Yes Bank box (usually your customer ID, or the date pattern the bank's mail describes — if unsure,
  type every candidate, one per line) and tap **Set**. It is kept on the server only, never shown again, never in any mail.
- **What happens then:** the server tries the password on the five locked Yes Bank statements at once, and again every night at 05:40
  for anything new. A file that opens is read like any other statement and its cell turns green. A file nothing opens says
  "the stored password does not open it" and Needs you tells you to replace the password.
- **How many are read:** today 16 of the 21 files on the shelf (all the ICICI ones). Once the right password is in, up to 21 of 21 —
  the five Yes Bank ones are July/August e-statements of the NK, clinic, Sanjeevni and savings accounts.
- **Amir's August pack:** not yet. It needs the Yes Bank Sanjeevni August statement, which is among the locked five. The moment that
  statement reads, the pack appears on his board (the ICICI half is already there).
- **The branch's own statements** (the ones the Yes Bank staff mail with the bare subject "statement") never reached Drive: the filer
  only files mail tagged `[STMT]`. That is a mail-filer rule for the chat to change, not this server. The shelf is ready for them: a
  branch copy is the one on the shelf and in the pack; the locked e-statement of the same month is then marked a duplicate.
- Also fixed: the ICICI Sanjeevni anchor is back on 31-Aug (it had moved to 10-Sep on a text statement's misleading header), and the
  ICICI text statements now show the dates they really cover.

https://followup.dr-manoj.in/finance/packs

## For the chat

### Pins — FROM → TO, md5 read back on the box after placing (14:09 IST)
| file | FROM (read live 13:17 IST) | TO (read back) |
|---|---|---|
| /root/finance/packs.py | afd429bf8c0e7f685adda7d688045ab7 | 359403f792eaafad37d4eeac3f762641 |
| /root/finance/packs.html | b46d817c7a77944c4280ac72f95a6808 | 2e06943b991063dad3b23c74858533d4 |
| /root/finance/stmt_shelf.py | e74c29c0a5bb41f21cd2f7c1c8d3ad5d | 94f456ce0a6f469ecd7d3f16ca1e874e |
| /root/finance/finance_icici.py | 6d55a28aac170b1ab5899faa60eaa257 | 7ace56b77cd87d29352acb2d0f6cbe48 |
| /root/finance/finance_yesbank.py (anchored, declared) | 825016c02364dc5d22027ff192d1d29d | 5a088cd91bc1b8d873cc779f3fa9b0a8 |

All five built on the box from the live bytes by `make_s412.py` (every anchor exactly once) and equal to the kit's pins. **Not touched
(declared):** `sanjeevni_approvals.py` (c5b93455) and `finance_approvals.html` (7de58315) — the Needs-you line rides the packs hook S408
wired, no byte was needed there. The five real locked files are AES-256 (R5) ×3 and RC4-128 ×2; the box has no qpdf/pikepdf/mutool, so
**`pypdf==4.3.1` was installed into `/root/wa/venv` at 13:58 IST** (site-packages time) by the installer's gate on its first run — the one
thing installed, venv only; `/usr/bin/python3` (the service) has no pypdf and needs none: the unlock runs as a venv subprocess. Compatibility
was probed first in a throw-away folder (`pip --target /tmp`, removed): both ciphers encrypt/decrypt, pdftotext reads the output, pypdf reports
the real files' V/R (5/5 ×3, 2/3 ×2).

### What the shelf does now (packs.py)
`stmt_secret(bank, secret JSON list, set_by, set_at)` + `stmt_secret_log` (set / replaced / opened file N — never a value);
`POST /finance/packs/api/secret` (owner-only, checker of unit packs; answer = counts). `process_inbox` → after each pass, `_unlock_locked`:
only when a secret is stored and a locked file is still closed, `venv python stmt_shelf.py unlock` (reads stmt_secret itself; pypdf; writes
`<inbox>/<id>.unlocked.pdf`; the locked original stays); the opened file is identified and read in the next pass; a file nothing opens →
`read_status='locked -- no password'`, retried on every run's first pass and at once when the password is replaced. `read_file`: reads the
unlocked copy; **branch-copy rule** (a non-locked READ file of the same slot + period exists → the locked twin is `duplicate of branch copy`,
not ingested; the reverse order marks the earlier-read locked one too); **Yes Bank non-Sanjeevni → `yesbank_account_statement_period/_line`
(slot_key set)**, Sanjeevni (`yes_cur_sanj`) → the shared tables as before; the proven period written back to the shelf row. `_anchor_refresh`
(3a): only `closing_printed`, layout ≠ pipe, from < to. Needs-you: "Yes Bank statements need their password on the packs page (N locked
files waiting)" when no secret, or "the stored Yes Bank password opens none of N locked statements" — only when a Yes Bank cell of the previous
month is empty. `cells` prefers the branch copy and skips duplicates. `stmt_file` +`locked`, `unlocked_path`, `unlocked_at` (ALTER at ensure).
`finance_icici._parse_pipe` (3b): a degenerate header (from == to) or none → the rows' first and last dates, the proof says so; VERSION 1.1 kept.

### The walk (install log, 14:04 IST) — `WALK_S412 GREEN -- 17/17`
Fixture Drive: Yes Bank statements in S360's proven PDF layout, three locked with pypdf under **random passwords made at run time** (AES-256-R5
×2, RC4-128 ×1), a branch copy of one, a non-Sanjeevni plain one, ICICI iCRM Aug/Jul + a pipe .txt with a degenerate header.
- pdftotext refuses the three locked fixtures with `Incorrect password` exactly as it refuses the bank's; pypdf sees them encrypted.
- Before a password: the three are unplaced, `locked=1`, noted "password-protected PDF -- type the bank's statement password once under
  'Statement passwords'…"; the branch copy read (01..31 Aug written back), the clinic's (01..30 Sep), the pipe .txt widened 10-Sep..10-Sep →
  01-Sep..10-Sep on the shelf row and in `icici_statement_period` (closing_printed 0); Needs you: "…(3 locked files waiting)"; the page has
  the card; api/state says not set for YES/ICICI/HDFC, `locked_open 3`, and carries no secret field.
- The clinic's statement, fetched alone: `yesbank_account_statement_period/_line` (slot_key yes_cur_clinic, tail 4123), nothing of 4123
  in `bank_statement_*`; the Sanjeevni branch copy (4122) in the shared tables (one period row); **the Bank card (`yesbank_position` +
  `bank_view`) byte-identical** around that ingest and around the two unlocked non-Sanjeevni ingests later.
- darpan 302, empty text 400; the owner's three candidates (one wrong): 200, action set, candidates 3, **opened now 2**. The AES NK file →
  `5.unlocked.pdf`, pdftotext reads it, placed by words, read into the per-account tables; the RC4 Sanjeevni twin → `duplicate of branch
  copy` ("file 6 is the branch copy"), shared lines unchanged (10 → 10), the cell shows the branch file; the third file → `locked -- no
  password`, note "none of the stored passwords opens it"; Needs you: "opens none of 1 locked statement"; log: set, opened file 5, opened
  file 7. Grid: Aug NK read (flagged from the locked file), Sanjeevni matched from the branch copy, Bhawna empty; Sep clinic read, ICICI
  Sanjeevni partial (01..10 Sep); Amir July not ready, August ready. Replace with the third candidate: action replaced, opened 1 → Bhawna
  read (yes_sav_bhawna, 4124 in the per-account tables only); api/state YES set, 1 candidate, 0 locked open, 3 opened; log set/opened/opened/
  replaced/opened.
- **The secret never appears** — asserted over the page, api/state, both answers, `stmt_shelf.py unlock` output, every stmt_file row and log
  row: `[False ×9]`; it is in `stmt_secret` only; VERSIONs `['1.1', '1.1']`.
- Anchor: the iCRM August (printed closing) moved it 31-Jul → 31-Aug; the pipe .txt read after it left it at 31-Aug. The seed on a copy left as
  S411's run left it: RESTORED from a backup row (31-Aug, its balance, 'seed S377'), the degenerate pipe row dropped, the .txt re-read widened;
  with no backup row: RECOMPUTED from the iCRM closing ('seed S412').
- **The real 21 files** (scratch copy, seeded as the install does): anchor 2026-09-10 → **2026-08-31 from the S411 backup** (entered_by
  `seed S377`; its balance equals the iCRM August printed closing: yes); 3 degenerate pipe rows dropped, the 4 .txt read again →
  …9819 12-Jul..09-Aug, …9819 11-Aug..10-Sep, …9822 15-Jul..14-Aug, …9822 15-Aug..14-Sep; 16 read before and after; 292 ICICI lines
  before and after; `bank_statement_period` 1 row / 7 lines before and after; 5 locked flagged, unplaced, none opened (no secret);
  Needs you "(5 locked files waiting)"; August's six ICICI cells read/matched; Amir August not ready.
- **Negative control** (S411's files, same fixtures): no card, `/api/secret` 404 for the owner (302 for darpan — the gate answers first),
  the locked files stay "password-protected" with no unlock and no `locked` column, the clinic's statement lands in the **shared** tables
  (4123 in `bank_statement_period`) and the Bank card **changes**, the pipe period stays 10-Sep..10-Sep and the anchor moves to 10-Sep on it.

Earlier kits' walks on the patched files: **S411 13/13**, S410 32/32, S409 24/24, **S408 26/27** (the one red is the S411-declared
supersession, accepted by name), S407 27/27, S406 27/27, S405 29/29, S404 65/65, S403 52/52, S400 63/63, S402 16/16.
**Declared for S411's re-run:** its frozen real-file check counts the first statement of each account "by words", but the live shelf has
carried the learned tails since S411's own seed (12:44 IST), so on today's data everything lands by tail (a 12/13 on the plain live copy in
run 3). The installer therefore starts S411's SCRATCH copy without learned tails — the box as S411 found it (a scratch pre-state, like the
table drops the S405/S407/S408 re-runs already need); S411's walk is then 13/13 with the S412 code. No S411 check was skipped.

### Placing, seed, restart, health
- Backups: `/root/finance/finance.db.bak_S412_20260926_140429` (backup API, 25,464,832 bytes); `packs.py.bak_S412_afd429bf`,
  `packs.html.bak_S412_b46d817c`, `stmt_shelf.py.bak_S412_e74c29c0`, `finance_icici.py.bak_S412_6d55a28a`,
  `finance_yesbank.py.bak_S412_825016c0` — each read back at its FROM md5.
- Seed on the live database (install log): anchor 2026-09-10 → 2026-08-31 restored from the S411 backup (`seed S377`, entered_at
  2026-09-23T09:50:07 kept; the balance equals the iCRM August closing); 3 degenerate pipe rows dropped, 4 .txt read again with the periods
  above; 5 locked files flagged (`locked=1`, note "…type the bank's statement password once under 'Statement passwords'…"); stored passwords 0;
  `process_inbox -> placed 4, unplaced 6, read 4, refused 0, unlocked 0`; the grid unchanged (July/August six ICICI read/matched, all Yes Bank
  empty, September Sanjeevni + one more ICICI account partial).
- `systemctl restart clinic-finance` — active; healthz 200 (local and public); `/finance/packs` 302 to a plain curl (login gate, expected);
  journal: only the two gunicorn "worker was sent SIGTERM" lines of the restart. The 05:40 fetcher run once by hand at 14:09:21: 0 new, 99 seen,
  identify rc 0, `unlocked 0`. Cron line unchanged (S408's).
- After (14:10–14:11 IST, read-only / a backup-API copy): tables `stmt_secret` 0 rows, `stmt_secret_log` 0, per-account Yes tables 0 rows;
  bank files 16 read + 5 "password-protected"; tails learned 6; **Needs you on a writable copy of the live database:** the two S408 lines +
  "Yes Bank statements need their password on the packs page (5 locked files waiting)"; api/state secrets: none set, locked_open 5;
  `stmt_shelf.py unlock` on the live box: "opened 0, still locked 5, candidates 0". The 6th unplaced row is file 1 in the cards folder root
  (S408's, unchanged by this kit).

### Not done / outside the brief
- **The two branch Yes Bank PDFs (§0):** not on Drive — `Bank Statements/2026` holds exactly the 21 files the shelf has, and the S195 filer
  takes only `[STMT]`-tagged mail. Nothing on this box reaches the mailbox, so the shelf cannot fetch them. Fix = a filer rule in
  `Bank_Statement_Filer.gs` (also file mail from the branch sender / subject "statement"), a GAS change for the chat. The shelf-side handling
  (primary, duplicate rule) is built and proven on fixtures.
- **The real Yes Bank e-statement layout is unproven** until the owner types the password: S360's reader (Period / Statement of account /
  the foot totals / "Cheque No/Reference No" header) is what the five files will meet. If a savings layout differs, the file will read
  "refused: …" naming what is missing, and that is a small anchored extension for a later kit (the walk shows exactly where it lands).
- The ICICI text statements are not calendar months (12-Jul..09-Aug, 11-Aug..10-Sep): with honest periods two September cells are now
  `partial`, which is the truth the S411 rule asks for.
- No permission asked; nothing outside the venv installed; no file the brief did not name touched. The database backup stays.
