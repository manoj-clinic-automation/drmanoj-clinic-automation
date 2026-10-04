# S476_STATEMENT_WATCH — session 294, 04-Oct-2026 (the parent) — F-723, F-725, F-243

**What it does**

1. **The statement road says so itself (F-723).** From the 3rd of a month, while no bank statement has reached the shelf this month and last month's cells are still empty or partial, the packs page shows an amber line above the summary card and `/finance/health` shows the row *Bank statements reaching Drive* in amber — it stays amber until one arrives. From the 3rd to the 10th, if some came and then none for three days while a cell is still empty, a grey note names what is missing. Otherwise nothing is shown on the packs page and the health row is green. Settings (data, not code): `packs.road_from_day` 3 · `packs.road_to_day` 10 · `packs.road_quiet_days` 3. **Known limit:** it measures the shelf's fetch (05:40, 07:30), not the relay itself — a relay that dies after the month's first file has come is said in grey, not amber.
2. **One door, the owner's only (F-725).** `GET /finance/packs/api/text/<id>` answers the text the readers see of one shelf file — `pdftotext -layout` of the unlocked copy when the shelf opened it. Read-only, never cached, no link on any page. It exists so a statement is read in its own bytes before its reader is judged; the reader for Yes Bank's monthly e-mailed statement is built from it.
3. **The encrypted nightly takes three more things.** `/root/portal/clinic_users.json` (F-243, open since S209) as a file; `/root/finance/statements/packs/handover` (Shavez's hand-over photos, S472) and `/root/finance/spine/orders` (the Sanjeevni chat's word at its S285 close) as trees — one source each.

**Files** (all four verified before any is written; every anchor exactly once)

| file | from | to |
|---|---|---|
| `/root/finance/packs.py` | `6099b525` | `1bc18b26` |
| `/root/finance/packs.html` | `1349b37b` | `73ff8c2f` |
| `/root/finance/finance_app.py` | `56eb421b` | `47a83382` |
| `/root/state_backup/clinic_state_backup.py` | `3bf7caea` | `be57fe75` |

**The owner's line (the server; it carries its own pull)**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S476_STATEMENT_WATCH/install_S476_STATEMENT_WATCH.sh
```

It walks first (hermetic), measures the three new backup sources without copying them (no login store, or over 200 MB together, and nothing is installed), then places, restarts `clinic-finance` (about 8 seconds) and reads the road on the live database; a road that could not be read is a red. A red after placing puts all four files back. Pasted again on an installed box it repeats the after-placing checks. `DRY=1` in front of `bash` places nothing. The health row itself is behind the login: the assistant reads `/finance/health` in its browser after the install.

**Undo (one line)** — the three app files at any time:

```
\cp -p /root/finance/packs.py.bak_S476_6099b525 /root/finance/packs.py && \cp -p /root/finance/packs.html.bak_S476_1349b37b /root/finance/packs.html && \cp -p /root/finance/finance_app.py.bak_S476_56eb421b /root/finance/finance_app.py && systemctl restart clinic-finance
```

**The backup script is NOT undone by hand after a night has run with it.** Its state file then lists the new sources, and the vanished-source guard (exit 41) would refuse the next night if the old script no longer names them. Its backup is `/root/state_backup/clinic_state_backup.py.bak_S476_3bf7caea`; putting it back before 01:50 on the night of the install is safe, afterwards tell the assistant first.

**Not touched:** the readers, `stmt_shelf.py`, the tables' shape, the checklist page, every other health row, the backup's tar, key and slot files. No statement is re-read; nothing is sent anywhere.
