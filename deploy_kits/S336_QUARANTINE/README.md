# S336_QUARANTINE — refused files kept by the one door, and a server-side rescan

**Project: Sanjeevni — Pharmacy & Marg · session S274 · 20-Sep-2026.** D567 **item 3**, Book v1.5 §11.4 **3d** ("`refused/` kept + server-side rescan — still next; the daily summary report is the first case that would use it").

## What changes

**The door** (`/root/marg_ingest/marg_take.py`, S240 → this kit, anchored edits, everything else byte-identical): a REFUSED or UNKNOWN export is no longer deleted on sight. It stays where the router already put it — `archive/_REFUSED/` or `archive/_UNKNOWN/`, beside the `.txt` the router writes — **only when `phi_scan.clean()` finds no person's detail in it**. Otherwise it is deleted exactly as before (S186), and the sidecar gains one line saying `kept: yes/no -- why`. `mi_file.kept` = 1 for a kept quarantine file. Source `rescan` is added for re-taken files.

**`phi_scan.py`** (NEW) — the one test. A file may rest here only if: it is a spreadsheet (never a PDF), it opens and is not empty, **no cell carries a 10-digit run starting 6–9** (text or numeric), and its first 25 rows carry none of SALE · SALES · PATIENT(S) · MOBILE · LEDGER · PRESCRIB… · DOCTOR · CUSTOMER · ADDRESS. Two lines are the report's own furniture and are exempt from the mobile rule: the shop header `Phone : …` (rows 1–8) and Marg's advertisement in the last 3 rows (`MARG ERP NANO for Chemist … Call`, `Digital Purchase | … | Call MARG …`). `PARTY` is Marg's word for a supplier on every purchase report, so it is deliberately not a person word.

**Measured on the whole real archive on manojz, 20-Sep (read-only):** every kept type CLEAN — STOCK_CLOSING 32/32 · SALT_WISE 7/7 · ITEM_MASTER 4/4 · CATEGORY 2/2 · PURCHASE_BILLWISE 18/18 · PURCHASE_ITEMWISE 15/15 · BILLITEMWISE 4/4 · STOCK_EXPIRY 9/9 · STOCK_VALUATION 2/2 · SUPPLIERWISE 5/5 (98/98); every PHI type PHI — SALE_BILLWISE 38/38 · SALE_RETURN 3/3 · SALE_BOOK 1/1 · STOCK_ITEM_LEDGER 1/1 · SALE_DAILY_PRINT 1/1 (44/44). The real quarantine: **7 of 8 would be kept** (the consolidated purchase book Amir exported on 17-Sep among them — contract §5's first case), 1 not (a SALES-titled sheet). Before the two furniture rules the same scan refused 96 of 98 kept exports — the shop's own phone and Marg's helpline are in every file.

**`marg_rescan.py`** — manojz's S229 tool, vendored **byte-identical** (`c6a28fc6`). **`marg_rescan_vps.py`** (NEW) — runs it under the collector's lock against `/root/marg_ingest/archive` with the box's own `signatures.json` (`--if-signatures-changed`, marker `_signatures_seen.md5` in the archive), then **re-takes every rescued file through `marg_take.take`** (source `rescan`; the old `mi_file` row is held in memory and put back if the door does not answer TAKEN), and leaves `archive/_rescued/` with sidecars only. `--status` prints one line (kept · sidecars · rescued records · signatures md5 · last judged · changed?).

**Crontab:** one root line, `25 6 * * * … marg_rescan_vps.py --if-signatures-changed --apply … # S336_QUARANTINE` — **declared to the parent**. Backup `crontab.bak_S336_<stamp>`. OFF switch: the collector's `/root/marg_ingest/OFF`.

**Restart:** `clinic-finance` (marg_door imports marg_take at start). No table, no `finance_app.py`, no portal, no screen.

## Proof

- `selftest_s336.py` **21/21** on the PC against a scratch copy of the live `marg_ingest` (the bundle's), a scratch archive and db, with synthetic Marg-shaped `.xlsx` written by the stdlib: an unrecognised report is kept (`kept=1`, in `_UNKNOWN`, sidecar `kept: yes`); the same with a mobile in a text cell, and in a numeric cell, is not kept (`kept: no -- a mobile-shaped number at row N`); a sale-titled sheet with a strange layout is refused and not kept; the same bytes answer ALREADY; a rescan with unchanged signatures does nothing; `--status` counts; **a signature added → the rescan rescues the kept file into its type folder, the door re-takes it (mi_file VERIFIED, kept=1), quarantine empty, `_rescued/` sidecar only, the marker remembered**; a real item master still verifies and is kept as before; made to fail on purpose: a PATIENT-titled sheet, a PDF, an empty sheet. The installer runs the same selftest on the box against a scratch copy of the live folder before placing anything.
- Installer rehearsed on a fake root on the PC: install · rerun ALREADY · wrong live bytes refused · forced-red restore (door back to 4bcf0243, new files removed, crontab restored).

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S336_QUARANTINE/install_S336_QUARANTINE.sh
```

## Said plainly

- A refused **sale** report is still deleted (its lines are what the door keeps); the complete raw copy is where it always was, on manojz in `MargArchive\_REFUSED\` and its Drive mirror.
- The rescan on the VPS judges with the **VPS** `signatures.json` (`b2dcb211`), which still lacks the CATEGORY_WISE_ITEM_LIST signature manojz carries (`a987a08e`, S270) — the known divergence. The next kit that syncs the two files will be the first real rescue on the box.
