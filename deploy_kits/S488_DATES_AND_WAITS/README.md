# S488_DATES_AND_WAITS — dates compared as dates; a waiting card says since when and for what

Kit S488 · faults **F-753, F-754** · no D-number · brief `claude_code_briefs/S488_DATES_AND_WAITS.md` (Sanjeevni chat, session 296, 06-Oct-2026).

## What and why

- **Part A (F-753 / F-754) — a date is compared as a date.** Marg's `dd-mm-yyyy` sorted as text puts 30-09 after 04-10, so *Stock now*
  read 30-09-2026 all October; `readiness` compared a dd-mm-yyyy day with an ISO one; `filed_vouchers` compared `entered_on` with ISO
  days and never counted a filed voucher. Every sort / MAX / BETWEEN named in the brief now goes through a key. The stored values are
  not rewritten. `readiness`'s "stock ahead of purchases" warning now follows the purchase exports' reach (`MAX(period_to)` in force),
  so a Sunday with no bill is not "behind"; on a day no purchase export comes, the warning stands (true by the rule).
  `filed_vouchers` reads the append-only log by its newest row per batch (counted only while it carries a voucher number), its day
  as a date. **Once, at install, `s454_shelf_gap` is re-judged** (`rejudge_s488.py`): a flag the filed vouchers explain is cleared, and a
  carried copy of a cleared flag with it. Idempotent.
- **Part B — the waiting card.** `stock_app._s446_proof` (state `export` only) adds `since`, `why` (no_closing · no_figure · pur_behind ·
  no_before · rebased), `closing_day`, `closing_at` (the earliest Marg push after the vouchers). Amir's card, his day's two lines and
  the voucher board's line say what is awaited, since when, and whose it is (Roman Hindi); the owner's lines say the same in English
  and warn once a proof has waited `amir.proof_wait_hours` (48). A refused report stays on Needs-you `amir.refused_keep_hours` (36) —
  past midnight — and every unrecognised file is one line.
- **Part C — the owner's own Marg lists are his duties.** `DUTY_MAP.json` v7 → v8: `manoj.salt_list`, `manoj.item_lists` (no door: the
  work is done in Marg; a finding by CLAUDE.md, stated in DUTY_MAP.md). Limits are setting rows (`owner.salt_list_days` 8,
  `owner.item_lists_days` 35), also read by `reports_tile.owner_lists` (guarded). **The map is read from the server's clone, so v8 is
  live at the `git pull` — before the installer runs and whether or not it succeeds.** That is safe by construction: both statements
  read only `mi_file` and `setting` and default without the setting rows. No staff list changes (walk §5).
- **Part D — a wrongly learnt item name can be struck.** `item_check`: `s454_item_name_struck`; `strike` / `unstrike` / `struck`;
  `learn` never learns a struck pair again. `purchase_app` (the Items check block only): **Wrong** on each learnt name, a collapsed
  *Struck: N* with **Put back**, `POST /finance/purchase/api/items/strike` (the doctor only). The kit strikes nothing.
