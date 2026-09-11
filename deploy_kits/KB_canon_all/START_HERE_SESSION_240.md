# START HERE: SESSION 240
**Written at the S239 close, 11-Sep-2026 (IST).** A new chat in the same project. **Read this whole file
first.** It carries the full context for the work he approved (Sanjeevni items 1–3), the August lock,
Amir's exports, Docterz and the staff app, so you should not need ten papers. Open `S239_BUILD_BRIEF.md`
only for build detail, and `claude/S239_SANJEEVNI_RESTART_PLAN.md` before building.

---

## §0 · THE STANDING OWNER RULINGS (restate these every session)

1. **Publishing is his double-click.** Name one file, with its full path:
   `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. **Always give full paths, including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **One line per command**, machine named above it. Use `\cp`. Never glue two commands together.
4. **Work token-lean, but never skip verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS from him means urgent.**
6. **Mask patient numbers to the last 4 digits; never print secrets or tokens.** The repository is
   PUBLIC (F-185): it holds no number at all.
7. **Nothing live is rebuilt without his OK; the manual path stays as the fallback.**
8. **Sub-agents read screens.** Screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask only for the one action nobody else can do.
10. **When a screen is wrong, read the screen's code first.**
11. **Do not put technical choices to him. Make the call and state it.** (He said it again at S239:
    *"It is your tech call. And if it is a sound and safe tech call, then I give my go ahead."*)
12. **IST times only.** The container clock is UTC.
13. **English with him; Hinglish for anything staff read.**
14. **Moving is the assistant's; deleting is his.** Never propose deleting anything whose surviving copy
    is not proven.

**Rulings that carry forward:** D442 his stated record is the authority · F-411 hash before reasoning ·
F-414 a probe copy must prove it read the live inputs · **F-428 (new): "ready" names the next human step,
never the state of the code** · **F-426/F-427 (new): render a permission preview from the grants file
and read the login list off the box before writing a per-user rule.**

---

## §1 · PHASE 0: connections, then verification, then work

1. **Connections, by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` · the assistant's
   browser. All three folders were connected at S239. ⚠ **The device shell mounts nothing** (Windows
   update of 8-Sep). Work is stage → container → commit → **verify md5 after staging back** — it worked
   for every file of S238 and S239. **F-242 is fixed on the server**, so the assistant's browser should
   now show the login form instead of looping: sign in once if it is needed.
