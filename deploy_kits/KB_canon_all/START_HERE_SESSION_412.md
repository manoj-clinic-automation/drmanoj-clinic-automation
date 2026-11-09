# START HERE — SESSION 412 — written at the S411 close (the Sanjeevni chat), 09-Nov-2026 (05:4x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **No code changed at S411.** It placed the S408 close's canon (the shell had been down), read the Sanjeevni Hub (`/finance/approvals`) live and mocked its redesign. **The owner approved the Returns mock (D873): newest first, petty refund differences gone.** This session: **finalise the summaries snapshot mock with him, then build the hub** — his words: *"will finalise summaries snapshot mock and hub build in next session".*

1. **The open:** follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`).
   - The device shell answered all through S411 (F-1197 not seen). If it fails, work as S408 did: the live code from the newest bundle, code only in the cloud (D656), placed by the file tools and read back by hash.
   - In the device VM: `TMPDIR=/tmp/s412w`; `pip3 install --no-cache-dir --target /tmp/s412w/pylib flask` and `PYTHONPATH=/tmp/s412w/pylib` when a walk needs flask. **The live code = the newest bundle** (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`): the 09-Nov bundle confirmed every pin of this project — DECLARED-PENDING 0.
   - **Remind him once of the packs page** (D713) **and F-1133** (D837) — one line each, no build.
