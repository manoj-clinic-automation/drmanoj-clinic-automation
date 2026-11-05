# S709_HOLD_WAIVE_OCT — September's holds taken off October's salary · the parent · session 385 · 05-Nov-2026

**For the owner, in one line.** October's salary no longer deducts September's held late charges ("Pichhle mahine ka late"): each one is marked WAIVED in the register's hold ledger, and October's Sheet 2 shows it as *already closed (waive)*.

## Why
The owner, 20:15 IST 05-Nov-2026: *"REMOVE PREVIOUS HOLD DEDUCTION FRM OCTOBER SALARY SHEET."* Read on October's Sheet 2 at 20:2x IST (not locked; Sheets 1 and 2 approved): September's hold is being **deducted** from October for Alisha 273.13, Awdhesh 390.46, Darpan 765.22, Sandip 219.16, Shavez 388.28, Shivani 89.14, Surendra 232.96 (₹2,358.35); Ranjeet's 62.50 and Vikki's 96.20 are already cancelled for improvement.

## What it changes
`/root/staff_register/hold_ledger.jsonl` — **append only**: one line per September hold that October would **deduct**, `{"action": "WAIVE", "staff", "ym": "2026-09", "amount", "reason", "by": "manoj", "ts"}`, written through `salary_policy.append_hold` (the ledger's only writer). `salary_policy.hold_state` already treats WAIVE as a closing action (RELEASE / LAPSE / WAIVE), so `compute('2026-10')` sets nothing to collect from September. No code, no setting, no other month, no restart (the ledger is read on every compute). The Sheet 2 approval is not tied to the figures — no re-approval needed. Ranjeet's and Vikki's holds, which October already cancels for improvement, are **left as they are** (October's lock records their cancellation as before).

## The tool — `hold_waive_s709.py`
Plan (default): lists the September holds October would deduct, and those it already cancels. `--apply`: refuses if October is LOCKED — the lock is read from the register's own database, found exactly as the register finds it (SR_DB_PATH, then staff_register_config.py, then the default), and any failure to read it STOPS; backup `hold_ledger.jsonl.bak_S709_<time>`; the lock and the ledger re-checked just before writing; appends the WAIVE lines; verifies — the old bytes untouched, exactly one new line per hold, each now WAIVE, the holds left HELD exactly the ones October cancels, October's own computation deducts 0 from September and each person's **exact** net (before the round-down to the last ₹10) rises by exactly what was being deducted, everyone else unchanged — and on any red cuts the ledger back to its original bytes (anything the app appended meanwhile is never wiped unless the old bytes themselves changed).

## Proven (S385, cloud workspace, the live salary_policy.py c3653896 from the 05-Nov bundle)
`walk_s709.sh` **18/18** on made-up ledgers (made-up names): plan writes nothing and lists only HELD holds of the right month; apply appends exactly the waives, old lines byte-identical, another month's hold and a released hold untouched; a second run says NOTHING TO WAIVE; with a stand-in October computation that rounds pay down to the last ₹10 exactly as the real one does (273.13 → pay 8,380 → 8,650), the exact nets rise by exactly the deduction and a hold October cancels is left HELD; **CONTROL** — a computation that ignores the waive goes RED and the ledger is cut back byte-identically; a locked October refuses; no register database, no lock table — STOP; the register's SR_DB_PATH honoured; a wrong month pair refuses.

**Cold review** R1 NOT SAFE (fails safe, but would always go red): (1) the check compared the rounded net — now the exact net; (2) the lock guard failed open on an unreadable database — now it STOPS and finds the database the register's way. Its should-fix built: restore cuts back to the original size instead of overwriting; the lock re-checked before writing; holds October already cancels left alone. The installer runs the same walk on the server against the LIVE salary code before it writes.

## Install (on the server, after the publish; any time)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s709kit && cp -rp /root/deploy/repo/deploy_kits/S709_HOLD_WAIVE_OCT /tmp/s709kit && bash /tmp/s709kit/install_S709_HOLD_WAIVE_OCT.sh
```
## Undo
The tool prints the exact line at the end (it copies its backup back).
