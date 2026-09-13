# SANJEEVNI SYSTEM BOOK — v1.1 · S243 close · 13-Sep-2026

*The one document that describes the Sanjeevni (pharmacy) system as it actually is. Written from the code matched to its live pins, the box's own listing of 12-Sep 23:53 IST, and the live pages read the same night. Twelve sections; each subsection names what lives there today — machines, files, tables, pages, jobs, people — and its state: **LIVE** (in use) · **FALLBACK** (kept switched on behind the live path) · **SHADOW** (runs, writes, feeds no screen) · **BUILT** (in the repository, not installed) · **PLANNED**. Supersedes `S212_SANJEEVNI_SYSTEM_MAP` (retracted) and folds in the lane table of `S229_SANJEEVNI_ARCHITECTURE_TAKE`. Section 12 is the residue register; section 11 the plan of record. Money figures and patient data are never in this book.*

---

## 1 · FOUNDATIONS

### 1.1 Machines and direction
Four machines, one rule: **the VPS reaches nothing; both PCs push to it.**

| machine | role | key paths |
|---|---|---|
| **Medical PC** (the counter, Windows, account `SET`) | Marg runs here; exports are captured and pushed | `D:\MARGERP\users\<login>\report\REPORT_n.XLS` (Marg's reused slots) · `D:\SendToClinic\` (agent, watcher, pusher, `_captured\` spool, `token.txt`) |
| **manojz** (the owner's PC) | the pull chain and the only complete raw archive — FALLBACK sender | `D:\Downloads\margsync\MargPull\` (router, gate, rescan, pushers) · `D:\Downloads\margsync\MargArchive\<TYPE>\<YYYY-MM>\` + `index.csv` · `D:\Downloads\margsync\_config\` (numbers, never in git) |
| **VPS** `followup.dr-manoj.in` (`srv1746119`) | every door, every table, every screen | `/root/finance/` (the apps + `finance.db`) · `/root/marg_ingest/` (collector, door, shadow) · `/root/portal/` (tiles, logins) |
| **Google** (`drmka.ortho`) | mirrors and backups | Drive `Clinic Data Archive\MargArchive` (mirror the server reads) · `MargBackups` · `FinanceDB_Backups` (nightly db) · `ToMedical\_kit` (agent self-update) · `FromMedical` (heartbeat) |

### 1.2 People, logins and roles
Portal logins (13 staff + owner): role `doctor` / `manager` / `staff`, mapped inside finance to **unit roles** in table `unit_role` on unit `medical`: **maker** (Darpan — files the day), **checker** (the owner alone — approves), **viewer**. Amir's page is gated on *any role on the medical unit* (D478). Tiles are convenience only — `tile_grants.json` shows, the route's own gate decides (S242 lesson). Who does what: **Amir** exports purchase reports, enters bills in Marg, does renames, raises claims · **Darpan** files the day, keeps the drawer, chases claims and corrections, does shelf counts · **counter staff** sell, take returns · **owner** approves, decides, locks.

### 1.3 Tokens and keys
One machine token, `FINANCE_MARG_TOKEN` (systemd drop-in on the VPS), opens seven token-only doors and is cached on both PCs. **Target (§11):** one token per sender, constant-time compare everywhere, one config file per machine holding hosts, Drive ids, key path and baseline date — today these are typed into six files.

### 1.4 Standing rules
Marg is never written to · the manojz pull chain stays as the fallback until the server path has earned it (D402) · no patient number at rest on the VPS (F-185; phones masked to last 4, names present in three tables — §6.5) · ingested-but-unaccepted is inert (D407) · dating happens at capture (D408) · junk is moved, never deleted, by the assistant; deleting is the owner's · nothing already live is rebuilt without the owner's OK; the manual path stays.

---

## 2 · CAPTURE AND TRANSPORT

### 2.1 The Marg report register
Marg writes every report into a reused slot file whose name carries no type and no date (D188); identity comes from **content signatures** (`signatures.json`, one copy per machine — §3.1). Types known: SALE_BILLWISE (DETAIL — the only one allowed to travel to the books; SUMMARY1 never exported), STOCK_CLOSING (DEFAULT/TOTALS), STOCK_EXPIRY, PURCHASE_SUPPLIERWISE / BILLWISE / ITEMWISE / BILLITEMWISE, SALE_RETURN, SALE_BOOK, STOCK_ITEM_LEDGER (carries PHI — never into the repo), SALT_WISE_ITEM_LIST, STOCK_VALUATION, ITEM_MASTER (avoided, D403/D404). Cadence rulings: supplier-wise month-end only; stock closing by 10:30 next morning (D463).

### 2.2 Capture on the medical PC — LIVE
`medical_agent.py` (S205.1) starts at power-on under `SET` (D480, proven 12-Sep), supervises `marg_watch.py` (event-driven capture into `D:\SendToClinic\_captured\`, md5-deduplicated), writes a heartbeat to Drive `FromMedical` every 300 s, backs Marg up hourly to Drive `MargBackups`, and self-updates from Drive `ToMedical\_kit` by an md5 allow-list. The counter reaches its own account with **Ctrl+Alt+Del → Switch user**; SET stays signed in behind it. Drive's letter on this machine moves between reboots — never hard-coded in anything a person opens (F-442).

### 2.3 The three legs
| leg | path | state |
|---|---|---|
| **A · direct push** | `marg_push.py` (a thread inside the watcher) → HTTPS `POST /finance/api/marg-file` → the one door | **LIVE** — 94 reports on 12-Sep, export-to-server in seconds, every row on the upload page "came by medical PC" |
| **B · pull** | manojz task *Marg pull from medical* every 10 min over Tailscale → `_spool` → router → archive → `_outbox` → `marg_gate send` → `POST /finance/api/marg-push` (sale) · `push_snapshot` / `push_expected` → `/finance/stock/api/snapshot` · `push_purchases` / `push_sale_bills` → `/finance/purchase/api/push` | **LIVE as the feed to the books; FALLBACK by ruling** |
| **C · Drive collector** | manojz robocopies the archive to Drive → `/root/marg_ingest/marg_ingest.py` every 5 min reads it with the service account → the one door | **SHADOW** (de-duplicates against leg A by md5; OFF file `/root/marg_ingest/OFF`) |
| **D · browser** | `/finance/clinic/marg/upload` (clinic maker/checker) → the one door | **LIVE, manual** |

### 2.4 The one door — LIVE
`/root/marg_ingest/marg_take.py` · `take(raw, name, source)`: md5 de-dup → router → verdict **TAKEN / ALREADY / REFUSED / BUSY** (flock) → sale reports parsed to PHI-free lines and the file deleted; other types kept in `/root/marg_ingest/archive/<TYPE>/<yyyy-mm>/`; every file rowed in `mi_file`. Wraps: `marg_door.py` (`/finance/api/marg-file` GET/POST with hmac compare; the upload page). **Gap:** refused files are deleted with no server-side rescan (§3.3–3.4).

### 2.5 Archives and the PHI rule
| archive | where | holds | rule |
|---|---|---|---|
| medical spool | `D:\SendToClinic\_captured\` | every capture | the edge archive by design; never pruned by a script |
| manojz archive | `MargArchive\` + `index.csv`, `_REFUSED\` | every routed export, raw | the only complete raw copy; PHI stays on the PC |
| Drive mirror | `Clinic Data Archive\MargArchive` | the same, unfiltered | **the one place raw sale exports with full mobiles sit outside the clinic** — to be filtered (§11) |
| VPS archive | `/root/marg_ingest/archive/` | non-sale types only | sale reports deleted after read (S186) |
| hand-named workbooks | `D:\Downloads\MARG REPORTS CLAUDE\`, two session kits | historical source | never routed |

---

## 3 · IDENTIFICATION

### 3.1 Router and signatures
`marg_router.py` (manojz `MargPull\`; vendored on the VPS in `/root/marg_ingest/` and `lib/`) classifies by content, deep-verifies via `marg_report.py`, archives, and marks `uploadable`. `signatures.json` is the same bytes on both machines today (S240) with **no mechanism keeping them equal** — target: single-sourced from the VPS. Repairs so far: F-351 (rescan), F-429 (ITEMWISE end row).

### 3.2 The file register — LIVE
`mi_file` (212 rows on 12-Sep: type, variant, verdict, kept, pc_verdict, agree) · `mi_run` (collector runs) · `mi_sale_line` (4,152 PHI-free sale lines keyed by file md5). Read by `marg_shadow` and the upload page's "last 20" list; **feeds no book yet** (§6.2).

### 3.3 Verification and refusal
Six refusal grounds at `/finance/api/marg-push`; the door's REFUSED verdict at `marg_take`. On manojz a refused file goes to `_REFUSED\`; on the VPS it is deleted and its md5 remembered.

### 3.4 Rescan — manojz only
`marg_rescan.py --if-signatures-changed --apply` re-files quarantine after a signature fix. **No server equivalent** — a `refused/` folder and a rescan on the VPS are §11 items.

### 3.5 Pipeline status and the export watch — LIVE
`pipeline_status.py` (end of every pull) → `POST /finance/api/pipeline-status` → table `pipeline_status` → page `/finance/pipeline` ("medical PC → manojz → this server → matcher", heartbeat, last 7 days, pending imports). `export_watch.py` (cron 23:40 today / 10:45 yesterday with ntfy) answers "did Amir export today" against his punch (machine id 101) → table `export_watch`. The "no export today" alarm on the server side is PLANNED (D467 phase 2c).

---

## 4 · THE ITEM SPINE

### 4.1 Items, names, facts — LIVE
`marg_spine.py` (S229; run by `spine_cadence.py` every 30 min 09–23 with `--if-changed`, nightly 23:50): one row per product in `marg_item` (374), every spelling in `marg_item_name` (424), facts in `marg_item_fact` (1,132 — salt, pack, MRP, from `purchase_salt_marg`, `stock_count_item`, `stock_rate`). **Only Marg's own export may create an item**; a computed name that cannot be resolved raises a task, never a row.

### 4.2 Unresolved names and tasks
`marg_name_unresolved` (10) · `marg_task` (42: derived_name, question, ambiguous). Amir's rename list (22 open, on him) and the two merges awaiting the owner's word (`DISPO SYRINGE NIPRO`/`NIPRO 3 ML DISPO SYR`, `PARI CR 12.5`/`PARI 12.5`).

### 4.3 Cadence and drift
`marg_spine_run` (10) · `marg_spine_drift` (9) · `spine_drift_latest.txt`. Drift = a name or fact that moved between runs; read on the spine page and in the health legs.

### 4.4 Renames and merges
Amir's salt work list `/finance/purchase/page/salts` (60 of 113 ticked; Marg confirms against a SALT WISE list of 04-Sep — a fresh export settles 38 rows, F-441) and his downloadable sheet `/finance/amir/salts` (matched by row id, never by name). Merges in Marg: owner's word only.

### 4.5 Discount rulings
`marg_item_discount` (93 items, T1 rulings from S236; HYLASTO approved and never re-raised, D464) · `marg_item_discount_history` · `marg_discount_run`. Feeds attribution (§6.3).

---

## 5 · PURCHASE LANE — LIVE

### 5.1 Exports → bills → lines
`push_purchases.py` (manojz; nightly 22:30 and every 30 min) sends every archived PURCHASE_* export → `POST /finance/purchase/api/push` → `purchase_export` (26, md5-keyed, supersede-by-period), `purchase_bill` (497), `purchase_line` (1,302), `purchase_audit`. Marg's purchase serial is in no export (F-436, parked).

### 5.2 Months — provisional and final
`purchase_month` (0 — no month finalised yet); the hub shows Apr–Sep 2026 all PROVISIONAL with bill counts; finalise/reopen at `/finance/purchase/api/finalise|reopen`.

### 5.3 Vendors and the phone book
`purchase_vendor_contact` (38) — `/finance/purchase/page/book`; numbers live in `_config\stockist_phones.json` on manojz, never in git.

### 5.4 Scan links
`purchase_scan_link` (0) — `/finance/purchase/page/scans`; 496 Marg bills with no scan.

### 5.5 Salts and new items
`purchase_salt_marg` (373), `purchase_salt_name` (196), `purchase_salt_task` (125), `purchase_new_item` (5) — the salts page, Amir's sheet, `/purchase/api/salt_task`.

### 5.6 Feed health and the hub
`purchase_feed` (10) — "Last purchase data received 11-Sep 14:31 · manojz is awake · last Marg pull 22:30" on `/finance/purchase/page/hub`. **Known 404:** `/finance/purchase/` (the bare prefix) — fixed in kit `S243_SCREEN_FIXES`.

---

## 6 · SALE AND MONEY LANE

### 6.1 Bill money rows — LIVE
`push_sale_bills.py` (manojz, every 30 min) sends VERIFIED SALE_BILLWISE money rows (gross/discount/net/cash) → `/finance/purchase/api/push` type `SALE_BILL` → `sale_bill` (648), `sale_bill_push` (34). Rung 1 (S237/S240), backfilled 31 exports.

### 6.2 Item lines — TWO STORES, target ONE
| store | filled by | read by | rows |
|---|---|---|---|
| `sale_line_item` | `/finance/api/marg-push` → checker taps **Apply** → `finance_returns.load_lines` | the spine, attribution, returns audit, stock arithmetic | 18,376 |
| `mi_sale_line` | the one door (`marg_take`, legs A/C/D) | the shadow only | 4,152 |
Also `sale_item` (3,618, day-level via the ingest adapter) and `marg_push_staging` (31, the pending Apply queue — 3 pending on 12-Sep). **Target (§11 3e):** the spine and attribution read the one-door store behind a flag; shadow-compare; switch; retire the second parser's store.

### 6.3 Attribution and discounts — LIVE
`sale_attribution.py` (cron every 30 min 09–23, 23:55) attributes bill discount to lines using T1 rulings → `sale_line_discount` (2,796), `sale_bill_attrib` (648), `sale_attrib_run` (6). Rung 2; gross → net side by side (Rung 3) waits on the owner's word.

### 6.4 Cash ↔ UPI corrections
`marg_correction` (7) · Darpan's page `/finance/darpan/corrections` ("2026-09: 26 pending · 0 corrected") · `bank_match.py` (09:45, every 15 min 10–12, final 12:00) against `upi_txn` (1,244) → `upi_match` (50) · the correction checklist `/finance/marg-worklist`. Rule: corrections are done in Marg by Darpan; the page tracks, never edits.

### 6.5 The boundary with the clinic books
Sale reports reach the **day books** (`day_entry`, `day_line`, `recon_exception`, `ingest_batch`) only through the checker's Apply; the day is then filed by the maker and approved by the checker (`/finance/review`). Patient references: `patient_ref` (7,909; phone last 4 only, **names present**), `patient_visit` (2,037), `marg_push_staging.parsed_json` (names). The returns desk shows names in the clear to the counter — masking is a §11 item.

---

## 7 · STOCK LANE — LIVE

### 7.1 Marg's closing snapshot
`push_snapshot.py` (manojz, on capture every 15 min) → `POST /finance/stock/api/snapshot` (source `push_snapshot`, as-on = Marg's date) → `stock_snapshot` (4,489), `stock_rate` (194), `stock_feed` (append, 15,689). "Marg closing stock as on 12-09-2026, processed 23:01, 373 items".

### 7.2 The computed expected figure
`push_expected.py` (manojz, on capture and nightly; baseline 03-09-2026 + purchases − sales; source `push_expected …`, as-on = **last sale date**) → the **same door and the same table**. Server-side twin: `marg_shadow.py` (23:20, 06:20) computes the same over server data → `sh_feed` (12), `sh_diff` (0), `sh_run` (3): **373 compared, 370 agree, 3 differ** — the witness for retiring the PC job.

### 7.3 Drift and reconcile — the S243 defect
`stock_snapshot` is keyed on (as_on, item) with no source; when Marg's figure and the computed figure land for the same date, the later one silently becomes "Marg's" and `reconcile()` may auto-close a real difference. Every reader of the computed figure goes through `stock_feed` (verified, 11 readers). **Fix built and walked:** kit `S243_SNAPSHOT_SOURCE` — computed rows go to a new `stock_expected` table, `stock_snapshot` holds Marg only, `stock_feed` unchanged, a conservative migration for the past rows. Pages: `/finance/stock/page/drift`, `/page/now`.

### 7.4 The count cycle
readiness (`stock_check_readiness`, the S240 gate: physical | Marg | ours must agree) → pads (`padwriter`/`padreader`, `stock_count_pad_file`, `/page/pad`) → count (`stock_count` 1, `stock_count_item` 373) → diffs (`stock_diff` 207, `stock_diff_lane` 39, `stock_diff_answer`, `stock_diff_decision` 35) → decisions (`/page/desk`, "Card 1 of 100") → close (`stock_count_close`). Count #1 of 06-Sep-2026: 174 lines still open, 33 decided. No stock screen on a phone until the three agree (S228).

### 7.5 Loss desk and recovery
`/finance/stock/page/loss` · `stock_loss_tick / share / recovery` (0) · `stock_finding` (1) · Amir's board `/page/amir` · report `/page/report`; F-379 (₹ short on orthotics) recorded, unexplained items recorded as unexplained (F-434).

### 7.6 Vouchers and write-offs
`stock_voucher` (0) · rule R6: every expiry removal is a Marg voucher, never an in-place edit · one tap pending (VINTAZ P 4500 INJ) at `/finance/stock/page/desk?count=1`. The voucher engine (D388/D397) is parked on the owner's "share it".

---

## 8 · RETURNS AND EXPIRY

### 8.1 Vaapsi desk — LIVE (Hindi, counter)
`returns_desk.py` · `/finance/returns/desk/` · three steps (patient / medicines / slip) · `return_visit`, `return_line` (0 — slips have not started), `jaankari_answer` (2). Roles viewer/maker/checker on medical.

### 8.2 Jaankari — questions to the counter
"name does not match (9)" and "count needed (10)" queues on the desk; answers feed the returns audit.

### 8.3 Return intent and flags
`finance_intent.py` (01:30) → `intent_signal` (210) · `finance_returns_audit.py` / `finance_returns_escalate.py` · `pret*` tables (S207 credit-note chain) · exceptions `return_flagged` ("NEVER BOUGHT", "DISCOUNTED RETURN") on the review page.

### 8.4 Near-expiry and credit notes
Window 3 months (D409); credit note due by the 7th (R5); STOCK_EXPIRY exports archive-only today — a near-expiry screen is a §11 (Phase D) item.

---

## 9 · ORDERING — LIVE

### 9.1 Short list by stockist
`/finance/purchase/page/staff` — "Stock as on 12-09-2026", 19 suppliers + "no supplier on record", item · stock now · order qty.

### 9.2 Orders and PDFs
`purchase_order`, `purchase_order_line` (0 open) · `/finance/purchase/page/orders` · `/order/<id>/pdf`.

### 9.3 Sent, chased, arrived
"Send on WhatsApp / Call" from the page; arrival closes against the purchase export (S225_ARRIVAL). Chasing is Darpan's (claims — §10.2).

---

## 10 · PEOPLE AND SCREENS

### 10.1 Amir's day — LIVE
`/finance/amir` → `/finance/amir/step/<n>` (seven steps, Hinglish, phone-first, no JavaScript) · `/finance/amir/day` (the owner's English view) · `/finance/amir/salts` (+ `.xlsx`). Tables `amir_day` (1), `amir_step` (1), `amir_bill_disposition` (0), `amir_claim` (0), `amir_salt_upload` (0). He is never asked whether a report arrived; he types no bill number; a bill with no answer comes back; a half-done day stays OPEN; he raises, never chases. One tile only (D483); five parked.

### 10.2 Darpan's queue
Today: `/finance/darpan` (day card, drawer, cash position), `/finance/darpan/corrections`, the stock recheck cards sent from the desk. **Next build:** the claim queue `open → contacted → settled` (settled names an outcome; self-closes on a matching purchase return; ages to the top at 14 days, D471) — `amir_claim` is empty, so it opens quiet.

### 10.3 Owner: hub, review, health, pipeline
`/finance/approvals` (the hub: cards for today, counter, bank MPR, returns, Marg, cash position, drawer, month, orthotics, review queue, staff, open differences) · `/finance/review` = `/finance/` (approve days, month close, exceptions) · `/finance/health` (what needs you / worth knowing / running normally; the freshness legs) · `/finance/pipeline`. **Known bounce:** `/finance/daily` sends the doctor to the portal because it is the maker's entry form — kit `S243_SCREEN_FIXES` sends a checker to `/finance/review` instead.

### 10.4 Reception and counter
Docterz daily collection `/finance/clinic/register` (reception: Shavez, Shivani, Alisha — D481; opens on today, D482) · the drawer count is optional by design (D484) · the returns desk (counter). Clinic pages are the clinic's, not Sanjeevni's — they share the process and the database today (§11 Phase 4–5).

### 10.5 Tiles, grants and what each login sees
`portal.py` `_visible_sections` decides from role + `tile_grants.json` (v12). Money & Accounts tiles: Daily Sale · Vaapsi Desk · Stock Check · Marg Purchases · Order Medicines · Amir ka kaam · Corrections · Docterz Revenue · Docterz daily collection · Sanjeevni Medicos · Clinic.

---

## 11 · WATCH, BACKUP, RECOVER — and the plan of record

### 11.1 Watch
`export_watch` (§3.5) · `freshness.py` 08:05 with `freshness_legs.json` (26+ legs incl. three S240 Sanjeevni legs) → `/finance/health` · `clinic_watchdog.py` every 5 min guards 11 units — **`clinic-finance` is not among them**; kit `S243_WATCHDOG_FINANCE` adds it with `staff-register` and `assetapp` · ntfy is the notification layer (D425) · `finance_heal.py` every 30 min 08–21.

### 11.2 Backup
`finance_backup.sh` 01:05 → `/root/backups/finance/` (daily + monthly, pruned) · `finance_drive_backup.py` 01:40 → Drive `finance_nightly.db.gz` · `clinic_state_backup.py` 01:50 → encrypted state bundle to Drive (console.db, assets.db, punches, staff registers; **not the finance code**) · `sheets_pull.py` 01:45 · `gas_export.py` weekly · hourly Marg backup from the medical PC. **Gap:** the live code has no off-box copy — kit `S243_CODE_BUNDLE` adds `code_nightly.tar.gz` at 01:35 beside the db (one owner step: create the slot file once from the owner's Drive).

### 11.3 Recover
`verify_restore.py` — the restore drill (state `finance_restore_verify.state.json`, verified 12-Sep 01:05) · every kit installer backs up to `.bak_S###_<pin>` and rolls back byte-identical on failure · `/root/_retired/S243_2026-09-13_0007/UNDO.sh` restores the retired residue.

### 11.4 The plan of record (S243) — one table, one status each
| # | item | state |
|---|---|---|
| P1 | this book + the estate register | **DONE** (records) |
| P2 | residue out of `/root` and `/root/finance` — 495 moved, undo kept | **DONE 13-Sep 00:07** |
| K1 | `clinic-finance`, `staff-register`, `assetapp` on the watchdog | **LIVE 13-Sep** (35e40626) |
| K2 | nightly code bundle to Drive (01:35); live code captured byte-exact (private zip + SSD) | **LIVE 13-Sep** (v1.2; F-456 fixed) |
| K3 | `stock_snapshot` Marg-only; computed → `stock_expected`; 1,119 rows restored | **LIVE 13-Sep** (D490) |
| K4 | `/finance/purchase/` redirect · `/finance/daily` checker → review | **LIVE 13-Sep** (D486) |
| 3a | one `sanjeevni.conf` per machine (hosts, Drive ids, key path, baseline) | next |
| 3b | per-sender tokens, constant-time compare | next |
| 3d | `refused/` kept + server-side rescan | next |
| 3e | spine + attribution read the one-door store behind a flag → switch → retire second store | after seven clean shadow nights |
| 3f | retire manojz senders one at a time (3 clean days each; pull last; Docterz pickup stays by ruling) | after 3e |
| 3g | manojz live tools out of the git checkout into `D:\Downloads\margsync\bin\` | with 3a |
| 3h | OFF switch for every job (pusher, spine, attribution, export watch) | with 3a |
| 3i | filter full mobiles out of the Drive archive mirror (§2.5) | with 3a |
| 3j | full phone numbers on the returns desk (D493 — ruling reversed the masking) | **LIVE** where the master has the number; phase 2 = write at Apply |
| D1 | Darpan's day `/finance/darpan/kal` (D491) **LIVE 13-Sep**; the claim tab (D471) | next |
| P4 | Sanjeevni in its own process (`sanjeevni` service; sections 2–10; same URLs; one lane at a time) | after Phase 3 |
| P5 | its own database (`sanjeevni.db`), attached read-only from the clinic side | optional, last |
| A1 | sale reports apply on arrival (D488) | **LIVE 13-Sep** |
| A2 | salt list refreshes itself (D489) | **LIVE 13-Sep** |
| A3 | Shavez's "Aaj ki reports" · Amir's salt prompt + visit summary · "Kal ka hisaab" tile (D495) | **LIVE 13-Sep** |
| A4 | CA: corrections read-only; monthly accountant report (D492) | **LIVE 13-Sep** |
| — | Rung 3 (gross → net) · vouchers (D388/D397) · parked tiles · merges · F-436 serial | owner's word |

---

## 12 · RESIDUE AND RETIREMENT REGISTER

| what | where | state |
|---|---|---|
| 495 superseded files (≈60 `finance_app.py.bak_*`, ≈50 `finance.db.bak_*`, patchers, walks, selftests, S180/S195 install residue, one-off scripts) | `/root/_retired/S243_2026-09-13_0007/` | **retired 13-Sep**; the `finance_app.py.bak_*` chain is the only history of the live file — never delete until K2 has put the live file in the repository |
| 12 items HELD by a live reference (`patch_finance_app_darpan.py`, `seed_desk_roles.py`, `medical_*.csv`, `S195_A123B`, …) | `/root`, `/root/finance` | left in place; re-check after K2 |
| `_quarantine_S232_F368_…/` (six stale `.env` copies) | `/root` | held until the WABA token rotation completes |
| six stale `.env.bak*` / `.env.preswap*` | `/root/wa/` | secrets inside — retire on the owner's word |
| migration tables `s184_*`, `s184c2_*`, `s186_*` (7 tables, 2,335 rows) · 37 empty tables | `finance.db` | candidates, never verdicts — after 3e |
| `sale_line_item` beside `mi_sale_line` · `stock_feed` beside `sh_feed` · `MargArchive` beside `/root/marg_ingest/archive` | VPS | structural duplicates — retire by evidence in 3e/3f |
| seven manojz scheduled Marg jobs | manojz Task Scheduler | FALLBACK; retire one at a time in 3f |
| ~300 `marg_watch.py.before_*` · `_captured` spool | medical `D:\SendToClinic\` | clutter / edge archive; deletion is the owner's |
| unmasked `marg_report.py` (two PC copies) vs masked `eeab5605` | manojz, medical | replace with the next PC kit |
| `deploy_kits/S205_LIVE_TOOLS/medical/medical_agent.py` stale (S203.3 vs live S205.1) · `VPS_Push_UPI.gs` duplicate · `signatures.json` in nine kits · S179-era `finance/finance_app.py`, `margpull/*` at repo top level | repository | correct with the next builds; prune duplicates, keep lineage |
| `clinic_upi_check` cron (09:40) never installed · `push_purchases.py` pinned at a VPS path · `finance_app.py` pin row reads `81db4854` while the record says `72bc8323` since S241 | records | correct at the S243 close |

---
## 13 · THE OWNER'S RULINGS OF 13-Sep-2026 (his words are the spec)

- **Machines.** SET is his RDP login on the medical PC, used mainly to run Marg reports himself; Darpan and Amir use the staff account. All clinic PCs are off at close and on in the morning — the medical PC after 8–8:30, sometimes 10–10:30. *No server job may assume the medical PC is up before mid-morning.*
- **Darpan.** Generates sales and sale returns only; hands the day's cash to the owner or Dr Bhawna = printout − home/procedure medicines − POS online sum, noted in a physical notebook. His screen follows that exactly: prefilled morning form, two inputs, differences shown, five reasons, server-checked. ₹50 day line · ₹2,000 month cap · no kharcha · excess = his calculation error, owed back to him · a received tap by the recipient, later allowed (the physical copy is the proof) · flagged returns asked on the same screen · **no deterrent notice — "the data surfacing there is the deterrent"** · the owner a passive viewer with a filtered queue; the system is the main checker.
- **Amir.** A distinct role (bills, renames, supplier payments in Marg), owner as backup; after visit-day work the system asks him for the salt-wise export and keeps it raised until it arrives; the owner gets a collapsed "Amir's visit — what was done".
- **Shavez.** Marg report generator, a morning job before any sales and on Amir's days: "Aaj ki reports" confirms each arrival and shows what is pending or refused.
- **CA ruling.** No cash↔UPI corrections in Marg — they reopen bills to unauthorised edits; the system keeps the record as a monthly accountant report.
- **Numbers and data.** Full phone numbers everywhere on staff desks including the returns desk; the Drive mirror keeps full PHI ("required for many correlation jobs, safe there"); the repository stays number-free (F-185).
- **Machines and moves.** Everything PC-side moves to the VPS if technically better; the vendor phone book lives at the VPS; the spine is Claude's call; renames delegated to Amir; discount rulings flagged for the owner to edit in Marg.
- **Mandate.** *"I have to depend upon you and your skills. Whatever you think, say first and best to arrange everything properly and everything remains stable and working."*

---
*SANJEEVNI_SYSTEM_BOOK_v1_1_S243close · 13-Sep-2026 · v1 + §13 and the §11.4 statuses of the S243 close · written from evidence · the manifest decides what is current.*
