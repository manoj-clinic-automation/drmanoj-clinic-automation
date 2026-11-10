# START HERE — SESSION 426 — written at the S425 close (the Sanjeevni chat), 11-Nov-2026 (04:3x IST)

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. **The order screen is live** (kit S778, 19:15 IST 10-Nov; CONFIRMED by the 11-Nov bundle): `/finance/porders/s454/order` — old orders in a red box at the top, *Ab nahi milta* → `/finance/porders/s454/abnahi`, the wrong-dealer check. **His word at 04:29: the provisional-bills mock V3 is approved — build it first** (D891, D892).

1. **The open:** `OPEN_ROUTINE_v1`.
   - In the device VM: **`/sessions` may be full** — work in `/tmp/s<kit>w` (`chmod 700`), the database copy there (`gunzip -c D:\Downloads\_kbtools\vps_code\<day>.finance_nightly.db.gz`), never in the cloud workspace (D656). Flask: `TMPDIR=<dir>/piptmp python3 -m pip install --no-cache-dir --target <dir>/pylib flask`. **Every python run against the repository: `-B` and `PYTHONDONTWRITEBYTECODE=1`** (F-1239). **A device commit over an existing file: commit under a new name, `mv`, read the md5** (F-1245).
   - **The pins:** nothing DECLARED-PENDING at this close (S778 and S423's four CONFIRMED by the 11-Nov bundle).
   - **The medical PC:** Drive `FromMedical\heartbeat.txt` (file `12pSKOTfeeGXtdu6-m2IXFDM-3f8Lkt3x`) — one watcher, `afcc3fd9`; the log `1eRmOrI_tdliI4MbBZikCt8TZ2cPHWcVG` read by a sub-agent.
   - **Remind him once of the packs page** (D713).
2. **Read live once (sub-agent, read only, nothing pressed):** the order screen's box and the doctor's page (`/finance/porders/s454/abnahi`) — what the staff did with it on its first full day (*Order again*, *No longer available*, any wrong-dealer catch).
3. **The rules:** the charter v1.1 beside the parent's `BUILD_NORM_v1.md` (D704). The close is `CLOSE_ROUTINE_v1`; this project's `close.json` is in `03_WORKING_PAPERS\S425\close_parts\` — copy it, change what changed.
4. **The papers:** the brief `S425_BUILD_BRIEF.md`; the mock `https://claude.ai/artifact/EQSpsWTkBuRtqTH7fQEvKB` (V3, APPROVED, D892); the October measure `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S425\OCTOBER_SCANS_MEASURE_S425.txt` and `measure_oct_v2.py` (the rules as a script); the kit `deploy_kits\S778_ORDER_SCREEN\` (its maker, walk on made-up rows built from the live layout, proof on a copy, rehearsal — the pattern to copy).

*FIRST ACT: take your session number from the System Board's `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).* **426 is RESERVED for the Sanjeevni chat at this close** (v1203). The parent's 424 open; the NK Pathology chat's 365 open; the Scan App chat's 410 reserved. **No D or F number is cited before it is taken** (F-1242).

---

## 0 · THE WORK — in order

**A · THE OPEN** — the board; the day's checks; the four numbers; the reminder; the medical PC.

**B · THE WORK**
1. **PROVISIONAL PURCHASE BILLS (D891, D892) — the mock APPROVED; build it.**
   - **Read first:** `scan_register.py` (5712 lines; `Ctx`, `supplier`, `billno_compat`, `date_md`, `total`, `agree`, `pair_state`, `sarvam_flags`, `page_body`) by a sub-agent with questions; `purchase_app._s454_register_page` (:7909) and `_s454_bar`; the S740 returns door (`api_s740_wapsi`) before *Raise a purchase return*; S771's `section_count.py` bills card (the scan inline, `assets.db` `bill_items` READ ONLY, `amir_job` taps) — the pattern for *Check here*.
   - **(a) The month in three parts** at the top of the Purchase bills page: in Marg · scanned, not yet in Marg (provisional) · both; and the reliability line (the strict counter beside the rules' count, by month).
   - **(b) The provisional list:** each scan with no Marg bill yet (`purchase_scan_state.why = 'no_bill_yet'`, 6 on 10-Nov) — dealer · bill no. · date on the paper · total · *N lines ▸* (the read lines: item, packing, batch, expiry, quantity, free, rate, MRP, discount, GST, amount; a field not read shows *not read*) · *Reads right* / *Check the paper — <why>*. Judged by the October rules (`measure_oct_v2.py`): supplier by `supplier()` with the learnt spellings; number by `billno_compat` (a one-digit *close* only with dealer + total agreeing); date as read (a misread year named); the lines read add up to the total. It leaves the list when Marg's bill arrives (the link).
   - **(c) When Marg's bill differs from its scan:** *Check here ▸* — the scan inline (loaded on the tap, the Scan App's own route and access), the paper's lines beside Marg's newest export (a line on one side only marked), the difference named; *Amir fixes Marg* (one `amir_job` tap, Hindi) / *Marg is right — clear* / *Raise a purchase return* / *Flag something else* (short supply, damaged / broken, wrong batch or near expiry, rate above the agreed rate, free goods missing, a note) — the doctor's English.
   - **Never into stock** (D891). The counter `purchase_sarvam_check` stays strict (it measures the reader).
   - A second reading of a field the reader missed is the Scan App's (`assetapp/claude_reread.py`): a PLANNED line on the board first (D646), or leave it to that chat.
   - Walk (made-up rows, the live layout read only), control, rehearsal, cold review, screen review on a local preview (PC first, the Fold second, D853), the proof on a copy, read live after install.
2. **Amir's three more dates** (Kedar 226 → 24-Oct; Kedar A000209 → 11-Oct; Janta JP23217 → 12-Oct): the Hindi message for his paste, beside D889's 13.
3. **The first orthotics count** — when he names who and when.
4. **F-1232** · **F-1243** (read, then his word).
5. **F-1220's repair**, the mock first; **the order-list kit** on his "go".
6. **Small / his / staff / parked / not ours:** as `HANDOFF_RUNBOOK` v337 §2B items 6 – 9.
7. **The close** — `CLOSE_ROUTINE_v1`.

**NEVER** (whole, as the Runbook v337 §2B lists), plus: add to stock from a scan (D891); change a FINAL month's lines without his word (F-1243); ship a `__pycache__` (F-1239); cite a number not taken (F-1242).

**THE RULINGS THAT STAND:** as `START_HERE_SESSION_425` listed them, plus **D891, D892**.

## 1 · THE STANDING OWNER RULINGS

1. **Publishing is HIS double-click** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. **ONE line per command.**
3. **Token-lean — never at the cost of verification.** **Plain language. Short chat. English to him.** **ALL-CAPS = urgent.** **"Only answer" / "do not build" = study and answer only.**
4. **Mask patient numbers (last 4); never print secrets.** **Nothing live is rebuilt without his OK; the manual path stays.**
5. **Sub-agents read screens. Do not hand him diagnostics. When a screen is wrong, read its code first.**
6. **Never put a technical choice to him** — decide, say it in one line. **A screen for staff or for him: the mock first — simple; he judges what he sees.** **His own pages: PC first, the Fold phone second (D853).**
7. **Two different things never share a word** — *Marg's item lines* and *the scanned paper* are said apart.