2. `CANONICAL_MANIFEST.md`; verify rows by md5 from inside `deploy_kits\KB_canon_all\`. Halt on a hash
   mismatch, never on a missing file.
3. Tier 0 only, then `OWNER_TODO_LIVE.md`.
4. **Canon at this close:** Archive **v1.86** · Register **v5.89** · Fault Register **v2.71**
   (F-0 … F-428) · Runbook **v170** · this file · `S239_BUILD_BRIEF` · manifest.
5. **Next free: D463 · F-429 · Session 240.**

---

## §2 · THE FIRST FOUR CHECKS (each has a clock on it — do them before building)

### §2a · ⏰ Where is the August lock? (D460 — his sequence, not ours)

**Not locked at the S239 close.** His words: *"not ready for lock. It is ready for the initiation of the
lock process with the attendance verifier from physical sheet going into the staff today. Their advanced
checking going into them, and after their approvals, they will go through this sheet … then the
corrections … and then the salary sheet lock. … by today evening or maximum tomorrow."*

The sequence: **1** staff verify attendance against the physical register (Step 0) → **2** staff check
their advances → **3** staff approvals → **4** he reviews the money sheets → **5** corrections → **6** lock.
**Ask him in one line which step he is on, then help with that step only. Never lock for him.**

```
https://attendance.dr-manoj.in/register/salary/flow/verify?ym=2026-08
```

```
https://attendance.dr-manoj.in/register/salary/flow?ym=2026-08
```

- Money page as he now reads it (S239, `salary_policy.py` v1.16 `c7577174…`): fines table without
  "Leave days counted", with Late minutes, Overtime (min, ₹) and Cover duty as `₹ (days)`; part-time staff
  (Amir Sohail) in their own "days punched" list and paying **no leave charge** (D459). Amir's August net
  ₹2,500.00 — correct: he joined the biometric machine on 06-Sep, so August has no punches.
- Darpan read −4,443.82 until his missed punches are fixed (S238) — a Step 0 question, not money.
- **The lock is the first ever (F-407).** Read its output back.

### §2b · Amir's Marg exports

**Missing at 09:50 IST on 11-Sep: no purchase report since 06-Sep** (none on 8, 9, 10 or 11-Sep by then);
last stock closing 08-Sep. A re-check was scheduled for 12:15 IST in the S239 chat. Re-check by staging:

```
D:\Downloads\margsync\MargArchive\index.csv
```

```
D:\Downloads\margsync\MargPull\_last_pull.txt
```

Look for `PURCHASE_*` rows `seen_at` 11-Sep or later. If still missing, tell him in one line: PURCHASE
BILL WISE · PURCHASE BILL ITEM WISE · PURCHASE SUPPLIER WISE, each **01-09-2026 to today**, plus today's
STOCK CLOSING. One export each covers all missing days. **This is also plan item 1's first real input.**

### §2c · Read one hash the S239 close could not

The VPS call-list picker was patched by his sed line (`PATCHED`) but its new md5 was never read. Ask for
this one line (VPS):

```
md5sum /root/wa/push_followups_vps.py
```

Record it in the Register's live-file table (the row says *to be read at the S240 open*).

### §2d · Docterz — is the pickup healthy?

Stage and read (the heartbeat should be minutes old on a clinic day):

```
D:\Downloads\DocterzArchive\_last_pass.txt
```

```
D:\Downloads\DocterzArchive\_pickup_log.txt
```

```
D:\Downloads\DocterzArchive\DOCTERZ_SHOUTS.txt
```

Also still unverified from S238: the Day Revenue 09:30 cron run (`/root/finance/logs/docterz_ingest.log`
has entries; 11-Sep's sheet loaded). A shout or a quarantined file is read before anything else.

---

## §3 · THE WORK HE APPROVED FOR THIS CHAT — Sanjeevni plan items 1, 2, 3 (D462)

**His words at the S239 close:** *"It is your tech call. And if it is a sound and safe tech call, then I
give my go ahead for that, but not in this chat session. We do EOS here, and then in the same project, in
a fresh chat, we start with this work."* The work is the first three items the assistant offered when he
asked what could start without inputs (full plan: `claude/S239_SANJEEVNI_RESTART_PLAN.md`):

1. **Missed-export check, keyed to Amir's punches.** A red line on his card and the owner's when Amir
   punches in but the purchase reports or the stock closing do not arrive by close of day. Inputs that
   already exist: his biometric punches (the staff register; he is `dates_only_staff`, on the machine
   since 06-Sep) and `MargArchive\index.csv` (on manojz — the VPS sees only what the gate pushes; decide
   where the check runs and state it).
2. **The item spine refreshing itself (Rung 4 cadence).** After every capture and nightly, with a short
   "what changed" drift report (new names, new unresolved, new tasks). It has run once, 07-Sep.
3. **Bill-history backfill (Rung 1).** Every archived SALE_BILLWISE export's bill totals (gross,
   discount, tax, dr/cr, net) into `sale_bill`. **The assistant's call at S239: ship the archived exports
   through the existing `marg-push` door, not a copy of the database.** Clubbed with item 2 as one
   scheduled job.

**Then, in order (no new input needed):** 4 T1 install + Rung 2 attribution (fixture A003495 to the
paisa: ₹3,170 gross, ₹870 discount, ₹2,300 net) · 5 three-column stock view + stale-export refusal ·
6 the check for Amir's 22 renames · 7 draft of Amir's app picture · 8 draft fixes for the six confusing
money-tile names and the dead tiles. **Waiting on him:** his yes on the Amir app picture; Rung 3 "say the
word"; vouchers "share it". **Waiting on Amir:** the renames in Marg; daily exports. **Waiting on Ram
Singh (not blocking):** per-line rate/discount/amount in the Excel sale export; wider names.

**How each item ships:** build offline against the newest nightly `finance.db` (take it from the nightly
bundle, never by asking) → live-shape walk → kit with SUMS verified from inside its folder → publish (his
double-click) → one VPS line `bash /root/deploy/vps_deploy.sh <KIT>` → read back GREEN. Build beside,
never over; every URL keeps working; nothing visible changes until he compares side by side.

### §3.1 · The architecture (unchanged since S238 — data only flows inward; the VPS cannot reach a PC)

- **Medical PC** (Marg; user `SET`): staff export to `D:\MARGERP\users\<id>\report\REPORT_n.XLS`;
  `marg_watch.py` catches into `D:\SendToClinic\_captured\`; `medical_agent.py` heartbeat + hourly Marg
  backup to Drive.
- **manojz** `D:\Downloads\margsync\MargPull\`: `PULL_FROM_MEDICAL.bat` every 10 min (Tailscale SMB,
  read-only); `marg_router.py` routes by content (17 signatures) into `MargArchive\<TYPE>\<YYYY-MM>\` +
  `index.csv`; `marg_gate.py` POSTs to `https://followup.dr-manoj.in/finance/api/marg-push`;
  `pull_watchdog.py` every 15 min; nightly push 22:30.
