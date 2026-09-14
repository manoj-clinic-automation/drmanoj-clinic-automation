# HANDOFF RUNBOOK — v176 · Session 255 close · 14-Sep-2026 ~06:00 IST

## §0 · What happened (13/14-Sep, one night)

1. **Club A closed.** The exact live `finance_app.py` (684,004 B, `1fc62335…`) and 28 unit files captured off the box into `F:\ClinicBackup\DrManojClinic_Automation\04_LIVE_SOURCE\VPS_finance_2026-09-13_S255.zip` — the first byte-exact copy in any store. Three missing unit files into the repository; `clinic-finance.service` sanitised (F-465: it holds two real tokens). The watchdog was already live since S243 (F-466).
2. **The portal channel, three times.** `S255_PORTAL_CHANNEL` split on the Docterz mode word, was refuted by the box within the hour (F-467, F-468), rolled back. Docterz was found to append the Razorpay id to the Mode cell and the reader to discard it. `S256_GATEWAY_REF` keeps it; `S257_PORTAL_EVIDENCE` reads it (D510) and back-filled 76 days. Live: August Portal ₹1,400 · 2 payments by id.
3. **Club B closed by inspection** — three items fixed at S243, one not a fault by ruling, one by design; pipeline healthy.
4. **Club C.1 live** — `S258_CONSTANT_TIME`: nine plain compares → `hmac.compare_digest`; `finance_app.py` patched on the box to an md5 predicted from the capture (F-470; F-471 the gitignore refusal).
5. **The tidy** — 86 items to the Recycle Bin on the owner's word.
6. **12-Sep answered** — ₹650 up in cash (unbilled consultation + test), ₹2,050 on his phone, ₹1,500 in transit; not short.

New fault codes: F-465 … F-471. New decision: D510. No SOP or surveillance-scope change.

## §1 · Mental models that earned their place this session

- **A plan is not a pin list.** The S243 architecture paper listed four things as open that had been fixed the same night. Before building or reporting any plan item, grep the kits and the pin list.
- **A sentence in a brief is a claim to test.** D507 said Wallet/Patient APP/Net Banking are Razorpay; one receipt and one MPR pairing disproved it. The owner's "there is no email" was the right challenge. S256/S257 were built only after the premise was verified in the source file itself.
- **One list, many readers.** A change to which entries count is made where the list is built. S255 split in one reader and passed a figure to the other — the F-459 class, reintroduced (F-468).
- **The capture pays.** With exact bytes in hand, an on-box patch can be predicted offline and the installer can refuse anything else. S258 did it.
- **The publish gate scans the folder.** No "token" or "secret" in kit filenames; a rename before first publish must remove the old file.
- **Sub-agent output is data.** A browser sub-agent editorialised ("the rollback makes ₹1,100 of portal money invisible") — wrong, and not passed on.
- **Judge a batch by its counts.** An exit code lied about a 76/78 backfill (F-469).

## §2 · The live backlog (in this order)

1. **Re-hash on the box at the open** — owed twice now: `md5sum /root/finance/amir_day.py /root/staff_master.csv` (expect `a9f20622…` and `e48ae0b0…`).
2. **Club C.2 — OFF switches** for the four PC-side jobs with none: manojz `pull_watchdog.py` (15-min), `PUSH_STOCK_DAILY/NIGHTLY.bat`; medical `marg_push.py` (60 s thread), `marg_watch.py` (5 s poll). Medical may go through the agent's Drive self-update; manojz needs a paste while the device shell is dead.
3. **Club C.3 — one `sanjeevni.conf` per machine**: the Tailscale UNC in `push_snapshot.py`, the Drive folder id and the `*.json` key glob in `marg_ingest.py`, the baseline date `03-09-2026` in two places, the three `followup.dr-manoj.in` URLs.
4. **Club C.4 — per-sender tokens**, folded into the F-456 rotation: medical and manojz get different `X-Finance-Marg` values; `clinic-finance.service` is the token store (F-465); rotate once, everywhere.
5. **The PWA reorganisation, with the owner** — after a week of real use of the money/match screens; his morning walk is the spec.
6. **Club D — one sale-line store** (needs C.4); **Club E — one sender per machine**; **Club F — Sanjeevni in its own process**.
7. Carried: the Yes Bank settlement leg (low priority at 2–3 portal payments a month) · Bhati's itemising · the learning step · the physiotherapy system · D493 phase 2 · the F-458 gate · F-451 cron.

## §3 · Install discipline (unchanged, plus this session's)

Build offline → `py_compile` → selftest on a real sqlite day → installer mock-tested four ways (clean · rerun · wrong base · forced failure) → `git check-ignore` every kit file → owner publishes → one VPS line carrying `git pull --ff-only` → live-shape walk by the browser sub-agent → the record. A plan item is checked against the live pins first. Kit filenames never contain "token" or "secret".

## §4 · The boundary

Never written to: Marg. Never touched without the owner's word: `_PHI_QUARANTINE_S202`, `_S204_WORK`, `patient_fp.env.BACKUP_KEEP_SAFE`, the VPS quarantine, `/root/_retired/S243_…` (his one line, not before Session 256). The private capture never enters the public repository. Deletions are the owner's; this session's 86 went to the Recycle Bin on his instruction.
