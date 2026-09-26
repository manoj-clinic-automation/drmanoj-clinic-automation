# S412_YESBANK_UNLOCK — the shelf opens Yes Bank's password-locked statements itself; two S411 loose ends

**Session 283 · 26-Sep-2026 · follow-up to S408 / S411 · OWNER: PARENT (clinic).** The owner will not open PDFs by hand every month:
the server does it. Read on the box first (13:17 IST, read-only): the five locked Yes Bank PDFs are three AES-256 (R5) monthly savings
e-statements and two RC4-128 "YFB monthly" current-account ones; the box has no qpdf / pikepdf / mutool; the venv's `cryptography` (49.0.0)
plus `pypdf 4.3.1` opens both ciphers and `pdftotext` reads what pypdf writes (probed in a throw-away folder before anything was built).

## §0 of the brief — the branch copies
The two ~600 KB branch statements (bare subject "statement", 22-Aug and 02-Sep) are **not on Drive**: Bank Statements/2026 holds exactly
the 21 files the shelf already has, and the S195 filer takes only mail tagged `[STMT]`. Nothing on this box can reach the mailbox, so the
shelf cannot fetch them; the fix is a filer rule (GAS), outside this brief and named in the report. The shelf is READY for them: a Yes Bank
statement that is not locked is placed and read like any other, is the one on the shelf and in the pack, and a locked e-statement of the
same account-month is then `duplicate of branch copy` (never read into the tables). Until a branch copy arrives, the unlocked e-statement
stands in.

