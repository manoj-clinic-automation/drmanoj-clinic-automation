# S474_FINANCE_TIDY — the finance app after its whole read, and F-716 (session 293, 04-Oct-2026)

**Why.** The §1.5 whole read of `finance_app.py` (S293, 04-Oct) found three dead items — at the line — and the Sanjeevni chat's
proof of the parent's Marg-apply lead became **F-716**: a money-record fault, "not urgent".

| where | from → to | what |
|---|---|---|
| `/root/finance/finance_app.py` | 727a2e7a → 56eb421b | (a) the clinic tile answers a non-checker (reception's deposit banner, S469) **first**: no `refresh_missing_days` write on every page load, no month figures computed and thrown away; the checker's answer unchanged · (b) `selftest()` puts `LEDGER_DIR`, `FINANCE_LEDGER_JSONL`, `LEDGER_JSONL` back at teardown · (c) `CLINIC_TENDERS` (never used) removed · (d) **F-716**: the S243 push apply, the autoreplay at save and the portal upload call the two loaders with `commit=False` and commit once per day — their `con.rollback()` on a bill-count mismatch is real · (e) a file the reader refused may be sent again: a `rejected` staging row is not "received", and is replaced when the same bytes read |
| `/root/finance/finance_ingest.py` | 747b4a50 → d7b07fb6 | `ingest_day(..., commit=True)` |
| `/root/finance/finance_returns.py` | a46a87e6 → 68d87d00 | `load_lines(..., commit=True)` |
| `/root/finance/marg_backfill.py` | fa33ec8a → b706456a | the backfill tool commits once per day, after bills and lines |

Every other caller of the loaders is unchanged (the default still commits). No schema change, no page, no setting.

## Proven — `walk_s474.py`, hermetic (F-709), on the S469 walk's harness
The app's code copied to `/tmp` twice (old / new), each with an EMPTY database from the app's own schema (+ the two S193
columns that exist on the box only), made-up logins, a made-up clinic day and a made-up Marg export. 20 checks; each change
SHOWN on the old file first: reception's tile call wrote `missing_day` rows there and writes nothing now (the banner and the
checker's answer identical old/new); a second export run with `commit=False` and rolled back no longer supersedes the first
batch (on the old file it did, in spite of the rollback); `load_lines(commit=False)` + rollback leaves no line while the default
still commits; refused bytes answer REFUSED twice now (ALREADY-RECEIVED for ever before). Offline 04-Oct: `WALK_S474 GREEN 20 ok, 0 fail`.

## Install (the owner's one line; the lock F-694; DRY=1 places nothing)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S474_FINANCE_TIDY/install_S474_FINANCE_TIDY.sh
```
Red after placing → all four files are put back. Backups `.bak_S474_<from8>` beside each.
