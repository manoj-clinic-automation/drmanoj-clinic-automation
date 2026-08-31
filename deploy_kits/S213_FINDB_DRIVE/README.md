# S213_FINDB_DRIVE — finance.db into the nightly Drive backup (F-261)

**Built and proven offline at Session 213, 31-Aug-2026. NOT YET INSTALLED.**
*(And per the S212 rule: this line is a claim, not evidence — the live pin and
the cron table are the evidence, once installed.)*

## The gap this closes

S212 measured it (F-261): the nightly Drive job carries twelve follow-up-tracker
CSVs, and `finance.db` — 17,146 item lines, the stock ledger, the patient spine —
is in none of them. `finance_backup.sh` (S179) takes a verified copy every night
at 01:05, but every copy sits on the same disk as the original. Its own closing
comment says an off-box copy is an owner decision. The owner made that decision
at S212: safety before features, item 1 of the S213 order.

## The design — no new credential anywhere

The VPS already holds a Google **service account** (the follow-up tracker's
gspread json). The same json speaks the Drive API. So:

```
01:05  finance_backup.sh          sqlite .backup -> verify -> /root/backups/finance/   (existing, untouched)
01:40  finance_drive_backup.py    newest copy -> RE-VERIFY -> gzip -> Drive folder
                                  -> read back Drive's own md5Checksum, compare
                                  -> only then: monthly copy + prune (30 daily / ~13 monthly)
```

Refusal stances, inherited from S179 and kept absolute:
- a copy that fails `integrity_check`, or has an empty `day_entry`, never leaves the box
- a copy older than 30 h never leaves the box (it means the 01:05 job is broken — fix that, not this)
- an upload whose read-back md5 differs is deleted and **nothing is pruned**
- pruning is only reachable after tonight's upload verified

The owner's one-time GUI step: share ONE Drive folder with the service-account
identity (preflight prints it) and put the folder id in
`/root/finance/drive_backup.conf`. The folder id and json path live in that conf
on the VPS — never in this repository (F-185 discipline: no secrets in git).

## Files

| file | role |
|---|---|
| `finance_drive_backup.py` | the whole job: `preflight` / `run` / `list` |
| `WALK_drive_backup.py` | the live-shape walk: real sqlite db, real backup dir, a fake Drive that md5s the bytes it actually receives; 15 checks across 8 paths incl. every refusal |
| `INSTALL_ONE_PASTE.txt` | the owner's steps, one line per command, full paths |
| `SUMS.md5` | the gate — verify from INSIDE this folder: `md5sum -c SUMS.md5` |

## What the walk proves (and a gate cannot)

Corrupt copy refused before any network call · mangled upload detected by
read-back and the bad Drive copy deleted · prune untouchable on a failed night ·
exactly 30 dailies survive a prune · monthly created once, never duplicated ·
stale local copy refused · empty book refused · preflight's test file cleaned up.

## Known limits, stated plainly

- Files uploaded by a service account count against the SERVICE ACCOUNT's own
  15 GB Drive quota, not the owner's. Preflight prints usage; retention keeps
  the folder bounded (~30 dailies + ~13 monthlies). If quota is ever refused,
  plan B is rclone with the owner's own OAuth — a decision, not built here.
- The db.gz contains patient names. It goes only to the clinic's own Drive
  account, which already receives `patient_diagnosis.csv` nightly. Encryption
  before upload was considered and not added — one more key to lose against a
  copy in the same trust domain as the existing nightly data. Owner may rule
  otherwise; the hook is a one-line gpg pipe in `gzip_to_tmp`.
- `preflight` uploads one tiny test file and deletes it. That pair of calls is
  the proof the folder is writable; nothing else is touched.