## What was built
1. **`packs.py`** (anchored, 20 edits): `stmt_secret` (per bank, the candidates as a JSON list — **in finance.db only; never printed,
   logged, or sent back to any page**; the page gets `set on <date> by <who>, n candidates`), `stmt_secret_log` (set / replaced / opened
   file N — no value), `POST /finance/packs/api/secret` (owner-only over the existing gate; one candidate per line, max 10; the answer
   carries counts only). `process_inbox` runs an **unlock step** after each identification pass: when a secret is stored and a locked
   file is still closed, the venv python runs `stmt_shelf.py unlock` (pypdf lives there only) which writes `<inbox>/<id>.unlocked.pdf`
   beside the locked original; the opened file is then identified and read as any other. A file no candidate opens reads
   **`locked -- no password`** (retried on every run's first pass, and at once when the password is replaced). `read_file`: a locked file
   is read from its unlocked copy; the **branch-copy rule**; the **four non-Sanjeevni Yes Bank accounts go to
   `yesbank_account_statement_period/_line`** (ICICI's shape + `slot_key`) — never `bank_statement_*`, which the owner's Bank card,
   `_statement_covers`, `_seen_in_yesbank` and S407's bank check read as "the Yes Bank statement" with no account filter; the period the
   reader proved is written back to the shelf row. **Anchor rule (3a)**: `_anchor_refresh` moves the ICICI anchor only on a statement
   whose header period is real (from < to) and whose closing is printed — never the pipe .txt. Needs-you (after the 10th, only when the
   previous month's Yes Bank cell is empty on both routes): "Yes Bank statements need their password on the packs page (N locked files
   waiting)" or "the stored Yes Bank password opens none of N locked statements". The cells prefer the branch copy; `stmt_file` gains
   `locked`, `unlocked_path`, `unlocked_at` (ALTER on the live table).
2. **`packs.html`**: the **Statement passwords** card (masked textarea per bank — Yes Bank, ICICI, HDFC — Set / Replace; the box is
   cleared after the send); the cell says "opened from the locked e-statement"; the unplaced table says "password needed" / "the stored
   password does not open it".
3. **`stmt_shelf.py`**: the `unlock` command (counts only: opened / still locked / candidates).
4. **`finance_icici.py`** (3b): a pipe .txt whose header period is degenerate (from == to) takes its rows' first and last dates; the proof
   says so. `VERSION` stays 1.1 (S411's frozen walk asserts it).
5. **`finance_yesbank.py`** — **anchored, declared**: `ingest_statement(..., tables=None)`; the default pair is the shared tables, so
   every existing caller is unchanged; the reader itself is not touched.
6. **`seed_s412.py`**: the anchor **restored from the S411 backup's row** (`finance.db.bak_S411_20260926_124432`, beside the database)
   when the current one rests on a `dd..dd` period, else recomputed from the newest iCRM statement with a printed closing; the four
   degenerate pipe period rows dropped and the .txt files read again (widened periods); the five locked files flagged; the grid printed.
7. **Installed into the venv, stated:** `pypdf==4.3.1` (pure python, `/root/wa/venv` only; the service python is untouched). The
   installer's gate installs it when missing and checks that its AES provider is the venv's `cryptography`.
8. **Not touched (declared):** `sanjeevni_approvals.py` and `finance_approvals.html` — the Needs-you line arrives through
   `packs.needs_you_lines`, the hook S408 wired; nothing in those two files needed a byte.

## Pins (read live 26-Sep-2026 13:17 IST)
| file | FROM | TO |
|---|---|---|
| /root/finance/packs.py | afd429bf8c0e7f685adda7d688045ab7 | 359403f792eaafad37d4eeac3f762641 |
| /root/finance/packs.html | b46d817c7a77944c4280ac72f95a6808 | 2e06943b991063dad3b23c74858533d4 |
| /root/finance/stmt_shelf.py | e74c29c0a5bb41f21cd2f7c1c8d3ad5d | 94f456ce0a6f469ecd7d3f16ca1e874e |
| /root/finance/finance_icici.py | 6d55a28aac170b1ab5899faa60eaa257 | 7ace56b77cd87d29352acb2d0f6cbe48 |
| /root/finance/finance_yesbank.py | 825016c02364dc5d22027ff192d1d29d | 5a088cd91bc1b8d873cc779f3fa9b0a8 |

Restarts `clinic-finance` only. `finance.db` backed up first (`finance.db.bak_S412_<stamp>`); `.bak_S412_<from8>` beside each file.

## Proof
`walk_s412.py` — the real finance app over scratch copies: (1) a fixture Drive with Yes Bank statements in S360's proven PDF layout,
three of them **locked with pypdf** (AES-256-R5 twice, RC4-128 once — the real files' ciphers) under **random passwords made at run
time and never printed**; a branch copy of one; a plain non-Sanjeevni one; ICICI iCRM PDFs and a pipe .txt with a degenerate header.
Before a password: the locked files wait, named; Needs-you names them. The clinic's statement lands in the per-account tables and the
owner's Bank card (`yesbank_position` + `bank_view`) is byte-identical before and after. The owner's candidates (one wrong, two right):
darpan refused, empty refused; the AES file opens and reads (pdftotext reads the copy), the RC4 twin of the branch month is
`duplicate of branch copy`, the third file is `locked -- no password`; Replace with the third candidate opens it; the log reads set /
opened / opened / replaced / opened. **The secret appears in no page, answer, log line, shelf row or unlock output** (asserted). The grid,
Amir's pack (July not ready, August ready). The anchor: moved by the iCRM August statement, left alone by the pipe .txt; the seed's two
restore routes on copies. (2) **The real 21 files** in a scratch copy, seeded exactly as the install does it: anchor back on 31-Aug, the
four pipe periods widened, the five locked files flagged and waiting, 16 still read, the Yes Bank tables unchanged, Amir's August pack not
ready. Negative control: S411's files on the same fixtures — no card, no route (404), the clinic's statement in the SHARED tables and the
Bank card changed, the pipe period degenerate, the anchor moved to 10-Sep. Then S411's, S410's, S409's, S408's (26/27 + the declared
supersession), S407's, S406's, S405's, S404's, S403's, S400's and S402's own walks re-run.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S412_YESBANK_UNLOCK/install_S412_YESBANK_UNLOCK.sh
```
Undo: the five `.bak_S412_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. The seed's data changes (anchor, pipe
periods, flags) are harmless; the database backup is used only if the owner says so. pypdf stays in the venv (inert without the kit).
