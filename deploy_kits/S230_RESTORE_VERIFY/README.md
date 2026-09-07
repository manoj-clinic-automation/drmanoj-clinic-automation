# S230_RESTORE_VERIFY — proving the Drive copy of `finance.db` can actually be restored

**Built at Session 230, 07-Sep-2026. Companion to `deploy_kits/S213_FINDB_DRIVE/`.
Not installed by the build — see `INSTALL_ONE_PASTE.txt`.**

## What the backup already proves, and what it does not

The chain today:

```
01:05  finance_backup.sh         sqlite .backup -> integrity_check -> /root/backups/finance/   (S179)
01:40  finance_drive_backup.py   newest verified copy -> gzip -> OVERWRITE the owner-owned
                                 Drive slot file -> read Drive's md5Checksum back and DIE
                                 if it differs -> stamp the description                        (S213)
```

That md5 read-back is a real check, and it proves a real thing: **the bytes now
sitting in Google Drive are the bytes that left the box.** That is transport.

It does not prove **recoverability**. In the whole life of this backup nobody
has ever downloaded that object, decompressed it, and opened the database
inside it. A `.gz` with a broken CRC, or a database that fails
`integrity_check`, would be gzipped, shipped, md5-matched and description-
stamped in exactly the same way as a good one, every night, silently. The
first person to find out would be the person restoring it, on the worst day.

**This kit is the missing half.** It pulls the slot file down, checks the md5,
**gunzips it — the check that has never once been run** — opens the result
read-only, runs `PRAGMA integrity_check`, counts what is inside, and compares
that count with the one the shipper recorded at ship time.

## Strictly read-only, on both sides

There is no upload, no `patch_meta`, no `update_content`, no revision pin and
no `PATCH` or `PUT` request anywhere in `verify_restore.py` — the `Drive` class
in it has only `list`, `get` and `download`. The walk asserts all of that as a
check, not as a promise. Running the verifier cannot damage the backup, cannot
add a Drive revision, and cannot consume a pin.

On the local box it writes exactly two things: temp files in the work dir
(deleted at the end of every run, success or failure, unless `--keep`) and its
own small JSON state file.

## The one line to run it

```
/root/wa/venv/bin/python3 /root/finance/verify_restore.py nightly
```

The monthly slot, and keeping the restored database to look at:

```
/root/wa/venv/bin/python3 /root/finance/verify_restore.py monthly --keep
```

`nightly` is the default, so the bare command does the same as the first line.
There is no cron and no service. This is a thing a person runs and reads.

## What a run prints

1. the slot file — name, size, Drive md5, description
2. the download, streamed to disk in the work dir (never held in memory)
3. md5 of the downloaded bytes against the md5 Drive reported
4. the gunzip, and its CRC
5. the read-only open and `PRAGMA integrity_check`
6. total tables, the `day_entry` row count, and the ten largest tables
7. the cross-check against the description the shipper stamped
8. deletion of the temp files
9. `RESTORE VERIFY PASS — <slot> · <N> tables · <N> day-entries · <N> bytes`

### The description cross-check is a WARNING, never a failure

The shipper stamps
`verified backup of <name> · md5 <gz md5> · <N> day-entries · shipped <ts>`.
The verifier parses that `<N>` back out and compares it to what it just
counted. A disagreement is printed loudly but **passes**, because the
description records the state at ship time and the file may legitimately hold a
later revision — or a description may have been stamped by a run whose content
update was refused. The restore itself is what is being judged, and if the
bytes decompressed and the database opened, the restore is sound. A slot with
no count in its description (or none at all) is likewise not a failure.

## Config

The same conf the shipper already uses, read at runtime, never in git (F-185):
`/root/finance/drive_backup.conf`, `KEY=VALUE`, chmod 600.

| key | required | default | used for |
|---|---|---|---|
| `SA_JSON` | yes | — | the service-account json. This file carries no key path of its own; whatever the shipper found, the conf already records. |
| `FOLDER_ID` | yes | — | the Drive folder holding the two slot files |
| `WORK_DIR` | no | `/tmp` | where the download and the restored db are written |
| `VERIFY_STATE_FILE` | no | beside the conf, `finance_restore_verify.state.json` | the state file below |

Slot file names are taken from the same constants as the shipper —
`finance_nightly.db.gz` and `finance_monthly.db.gz`.

## The state file

**A verification that cannot state its own age has not been done.** Every run,
pass or fail, leaves:

```json
{"last_verify_iso": "...", "slot": "...", "result": "PASS",
 "tables": 0, "day_entries": 0, "bytes": 0, "gz_md5": "..."}
```

so the next person can ask when the backup was last proved restorable and get a
date instead of an opinion. `result` on a failure names the stage that failed.

## Exit codes

| code | meaning |
|---|---|
| `0` | PASS — downloaded, decompressed, opened, counted (possibly with warnings) |
| `2` | bad arguments; usage printed |
| `10` | no conf at the expected path, or `SA_JSON` unset / not pointing at a file |
| `11` | `FOLDER_ID` not set in the conf |
| `13` | the slot file is not in the Drive folder — it is owner-owned; recreate it from the owner's account (the service account has zero quota and cannot) |
| `20` | Google Drive unreachable — no network, bad credentials, folder not shared |
| `30` | the download is bad — zero bytes, truncated against the size Drive reported, or its md5 does not match Drive's `md5Checksum` |
| `31` | **gunzip failed** — the archive is corrupt. The transport check cannot catch this; it is the whole reason this kit exists. |
| `32` | the database is unusable — will not open, `integrity_check` not `ok`, no `day_entry` table, or `day_entry` empty (the shipper refuses to ship an empty book, so an empty one here means the chain is broken) |

## Files

| file | role |
|---|---|
| `verify_restore.py` | the verifier: `nightly` / `monthly`, `--keep` |
| `WALK_restore_verify.py` | the live-shape walk — a real sqlite database, really gzipped, served by a fake Drive; 77 checks over 12 paths including every exit code, the never-run gunzip check, and "this script cannot write to Drive" |
| `INSTALL_ONE_PASTE.txt` | the owner's steps, one line per command, full paths |
| `SUMS.md5` | the gate — verify from INSIDE this folder: `md5sum -c SUMS.md5` |

## How often

**Twice a year, and after any change to the backup chain** — a new VPS, a new
service account, a change to `finance_backup.sh` or
`finance_drive_backup.py`, a schema change in `finance.db`, or any night the
shipper logged something unusual.

Not nightly: it downloads the whole archive each time and the value is in
having done it recently, not in having done it constantly. But not never
either, because **a backup nobody has restored is a hypothesis, not a backup.**

## Known limits, stated plainly

- It verifies the **head revision** of a slot file. It does not walk Drive's
  revision history, so an older restore point inside that ~30-day window is not
  checked. If the head restores, the machinery that produced the others worked.
- The restored database is opened read-only and counted; nobody claims the
  *contents* are correct, only that the file is a sound, openable, non-empty
  finance book. Content truth is the reconciliation work, not this.
- The temp download needs free space for the archive plus the decompressed
  database. On a small box set `WORK_DIR` to a partition that has it.
- `--keep` leaves a decompressed copy of the book, patient names and all, in
  the work dir. Use it while looking at something, then delete it.
