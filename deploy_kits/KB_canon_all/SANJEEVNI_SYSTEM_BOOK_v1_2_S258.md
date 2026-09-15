# SANJEEVNI SYSTEM BOOK — v1.2 · S258 · 15-Sep-2026

*The one document that describes the Sanjeevni (pharmacy) system as it actually is. **Supersedes
`SANJEEVNI_SYSTEM_BOOK_v1_1_S243close.md` in full** — this is a complete document, never a delta
(D202/D247). Twelve sections plus the owner's rulings; each subsection names what lives there today —
machines, files, tables, pages, jobs, people — and its state: **LIVE** (in use) · **FALLBACK** (kept
switched on behind the live path) · **SHADOW** (runs, writes, feeds no screen) · **BUILT** (in the
repository, not installed) · **PLANNED**. Money figures and patient data are never in this book.*

**How v1.2 was checked.** v1.1 was written 13-Sep from the box's own listing of 12-Sep 23:53. Four
closes ran after it — S244, S255, S256, S257 — and none checked it against the running system, which
put the **stale** count at **4, over the line of 3**. This revision closes that. Three sources, each
named at the row it supports:

- **[live]** — read from the running pages on `followup.dr-manoj.in` on **15-Sep-2026, ~06:00 IST**,
  through the assistant's browser.
- **[code]** — read from **the box's own nightly bundle**, `code_nightly.tar.gz`, built on
  `srv1746119.hstgr.cloud` at **01:35:03 on 15-Sep-2026**, brought within reach by kit S272 and
  verified three ways: its md5 matches what Drive's own metadata declares, its internal
  `MANIFEST.md5` verifies **218 of 218 rows**, and `/root/finance/purchase_app.py` inside it is
  `3535dc978d4ec53846368c8772347a50` — **byte-identical to the reconstruction this session built
  independently** by replaying the eight patchers over the last whole copy. Two methods, one answer.
- **[pins]** — **109 of the Register's live VPS pins were held against the box's own bytes. 109
  matched. Zero mismatched.** The first time the Register has been checked against the live machine
  in bulk rather than file by file.
- **[record]** — from a kit's own README and the close that installed it, where no live surface shows
  it. **A [record] row is not a live read and does not claim to be** (F-443).

**⚠ One Phase 0 instruction is now wrong and is corrected here.** `START_HERE_PROMPT_v8` says *"the
assistant's browser is stuck in the F-242 login loop … it needs a fresh profile or my sign-in before
any live page can be read."* **It is not.** Every page below was read on the first attempt, signed in
as `manoj (doctor)`. F-242 was closed at S239 with AF-12; the warning outlived the fault.

---

## 1 · FOUNDATIONS

### 1.1 Machines and direction
Four machines, one rule: **the VPS reaches nothing; both PCs push to it.**