2. **The rules:** the charter v1.1 (`claude/S307_BUILD_CHARTER_v1_1.md`) beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S411\close_parts\` — copy it, change what changed; a kit's Book section goes back in (`"book"`).
3. **This close's papers:** the brief `S411_BUILD_BRIEF.md`; the mocks on the Design canvas:

```
https://claude.ai/artifact/8JhQwrXJ56WAtdCZGUUHN1
```

   Page *Hub page*: `Hub.dc.html` (the whole hub, PC) and `GoTo.dc.html` (every pharmacy page). Page *Returns*: `Main.dc.html` (the card, PC — approved), `Batch.dc.html` (the batch check's two answers), `Phone.dc.html` (Fold phone). Read the canvas first (`Artifact` read, `project/canvas.json`, then the boards) — he may have commented or edited.

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **412 is RESERVED for the Sanjeevni chat at this close.** The NK Pathology chat's 365 and the parent's 404 are open; the Scan App chat's 410 reserved. A kit number before the scratch folder is named; D and F at the close; re-read `_numbers` just before every pinned write (read with `out_dir`, write with `file_path`).

**Connections and machinery:** connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`. **Never `git` in the device shell** (F-511, F-1152) — read `.git\refs\heads\main`, `.git\refs\remotes\origin\main`, `.git\logs\HEAD` as files. Placing a kit: `cp` in the device shell; `rm` is refused in a connected folder, `mv` within it works (`_to_delete_S412\` + `WHY_SAFE.txt`). **The S755 kit is the pattern to copy** (`deploy_kits\S755_SUMMARY_REMINDERS\`): makers with anchored edits on the live bytes · the walk with a CONTROL · the earlier walks compared · the proof by the live files, `mode=ro` · the installer rehearsed · a cold review until SAFE · the screens read live by a sub-agent as manoj. **A close's pin rows are `| path | full md5 | state |`** (F-1198).

**What S411 read live (keep it):**
- **The hub** = `https://followup.dr-manoj.in/finance/approvals` (tile *Sanjeevni Medicos*; `finance_ui/finance_approvals.html` served by `finance_app.py`; its data from `sanjeevni_approvals.py`, the Returns card from `/finance/darpan/api/cn-detail?month=` with `returns_kinds`). Cards: alertBar, oosBar, needsCard (38 `li`, colour on the dot, `goSec(...)`), daysCard, cashPosCard, bankCard, returnsCard (`loadCN`, `cnLineHtml`, `cnDetailHtml`, `cnStatusHtml`), porders, monthsCard, checksCard (18 folds), linksCard (*Other pages*).
- **The waiting returns (10, ₹6,430):** CN00283 05-Nov · CN00264 22-Oct · CN00247 10-Oct · CN00245, CN00244 09-Oct · CN00243 08-Oct · CN00236 05-Oct · CN00203 08-Sep · CN00198, CN00197 02-Sep. Batch repeats: TYRO BR LGQ07/107/11 (3), TRAMAVIN P 260306 (2). *Can't be checked yet:* CN00286, CN00215, CN00208, CN00201, CN00200.
- **F-1200:** the *withheld* badge ignores `returns.noise_p` / `noise_pct` (`diff_p` null, `noise` false on those notes). **F-1199:** Cash *2 days awaiting* vs Days 4; *banked* ₹8,00,000 vs ₹23,70,600; *13 items* naming 8.
- **The summaries:** row 7 of `https://followup.dr-manoj.in/finance/purchase/page/check?month=2026-10` — header at 89% of the closed page, the 6 awaited ~1,000 px inside it (Bass, Ess Kay, Jubilee, Kedar, Krishna, Saisun); also on reception's `/finance/porders/s454/billkaam` (*Scan the dealer's month summary · 6*) and the pay page's *Dealer's summary* column. No dealer-facing message exists for summaries; `supplier_msg` (S407, D623; the reception phone's MacroDroid, one a minute while awake) is the road for a reminder — **never send one without his approved wording (charter; NEVER below).**

---

## 0 · THE WORK — in order

**A · THE OPEN (OPEN_ROUTINE_v1)** — the board (messages to `sanjeevni`; his notes); the day's checks; the four numbers; the two one-line reminders. Read the canvas for his comments.

**B · THE WORK**
1. **THE SUMMARIES SNAPSHOT MOCK — finalise with him** (add boards to the same canvas, page *Summaries*): at the top of the purchase check, one screen — the awaited dealers (bills, Marg ₹, days waiting, last reminder), the one that differs, the agreed folded; earlier months still awaited shown too. **The dealer reminder:** from the 7th of the next month, one WhatsApp a day to each awaited dealer through the reception phone until its summary is recognised; skipped for *gives no summary*; *number missing* shown; a pause per dealer. **His three decisions:** the wording (draft it), the hour, Sundays. Then the build plan.
2. **THE HUB BUILD** (D873; the canvas is the spec): the Returns card as approved (newest first; F-1200; the batch check as a count; Reject on the questioned amount; can't-be-checked; months folded; history); Needs you grouped (red first; *arrived but not in Marg* by dealer; information folded); the Go to panel with live counts (Amir's step page left out — its GET writes); Cash and Bank as figures; F-1199. Read each file whole first; the mock is approved before code for any part he has not yet seen settled. **A PLANNED line on `board/_numbers` before touching a file the parent owns** (D646) — `finance_app.py` is the parent's.
3. **F-802's permanent fix** — its own small kit (D867 / D868; `START_HERE_SESSION_411` B1).
4. **The order-list kit**, on his "go", the mock first (`S402_ORDER_LIST_PLAN.md`).
5. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v324 §2B items 5 – 8.
6. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as `START_HERE_SESSION_411` listed): run `deliver_S488.ps1`; install S638 / S672 / S673; add to Amir's *Aaj ka kaam* list (D690); change the expiry page without his word; change the meaning of a name the parent's console reads without a word to the parent; put anything but fixed text and pictures on the flow pages; book a voucher in `sp_move`; **send a supplier WhatsApp or tap a staff or owner button for him without his explicit word**; let a tap stand for a Marg correction; let a counted difference be nobody's; call a writer from a page or create a table from a reader; take the pharmacy's own name as a dealer or match a short bill number as a tail; run S751 again or convert a staff scan by hand; **put another patient's name, ID, phone or bill on his screen in a returns check** (D873).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_411` listed them, plus **D873** (the Returns redesign, above).

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first.** **His own pages: PC first, the Fold phone second (D853).**
