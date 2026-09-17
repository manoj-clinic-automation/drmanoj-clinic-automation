# S287_ASSETAPP_DRIVE — the asset register's backup goes to Google Drive

**Session 263 · 17-Sep-2026 · VPS only · upgrades S286 (installed 09:04 IST).**

## Why

The owner, 17-Sep: *the asset register's backups were multiple copies on the VPS itself; set it right and add
an off-site copy — the off-site location is the connected Google Drive.* S286 made the backup verified and
logged, but on the box only. Its first live run measured what that means: **one archive 204,157,240 B,
64 photos, 16 tables — and fifteen such archives (~3 GB) on the same disk as the app, with no copy anywhere else.**

S286 was published and installed while this off-site leg was still being written, so it ships as its own kit on
top of S286 rather than as an edit to a published one.

## What changes

`/root/state_backup/assetapp_backup.py` S286 → v2. **The crontab is only read** — S286's 02:30 line and log stay.

- The verified archive goes to Google Drive, folder **`FinanceDB_Backups`** — the route the finance database has
  used nightly since S213, its Drive calls and config imported from `/root/finance/finance_drive_backup.py`
  (Register pin `14b40677…`). Nothing new to configure; no secret in this kit.
- The server's Google identity has no storage of its own and can only refresh files the owner's account owns, so
  **two slot files were created from the owner's account at S263** (the service account already writes to them
  through the folder):

| Drive file | holds |
|---|---|
| `assetapp_nightly.tar.gz` | the latest verified archive — replaced only on nights the register changed |
| `assetapp_monthly.tar.gz` | the first verified night of each month, **kept forever** while under 500 MB |

- A night identical to what Drive holds (same rows, same photos by name/size/time) **uploads nothing** — proven by
  the fingerprint and md5 recorded on the Drive file, the md5 being Drive's own. Every upload is read back by md5.
- **With a verified Drive copy the server keeps 3 days** (≈600 MB instead of ≈3 GB); **without one, the old 14.**
- One line a night: `OK` · `PART` (server copy verified, Drive failed — why) · `FAIL` (no verified archive — why).

## How it was proven

- **Self-test 29 of 29** (temporary folder + fake Drive) — every S286 guarantee kept, plus: ships and verifies ·
  pins the month · unchanged night uploads nothing · new photo ships again · new month pins again · unverified Drive
  copy / Drive unreachable / missing slot / no config → PART with the reason, keeps 14 days · over 2 GB → not shipped.
- **Driven through the real `finance_drive_backup.py`** (bundle `14b40677…` = Register) against a stand-in speaking
  Drive's REST shapes: resumable upload, md5 read-back, monthly pinned, second night no upload, the finance file in
  the same folder untouched.
- **Installer rehearsed on a fake root shaped like the server now** (S286 script + S286 crontab line): upgrades;
  crontab unchanged by md5 · repeat = already installed · first run with no verified archive → S286 script restored
  byte-identically · a changed script refused · S286's line missing refused.
- The two Drive slot files checked from the owner's side: owner drmka.ortho, service account `writer`.

## Pins

| file | before | after |
|---|---|---|
| `/root/state_backup/assetapp_backup.py` | `9fdc66a3d7d0bfe94541b2eb228302e9` (S286) | `b816504c89fa127b7519d29a77e54658` |

## To install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S287_ASSETAPP_DRIVE/install_s287.py
```

The first run makes a fresh archive and sends ~200 MB to Drive — a few minutes.

## To undo

```
\cp /root/state_backup/assetapp_backup.py.bak_S287_9fdc66a3 /root/state_backup/assetapp_backup.py
```