| machine | role | key paths |
|---|---|---|
| **Medical PC** (the counter, Windows, account `SET`) | Marg runs here; exports are captured and pushed | `D:\MARGERP\users\<login>\report\REPORT_n.XLS` (Marg's reused slots) · `D:\SendToClinic\` (agent, watcher, pusher, `_captured\` spool, `token.txt`, and since S259 `TURN_ON_ALL.bat` / `TURN_OFF_ALL.bat` / `_off_READ_ME.txt`) |
| **manojz** (the owner's PC) | the pull chain and the only complete raw archive — FALLBACK sender | `D:\Downloads\margsync\MargPull\` (router, gate, rescan, pushers) · `MargArchive\<TYPE>\<YYYY-MM>\` + `index.csv` · `_config\` (numbers, never in git) · **`D:\Downloads\_kbtools\`** (the KB manifest tool S268, the paper shelf S269, the nightly maintenance S272 — none of it Sanjeevni, all of it the record-keeping this book depends on) |
| **VPS** `followup.dr-manoj.in` (`srv1746119`) | every door, every table, every screen | `/root/finance/` (the apps + `finance.db`) · `/root/marg_ingest/` (collector, door, shadow) · `/root/portal/` (tiles, logins) |
| **Google** (`drmka.ortho`) | mirrors and backups | Drive `Clinic Data Archive\MargArchive` (mirror the server reads) · `MargBackups` · `FinanceDB_Backups` (nightly db **and, since S243 K2, the nightly code bundle**) · `ToMedical\_kit` (agent self-update) · `FromMedical` (heartbeat) |

**[live]** Tailscale, 15-Sep 05:51: manojz `100.75.93.88` Running; medical online at
`100.119.151.40`, direct `192.168.1.26:41641`. *A green Tailscale is not a working pipeline — on
26-Aug it read active and direct through a whole outage. The page says so itself.*

### 1.2 People, logins and roles
Portal logins (13 staff + owner): role `doctor` / `manager` / `staff`, mapped inside finance to **unit
roles** in table `unit_role` on unit `medical`: **maker** (Darpan — files the day), **checker** (the
owner alone — approves), **viewer**. Amir's page is gated on *any role on the medical unit* (D478).
Tiles are convenience only — `tile_grants.json` shows, the route's own gate decides (S242 lesson).
Who does what: **Amir** exports purchase reports, enters bills in Marg, does renames, raises claims ·
**Darpan** files the day, keeps the drawer, chases claims and corrections, does shelf counts ·
**counter staff** sell, take returns · **owner** approves, decides, locks.

**Changed since v1.1 [record]:** S250 added the **Staff Register** working roles — Shivani and Alisha
**makers**, Shavez **checker** (D272; he still may not approve). One decision is open with the owner:
the S262 note says Shavez writes the cheque register, but he is a **viewer** there, so as built he
reads it and cannot write it (⭐0 item 14).

### 1.3 Tokens and keys
One machine token, `FINANCE_MARG_TOKEN` (systemd drop-in on the VPS), opens seven token-only doors and
is cached on both PCs.

**Changed since v1.1 [record]:** **§11.4 item 3b is half done.** `S258_CONSTANT_TIME` (Club C step 1)
made **every machine-door token check on the VPS a constant-time compare** — seven sites in
`finance_app.py`, plus the other door modules. What remains of 3b is **per-sender tokens** (Club C.4),
which needs the owner's credentials and rides his F-456 key rotation.
**⚠ Standing exposure (F-465):** `clinic-finance.service` carries the real values of
`FINANCE_CRON_TOKEN` and `FINANCE_MARG_TOKEN` as plain `Environment=` lines. This is why the live
capture of that file may never go to the public repository.

### 1.4 Standing rules
Marg is never written to · the manojz pull chain stays as the fallback until the server path has
earned it (D402) · no patient number at rest on the VPS (F-185; phones masked to last 4, names present
in three tables — §6.5) · ingested-but-unaccepted is inert (D407) · dating happens at capture (D408) ·
junk is moved, never deleted, by the assistant; deleting is the owner's · nothing already live is
rebuilt without the owner's OK; the manual path stays.

**Added since v1.1:** **D513** — a vendor not on the authorised NEFT register never enters the NEFT
file; he is paid by cheque **and the cheque is logged** · **D520** — figures going to the bank carry
no thousands separators · **D521** — a cheque may be logged on a FINAL month; a live cheque number is
unique; nothing on the cheque register is ever deleted, only voided with a reason · **Amir must not
rename a supplier in Marg** · **no cash↔UPI corrections in Marg** (the CA's ruling, D492).

---

## 2 · CAPTURE AND TRANSPORT

### 2.1 The Marg report register
Marg writes every report into a reused slot file whose name carries no type and no date (D188);
identity comes from **content signatures** (`signatures.json`, one copy per machine — §3.1). Types
known: SALE_BILLWISE (DETAIL — the only one allowed to travel to the books; SUMMARY1 never exported),
STOCK_CLOSING (DEFAULT/TOTALS), STOCK_EXPIRY, PURCHASE_SUPPLIERWISE / BILLWISE / ITEMWISE /
BILLITEMWISE, SALE_RETURN, SALE_BOOK, STOCK_ITEM_LEDGER (carries PHI — never into the repo),
SALT_WISE_ITEM_LIST, STOCK_VALUATION, ITEM_MASTER (avoided, D403/D404). Cadence rulings:
supplier-wise month-end only; stock closing by 10:30 next morning (D463).

### 2.2 Capture on the medical PC — LIVE
`medical_agent.py` (S205.1) starts at power-on under `SET` (D480, proven 12-Sep), supervises
`marg_watch.py` (event-driven capture into `D:\SendToClinic\_captured\`, md5-deduplicated), writes a
heartbeat to Drive `FromMedical` every 300 s, backs Marg up hourly to Drive `MargBackups`, and
self-updates from Drive `ToMedical\_kit` by an md5 allow-list. The counter reaches its own account with
**Ctrl+Alt+Del → Switch user**; SET stays signed in behind it. Drive's letter on this machine moves
between reboots — never hard-coded in anything a person opens (F-442).

**[live] 15-Sep 05:52:** watcher **alive**, **0 captures today**; the last pull reached the machine;
the share was read in 0 ms. **The Marg backup is 1.8 days old** and drifting (it was 0.7 d on 13-Sep,
1.6 d on 14-Sep). Marg's own serverbackup sits on `D:`, the same disk as the data — *"not a disaster
copy"*, in the heartbeat's own words.
**[record]** The watcher has restarted by itself twice in three nights (pid 11516 → 11292) and come
back unaided both times. Recorded, not diagnosed.

### 2.3 The three legs
| leg | path | state |
|---|---|---|
| **A · direct push** | `marg_push.py` (a thread inside the watcher) → HTTPS `POST /finance/api/marg-file` → the one door | **LIVE** |
| **B · pull** | manojz task *Marg pull from medical* every 10 min over Tailscale → `_spool` → router → archive → `_outbox` → `marg_gate send` → `POST /finance/api/marg-push` (sale) · `push_snapshot` / `push_expected` → `/finance/stock/api/snapshot` · `push_purchases` / `push_sale_bills` → `/finance/purchase/api/push` | **LIVE as the feed to the books; FALLBACK by ruling** |
| **C · Drive collector** | manojz robocopies the archive to Drive → `/root/marg_ingest/marg_ingest.py` every 5 min reads it with the service account → the one door | **SHADOW** (de-duplicates against leg A by md5; OFF file `/root/marg_ingest/OFF`) |
| **D · browser** | `/finance/clinic/marg/upload` (clinic maker/checker) → the one door | **LIVE, manual** |

**[live]** Last Marg pull **14-Sep 22:30 IST**; the pipeline heartbeat from manojz was **2 minutes
old** when read. **The last Marg report to arrive was 12-Sep 23:01 — 31 hours before the read**, which
the health page raises as *"A day may not have been sent yet"* (Sunday closed). **Reports queued but
not sent: nothing waiting.** So the transport is alive and the queue is empty; what is missing is an
export nobody has generated.

### 2.4 The one door — LIVE
`/root/marg_ingest/marg_take.py` · `take(raw, name, source)`: md5 de-dup → router → verdict **TAKEN /
ALREADY / REFUSED / BUSY** (flock) → sale reports parsed to PHI-free lines and the file deleted; other
types kept in `/root/marg_ingest/archive/<TYPE>/<yyyy-mm>/`; every file rowed in `mi_file`. Wraps:
`marg_door.py` (`/finance/api/marg-file` GET/POST, **constant-time hmac compare since S258**; the
upload page). **Gap, unchanged:** refused files are deleted with no server-side rescan (§3.3–3.4,
§11.4 item 3d).

### 2.5 Archives and the PHI rule
| archive | where | holds | rule |
|---|---|---|---|
| medical spool | `D:\SendToClinic\_captured\` | every capture | the edge archive by design; never pruned by a script |
| manojz archive | `MargArchive\` + `index.csv`, `_REFUSED\` | every routed export, raw | the only complete raw copy; PHI stays on the PC |
| Drive mirror | `Clinic Data Archive\MargArchive` | the same, unfiltered | **the one place raw sale exports with full mobiles sit outside the clinic.** The owner has since ruled it stays full: *"required for many correlation jobs, safe there"* (§13). §11.4 item 3i is therefore **withdrawn, not owed.** |
| VPS archive | `/root/marg_ingest/archive/` | non-sale types only | sale reports deleted after read (S186) |
| hand-named workbooks | `D:\Downloads\MARG REPORTS CLAUDE\`, two session kits | historical source | never routed |

---

## 3 · IDENTIFICATION

### 3.1 Router and signatures
`marg_router.py` (manojz `MargPull\`; vendored on the VPS in `/root/marg_ingest/` and `lib/`) classifies
by content, deep-verifies via `marg_report.py`, archives, and marks `uploadable`. `signatures.json` is
the same bytes on both machines today (S240) with **no mechanism keeping them equal** — target:
single-sourced from the VPS. Repairs so far: F-351 (rescan), F-429 (ITEMWISE end row).

### 3.2 The file register — LIVE
`mi_file` (212 rows at 12-Sep **[record]**) · `mi_run` (collector runs) · `mi_sale_line` (4,152 PHI-free
sale lines keyed by file md5). Read by `marg_shadow` and the upload page's "last 20" list; **feeds no
book yet** (§6.2).

### 3.3 Verification and refusal
Six refusal grounds at `/finance/api/marg-push`; the door's REFUSED verdict at `marg_take`. On manojz a
refused file goes to `_REFUSED\`; on the VPS it is deleted and its md5 remembered.

### 3.4 Rescan — manojz only
`marg_rescan.py --if-signatures-changed --apply` re-files quarantine after a signature fix. **No server
equivalent** — a `refused/` folder and a rescan on the VPS remain §11 items (3d).

### 3.5 Pipeline status and the export watch — LIVE
`pipeline_status.py` (end of every pull) → `POST /finance/api/pipeline-status` → table
`pipeline_status` → page `/finance/pipeline`. `export_watch.py` (cron 23:40 today / 10:45 yesterday
with ntfy) answers "did Amir export today" against his punch (machine id 101) → table `export_watch`.
The "no export today" alarm on the server side is PLANNED (D467 phase 2c).

**Changed since v1.1 [record]:** `S259_OFF_SWITCHES` (Club C.2) gave **every PC-side job an OFF
switch** — the four jobs that previously could only be stopped by killing a scheduled task or a
process. `S260_MACHINE_CONF` (Club C.3, manojz half) put **the machine's settings in one file**
instead of typed into four. **The medical PC's own two settings** (the server address in `marg_push.py`
and in `SEND_TO_CLINIC.bat`) are **not yet moved** and are held to ride the next medical change.

---

## 4 · THE ITEM SPINE

### 4.1 Items, names, facts — LIVE
`marg_spine.py` (S229; run by `spine_cadence.py` every 30 min 09–23 with `--if-changed`, nightly 23:50):
one row per product in `marg_item` (374), every spelling in `marg_item_name` (424), facts in
`marg_item_fact` (1,132 — salt, pack, MRP, from `purchase_salt_marg`, `stock_count_item`, `stock_rate`).
**Only Marg's own export may create an item**; a computed name that cannot be resolved raises a task,
never a row. *(Counts [record], 12-Sep.)*

### 4.2 Unresolved names and tasks
`marg_name_unresolved` (10) · `marg_task` (42: derived_name, question, ambiguous). Amir's rename list
(22 open, on him) and the two merges awaiting the owner's word (`DISPO SYRINGE NIPRO` / `NIPRO 3 ML
DISPO SYR`, `PARI CR 12.5` / `PARI 12.5`).

### 4.3 Cadence and drift
`marg_spine_run` · `marg_spine_drift` · `spine_drift_latest.txt`. Drift = a name or fact that moved
between runs; read on the spine page and in the health legs.

### 4.4 Renames and merges
Amir's salt work list `/finance/purchase/page/salts` and his downloadable sheet `/finance/amir/salts`
(matched by row id, never by name). Merges in Marg: owner's word only.
**[live]** The hub reports **6 new medicines first seen this month** — SHOULDER IMMOBILISE UNISON,
LOFTYPRED 80 INJ, DENGEN PLUS, and three TYNOR WRIST SPLINT variants — and says of each that *"the salt
of a new item is not yet on this server (Amir's salt list is owed)"*. v1.1 recorded `purchase_new_item`
at 5; it is **6**.

### 4.5 Discount rulings
`marg_item_discount` (93 items, T1 rulings from S236; HYLASTO approved and never re-raised, D464) ·
`marg_item_discount_history` · `marg_discount_run`. Feeds attribution (§6.3).

---

## 5 · PURCHASE LANE — LIVE

**This is the section that changed most since v1.1. Nine kits landed here in two days: S261, S262,
S263, S264, S265, S266, S267, S270, S271. The month's vendor payment left the owner's workbook and
became part of the system.**

### 5.1 Exports → bills → lines
`push_purchases.py` (manojz; nightly 22:30 and every 30 min) sends every archived PURCHASE_* export →
`POST /finance/purchase/api/push` → `purchase_export`, `purchase_bill`, `purchase_line`,
`purchase_audit`. Marg's purchase serial is in no export (F-436, parked).

**[live]** Months on file **April 2026 → September 2026, 18 exports**. September carries **39 bills**,
August 84 (one with a purchase return), July 103 (two), June 102, May 79 (one), April 94 (two).
**Zero bills "with no lines" and zero "wrong" in every month** — the item-wise net reconciles to the
supplier-wise total to the rupee in September, and to within a few rupees in the older months where
only a bill-wise export exists.

### 5.2 Months — provisional and final
`purchase_month` · the hub shows every month Apr–Sep 2026; finalise/reopen at
`/finance/purchase/api/finalise|reopen`.

**[live] Still no month finalised — all six read PROVISIONAL, and all six say "ready to finalise."**
This is unchanged from v1.1 and is the single oldest open thing in this lane. August is the one the
owner has been asked to close (⭐0 item 4): **Check it now**, then **Lock it**.
**⚠** Supplier-wise exports exist only for **July, August and September**; April, May and June fall
back to bill-wise, and the hub says so on each row rather than hiding it.

### 5.3 Vendors, the phone book, and the two names — LIVE
`purchase_vendor_contact` · `/finance/purchase/page/book`; numbers live in
`_config\stockist_phones.json` on manojz, never in git.

**New since v1.1 [record], `S263_VENDOR_LINK`:** the bank details of 22 vendors were imported at S225
from the April–July NEFT advice sheets **under the name the bank knows**; Marg's bills carry **the name
the vendor prints**, and for **14 of the 22 those are not the same string**. S263 added the alias, so
one firm with two names is one vendor.

**⚠ A claim this revision made and then RETRACTED — recorded, not tidied away.** Reading the payment
sheet as plain text, one vendor appeared to read `AGARWAL SURGICALS AND MEDICALS CHEQUE`, and this
section first reported that the payment mode had been typed into the supplier's name in Marg. **It had
not.** `CHEQUE` is a chip — `'<span class="chip warn">CHEQUE</span>'`, `purchase_app.py` line 2215 —
rendered beside the name to mark the cheque lane, and a plain-text read of the page runs the two
together. Checked against the data afterwards: `purchase_bill` holds the supplier as
**`AGARWAL SURGICALS AND MEDICALS`** across nine bills, clean, and `purchase_vendor_contact` **has a
row for it** (added 14-Sep 22:30, with a phone). **Nothing is wrong with the name.**

What is actually missing is narrower and is already on the owner's list: the row has **no
`acct_no`, no `ifsc`, no `acct_name`** — which is precisely why the vendor sits on the cheque lane and
why ⭐0 item 2 asks for its bank details. Give those and it moves to NEFT by itself, with no alias and
no rename anywhere.

### 5.4 Scan links
`purchase_scan_link` · `/finance/purchase/page/scans`.
**[live] 0 pharmacy scans with no Marg bill · 501 Marg bills with no scan** (v1.1: 496).

### 5.5 Salts and new items
`purchase_salt_marg`, `purchase_salt_name`, `purchase_salt_task`, `purchase_new_item` — the salts page,
Amir's sheet, `/purchase/api/salt_task`. See §4.4 for the live new-item count.

### 5.6 Feed health and the hub
`purchase_feed` — the hub's own card.
**[live] "Last purchase data received: 13-Sep 10:20 IST"** — **two days before this read**, while the
Marg pull itself ran at 14-Sep 22:30 and manojz reported two minutes ago. **The transport is alive;
no purchase export has been generated since 13-Sep.** That is Amir's step, not a fault in the lane,
and it is the same shape as the S238 finding (no purchase exports on 8–10 Sep).
**✅ The v1.1 "Known 404" is closed:** `/finance/purchase/` (the bare prefix) redirects — `S243_SCREEN_FIXES`, LIVE 13-Sep (K4).

### 5.7 The vendor payment sheet — NEW, LIVE (S261 · S264)
`/finance/purchase/page/pay/<month>` — **one line per vendor, prepared from this server's own figures**,
replacing the workbook on the owner's PC that a script used to prefill from an export. A vendor row
opens to its bills; a bill opens to the bill. **`Carried in` is the only thing typed on the page** —
what an earlier month left outstanding, settled outside this system.
Three numbered steps on one screen: **1 · The sheet** · **2 · Verify against the supplier-wise
statement** · **3 · Lock it**. Step 2 is a real cross-check, not a tick-box: Marg's supplier-wise export
is held against the sheet **three ways — every bill it carries, the per-bill amounts, and the
statement's own printed grand total.**
**[live]** September reads **not checked yet**, with the page saying so in its own words: *"The sheet
above is what this server believes; the statement is what Marg says. They are not the same claim until
they have been held against each other."*
**S264** gave the page its **month strip** (Sep 26 → Apr 26) — before it, the tile opened on September
with no route to any other month, and the hub's month link goes to the *purchase audit*, not here.

### 5.8 The bank advice, the letter, and the file — NEW, LIVE (S265 · S266 · S267)
Step **4 · The advice, exactly as the bank gets it** — the same lines, the same columns, the same order
as the sheet printed on blank A4 and emailed to the bank. Held to the files actually sent, April–July
2026. Carries the firm's GSTIN, mobile and drug licence numbers as the real sheet does.
**A month that is not locked prints as DRAFT and says so** — *"DRAFT — this month is not locked yet.
Lock it before this is printed or emailed."* **[live]**
**S266** adds the **covering letter** authorising the debit, word for word as Sanjeevni has always sent
it, with three fields filled rather than typed. **S267** generates the **workbook** for the email — the
bank's own file shape, not a lookalike — from the same rows the page shows.
**D520 applies here:** figures going to the bank carry no thousands separators.

### 5.9 The cheque register — NEW, LIVE (S270 · S271)
`/finance/purchase/page/cheques` — *"every cheque written to a vendor who is not on the NEFT lane —
number, date, payee and the month it settles."*
This is **the half of D513 that had never been built**: S261–S263 built the first half (the sheet names
the cheque vendors and keeps them out of the NEFT file); S270 built the logging.
**Rules, on the page itself:** nothing is ever deleted; a wrong entry is **voided with a reason and
stays**; a live cheque number is unique; a cheque may be logged on a FINAL month (D521).
**S271** was a correction found on the live screen within the hour: the month strip had been built from
the cheques already logged, so an empty register offered no months at all. It now comes from the book.
**[live] The register is empty — 0 cheques, 0 handed over, 0 voided — and September owes one cheque to
one vendor on the cheque lane.** Cheques are logged **from the payment sheet, on the vendor the cheque
settles**, not from the register itself.

---

## 6 · SALE AND MONEY LANE

### 6.1 Bill money rows — LIVE
`push_sale_bills.py` (manojz, every 30 min) sends VERIFIED SALE_BILLWISE money rows → `/finance/purchase/api/push`
type `SALE_BILL` → `sale_bill`, `sale_bill_push`. Rung 1 (S237/S240), backfilled 31 exports.

### 6.2 Item lines — TWO STORES, target ONE
| store | filled by | read by |
|---|---|---|
| `sale_line_item` | `/finance/api/marg-push` → checker taps **Apply** → `finance_returns.load_lines` | the spine, attribution, returns audit, stock arithmetic |
| `mi_sale_line` | the one door (`marg_take`, legs A/C/D) | the shadow only |

Also `sale_item` (day-level via the ingest adapter) and `marg_push_staging` (the pending Apply queue).
**Target (§11 item 3e), unchanged:** the spine and attribution read the one-door store behind a flag;
shadow-compare; switch; retire the second parser's store.
**Changed since v1.1 [record]:** **A1 (D488) is LIVE — sale reports apply on arrival**, so the Apply
queue is no longer the owner's standing chore.
**[live]** *Reports queued but not sent: nothing waiting.*

### 6.3 Attribution and discounts — LIVE
`sale_attribution.py` (cron every 30 min 09–23, 23:55) attributes bill discount to lines using T1
rulings → `sale_line_discount`, `sale_bill_attrib`, `sale_attrib_run`. Rung 2. **Rung 3 (gross → net
side by side) still waits on the owner's word.**

### 6.4 Cash ↔ UPI corrections
`marg_correction` · Darpan's page `/finance/darpan/corrections` · `bank_match.py` (09:45, every 15 min
10–12, final 12:00) against `upi_txn` → `upi_match` · the correction checklist `/finance/marg-worklist`.
**The CA's ruling, 13-Sep (D492), changed this lane's purpose:** *no cash↔UPI corrections in Marg* —
they reopen bills to unauthorised edits. **The system keeps the record as a monthly accountant report
instead** (A4, LIVE 13-Sep). The page tracks; it never edits.
**[live] 15-Sep:** 27 bills this month reclassified cash → UPI, *"the bank proves UPI, Marg rang cash"*,
kept for the accountant report. Six days this month have UPI booked as cash; seven older days before
1-Aug also differ and **are deliberately not being chased**.
**⚠ [live] The UPI evidence leg is RED** — bank and books disagree on four September days (12, 09, 05
and 02 September). The page states the consequence plainly: *"Cash is total minus UPI, so a wrong UPI
moves the drawer with it."* The split is typed from the POS screen, not captured at billing (§13).

### 6.5 The boundary with the clinic books
Sale reports reach the **day books** (`day_entry`, `day_line`, `recon_exception`, `ingest_batch`) only
through Apply; the day is filed by the maker and approved by the checker (`/finance/review`). Patient
references: `patient_ref` (phone last 4 only, **names present**), `patient_visit`,
`marg_push_staging.parsed_json` (names).
**Changed since v1.1:** the returns desk showing names and numbers in the clear is **no longer a gap** —
**D493 reversed the masking** and full phone numbers on staff desks are the owner's ruling (§13). Phase
2, writing the number at Apply where the master does not have it, is still open.
**[live] Month vs Marg: −₹200 unexplained across 11 days, all of it on 2026-09-04.** Small, named, and
the only unexplained difference this month.

---

## 7 · STOCK LANE — LIVE

### 7.1 Marg's closing snapshot
`push_snapshot.py` (manojz, on capture every 15 min) → `POST /finance/stock/api/snapshot` (source
`push_snapshot`, as-on = Marg's date) → `stock_snapshot`, `stock_rate`, `stock_feed`.

### 7.2 The computed expected figure
`push_expected.py` (manojz, on capture and nightly; baseline 03-09-2026 + purchases − sales; source
`push_expected …`, as-on = **last sale date**) → the same door and the same table. Server-side twin:
`marg_shadow.py` (23:20, 06:20) computes the same over server data → `sh_feed`, `sh_diff`, `sh_run`.

**⚠ [live] The agreement has moved, and not the right way.** v1.1 recorded **373 compared, 370 agree,
3 differ**. The hub now reads **"Latest comparable day 12-09-2026: 373 items compared, 364 agree,
9 differ. 4 days of feed so far."** **The disagreement has tripled — 3 → 9 — and the latest comparable
day is 12-Sep, three days before this read.** This is the witness the plan intends to use for retiring
the PC-side job (§11.4 item 3f), so it is the number that decides when that may happen. **Recorded,
not diagnosed.**

### 7.3 Drift and reconcile — the S243 defect, now fixed
v1.1 described the defect: `stock_snapshot` keyed on (as_on, item) with no source, so Marg's figure and
the computed figure landing on the same date meant the later silently became "Marg's", and
`reconcile()` could auto-close a real difference.
**✅ Fixed and live.** `S243_SNAPSHOT_SOURCE` (K3) went **LIVE 13-Sep (D490)**: computed rows go to a
new `stock_expected` table, `stock_snapshot` holds Marg only, `stock_feed` is unchanged, and 1,119 past
rows were migrated conservatively. Pages: `/finance/stock/page/drift`, `/page/now`.

### 7.4 The count cycle
readiness (`stock_check_readiness`, the S240 gate: physical | Marg | ours must agree) → pads
(`padwriter`/`padreader`, `stock_count_pad_file`, `/page/pad`) → count (`stock_count`,
`stock_count_item`) → diffs (`stock_diff`, `stock_diff_lane`, `stock_diff_answer`,
`stock_diff_decision`) → decisions (`/page/desk`) → close (`stock_count_close`). Count #1 of
06-Sep-2026 remains open. No stock screen on a phone until the three agree (S228).

### 7.5 Loss desk and recovery
`/finance/stock/page/loss` · `stock_loss_tick / share / recovery` · `stock_finding` · Amir's board
`/page/amir` · report `/page/report`; F-379 recorded, unexplained items recorded as unexplained
(F-434).

### 7.6 Vouchers and write-offs
`stock_voucher` · rule R6: every expiry removal is a Marg voucher, never an in-place edit · one tap
pending (VINTAZ P 4500 INJ) at `/finance/stock/page/desk?count=1`. The voucher engine (D388/D397) is
parked on the owner's word.

---

## 8 · RETURNS AND EXPIRY

### 8.1 Vaapsi desk — LIVE (Hindi, counter)
`returns_desk.py` · `/finance/returns/desk/` · three steps (patient / medicines / slip) · `return_visit`,
`return_line` (slips have not started), `jaankari_answer`. Roles viewer/maker/checker on medical.
**Full phone numbers show here by ruling (D493), not by oversight.**

### 8.2 Jaankari — questions to the counter
"name does not match" and "count needed" queues on the desk; answers feed the returns audit.

### 8.3 Return intent and flags
`finance_intent.py` (01:30) → `intent_signal` · `finance_returns_audit.py` /
`finance_returns_escalate.py` · `pret*` tables (S207 credit-note chain) · exceptions `return_flagged`
("NEVER BOUGHT", "DISCOUNTED RETURN") on the review page.
**[live] Flags over 30 days:** MISSING_SCAN ×16, RETRO_INSERT ×12, EDITED_AFTER_REVEAL ×2,
MARG_BILL_RANGE_GAP ×1 — *"notes, not failures."* **Flags are never deleted (D505).**

### 8.4 Near-expiry and credit notes
Window 3 months (D409); credit note due by the 7th (R5); STOCK_EXPIRY exports archive-only today — a
near-expiry screen remains a §11 (Phase D) item.

---

## 9 · ORDERING — LIVE

### 9.1 Short list by stockist
`/finance/purchase/page/staff` — item · stock now · order qty, by supplier, plus "no supplier on record".

### 9.2 Orders and PDFs
`purchase_order`, `purchase_order_line` · `/finance/purchase/page/orders` · `/order/<id>/pdf`.
**[live] 0 open orders (draft or sent).**

### 9.3 Sent, chased, arrived
"Send on WhatsApp / Call" from the page; arrival closes against the purchase export (S225_ARRIVAL).
Chasing is Darpan's (claims — §10.2).

---

## 10 · PEOPLE AND SCREENS

### 10.1 Amir's day — LIVE
`/finance/amir` → `/finance/amir/step/<n>` (seven steps, Hinglish, phone-first, no JavaScript) ·
`/finance/amir/day` (the owner's English view) · `/finance/amir/salts` (+ `.xlsx`). Tables `amir_day`,
`amir_step`, `amir_bill_disposition`, `amir_claim`, `amir_salt_upload`. He is never asked whether a
report arrived; he types no bill number; a bill with no answer comes back; a half-done day stays OPEN;
he raises, never chases. **One tile only (D483); five parked, awaiting the owner's ruling.**

**Changed since v1.1 [record] — two kits, and one published kit that must never be installed:**
- **`S244_AMIR_PROCESSING`** — the report acceptance flow became **processing → processing done → what
  is still to be made**, to the owner's ruling that Amir must be able to start his next step while a
  report is still being generated.
- **`S246_AMIR_LIST_REOPEN`** — the bill list shows **only purchase bills from 1 September onwards**
  (everything earlier is settled) and **only bills marked not-OK, until they are corrected and cleared**;
  and a day can be **opened again**.
- ⛔ **`S245_AMIR_BILLTAP` is superseded and its installer must not be run.** It refuses correctly and
  touches nothing. S246 was built on the file S245 had already made live.

### 10.2 Darpan's queue
`/finance/darpan` (day card, drawer, cash position), `/finance/darpan/corrections`, `/finance/darpan/kal`
(**LIVE 13-Sep, D491**), the stock recheck cards sent from the desk.
**Next build, unchanged:** the claim queue `open → contacted → settled` (settled names an outcome;
self-closes on a matching purchase return; ages to the top at 14 days, D471). `amir_claim` is empty, so
it opens quiet.

### 10.3 Owner: hub, review, health, pipeline
`/finance/approvals` (the hub) · `/finance/review` = `/finance/` · `/finance/health` ·
`/finance/pipeline`.
**✅ The v1.1 "Known bounce" is closed:** `/finance/daily` no longer sends the doctor to the portal; a
checker goes to `/finance/review` — `S243_SCREEN_FIXES`, LIVE 13-Sep (K4).

**[live] `/finance/health`, 15-Sep 05:52 — what needs you 3 · worth knowing 6 · running normally 10.**
The three red: **UPI evidence** (§6.4), **This month vs Marg** (§6.5), **Marg report 31 hours old**
(§2.3). Running normally includes backup verified 15-Sep 01:05, the pipeline heartbeat 2 minutes old,
nothing queued, the medical PC reachable and its watcher alive.

**⚠ [live] The health page raises a fault about itself, and it deserves to be carried forward.**
*"Checks that have never fired — 7 checks have never once reported a problem in 14+ days: backup,
drawer, flags, margqueue, outbox, renewals, watcher. Either they guard something that never breaks, or
they are dead and cannot say so. AF-2 was born dead and stayed green for five sessions. Worth one look
each, once."* **This is the right instinct and nothing has acted on it.** Note the shape of the
evidence: `renewals` is on that list, yet the same page correctly shows the arms licence at 12 days —
so at least one of the seven is demonstrably *computing* while never having *reported*. The two states
are not the same and the check cannot currently tell them apart.

### 10.4 Reception and counter
Docterz daily collection `/finance/clinic/register` (reception: Shavez, Shivani, Alisha — D481; opens
on today, D482) · the drawer count is optional by design (D484) · the returns desk (counter). Clinic
pages are the clinic's, not Sanjeevni's — they share the process and the database today (§11 Phase 4–5).

**Changed since v1.1 [record] — the clinic-money chain, four kits in one day:**
`S249`/`S251_CLINIC_MONEY` (the morning match · other UPI · the float · physiotherapy · F-459) →
`S252_FLOAT_FLOW` (*"I find the flow to be a friction one"* — the float without friction) →
`S253_MATCH_PLAIN` (*"your match page data is very taxing … if you can simplify it"* — the morning-match
card in plain words) → `S254_SHEET_PHONE` (the counter sheet on a regular Android phone: bigger entry
boxes, optional sections collapsed by default with their names on the closed boxes).
**S251 is S249 re-issued under the next number (F-458)** because `S250_STAFF_REGISTER_TILE` moved
`tile_grants.json` between S249's commit and its install and S249's installer correctly refused at the
currency gate. **⛔ The float is never revenue (D506). ⛔ The counter sheet's history before 12-Sep
stays.**

**And the Docterz payment channel, on evidence:** `S256_GATEWAY_REF` and `S257_PORTAL_EVIDENCE` keep the
**Razorpay reference Docterz already sends**, which was previously thrown away, and S257 re-read every
Docterz export on Drive so past days get their Razorpay ids. **D510: the channel of an online payment
comes from its independent record, never from the Docterz mode word.**
⛔ **`S255_PORTAL_CHANNEL` is published, refuted, and NOT to be installed (F-460).** A published kit is
immutable; it stays in the repository with its refutation beside it.

### 10.5 Tiles, grants and what each login sees
`portal.py` `_visible_sections` decides from role + `tile_grants.json`.
**⚠ v1.1 recorded `tile_grants.json` at v12. It is now v17** — `2eb2f2714091d97ae8f53a80902c913f`.
The path: **v14 → v15** (S250, the Staff Register mask lifted for shavez, shivani, alisha) → **v16**
(S251, the S249 grants folded onto the live v15) → **v17** (S262).
**S262 added one tile: `Vendor payments`, in Money & Accounts, immediately after `Marg Purchases`** —
*"because the two are read together: what came in, and what is owed for it."*
**[live]** The purchase-lane nav now reads: Hub · Scan links · Orders · Order medicines · Phone book ·
Salt list · **Vendor payments** · Stock check.

---

## 11 · WATCH, BACKUP, RECOVER — and the plan of record

### 11.1 Watch
`export_watch` (§3.5) · `freshness.py` 08:05 with `freshness_legs.json` → `/finance/health` ·
`clinic_watchdog.py` every 5 min.
**✅ K1 is LIVE (13-Sep, `35e40626`):** `clinic-finance`, `staff-register` and `assetapp` are on the
watchdog. v1.1's "`clinic-finance` is not among them" no longer holds.
ntfy is the notification layer (D425) · `finance_heal.py` every 30 min 08–21.
**⚠ Two watch gaps carried, both about something that is not being watched rather than something that
broke:** **UptimeRobot watches the `.in`, not the `.com`** — the condition that let a full-day
certificate outage pass unreported on 10-Sep; and **`S237_CERT_WATCH` has sent nothing in eleven days**.

### 11.2 Backup
`finance_backup.sh` 01:05 → `/root/backups/finance/` · `finance_drive_backup.py` 01:40 → Drive
`finance_nightly.db.gz` · `clinic_state_backup.py` 01:50 → encrypted state bundle to Drive ·
`sheets_pull.py` 01:45 · `gas_export.py` weekly · hourly Marg backup from the medical PC.

**✅ The v1.1 gap is closed. K2 is LIVE and measured.** `code_bundle.py` writes
`code_nightly.tar.gz` to Drive `FinanceDB_Backups` at **01:35** every night. **Read 15-Sep: shipped
01:35:08 IST, 217 files, 2,014,229 B, md5 `4dd4ddc1…`.** The three nightly bundles have shipped on time
for six consecutive nights.

**✅ And it is now within a session's reach.** The bundle lands in a Google Drive folder no Cowork
session can see. Kit **`S272_NIGHTLY_MAINTENANCE`**, installed 15-Sep, copies it into
`D:\Downloads\_kbtools\vps_code\` as part of the 03:10 nightly on manojz, alongside the dated KB
mirror to the SSD and the folder counts. **From this session on, the live server's own code can be
read directly rather than inferred.**

### 11.2b · WHAT THE BUNDLE DOES *NOT* CARRY — measured at S258

`code_bundle.py` takes code, templates, SQL, shell, unit files and the root crontab. It deliberately
excludes — and is **right** to exclude — any `.env`, `.conf`, database, log, `.bak`, key json,
`*config*.py`, the portal user file, the staff settings, and **anything under `_retired`,
`__pycache__`, `backups` or `deploy`**. Those walls were built at S243 after v1.0's first bundle
shipped literal passwords (F-456). **Nothing here argues with a single one of them.**

But *excluded for a good reason* is not the same as *has a copy somewhere*. Every live-pinned VPS file
was held against the bundle, then every absentee against GitHub, **and then against the encrypted state
bundle's own `SRC_FILES` and `SRC_DIRS`** — the third store, and the one the first pass of this check
forgot to read. **Six live-pinned files have no byte-exact copy in any store:**

| file | why the bundle skips it | why GitHub does not save it |
|---|---|---|
| `/root/finance/freshness_legs.json` | `.json` is not a source under `/root/finance` | **not in the repository at all.** Its own pin note says *"Configuration, not code: a window is widened or a leg retired HERE, never in `freshness.py`."* **The 26+ legs that decide what `/finance/health` watches exist only on the box.** |
| `/root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py` | under `deploy` | the repository's copy is **a different file.** **The live item spine — the whole of §4 — exists byte-exact nowhere but the box.** |
| `/root/assetapp/asset_register.py` | `/root/assetapp` is not a source at all | the repository's copy is a different file. **`assets.dr-manoj.in` is a live application with no off-box copy.** |
| `/root/deploy/email_agent.py` | under `deploy` | the repository's copy is a different file |
| `/root/deploy/gen_live_pins.py` (with `verify_live_pins.py`) | under `deploy` | the repository's copy is a different file. **These are the tools that generate and check the pin list itself.** |
| `/root/deploy/sweep_baseline.txt` | under `deploy` | not in the repository at all |

**Withdrawn after checking rather than asserted — and one of them was withdrawn only on a second look,
which is recorded here rather than tidied away.** `/root/staff_master.csv` was first written up as a
gap on the strength of `SRC_DIRS` alone; `clinic_state_backup.py` also has a `SRC_FILES` list, and
`/root/staff_master.csv` is **the fifth line of it**, beside `console.db`, `assets.db`, `punches.csv`
and `punches_raw.log`, under the heading *"INCLUDED — the data with no other off-box copy."* **It is
covered, nightly and encrypted.** The lesson is the project's own: a store is not checked until every
one of its inclusion lists has been read, and reading one of two is how a false gap gets minted.
`/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf` looked like a gap too, but
`clinic_state_backup.py` gathers `VHOST_DIR` into the same bundle by design, so the routing **is**
covered. `/root/portal/clinic_users.py`, `/root/shared/sarvam_ocr.py`,
`/root/assetapp/scanner_widget.js`, `/root/assetapp/smoke_test.py`, `/root/finance/cards_registry.json`
and `/root/wa/casepack/casepack_page.html` are each **byte-exact in the repository** and need nothing.
`/root/finance/push_purchases.py` is the row struck at S257 as F-482 — it has never existed on the box,
and the bundle agrees with the strike.

**The shape of the gap, plainly: two live applications and one live configuration file.** Not a fault
in `code_bundle.py`, which does what it says. A gap between what three backups each cover, which nobody
could see until the bundle and the pin list could be held against each other in one place — which is
what S272 made possible on its first night.

### 11.3 Recover
`verify_restore.py` — the restore drill (verified 12-Sep 01:05) · every kit installer backs up to
`.bak_S###_<pin>` and rolls back byte-identical on failure · `/root/_retired/S243_2026-09-13_0007/UNDO.sh`
restores the retired residue.
**Rollbacks held open:** `finance.db.bak_S265` and `.bak_S266`; `purchase_app.py.bak_S270_34628cd8` and
`.bak_S271_800d58a3` — **keep until the cheque register has carried a month.**

### 11.4 The plan of record — restated at S258

| # | item | state at S243 | **state at S258** |
|---|---|---|---|
| P1 | this book + the estate register | DONE | **DONE** — this is v1.2 |
| P2 | residue out of `/root` — 495 moved, undo kept | DONE | **DONE** |
| K1 | `clinic-finance`, `staff-register`, `assetapp` on the watchdog | LIVE | **LIVE** |
| K2 | nightly code bundle to Drive (01:35) | LIVE | **LIVE**, 217 files, shipping on time |
| K3 | `stock_snapshot` Marg-only; computed → `stock_expected` | LIVE | **LIVE** |
| K4 | `/finance/purchase/` redirect · `/finance/daily` checker → review | LIVE | **LIVE**, both confirmed |
| 3a | one settings file per machine | next | **manojz DONE (S260); the medical PC's own two settings held to ride the next medical change** |
| 3b | per-sender tokens, constant-time compare | next | **constant-time compare DONE (S258); per-sender tokens = Club C.4, on the owner's key rotation** |
| 3d | `refused/` kept + server-side rescan | next | **still next** |
| 3e | spine + attribution read the one-door store | after 7 clean shadow nights | **not started — and §7.2 says the shadow's agreement has gone 3 → 9 differing, so the clean nights have not been earned** |
| 3f | retire manojz senders one at a time | after 3e | **after 3e** |
| 3g | manojz live tools out of the git checkout into `margsync\bin\` | with 3a | **carried** |
| 3h | OFF switch for every job | with 3a | **PC side DONE (S259, both machines); the VPS-side switches remain** |
| 3i | filter full mobiles out of the Drive archive mirror | with 3a | **WITHDRAWN — the owner ruled the mirror keeps full PHI (§13)** |
| 3j | full phone numbers on the returns desk (D493) | LIVE where the master has it | **LIVE**; phase 2 (write at Apply) open |
| D1 | Darpan's `/kal` LIVE; the claim tab (D471) | next | **`/kal` LIVE; the claim tab still next** |
| P4 | Sanjeevni in its own process | after Phase 3 | **after Phase 3** |
| P5 | its own database, attached read-only | optional, last | **optional, last** |
| A1–A4 | apply on arrival · salt list refresh · Shavez/Amir/Kal tiles · the CA report | LIVE | **LIVE** |
| — | Rung 3 · vouchers · parked tiles · merges · F-436 serial | owner's word | **owner's word** |
| **NEW** | the vendor payment sheet, the bank advice, the covering letter, the workbook, the cheque register | — | **LIVE (S261–S267, S270, S271)** — §5.7–5.9 |
| **NEW** | the four PC-side jobs' OFF switches; one settings file on manojz | — | **LIVE (S259, S260)** |
| **NEW** | the Docterz Razorpay reference kept, and backfilled from Drive | — | **LIVE (S256, S257)** |

---

## 12 · RESIDUE AND RETIREMENT REGISTER

| what | where | state |
|---|---|---|
| 495 superseded files | `/root/_retired/S243_2026-09-13_0007/` | **retired 13-Sep.** The `finance_app.py.bak_*` chain is the only history of the live file. **K2 is now live, so the bundle carries the live file nightly — but the chain is still the only record of its past, and the owner's own one-line deletion (⭐0 item 11) is his alone and only after a full cycle.** |
| 12 items HELD by a live reference | `/root`, `/root/finance` | left in place |
| `_quarantine_S232_F368_…/` (six stale `.env` copies) | `/root` | held until the WABA token rotation completes |
| six stale `.env.bak*` / `.env.preswap*` | `/root/wa/` | secrets inside — retire on the owner's word |
| `/root/wa/staff_ledger.py` (stray) · `/root/deploy/repo/staff_ledger/` (fossil) | VPS | the owner's to decide |
| migration tables `s184_*`, `s184c2_*`, `s186_*` · 37 empty tables | `finance.db` | candidates, never verdicts — after 3e |
| `sale_line_item` beside `mi_sale_line` · `stock_feed` beside `sh_feed` · `MargArchive` beside `/root/marg_ingest/archive` | VPS | structural duplicates — retire by evidence in 3e/3f |
| seven manojz scheduled Marg jobs | manojz Task Scheduler | FALLBACK; retire one at a time in 3f |
| ~300 `marg_watch.py.before_*` · `_captured` spool | medical `D:\SendToClinic\` | clutter / edge archive; deletion is the owner's |
| unmasked `marg_report.py` (two PC copies) vs masked `eeab5605` | manojz, medical | replace with the next PC kit |
| `finance.db.bak_S265`, `.bak_S266` · `purchase_app.py.bak_S270_34628cd8`, `.bak_S271_800d58a3` | VPS | **the live rollbacks — keep until the register has carried a month** |
| **NEW ·** 14 copies of `purchase_app.py` across `deploy_kits/`, every one a different file | repository | **lineage, not clutter — this is what made the S258 reconstruction possible.** Keep. Prune nothing here without reading §11.2 first. |
| **NEW ·** 71 loose files at `D:\Downloads\`, 7 at `D:\dr-manoj-git\` | manojz | **measured at S258.** `S272` step C now counts them nightly and names what grew. `patient_fp.env.BACKUP_KEEP_SAFE` is **KEEP**. |
| **NEW ·** `S245_AMIR_BILLTAP`, `S255_PORTAL_CHANNEL` | repository | **published and superseded/refuted. Immutable (F-460). Never install.** |

---

## 13 · THE OWNER'S RULINGS (his words are the spec)

*Carried unchanged from v1.1 — these are his words of 13-Sep-2026 and nothing since has revised them.*

- **Machines.** SET is his RDP login on the medical PC, used mainly to run Marg reports himself; Darpan
  and Amir use the staff account. All clinic PCs are off at close and on in the morning — the medical PC
  after 8–8:30, sometimes 10–10:30. *No server job may assume the medical PC is up before mid-morning.*
- **Darpan.** Generates sales and sale returns only; hands the day's cash to the owner or Dr Bhawna =
  printout − home/procedure medicines − POS online sum, noted in a physical notebook. His screen follows
  that exactly: prefilled morning form, two inputs, differences shown, five reasons, server-checked.
  ₹50 day line · ₹2,000 month cap · no kharcha · excess = his calculation error, owed back to him · a
  received tap by the recipient, later allowed (the physical copy is the proof) · flagged returns asked
  on the same screen · **no deterrent notice — "the data surfacing there is the deterrent"** · the owner
  a passive viewer with a filtered queue; the system is the main checker.
- **Amir.** A distinct role (bills, renames, supplier payments in Marg), owner as backup; after visit-day
  work the system asks him for the salt-wise export and keeps it raised until it arrives; the owner gets
  a collapsed "Amir's visit — what was done".
- **Shavez.** Marg report generator, a morning job before any sales and on Amir's days: "Aaj ki reports"
  confirms each arrival and shows what is pending or refused.
- **CA ruling.** No cash↔UPI corrections in Marg — they reopen bills to unauthorised edits; the system
  keeps the record as a monthly accountant report.
- **Numbers and data.** Full phone numbers everywhere on staff desks including the returns desk; the
  Drive mirror keeps full PHI ("required for many correlation jobs, safe there"); the repository stays
  number-free (F-185).
- **Machines and moves.** Everything PC-side moves to the VPS if technically better; the vendor phone
  book lives at the VPS; the spine is Claude's call; renames delegated to Amir; discount rulings flagged
  for the owner to edit in Marg.
- **Mandate.** *"I have to depend upon you and your skills. Whatever you think, say first and best to
  arrange everything properly and everything remains stable and working."*

---

## 14 · WHAT THIS REVISION FOUND THAT NOBODY WAS LOOKING AT

Seven things, each read rather than inferred, each carried into the close report.

**First, what came back clean, because a clean result measured is worth as much as a fault found:**
**109 of the Register's live VPS pins were held against the box's own bytes and 109 matched, with zero
mismatches.** The Register is correct on every row the bundle can reach. That is the ground everything
below stands on.

0. **Six live-pinned files have no byte-exact copy in any store** (§11.2b) — among them the **live
   item spine**, the **live asset register application**, and **`freshness_legs.json`, the configuration
   that decides what the health page watches.** `code_bundle.py` excludes each of them for a reason
   that is individually correct, and the repository's copies differ or are absent. **No single store is
   wrong. The gap lives between them, and nothing was positioned to see it until the bundle and the pin
   list could be read side by side.** *(This read seven in the first draft of this section. The seventh,
   `/root/staff_master.csv`, is covered by the encrypted state bundle's `SRC_FILES` and was withdrawn
   the same session — see §11.2b.)*
1. **The stock shadow's agreement has tripled its disagreement — 3 differing → 9** (§7.2), and its
   latest comparable day is three days old. This is the witness for retiring the manojz senders, so it
   decides when item 3f may start.
2. ~~A payment mode typed into a supplier's name in Marg.~~ **RETRACTED within the session** (§5.3):
   `CHEQUE` is a lane chip beside the name, and a plain-text read of the page ran the two together.
   The vendor's name is clean and it **is** in the register; only its bank details are missing. **The
   lesson is the one this revision earned twice: a page read as text is not the data.** Both
   retractions in this document — this and `staff_master.csv` in §11.2b — came from asserting on a
   partial reading, and both were caught by checking the underlying store afterwards. **The store is
   the check; the page is the symptom.**
3. **Seven health checks have never once fired in 14+ days**, and the page says so about itself (§10.3).
   At least one of them is demonstrably computing while never reporting — the check cannot tell a quiet
   guard from a dead one.
4. **The purchase feed has received nothing since 13-Sep 10:20** while every leg of the transport is
   alive (§5.6). The missing step is an export nobody has generated.
5. **The nightly code bundle is now within a session's reach** and corroborated the reconstruction of
   `purchase_app.py` independently — two methods, one answer (§11.2).
6. **The Phase 0 instruction about the assistant's browser is wrong** — F-242 was closed at S239 and the
   browser reads live pages on the first attempt. The warning outlived the fault by nineteen sessions
   and has been costing every session a capability it already had.

---
*SANJEEVNI_SYSTEM_BOOK_v1_2_S258 · 15-Sep-2026 · supersedes v1.1 in full · written from live pages, a
whole read of the live `purchase_app.py`, and the kit records of S244–S271 · the manifest decides what
is current.*