- **Part E — the medical PC's `marg_watch.py`: PACKED, NOT PLACED.** A refused text's body reaches Drive only when `_may_leave` admits
  it (kinds PURCHASE, SALT, CATEGORY, ITEMS, VALUATION, EXPIRY, STOCK; no person word in the head; no mobile-like run outside the shop's
  Phone line and Marg's footer); every `.why.txt` on Drive is the safe two lines; Drive's folder is swept. `deliver_S488.ps1` is run
  only after the chat has read the file — never by Claude Code.
- **Part F** — `marg_ingest.py` 828c4dad read only; its pin is confirmed by the installer (S482 closed both lines).

## Pins (server, `/root/finance`) — FROM → TO

| file | FROM | TO |
|---|---|---|
| stock_app.py | 7e159de7 | cc06dac9e3ab60a85d76e2409815b5af |
| darpan_app.py | 5bfabbec | a55ecbed4bbe1230b24565b4185b8755 |
| owner_sheets.py (the parent's — one statement) | 8b1aea31 | baa7ccc405a78bdbbd8b2485c00dc9a0 |
| stock_watch.py (one line, as it was) | 6d4d660f | 4fc0f6017825975e75ebacfdc2f122d2 |
| shelf_figure.py | 23c34ebb | 0d836de54672f3e624fcc763311ab22c |
| amir_day.py | 709f20c1 | 08d058a765278d6e119e70f8f0adeedd |
| item_check.py | 9000e376 | 6f3faf899df5120af6ee51167604d457 |
| purchase_app.py (the Items check block only) | 254b7793 | c29050c18795a059e3cfbfae252efc21 |
| reports_tile.py | ea15aacb | 6f7cf490c949495e3e714b7dd688b7af |
| claude_code_briefs/DUTY_MAP.json (v7 → v8) | 1595520d | f27423b61e50857875bb8f7ba4e5c57c (= this kit's DUTY_MAP.json) |
| claude_code_briefs/DUTY_MAP.md | d50a6f4e | cb78fe54f4d09fb4733dc1bac268cf9e |
| medical PC `D:\SendToClinic\marg_watch.py` (packed only) | 58b54f37 | 0a78ae15be60d8a0293b96ecfa38f35b |
| Drive `ToMedical\_kit\KIT_MANIFEST.txt` (packed only; CRLF on Drive) | ea2b437a | a1bf114fd9e6940befe74592ffa78322 (this folder's LF copy 59b31641) |

`finance.db`: four `setting` rows (INSERT OR IGNORE: `amir.proof_wait_hours` 48, `amir.refused_keep_hours` 36, `owner.salt_list_days` 8,
`owner.item_lists_days` 35); the table `s454_item_name_struck`; `s454_shelf_gap` re-judged once. One backup by the backup API first
(`finance.db.bak_S488_<stamp>`); `<file>.bak_S488_<from8>` beside each of the nine files. Restarts `clinic-finance` once.

The owner's settings card (`porders_s454.py`, parked by S486) lists only the keys it knows; the four new rows join it when that file is
next opened.

## Not touched (md5 before = after, or the install is undone)

`finance_app.py`, `/root/portal/portal.py`, `tile_grants.json`, `aaj_kaam.py`, `aaj_duties.json`, `owner_console.py`, the twelve files
S486 parked (`order_rules.py`, `porders_s454.py`, `porders.py`, `porders.html`, `darpan_kal.py`, `darpan_kal.html`, `order_sheet.py`,
`order_sheet_pdf.py`, `finance_approvals.html`, `spine/spine_read.py`, `spine/order_rehearsal.py`, `spine/selftest_spine.py`),
`/root/marg_ingest/marg_ingest.py`, the crontab.

## Files

| file | what |
|---|---|
| `install_S488_DATES_AND_WAITS.sh` | gates → FROM pins → build → compile on both pythons → walk + measures on scratch copies → (DRY=1 stops) → lock → backups → place → md5 read-back → data → restart → healthz → read-back → nothing else moved; restore on red |
| `make_s488.py` | the anchored patcher of the nine server files (each anchor exactly once) |
| `PINS.sh` | the nine TO pins |
| `walk_s488.py` | the walk, sections 1–7 of the brief, each with its control on the OLD files; staff-eye signed in through a scratch portal |
| `rejudge_s488.py` | the once-only re-judge of `s454_shelf_gap`; the shelf-figure measure; the measure of the flags that stay |
| `DUTY_MAP.json` | the v8 map the walk and the installer ran with (= claude_code_briefs/DUTY_MAP.json) |
| `marg_watch.py`, `KIT_MANIFEST.txt`, `deliver_S488.ps1` | Part E, packed for the medical PC (not run) |
| `make_marg_watch_s488.py`, `make_manifest_s488.py` | Part E's anchored patchers (they rebuild the two files byte for byte from the S480 kit) |
| `control_s488e.py`, `fdiff_s488e.py` | Part E's negative control (the walk §7.6 cases on the OLD file) and its function-level diff |

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S488_DATES_AND_WAITS/install_S488_DATES_AND_WAITS.sh
```

(Run once already from a byte-identical copy of this folder; run from the repository it answers ALREADY INSTALLED.)
