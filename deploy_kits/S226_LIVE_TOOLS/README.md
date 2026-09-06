# S226_LIVE_TOOLS — the manojz files as they run, captured at the S226 close (06-Sep-2026 14:00 IST)

| captured file | lives (and runs) at | md5 here | md5 of the LIVE file at capture | kit of record |
|---|---|---|---|---|
| `push_snapshot.py` | `D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\push_snapshot.py` (run in place by the pull cycle) | `03a845242ea29aec6bc46b1fc254809d` | `03a845242ea29aec6bc46b1fc254809d` | `S226_F322_SUBSET` (same md5) |
| `push_expected.py` | `…\deploy_kits\S208_STOCK_LEDGER\push_expected.py` | `a0e47a981cf03b8fdf7d35d1a9168295` | `a0e47a981cf03b8fdf7d35d1a9168295` | `S226_PURCHASE_BILLITEM` (same md5) |
| `MARG_WALL_CARD.html` | `D:\Downloads\margsync\MARG_WALL_CARD.html` | `f2b341ddd2b60c36b432cb9ae4d3dc3b` | `f2b341ddd2b60c36b432cb9ae4d3dc3b` | S225 — UNCHANGED at S226 (the `S226_WALL_CARD` draft `ad80019f…` NOT installed) |

Verified BOTH ways: each captured file hashed against its live source (the md5s above are the live file's at the moment of the copy) and against the kit of record. Install order: none needed — the two pushers run from the repo working copy on manojz and were replaced in place by the owner's one line each (backups `.bak_S226f322_20260906-032847`, `.bak_S226billitem_20260906-040949` beside them). Credentials: the pushers read the Marg share token from `D:\Downloads\margsync\_config\` (never its value here). Scheduled tasks unchanged at S226: *PULL_FROM_MEDICAL* every 10 min (carries both pushers) · *MargSnapshotOnCapture* and *MargExpectedOnCapture* every 15 min, 10-minute limits, the owner's account · *Clinic stock nightly* (another account; 30-minute limit still owed).
