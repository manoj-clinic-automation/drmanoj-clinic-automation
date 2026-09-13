# S243_SALTS_REFRESH — Marg's salt-wise list refreshes the salts page by itself

**What it fixes.** `/finance/purchase/page/salts` says *"Marg confirms N done in its list of 04-Sep-2026"*.
That line compares Amir's ticks against table `purchase_salt_marg`, which until now was loaded only by
`push_salts.py` on the owner's PC. A fresh `SALT_WISE_ITEM_LIST` export (12-Sep 22:49) has already reached
the VPS through the Marg door and, carrying no patient identity, is KEPT in the server archive:

```
/root/marg_ingest/archive/SALT_WISE_ITEM_LIST/2026-09/SALT_WISE_ITEM_LIST_DEFAULT__2026-09-12__20260912-224900__<md5-8>.XLS
```

This kit adds one server-side tool plus one cron line. Every future salt-wise export refreshes the page within
10 minutes with nobody touching anything.

**What it does NOT do.** Nothing is restarted. `purchase_app.py` is not changed. Amir's DONE ticks and the
doctor's answers (`purchase_salt_task`) are never in the payload — the handler only replaces
`purchase_salt_marg` (item -> salt, dated), which is exactly what the PC tool did.

## Install (on the VPS, as root)

```
bash /root/deploy/repo/deploy_kits/S243_SALTS_REFRESH/install_S243_SALTS_REFRESH.sh
```

Then apply the 12-Sep list now, without waiting for cron:

```
/root/wa/venv/bin/python3 -B /root/finance/salts_refresh.py --force
```

Expected one line, e.g. `salts_refresh 13-09-2026 09:05 file=SALT_WISE_ITEM_LIST_DEFAULT__2026-09-12__... as_on=2026-09-12 rows=373 salts=... -> server 200: ok marg_items=373 stored=0 kept=0`.
Reload the salts page: the line should now read *"... in its list of 12-Sep-2026"*.

## Rollback

```
bash /root/deploy/repo/deploy_kits/S243_SALTS_REFRESH/install_S243_SALTS_REFRESH.sh --rollback
```

Removes `/root/finance/salts_refresh.py` and restores the crontab from `/root/crontab.bak_S243_salts`.
The rows already in `purchase_salt_marg` stay (the next PC push would replace them, as before).

## Files installed

| path | what |
|---|---|
| `/root/finance/salts_refresh.py` | the tool (new file) |
| `/root/finance/salts_refresh.state.json` | last applied file name, md5, as-on, rows, time, server reply; `checked_at` on every cron run |
| `/root/finance/salts_refresh.log` | one line per send / refusal; silent when nothing changed |
| crontab | `*/10 8-22 * * * /root/wa/venv/bin/python3 -B /root/finance/salts_refresh.py --once >> /root/finance/salts_refresh.log 2>&1 # S243_SALTS_REFRESH` |

## How it works

1. Newest file under `/root/marg_ingest/archive/SALT_WISE_ITEM_LIST/*/` by the capture stamp in its name
   (`__YYYYmmdd-HHMMSS__`, the router's `canonical_name`), falling back to mtime.
2. Reads item -> salt with the vendored reader at `/root/marg_ingest` (`marg_report._open_sheet` and its
   `xlrd`), applying the same line rule as `push_salts.read_marg_salt_list`. `marg_as_on` = the stamp's date,
   as push_salts derives it.
3. POSTs `{"marg_items": [{"item","salt"}...], "marg_as_on": "YYYY-MM-DD", "marg_md5": <file md5>, "source", "host"}`
   to `http://127.0.0.1:8106/finance/purchase/api/salts` with header `X-Finance-Marg` read from
   `/etc/systemd/system/clinic-finance.service.d/marg_token.conf` (`Environment=FINANCE_MARG_TOKEN=...`). The token
   is never printed or written to state.
4. The handler (`purchase_app.api_salts` -> `_store_marg_salts`) deletes `purchase_salt_marg` and inserts the new
   rows, each stamped with `marg_as_on`; the page shows `MAX(as_on)`. Without a `tasks` key `_store_salts` is not
   called.

Flags: `--once` (cron; sends only if the newest file's md5 differs from the last applied), `--force`, `--dry-run`
(counts only), `--verbose`, `--min-rows=N` (default 100: a shorter list is treated as a truncated export and NOT
sent, so a bad file can never wipe the table), and path overrides `--archive= --ingest= --dropin= --state= --url=
--file=`; env `SALTS_REFRESH_ROOT` prefixes every default path for a mock.

Exit codes: 0 sent or unchanged · 1 server refused / unreachable · 2 nothing to send.

## Selftest

```
cd /root/deploy/repo/deploy_kits/S243_SALTS_REFRESH && /root/wa/venv/bin/python3 -B selftest_salts_refresh_s243.py
```

Needs the `S240_MARG_INGEST` kit beside it (vendored reader); uses `S225_SALTS` (push_salts comparison) and
`S240_SANJEEVNI_123` + flask (real-handler leg) when present. 44 checks; `EVIDENCE_S243.txt` holds the run.
