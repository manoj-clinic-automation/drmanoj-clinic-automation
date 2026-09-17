# SANJEEVNI SYSTEM BOOK — v1.3 · S264 · 17-Sep-2026

*The one document that describes the Sanjeevni (pharmacy) system as it actually is. **Supersedes
`SANJEEVNI_SYSTEM_BOOK_v1_2_S258.md` in full** — this is a complete document, never a delta
(D202/D247). Twelve sections plus the owner's rulings; each subsection names what lives there today —
machines, files, tables, pages, jobs, people — and its state: **LIVE** (in use) · **FALLBACK** (kept
switched on behind the live path) · **SHADOW** (runs, writes, feeds no screen) · **BUILT** (in the
repository, not installed) · **PLANNED**. Money figures and patient data are never in this book.
**Since D528 (S260–S262) this book lives in the project "Sanjeevni — Pharmacy & Marg"; the
repository row `SANJEEVNI_SYSTEM_BOOK_v1_2_S258.md` is frozen and this revision is rowed beside it.**

**Why v1.3 exists — F-493.** v1.2's §7.2 carried a figure under the wrong name: it wrote *"v1.1 recorded
373 compared, 370 agree, 3 differ"* as the **shadow's** reading, when 373 is the population of the
**hub card** — a different comparison, over a different population, answering a different question
(F-493, S259). The plan's condition for retiring the manojz senders (§11.4 item 3f, *"seven clean
shadow nights"*) had been read off the hub card, which **can never reach zero** while two spellings of
one product exist in Marg. §7.2, §11.4 and §14 are rewritten so that **every number in this book
carries the surface it was read from.** The rest of the book is brought current to S263 and re-checked
against the 17-Sep bundle and database; nothing else is silently changed.

**How v1.3 was checked.** Four sources, each named at the row it supports:

