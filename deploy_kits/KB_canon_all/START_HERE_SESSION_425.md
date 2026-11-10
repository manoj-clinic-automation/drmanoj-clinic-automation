# START HERE — SESSION 425 — written at the S423 close (the Sanjeevni chat), 10-Nov-2026 (15:1x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **The Orthotic bills card is live** (kit S771, 11:56 IST): `/finance/stock/page/hub`. **The item-wise reader joins fused / wrongly split bill numbers by evidence** (S773 13:00, S775 13:34): every October bill carries its lines. **His word at 15:08: the order-screen mock is approved — build it first** (D890).

1. **The open:** `OPEN_ROUTINE_v1`.
   - In the device VM: make your own copies (`gunzip -c D:\Downloads\_kbtools\vps_code\<day>.finance_nightly.db.gz`, `tar xzf …code_nightly.tar.gz`); **a database copy stays in the device VM** (D656). **Every python run against the repository: `-B` and `PYTHONDONTWRITEBYTECODE=1`** (F-1239). The device VM has no flask: walk in the cloud workspace on code only (`pip install flask`), the code staged by `device_stage_files`.
   - **The pins:** DECLARED-PENDING of this close — `section_count.py` a67da5a2 · `stock_hub.html` 53db6061 · `purchase_app.py` 51e42707 · `purchase_unspill.py` caf1e5cf (NEW). The 11-Nov bundle (01:35) should CONFIRM them, and S420's `stockmatch.py` 57d04d3e · `stockmatch.html` 0ec2e32d · `section_count.html` 1580a6d3 · the parent's `tile_grants.json` 66de5e20.
   - **The medical PC:** Drive `FromMedical\heartbeat.txt` (file `12pSKOTfeeGXtdu6-m2IXFDM-3f8Lkt3x`) — one watcher, `afcc3fd9`; the log `1eRmOrI_tdliI4MbBZikCt8TZ2cPHWcVG` read by a sub-agent (no traceback; an older *S679+S722* banner at a start = a watch item).
   - **Remind him once of the packs page** (D713).
2. **Read live once (sub-agent, read only):** the Items check October (`/finance/purchase/page/items?month=2026-10`) — no bill without lines; the card's six differing bills; after Amir's date corrections and a new bill-wise export, the 13 dates agree.
3. **The rules:** the charter v1.1 beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `03_WORKING_PAPERS\S423\close_parts\` — copy it, change what changed.
4. **The papers:** the brief `S423_BUILD_BRIEF.md`; the mocks `https://claude.ai/artifact/4gc42Z3vi67DUhrEBNz2Mk` (the orders, D890 — APPROVED) and `https://claude.ai/artifact/BNoWyzb4gvgs8AY5hXNaDF` (the card, built); the kits `deploy_kits\S771_ORTHOTIC_BILLS\`, `S773_UNSPILL_BILLS\`, `S775_UNSPILL_TAILS\` (their walks, makers, rehearsals — the pattern to copy).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **425 is RESERVED for the Sanjeevni chat at this close** (v1193). The parent's 424 reserved; the NK Pathology chat's 365 open; the Scan App chat's 410 reserved. **No D or F number is cited before it is taken** (F-1242).

---

## 0 · THE WORK — in order

**A · THE OPEN** — the board; the day's checks; the four numbers; the reminder; the medical PC.

**B · THE WORK**
1. **THE ORDER SCREEN (D890) — the mock APPROVED; build it.**
   - **Read whole first:** `porders_s454.py` (drift 6, 3668 lines) and `order_sheet.py` (2340) — by a sub-agent, with questions (the list builder `order_list()` :635-726, `_card()` :609, `_old_block()` :881, `old_page()` :894; `open_order()` groups :820-857, `old_day()` :879, `old_word()` :865; carries `src='carry'` :1307-1327; `order_rules.plan` is wrapped at :3019).
   - **(a) Old undelivered lines** at the TOP of *Order karna hai* (not behind *Purane pending: N*): a red box, the age in days big (old from 3 days after the order, Sundays not counted; orange under 7, red from 7), item · qty · dealer · order date, *Dobara order karo* (as `can_reorder()`), *Ab nahi milta*; on the dealer's card the line tagged *PURANA · N din*. Sources: the `old` group + `order_carry` + `late_orders`.
   - **(b) Ab nahi milta** (staff) → the line leaves today's list at once; the doctor's Needs-you line *<staff> says <ITEM> is no longer available (last bought <date>)* → **Stop it everywhere** (an `order_item_rule` 'never' marked *until a bill brings it*, cleared by itself by a Marg purchase line of the item) / **Keep ordering**. Out of the list, `order_proposal`, Darpan's tab, the only_system comparison. TOLTRIS PLUS is the first (22 proposals; last bought 28-Sep).
   - **(c) The wrong-dealer check:** an order line to a dealer who has NEVER billed that item in `purchase_line` while another dealer has → a warning on the card before sending (*Yeh dealer is dawa ko pehle kabhi nahi laya — <X> laata hai (N bill, aakhri dd-Mon)*; *<X> ke card par bhejo* / *<dealer> hi sahi*, remembered) and in the red box (*<X> ko order karo*); a weekly list for the doctor. PRETOL 8: Kedar 5 bills (last 05-Nov), Shivaaz never.
   - Staff words Hindi, his English. Walk, control, rehearsal, cold review, screen review on a local preview, read live after install.
2. **The scans for provisional data** (his 14:47 "do all whats needed"): measure October first (the Sarvam page: 54 of 81 read right; supplier 2, number 9, date 17, total 5 by the counter). The comparison in `scan_register.py` (`supplier`, `billno`, `billno_compat`, `sarvam_flags`, `autolink_ok`): punctuation; the number part (`YS/0738/2026-27` ↔ 738); a one-digit misread confirmed by dealer + date + total; a wrong year read as day-month; rounding; the paper's total against Marg's line sum (Kedar A000211: paper = lines, Marg's total +₹110); *entered N days after the bill* a named reason (D889). The second reading of an unread / far-off field is the Scan App's reader (`assetapp/claude_reread.py`): a PLANNED line on the board first (D646). Keep the Sarvam trial counter strict — it measures the reader; the judgement used for work gets the rules.
3. **Kedar 226** (paper 24-Oct, Marg 22-Oct): read the paper (sub-agent, the Scan App's page) before it goes to Amir.
4. **The first orthotics count** — when he names who and when (the card's stars feed it).
5. **F-1232** (read on the box first) · **F-1243** (Deepam 502 under Mannat, August FINAL — read, then his word).
6. **F-1220's repair**, the mock first; **the order-list kit** on his "go".
7. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v336 §2B items 7 – 10.
8. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as the Runbook v336 §2B lists), plus: change a FINAL month's lines without his word (F-1243); ship a `__pycache__` (F-1239); cite a number not taken (F-1242).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_423` listed them, plus **D888, D889, D890**.

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first — simple; he judges what he sees.** **His own pages: PC first, the Fold phone second (D853).**
7. **Two different things never share a word** — *Marg's item lines* and *the scanned paper* are said apart (his 13:43 correction).
