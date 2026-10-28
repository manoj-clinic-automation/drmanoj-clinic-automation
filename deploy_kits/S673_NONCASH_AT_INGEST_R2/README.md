# S673_NONCASH_AT_INGEST_R2 — a procedure or home-medicine bill is deducted the moment the sale export lands · project Sanjeevni · session 361 · 28-Oct-2026 · F-1037 · S672 refused by F-1038

**For the owner, in three lines.** Bill A004474 of 27-Oct (procedure, Rs 98) was never taken off the day's cash. The deduction was made only by a job that runs every half hour, and only on a day not yet approved; the export came at 08:31, the day was approved before the 09:00 run, and the job never touches an approved day. Now the deduction is made inside the sale ingest itself, so no day can be seen or approved without it; 27-Oct is corrected once (expected cash Rs 8,477 → Rs 8,379).

## Why this is R2
S672 (same files, same bytes) stopped at its own gate [4/8], nothing placed: its walk looked for the real 27-Oct export on the server, and the server deletes every raw sale export the moment it has read it (S186 — no file with a phone number kept at rest). S673 changes only the walk: on the server it ingests made-up bills into a made-up day on a copy of the live database, and runs the one-time 27-Oct step on a copy of the live day itself. The proof against the real 27-Oct export stands, run on manojz (14 of 14; the same walk with `--export`). S672's folder is frozen (F-512).

## Why
The owner, 28-Oct-2026 08:53 IST: *"There is one procedure bill which was not mentioned by the system. It is bill number 4474 for 97 rupees and 56 or something paisa. Find why it happened."* His "yes" to the fix, 08:57 IST.
**Read.** The export (captured 08:27, on the server ~08:31) holds A004474, customer text *PROSIJER <patient>*, one LOFTYPRED 80 INJ, net Rs 98.00, cash. The ingest read it right (no ID, no phone → the lookup ladder / the review queue, where `day_resync` pass 2 finds Darpan's label words). But pass 2 is a cron job (`*/30 7-23`) and only looks at unapproved days (`noncash_candidates`: status submitted/draft). The 08:30 run came before the export; 27-Oct was approved before 09:00; from then on pass 2 only *names* it in its log (`approved_label_missing`). Read live at 08:5x as the owner: 27-Oct approved, proc_p 0, no procedure bills, expected Rs 8,477. On the 28-Oct database copy no other approved day since 1-Sep carries the gap — every earlier one was caught because the job ran before anyone approved.

## Files
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/day_resync.py` | Sanjeevni | c62e98b9 | 00b45a15 | `noncash_day(..., commit=True, via=None)` (defaults keep pass 2 byte-for-byte in behaviour); NEW `at_ingest(con, unit, business_date)`: a medical day, unapproved, since 2026-09-01, the Sanjeevni switch not OFF → pass 2's own rows at once, never committing. |
| `/root/finance/finance_ingest.py` | shared (the parent's; PLANNED line on the board, v760) | d7b07fb6 | ce01a9e1 | ONE counted edit at the end of `ingest_day`, before its commit: `day_resync.at_ingest` under `SAVEPOINT s672_noncash`; any error rolls back to the savepoint and the ingest stands exactly as before. |
| `finance.db` · `day_noncash_bill` + `audit_log` | data step, by the installer, last | — | +1 row each | 27-Oct: A004474 procedure medicine (the row pass 2 makes), note *S672 one-time … the owner's yes 28-Oct*; refuses unless that is the day's ONLY undeducted label bill. If Darpan has already handed over 27-Oct, his day is re-decided on the corrected figure. |

Restarts `clinic-finance`. Pass 2 stays as the safety net (it now finds the rows PRESENT). No crontab change. No screen changes.

## Proven (`walk_s673.py`; on manojz with the real 27-Oct export, and in server mode on a live-shaped copy where 27-Oct is approved with A004474 undeducted)
Both modes **14 of 14 green**; the control on the live files **7 S673 red · 0 older red · 7 green**. N1 the ingest deducts the procedure bill at once (with the real export: A004474, Rs 98) with one audit row · N5 the half-hour job afterwards finds it PRESENT, one row · N2 old = new: sale_item, the review queue and the ladder's notes are the live file's row for row · N3 a rolled-back ingest leaves nothing · N4 an approved day: nothing added · N6 the switch OFF: nothing · N7 a failing door: the ingest stands, its half-write undone, the caller's next write commits · N8 the door's limits · N9/N10 made-up rows: a procedure and a home bill deducted, an ordinary bill not, a re-ingest adds nothing · N11 the one-time step adds A004474 to the approved 27-Oct once (on the server: on a copy of the live day), a second run says ALREADY · S `finance_ingest.py`'s own selftest ends exactly as the live file's (on today's data both stop at its *unidentified return goes to review* step — a stale check older than this kit, named in the close).
The installer was rehearsed on a made-up server: DRY, install, a second run ALREADY INSTALLED, and a forced red after placing that puts both files back byte-identically with nothing written to the database.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s673kit && cp -rp /root/deploy/repo/deploy_kits/S673_NONCASH_AT_INGEST_R2 /tmp/s673kit && bash /tmp/s673kit/install_S673_NONCASH_AT_INGEST_R2.sh
```
## Undo (the installer prints it)
```
\cp -p /root/finance/day_resync.py.bak_S673_c62e98b9 /root/finance/day_resync.py && \cp -p /root/finance/finance_ingest.py.bak_S673_d7b07fb6 /root/finance/finance_ingest.py && systemctl restart clinic-finance
```
