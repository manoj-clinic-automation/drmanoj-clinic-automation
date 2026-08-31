# S213_FINDB_DRIVE — finance.db into the nightly Drive backup (F-261) · v2

**Built at Session 213, 31-Aug-2026. v2 after a live refusal — see below.**

## The gap this closes

S212 measured it (F-261): the nightly Drive job carries twelve follow-up-tracker
CSVs, and `finance.db` — 17,146 item lines, the stock ledger, the patient spine —
is in none of them. `finance_backup.sh` (S179) takes a verified copy every night
at 01:05, but on the same disk as the original. The owner ruled at S212: safety
before features, item 1 of the S213 order.

## v1 → v2, and why — proven on the live box, not assumed

v1 had the service account CREATE a new Drive file per night. The first live
preflight (31-Aug-2026 20:13 IST) was refused: **HTTP 403 "Service Accounts do
not have storage quota."** Google no longer gives service accounts storage of
their own (the about endpoint shows `quota 0 of 0` — that IS the signature).

What a zero-quota service account can still do is write new **content into a
file the owner already owns** — those bytes bill the owner's quota. So v2:

```
01:05  finance_backup.sh          sqlite .backup -> verify -> /root/backups/finance/   (existing, untouched)
01:40  finance_drive_backup.py    newest copy -> RE-VERIFY -> gzip
                                  -> OVERWRITE finance_nightly.db.gz  (owner-owned slot file)
                                  -> read back Drive's md5Checksum, compare, stamp description
                                  -> first verified run of a month: OVERWRITE finance_monthly.db.gz
                                     and PIN that revision (kept forever)
```

Retention comes from Drive itself: a file's previous versions live ~30 days in
its revision history (pinned ones indefinitely, cap 200 — warned at 180). So the
nightly slot alone is ~a month of restore points, the monthly slot one immortal
copy per month, and the on-box 30 dailies + 12 monthlies remain the first stop.

The two slot files were created 31-Aug-2026 from the owner's own account
(via the Drive connector — no GUI needed) inside `FinanceDB_Backups`, which is
shared to the service account as Editor. **If either slot file is ever deleted,
the job stops with exit 13 and names it** — recreate it from the owner's
account; the service account cannot.

Refusal stances, inherited from S179 and kept absolute: a copy failing
`integrity_check`, with an empty `day_entry`, or older than 30 h never leaves
the box; a nightly update whose read-back md5 differs is FATAL and the monthly
is not touched (the previous good version still stands in revision history).
Preflight proves write access by a metadata-only touch — content is never
changed outside `run`.

## Files

| file | role |
|---|---|
| `finance_drive_backup.py` | the whole job: `preflight` / `run` / `list` |
| `WALK_drive_backup.py` | the live-shape walk: real sqlite db, fake Drive with per-file revision history; 18 checks across 8 paths incl. every refusal and "preflight touches no content" |
| `INSTALL_ONE_PASTE.txt` | the owner's steps, one line per command, full paths |
| `SUMS.md5` | the gate — verify from INSIDE this folder: `md5sum -c SUMS.md5` |

## Known limits, stated plainly

- Drive's ~30-day/100-version revision window is Google's behaviour, not a
  contract. The on-box S179 retention is the guaranteed tier; Drive is the
  off-box disaster copy. `list` mode shows the live revision count any day.
- The db.gz contains patient names. It goes only to the clinic's own Drive
  account, which already receives `patient_diagnosis.csv` nightly. Encryption
  was considered and not added — one more key to lose, same trust domain.
  Owner may rule otherwise; the hook is a one-line gpg pipe in `gzip_to_tmp`.
- Config (`/root/finance/drive_backup.conf`, chmod 600) holds the json path and
  folder id — never in git (F-185 discipline).