- **[db]** — computed from **the box's own nightly database**, `finance_nightly.db.gz`, built on
  `srv1746119.hstgr.cloud` on **17-Sep-2026 (the 01:35 bundle's companion, in reach at
  `D:\Downloads\_kbtools\vps_code\` from 05:05)**, by re-running the live code's own logic over it —
  the hub card by `_stock_card()` exactly as `purchase_app.py` writes it, the shadow from `sh_run` as
  `marg_shadow.py` wrote it. **A [db] figure is the server's state at 01:35 on 17-Sep, not at the
  moment of reading; anything that reached the box after 01:35 (the 06:51 exports, the three S262/S263
  kits) is not in it and is marked [record].**
- **[code]** — read from **the box's own nightly bundle**, `code_nightly.tar.gz`, built at **01:35:03
  on 17-Sep-2026**, md5 `10421813f8b0f730f6869bfb0c27afb5`, **244 files** (S273 widened it from 217
  — §11.2b).
- **[pins]** — the Register's live VPS pins (`live_pins_S263close.txt`) held against that bundle:
  **119 matched · 3 mismatched · 1 absent** — the three mismatches are `job_pulse.py`,
  `purchase_app.py` and `amir_day.py`, **each found at exactly its recorded predecessor hash**
  (`917713f5…`, `3535dc97…`, `a9f20622…`) because S283, S284 and S285 installed them after 01:35;
  the absentee is `assetapp_backup.py`, new at 09:04 (S286). The 18-Sep bundle is their proof. One
  further row, `marg_spine.py`, is a different matter and is §11.2b's finding.
- **[record]** — from a kit's own README and the close that installed it, where no live surface shows
  it. **A [record] row is not a live read and does not claim to be** (F-443).
- **[live]** — rows so marked were read from the running pages on **15-Sep-2026, ~06:00 IST** (v1.2)
  and are **carried, not re-read**: this revision opened no browser. Where a [db] or [record] fact
  supersedes a [live] row, the newer fact is stated beside it and the older kept for the trail.

*(v1.2's note that `START_HERE_PROMPT_v8`'s F-242 browser warning was stale has done its work — the
evergreen prompt has been at v9 and v10 since, and the warning is gone.)*

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
**makers**, Shavez **checker** (D272; he still may not approve).
**Changed since v1.2 [record] — the open decision is closed.** v1.2 recorded that the S262 note said
Shavez writes the cheque register while as built he was a **viewer** there (⭐0 item 14). The owner's
word on the board (F5): *"make him maker."* **`S284_SHAVEZ_MAKER` (D529, installed 17-Sep 07:38)**
did it **by a named grant, not a unit role**: a `unit_role` maker row would also have let him file the
day, give bill verdicts, type carry-forwards and read the vendor phone book — none of it asked for —
so the grant is the house pattern already used twice in the same file (`purchase.phonebook_users`,
`purchase.salt_users`): **setting `purchase.cheque_users = shavez`, read fail-closed.** He can log a
cheque, mark it handed over, or void it; nothing else changed for him.

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

**Changed since v1.2 [record] — one report the register does not know yet.** On 16-Sep at 23:55 an
export was refused at the door, *"no signature matches this title"*: a **BILL WISE SALES STATEMENT**
whose title row carries *"AS ON"* and **no date**, so the router could not date it. **The owner named
it: his own daily summary sale report — the one Darpan prints for the physical record and pays the
day's cash against.** The correct SALE_BILLWISE export a minute later was accepted. Teaching the router
that report's shape is owed (S262 brief); until then it is refused correctly and harmlessly each time
it is generated, and the file rests in `_REFUSED\` on manojz (§3.3).

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

**Changed since v1.2 [record] — leg B was down from 15-Sep to 17-Sep morning and the machine was not
the reason (S261).** The pull chain's own log: **146 consecutive failures from 15-Sep 10:20**, all
*medical PC unreachable*. `pipeline_status` distinguishes the machine from the share, and **the
machine answered throughout** — both Windows logins on the counter PC had been given passwords, and the
credential manojz holds for `\\<medical>\DDrive` (user `MEDICAL\SET`) no longer matched. One line, the
owner's (`cmdkey /add …`, the password typed by him and written nowhere), and **the 06:50 pull on 17-Sep
was clean** — `share_seen=1`, four steps rc 0 — and cleared the whole backlog in one pass: the 17-Sep
05:13 STOCK_CLOSING (as on 16-Sep) VERIFIED and pushed with the computed figure; the 15-Sep and 16-Sep
sale exports ACCEPTED by the server at 06:51; outbox empty. **Two lessons the lane now carries:** a
credential is a fourth thing that can fail between the machines, beside the machine, the share and the
export; and *the medical PC's own capture (leg A) kept running the whole time* — the 05:13 stock
closing was in `_captured\` before manojz could reach it. The leg that failed was the fallback.

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
**Changed since v1.2 [code]:** the VPS side has its switches too — **`S274_VPS_OFF`** (S258 close)
installed `/root/finance/sanjeevni_switch.sh` (`status` / `off` / `on` for spine, attribution, export
watch and salts refresh — marker files under `/root/finance/_off/`, *"no service, no cron line, no
database"*) and reads `/root/marg_ingest/OFF` beside them; `spine_cadence.py` honours `ALL_OFF` /
`SPINE_OFF` (lines 186–213 in the bundle). **§11.4 item 3h is therefore done on all three machines.**
The standing warning: `ALL_OFF` on the medical PC does not stop capture, by design — Marg reuses one
file name for every export, so the watcher must keep taking copies.

---

## 4 · THE ITEM SPINE

### 4.1 Items, names, facts — LIVE
`marg_spine.py` (S229; run by `spine_cadence.py` every 30 min 09–23 with `--if-changed`, nightly 23:50):
one row per product in `marg_item` (374), every spelling in `marg_item_name` (424), facts in
`marg_item_fact` (1,132 — salt, pack, MRP, from `purchase_salt_marg`, `stock_count_item`, `stock_rate`).
**Only Marg's own export may create an item**; a computed name that cannot be resolved raises a task,
never a row. *(Counts [record], 12-Sep; `marg_item` still 374 in the 17-Sep database [db].)*
**Where the spine's bytes are [code] — corrected at v1.3.** v1.2 §11.2b said the live spine *"exists
byte-exact nowhere but the box."* It does not: the 17-Sep bundle carries **`/root/finance/marg_spine.py`
and `/root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py`, both `b5956f59464671f23dc376391f9e8bae`,
and the repository's `deploy_kits/S229_ITEM_SPINE/marg_spine.py` is the same bytes.** What differs is the
**Register's pin**, `9a08b2c4…`, which has stood **DECLARED-PENDING since S229** — a prediction from
the kit that was never read back and matches nothing that can now be found. The cron runs the
`/root/finance` copy (`spine_cadence.py`, `cd /root/finance`). Re-pinning is a canon action at this
close (§11.2b, §14).

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
only a bill-wise export exists. *[db] 17-Sep 01:35: 33 exports · 502 bills · 1,551 lines; September
still 39 bills, the newest dated 12-Sep.*

**Changed since v1.2 — F-494 found (S259) and repaired (S262, `S282_LINE_OWNER`).** Bill **160 of
1-Sep exists twice** — DAANSHI PHARMA and KEDAR PHARMACEUTICAL, the same day. `purchase_line` placed a
line by **bill number and date**; where both collide the line could not be placed and was stored with
**no supplier** — five lines, present in September's month total and on **no vendor's payment sheet**.
Sixteen bill numbers are shared by two suppliers across April–September; the other fifteen resolve
because their dates differ. *A key that is unique per supplier is not unique across suppliers; the date
is a coincidence that usually holds, not a tiebreaker.* **The repair:** the ITEM WISE export carries the
same five lines under their owners, so a line whose (bill, date) names two suppliers goes to the one
supplier ITEMWISE names for that exact line, if it is a candidate; none, two, or a stranger leaves it
unowned **and named**. One anchored call in `_redate_lines` and a helper, and a one-off pass for the
five already stored — installed 17-Sep 07:38 (`purchase_app.py` `3535dc97…` → `216a0cd9…`). **[db] the
01:35 database still holds the 5 unowned lines; [record] after the install, none — the two vendors'
sheets carry them.** The same collision heals itself in future.

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
**[db] 17-Sep 01:35: still 13-Sep 10:20** — four days, two of them leg B's credential outage (§2.3),
during which nothing Amir exported could have travelled by leg B anyway; his visit was expected 17-Sep
and S285 waits on his export (§10.1).
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
settles**, not from the register itself. *[db] 17-Sep 01:35: `purchase_cheque` still 0 rows.*
**Changed since v1.2 [record]:** **Shavez writes it now** — `S284_SHAVEZ_MAKER`, by the named grant
`purchase.cheque_users` (§1.2, D529). The one September cheque, to AGARWAL SURGICALS AND MEDICALS, is
his to log.

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

**⚠ TWO SURFACES, TWO QUESTIONS, ONE VOCABULARY — corrected at v1.3 (F-493).** Two screens report
this subsection's agreement, both in the words *compared / agree / differ*, and **they are not the same
comparison.** v1.1 wrote *"the shadow at 373 compared, 370 agree, 3 differ"* and v1.2 repeated *"v1.1
recorded 373 compared, 370 agree, 3 differ"* — **373 was never the shadow's population; it is the hub
card's.** The two figures were compared across closes as if they were one series, and the plan's
condition for item 3f was read off the wrong one. From this revision on, **no figure in this book is
written without the surface it came from:**

| surface | what it compares | over what | the words on the screen |
|---|---|---|---|
| **the hub card** — *Stock verification*, `_stock_card()` in `/root/finance/purchase_app.py` [code] | the PC's **computed expected** figure against **Marg's own closing export** — `push_expected` vs `push_snapshot` rows in `stock_feed`, on the newest day that has both | the items carrying both sides that day (**373**) | *"Latest comparable day D: N items compared, A agree, X differ. K days of feed so far."* |
| **the shadow** — `sh_run` / `shadow_last.json`, `marg_shadow.py` at 23:20 and 06:20 [code] | the **server's own re-run** of the PC's arithmetic (baseline 03-09-2026 + purchases − sales from the one-door store) against **what manojz pushed** as its computed figure, for the same as-on | the baseline's items (**374**) | `same` · `differ` · `only_here` · `only_pc` · `verdict` (`same` / `differs` / **`no pc figure`**) |

**Marg's snapshot is not in the shadow's comparison at all. Neither figure is wrong; they answer
different questions.** The hub card asks *does the PC's arithmetic agree with Marg?* — and **it can
never reach zero while Marg carries two spellings of one product**: three of its nine differences on
12-Sep were exactly that (KNEE IMMOBILIS**E**R UNISON M +1 / KNEE IMMOBILI**Z**ER UNISON L −1 /
SHOULDER IMMOBILISE UNISON M −1). The shadow asks *does the server, computing on its own from the
one-door store, get what the PC got?* — which is the only question that bears on retiring the PC-side
sender (§11.4 item 3f).

**The figures, each under its own name [db], from the 17-Sep 01:35 database:**

*The hub card*, re-computed by `_stock_card()`'s own logic: **"Latest comparable day 14-09-2026: 373
items compared, 370 agree, 3 differ. 5 days of feed so far."** The day-by-day series the card would
have shown: 05-Sep 362/11 · 08-Sep 368/5 · 11-Sep 370/3 · 12-Sep 364/9 · 14-Sep 370/3 (agree/differ of
373). So v1.2's *"the disagreement has tripled"* was one day's reading of a series that moves by a few
units either way; **12-Sep was the high, not a trend.**

*The shadow*, from `sh_run` — eleven runs since 12-Sep 05:26: **runs 1–4** (12-Sep 05:26 → 13-Sep
06:20, as-on 11-09 then 12-09) **374 · 374 same · 0 differ · `same`** — four clean runs, two nights;
**runs 5–8** (13-Sep 23:20 → 15-Sep 06:20, still as-on 12-09, against the PC's `pur_to=13-09` figure)
**374 · 368 · 6 · `differs`**, `gap_units` 1,658; **runs 9, 10, 11** (15-Sep 23:20, 16-Sep 06:20,
16-Sep 23:20, as-on 15-09): **`no pc figure`** — the shadow takes its as-on from the server's own last
sale date (the one-door store, which leg A kept feeding), and that had moved to 15-Sep, while the
newest computed figure manojz had pushed was as-on 14-09 (`push_expected … pur_to=13-09-2026`, received
16-Sep 22:30); `pc_expected(con, as_on)` finds nothing for 15-09 and the run stops there. **Three runs
that are neither clean nor differing.** They do not count toward 3f's seven, and a
reader counting "quiet nights" as clean ones would have been wrong three times in a row. *Recorded,
not diagnosed* — whether this is leg B's credential outage (§2.3) starving `push_expected` or the two
legs' calendars drifting apart in general is the next thing to read, on the 18-Sep database, after the
06:51 catch-up.

**The rule this subsection now carries (F-493):** *a number carries the question it answers, or it
carries nothing.* Two surfaces measuring different things may not share a vocabulary, and a condition
written on a number must name the surface it is read from. **3f's witness is `sh_run.differ = 0 with
verdict `same` on seven consecutive runs** — never the hub card, and never a `no pc figure` run.

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

**Changed since v1.2 [record] — `S285_SUPPLIER_CHECK` (D530 · D531 · F-508), installed 17-Sep 07:55,
`amir_day.py` `a9f20622…` → `b3c20319…`.** The owner's August case: Amir entered a purchase under the
wrong supplier, found later, corrected by hand — and *Marg is consistent with such a mistake*, every
export repeats the wrong name, so nothing in the system could see it. **D530, the rule:** for each bill
still waiting for *Theek hai*, for each item on it, **if this supplier has never supplied the item and
another has on two or more earlier bills, the bill carries a warning** naming the item and the usual
supplier — on step 4, in Hindi, above *Theek hai* (*"… pehle hamesha KEDAR se aaya hai … Marg mein bill
dekh lijiye"*); one more reason under *Theek nahi*, **Supplier galat likha**, deliberately **not** a
claim for Darpan. A never-bought item raises nothing; a genuine second source trips once. Measured on the
17-Sep nightly database: **5 of 226 bills July–September would have warned**, three of them L.K. DRUG
HOUSE bills in August.
**D531 / F-508 — the part that had never worked:** S246's list joined `purchase_bill` to **every**
export that ever carried it, superseded or not, so a bill Amir corrected in Marg (which comes back under
the right supplier, the wrong one gone from Marg) stayed on his list for ever. **The list now shows only
bills a live BILLWISE export still carries**; the earliest export still decides *seen_day*, so *pichhla
baaki* keeps its meaning. *Superseded* must reach every reader of a table, not only the month total.
**[record] step 4 and the owner's day view read clean after the install; the warning shows when his
next export lands. S285's first live look is owed (START_HERE_SESSION_265 §6).**

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

**Changed since v1.2 [code] [record] — the server can now say whether its own jobs ran.** S259
measured the shape behind that paragraph as **F-495**: of 38 clinic jobs (46 cron lines resolving to
34, plus 4 systemd timers), **8 left a run record anyone could read back; 30 did not — all five nightly
backups among them** — and a job that is quiet looked exactly like a job that is passing. The fix that
was refused: a "record that you ran" line in thirty live files. The fix that was built: **45 of the 46
cron lines already name their own log**, so **`S279_JOB_PULSE`** (`/root/finance/job_pulse.py`, cron
`17 * * * *`, hourly) reads each job's own log and writes `/root/finance/job_pulse.json` — one row per
job with `last_seen` and a verdict — which the nightly bundle carries. **`S280`** corrected it the same
day; **`S283`** (v1.2, S263, installed 08:39 17-Sep, `917713f5…` → `5eae0eb7…`) taught it three words
after F-498: **EMPTY** and **NEVER RAN** are their own verdicts, distinct from **STALE**, in one
PROBLEM list. **[db] the 17-Sep 01:17 pulse (in `job_pulse.py`'s pre-S283 words): 36 ALIVE · 1 LATE
(`salts_refresh.py`, last 15-Sep 15:11 — quiet by nature: it writes only when a salt export gives it
work, and the 15-Sep list proved it alive) · 1 SILENT (`records_worker.py`, a separate app) · 1 NO TRACE (`tar`, a backup that names no log; S286
replaced it).** The seven never-fired *health legs* are a different thing from the job pulse and are
still open: they live in `freshness_legs.json` and are the parent project's **D525**.

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
ntfy is the notification layer (D425) · `finance_heal.py` every 30 min 08–21 · **`job_pulse.py`
hourly at :17 (S279 · S280 · S283) → `job_pulse.json`** — the run-record every job lacked (§10.3).
**⚠ `freshness_legs.json` — the file that decides what the health page watches — had been edited on
the box, unrecorded, for two weeks (F-507, S262):** the Register pinned it at `ad223bc6…` (S230); the
first bundle that carried it (17-Sep, S273) holds `eaa97691…`. The Register was re-pinned to the box's
bytes at S262; **which legs moved is the parent project's diff, still owed.** The rule: a file whose pin
note says *edited here* is re-pinned at every close that can read it.
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
**[code] 17-Sep:** built 01:35:03, **244 files**, md5 `10421813…`, copied to manojz at 05:05 with the
nightly database beside it; its internal manifest self-verifies. Three dated pairs are kept in the
folder (15, 16, 17-Sep). **[record] the parent's S286/S287 (17-Sep) added the asset register's own
backup and Drive copy; the job pulse's `tar` row is expected to give way to `assetapp_backup.py`,
ALIVE, on the 18-Sep bundle — an expectation, to be read, not a fact yet.**

### 11.2b · WHAT THE BUNDLE DID *NOT* CARRY — measured at S258, closed at S258's own close (S273), re-measured at S264

`code_bundle.py` takes code, templates, SQL, shell, unit files and the root crontab. It deliberately
excludes — and is **right** to exclude — any `.env`, `.conf`, database, log, `.bak`, key json,
`*config*.py`, the portal user file, the staff settings, and **anything under `_retired`,
`__pycache__`, `backups` or `deploy`**. Those walls were built at S243 after v1.0's first bundle
shipped literal passwords (F-456). **Nothing here argues with a single one of them.**

But *excluded for a good reason* is not the same as *has a copy somewhere*. At S258 every live-pinned
VPS file was held against the bundle, then every absentee against GitHub, **and then against the
encrypted state bundle's own `SRC_FILES` and `SRC_DIRS`**, and **six live-pinned files had no byte-exact
copy in any store.** **`S273_BACKUP_GAP` (the S258 close) added the six to the bundle by name**, and
the 17-Sep bundle is the proof. **Re-measured at S264 [code] [pins], the table now reads:**

| file | in the 17-Sep bundle | against the Register's pin | in the repository |
|---|---|---|---|
| `/root/finance/freshness_legs.json` | **yes**, `eaa97691…` | **matched — after S262 re-pinned it** (F-507: the S230 pin `ad223bc6…` was two weeks stale) | not in the repository, by design (configuration) |
| `/root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py` — **and `/root/finance/marg_spine.py`, the copy the cron runs** | **yes, both**, `b5956f59464671f23dc376391f9e8bae` | **MISMATCH — the Register's `9a08b2c4…` has been DECLARED-PENDING since S229** (a prediction from the kit, never read back) | **`deploy_kits/S229_ITEM_SPINE/marg_spine.py` is `b5956f59…` — the same bytes as the box.** v1.2's *"exists byte-exact nowhere but the box"* was measured against the pin, not the box, and is **withdrawn**: the live spine is in the repository and in the bundle. What is wrong is the pin. |
| `/root/assetapp/asset_register.py` | **yes**, `71bd3277…` | matched | the repository's `assetapp/asset_register.py` is `0cd8fc3b…` — a different file. The bundle is now its off-box copy. |
| `/root/deploy/email_agent.py` | **yes**, `e535c4f8…` | matched | the two kit copies (S194, S195) are different files |
| `/root/deploy/gen_live_pins.py` · `verify_live_pins.py` | **yes**, `9c402c36…` · `b4da75ec…` | matched | **byte-exact in `deploy_kits/S187_V1a/`** (the `KB_canon_all/gen_live_pins.py` copy is a different file) |
| `/root/deploy/sweep_baseline.txt` | **yes**, `01b6ad8a…` | matched | not in the repository |

**So the gap of S258 is closed by the bundle for all six, and one of the six was never a gap.** What
remains is a canon action, not a backup action: **the Register's spine pin is re-pinned to
`b5956f59…` at this close, with the S229 prediction recorded as never having matched.** The rule it
adds to F-507's: *a DECLARED-PENDING pin is a promise to read back, and a promise thirty-three sessions
old is a finding.*

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

**The shape of the gap at S258, plainly: two live applications and one live configuration file.** Not
a fault in `code_bundle.py`, which does what it says. A gap between what three backups each cover, which
nobody could see until the bundle and the pin list could be held against each other in one place —
which is what S272 made possible on its first night, and what S273 closed on the second.

### 11.3 Recover
`verify_restore.py` — the restore drill (verified 12-Sep 01:05) · every kit installer backs up to
`.bak_S###_<pin>` and rolls back byte-identical on failure · `/root/_retired/S243_2026-09-13_0007/UNDO.sh`
restores the retired residue.
**Rollbacks held open:** `finance.db.bak_S265` and `.bak_S266`; `purchase_app.py.bak_S270_34628cd8` and
`.bak_S271_800d58a3` — **keep until the cheque register has carried a month.**

### 11.4 The plan of record — restated at S264

| # | item | state at S243 | state at S258 | **state at S264** |
|---|---|---|---|---|
| P1 | this book + the estate register | DONE | DONE — v1.2 | **DONE — this is v1.3** (F-493 corrected; lives in the Sanjeevni project since D528) |
| P2 | residue out of `/root` — 495 moved, undo kept | DONE | DONE | **DONE** |
| K1 | `clinic-finance`, `staff-register`, `assetapp` on the watchdog | LIVE | LIVE | **LIVE** |
| K2 | nightly code bundle to Drive (01:35) | LIVE | LIVE, 217 files | **LIVE, 244 files** (S273 added the six of §11.2b); in reach on manojz by 05:05 (S272) |
| K3 | `stock_snapshot` Marg-only; computed → `stock_expected` | LIVE | LIVE | **LIVE** (`stock_expected` 2,619 rows [db]) |
| K4 | `/finance/purchase/` redirect · `/finance/daily` checker → review | LIVE | LIVE | **LIVE** |
| 3a | one settings file per machine | next | manojz DONE (S260) | **unchanged** — the medical PC's two settings still ride the next medical change |
| 3b | per-sender tokens, constant-time compare | next | constant-time compare DONE (S258) | **unchanged** — per-sender tokens on the owner's key rotation |
| 3d | `refused/` kept + server-side rescan | next | still next | **still next** — and the daily summary report (§2.1) is the first case that would use it |
| 3e | spine + attribution read the one-door store | after 7 clean shadow nights | not started; *"3 → 9"* — **which was the hub card, not the shadow (F-493)** | **not started.** The witness is **`sh_run`: seven consecutive runs with `verdict = same` and `differ = 0`**. Read at S264 [db]: runs 1–4 clean, 5–8 `differs` (6), 9–11 `no pc figure` — **0 consecutive clean runs on the newest reading**; the `no pc figure` runs count for nothing (§7.2) |
| 3f | retire manojz senders one at a time | after 3e | after 3e | **after 3e** — and S261's outage is the argument for it: the leg that failed for two days was the fallback (§2.3) |
| 3g | manojz live tools out of the git checkout into `margsync\bin\` | with 3a | carried | **carried** |
| 3h | OFF switch for every job | with 3a | PC side DONE (S259) | **DONE on all three machines** — VPS side by `S274_VPS_OFF` (S258 close): `sanjeevni_switch.sh` + `/root/finance/_off/` + `/root/marg_ingest/OFF` (§3.5) |
| 3i | filter full mobiles out of the Drive archive mirror | with 3a | WITHDRAWN (§13) | **withdrawn** |
| 3j | full phone numbers on the returns desk (D493) | LIVE where the master has it | LIVE; phase 2 open | **unchanged** — phase 2 (write at Apply) open |
| D1 | Darpan's `/kal` LIVE; the claim tab (D471) | next | `/kal` LIVE; claim tab next | **unchanged** — `amir_claim` still 0 rows [db]; *Supplier galat likha* (S285) is deliberately not a claim |
| P4 | Sanjeevni in its own process | after Phase 3 | after Phase 3 | **after Phase 3** |
| P5 | its own database, attached read-only | optional, last | optional, last | **optional, last** |
| A1–A4 | apply on arrival · salt list refresh · Shavez/Amir/Kal tiles · the CA report | LIVE | LIVE | **LIVE** — the salt refresh proved itself on the 15-Sep list (§10.3) |
| — | Rung 3 · vouchers · parked tiles · merges · F-436 serial | owner's word | owner's word | **owner's word — deferred at his word, 17-Sep (rule 13)** |
| **S258** | the vendor payment sheet, the bank advice, the covering letter, the workbook, the cheque register | — | LIVE (S261–S267, S270, S271) | **LIVE** — §5.7–5.9; **Shavez writes the register (S284)** |
| **S258** | the four PC-side jobs' OFF switches; one settings file on manojz | — | LIVE (S259, S260) | **LIVE**; VPS switches too (S274) |
| **S258** | the Docterz Razorpay reference kept, and backfilled from Drive | — | LIVE (S256, S257) | **LIVE** (clinic-side) |
| **NEW** | the job pulse — every server job proves it ran (F-495) | — | — | **LIVE (S279 · S280 · S283)** — §10.3, §11.1 |
| **NEW** | purchase lines owned by supplier where bill numbers collide (F-494) | — | — | **LIVE (S282)** — §5.1 |
| **NEW** | the item↔supplier warning on Amir's step 4; his list forgets superseded exports (D530, D531, F-508) | — | — | **LIVE (S285)** — §10.1; first live look owed |
| **NEW** | the router taught the daily summary sale report's shape | — | — | **owed** — §2.1 |
| **NEW** | the shadow's `no pc figure` runs read on the 18-Sep database | — | — | **owed** — §7.2 |

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
| **NEW at v1.3 ·** the S282 / S284 / S285 rollbacks (`.bak_S###_<pin>` beside `purchase_app.py` and `amir_day.py`) | VPS | **keep until each has carried a week of Amir's visits and one cheque** |
| **NEW at v1.3 ·** the daily summary sale report in `_REFUSED\` | manojz | **correct refusals, not junk** — they are the specimen for teaching the router (§2.1); leave until taught |
| **NEW at v1.3 ·** the frozen repository row `SANJEEVNI_SYSTEM_BOOK_v1_2_S258.md` | `KB_canon_all` | **frozen by D528; superseded by this v1.3.** Never edited, never deleted — the manifest names which is current |

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

## 14 · WHAT EACH REVISION FOUND THAT NOBODY WAS LOOKING AT

### 14.1 · At v1.3 (S264, 17-Sep-2026)

Five things, each read from the 17-Sep bundle and database rather than inferred; none from a screen.

**First, what came back clean:** **119 of the Register's live VPS pins matched the box's own bytes**;
the three that did not are the three files installed after the bundle was built, each found at exactly
its recorded predecessor. The Register is right on every row the bundle can reach, with one exception
below.

1. **v1.2's §7.2 carried the hub card's population under the shadow's name (F-493)**, and the plan's
   entry condition for retiring the PC-side sender was being read off a card that can never reach zero.
   Corrected: every figure in §7.2 now names its surface, and the witness is `sh_run` alone.
2. **The shadow's last three runs are neither clean nor differing — `no pc figure`** (§7.2). The
   server's own last sale date ran ahead of the newest computed figure manojz had pushed, and the
   shadow compares only the same as-on. Whoever counts "quiet nights" as clean ones is wrong three
   times running. Recorded; the cause is read on the 18-Sep database.
3. **The live item spine has a byte-exact copy in the repository and in the bundle after all**
   (§4.1, §11.2b). v1.2's *"nowhere but the box"* was measured against a Register pin that has been
   **DECLARED-PENDING since S229 and matches nothing** — a prediction never read back. The book was
   wrong because the pin was; the pin is re-pinned at this close and the thirty-three-session promise is
   minted as a finding.
4. **§11.4 item 3h was already done on all three machines** — `S274_VPS_OFF` landed at the S258 close,
   after v1.2's table was written, and no close since had moved the row.
5. **Leg B, the fallback, was the leg that failed for two days (S261)** — a stale share credential,
   while the machine answered and leg A kept capturing. The lane's fourth failure mode, beside the
   machine, the share and the export, is a password (§2.3).

*And one thing this revision did not do:* it read no live page. Every [live] row below is v1.2's
15-Sep reading, carried and so marked; where the 17-Sep database says otherwise, the database is
quoted beside it. The next revision that opens a browser should re-read §5.6, §6.4, §6.5 and §10.3
first — those are the rows most likely to have moved.

### 14.2 · At v1.2 (S258, 15-Sep-2026) — carried, with item 1 corrected

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
1. ~~**The stock shadow's agreement has tripled its disagreement — 3 differing → 9** (§7.2), and its
   latest comparable day is three days old. This is the witness for retiring the manojz senders, so it
   decides when item 3f may start.~~ **CORRECTED at v1.3 (F-493):** the 3 and the 9 were both the
   **hub card's** (373 items, computed vs Marg), not the shadow's, and the hub card is not the witness
   for 3f. The shadow that night read 374 · 368 · 6. Neither number was wrong; the name on it was.
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
*SANJEEVNI_SYSTEM_BOOK_v1_3_S264 · 17-Sep-2026 · supersedes v1.2 in full · the F-493 correction of
§7.2, §11.4 and §14, brought current to S263 from the 17-Sep 01:35 bundle and database, the Register's
pins, and the kit records of S273–S287 · no live page was read for this revision · lives in the
project "Sanjeevni — Pharmacy & Marg" and is rowed in `KB_canon_all` · the manifest decides what is
current.*