- **VPS** `/root/finance/`: `finance_app.py`, `finance_ingest.py`, `marg_report.py`, `marg_backfill.py`,
  `stock_app.py`, `sale_bill.py`, `finance.db`. **The push is parsed and the file deleted in the same
  request — the VPS keeps no export files.**
- Spine: `marg_item` 374 · `marg_item_name` 423 · `marg_task` 41 open · `marg_name_unresolved` 10 ·
  `marg_spine_run` one run (07-Sep). Pins: `marg_spine.py` `9a08b2c4…` installed (a newer `b5956f59…`
  is installed nowhere); T1 `marg_discount.py` `a49c733f…` built, not installed. ⚠ **F-395:** live
  `marg_report.py` `f9370dde…` and `finance_ingest.py` `747b4a50…` match no repo copy — never edit them
  from the repo.
- Amir's page: `https://followup.dr-manoj.in/finance/purchase/page/salts` (salts + the 22 renames).

---

## §4 · DOCTERZ — what is live now, and what is next

- **Ask 1 LIVE (D455):** task **DocterzPickup** every 5 min on the tracker PC runs `docterz_pickup.py`
  rev 2 `d117786f…` in `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\`. State in
  `D:\Downloads\DocterzArchive\`. `/run` untouched — the fallback. **After several clean days, tell him
  reception's upload step can retire.** Manual refresh of today's call list: `START_DOCTERZ_PICKUP_NOW.bat`
  in the tracker folder (or `python docterz_pickup.py --refresh-latest`).
- **D456 LIVE:** both call-list pickers choose the latest call day by the date in the file name.
- **Ask 2 MEASURED, NOT BUILT** — he said *"We will build this later."* Plan in
  `claude/S239_CLINICAL_DATA_REPORT_MEASURED.md`: diagnosis daily (fix F-425, the seeder that read 0
  rows and said "refreshed") → lost-script list → drug→Marg item map → follow-up cross-check → tests
  ordered vs done. **Only when he asks.**
- Small, carried: Day Revenue freshness leg 200 h → 26 h · rotate `docterz_ingest.log` · F-423 (the
  workbook name collision, mitigated) · **F-424 — his ruling:** the tracker's `data\` folder shows a
  Drive-upload marker (PHI may be syncing to Google).

## §5 · THE STAFF APP (phase 1 LIVE, D457)

`tile_grants.json` v10 `812cbbc6…`. Shavez (manager): Call Tracker · Forms & Downloads · Asset Register ·
Scan Purchase · Staff Ledger — Entry · Vaapsi Desk · Docterz Revenue. Shivani, Alisha: Call Tracker ·
Forms & Downloads · Scan Purchase · Vaapsi Desk · Docterz Revenue. Darpan: Forms & Downloads · Scan
Purchase · Daily Sale · Vaapsi Desk. Attendance and Staff Register held from all ten staff logins.
Install card (Hinglish + WhatsApp text): `D:\Downloads\Staff_App_Install_Card.html`. **Open:** did the
four install it and sign in? Any phone that still hangs: open
`https://followup.dr-manoj.in/portal/login` and sign in once (F-242 fixed, D461). Collapsible tiles:
later, with Amir's app (plan item 7).

## §6 · THE MARG VENDOR (unchanged)

Ram Singh (Marg dealer). Excel bill-wise sale export still 9 columns, one discount per bill (F-385);
names cut at 20 (sale) and 29 (stock). Ask him in one line whether the message went and what came back.
Test: header of any sale export stamped after 09-Sep 18:11 — more than 9 columns, or names longer than 20.

## §7 · EVERYTHING ELSE OPEN (full list: `OWNER_TODO_LIVE.md`)

Staff-money remainder (statement page rewrite — he sees the screen first; loan-restatement row;
actual-paid on the lock; the register's advance deduction reading only the ledger's month rows, D349) ·
Darpan's loan workbook (₹1,000 split, April SKIP) · tranche B terms · F-413 (numbers in the inherited
Archive — his ruling) · UptimeRobot on the wrong domain · arms licence 27-Sep · MyOperator token overlap
· `gen_live_pins.py` not found (no pin list since S234) · **his PC tidy: `TIDY_TO_DELETE_S239.bat`** (see
`OWNER_TODO_LIVE` §9 — read the log it wrote if he ran it).

## §8 · THE FIVE STORES, AND THE ONE RULE

project knowledge = canon · GitHub = code + `deploy_kits/KB_canon_all/` (PUBLIC — no numbers) ·
`D:\Downloads\ClaudeCowork\` = everything canon excludes · `F:\ClinicBackup\` = mirrors and cold kits ·
Drive = not set up. **No document may be live and editable in two stores.** The manifest decides.

---
*START_HERE_SESSION_240 · written at the S239 close, 11-Sep-2026.*
