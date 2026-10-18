# REPORT_S582 — X-ray costs (S582_XRAY_COSTS, D736) — built, walked and rehearsed; NOT installed, NOT published

**For Dr Manoj (plain English):**
- A new page, **"X-ray costs"**, is ready for your menu, right after Batteries. Only you see it. It shows the **X-ray department's
  expenses month by month**: X-ray films (counted exactly as The month counts them), any paper you mark for X-ray (for example B-0163,
  the envelopes, which stays in Stationery & packaging), the service, repair and cover of the machines you tick, and the batteries of
  the X-ray battery places. Each rupee is counted once.
- When it is installed, B-0163 and the two battery places "Digital X-ray" and "X-ray detector (FDR) battery" are marked for you.
  **B-0163 will show but add ₹0 for now:** it is still a challan waiting for its bill, with no amount, and The month doesn't count those
  yet either. A Personal paper you mark also shows without adding, because it isn't in any section of The month.
- It has been fully tested on a copy, with made-up entries only. Nothing on the live server has been changed.
- It is waiting for the Scan App chat's check. Then you publish and paste one server line (at the end of this report).

---

## For the chat

**Run:** 18-Oct-2026, 15:17–15:50 IST (box and PC clocks, read). The brief (v2) and `S582_BRIEF_R1.md` were read whole (md5 read back
`d3e0fa69fbb9367b94ee5a1861428957` = the brief's pin). Every BLOCKER and CORRECTION was built as R1 words it; the NOTES as below. Box clock
is IST (`timedatectl`: Asia/Kolkata), so R1 N7 needs nothing.

### Pins — read on the box at 15:17:27 IST, before anything was built
| file | brief's pin | live | role |
|---|---|---|---|
| `/root/assetapp/batteries.py` | 40eb8a91 (S575's TO) | **40eb8a91** ✔ | edited (2 counted edits) |
| `/root/assetapp/xray_costs.py` | — (new) | absent ✔ | NEW |
| `asset_register.py` | c39c084e | c39c084e ✔ | read only |
| `sorting_desk.py` | 110335ea | 110335ea ✔ | read only |
| `clinic_papers.py` | 6db07c12 | 6db07c12 ✔ | read only |
| `asset_machine.py` | 7d4fdffc | 7d4fdffc ✔ | read only |
| `stationery.py` | d11d7183 | d11d7183 ✔ | read only |
| `scanner_widget.js` | 10a8bb29 | 10a8bb29 ✔ | read only |
| `/root/finance/packs.py` | e46264b8 | e46264b8 ✔ | read only |

**FROM → TO (the kit's pins):** `batteries.py 40eb8a916aee48ef5a49337d3c4cc81d → 775471e6f7f4b8356142aafccdccfddd`;
`xray_costs.py (new) → 22e59f5a275d687bae767da8bf776a6a`. Both read back in the rehearsal's made-up root after placing. **Live, after
everything (15:45:33 IST):** batteries.py 40eb8a91, no xray_costs.py, no `.bak_S582_*`, no `xray_mark` table, lock free, healthz 200,
`/xray` 404 (not installed — as intended).

### The two counted edits (make_s582.py, each anchor found exactly once)
- **E1** `batteries.menu_items`: builds `[Batteries]` and appends `xray_costs.menu_items(role)` when `xray_costs` is loaded and MOUNTED,
  inside its own try/except (a failure prints "S582 menu: …" and Batteries shows as before). `xray_costs.menu_items` gives the item only
  to role `owner`.
- **E2** end of `batteries.init`, after `MOUNTED = True`, before `return VERSION`: guarded `import xray_costs; xray_costs.init(ar)`; a failure
  prints "xray_costs NOT mounted: …" to stderr and never leaves `batteries.init`.
- asset_register.py and sorting_desk.py (drift 8, F-836) not touched.

### What xray_costs.py does (as built)
- `/xray` (`s582_xray`) and `/xray/mark` (`s582_mark`, POST) inside `checker_required`, with its own owner gate (a manager gets 403; not
  batteries' `_gate`, which lets a manager in — R1 names this).
- **Films:** `MONTH_SECTIONS` looked up by key `xray`; `money, finals = sd._s566_paid_rows(db, key, subs, ym)`; total =
  `sd._s566_total(list(money)+list(finals))` (C1). Desk mounted test = `AR._s559_desk_mod()` (C2); not mounted → "The sorting desk is not
  mounted … ₹0".
- **Find by stamp:** `batteries.by_stamp(db, typed, True)` (C3) — B-0162 / B162 / b-162 / 162; refused papers get one line.
- **Marked papers (C4):** counted only if in `money + finals` of `_s566_paid_rows` for the section holding its `subgroup`, for the month
  `CP.MONTH_OF` gives it; else "not counted: <why>" in the brief's order (rejected / set aside · second scan · a page of B-x · challan
  awaiting · challan joined to B-x · challan closed · receipt · statement · held double (D710) · in no section of The month · not on the
  clinic lane · not accepted). A counted paper with no amount is counted ₹0, flagged "no amount". Pharmacy and patient papers are never
  listed (D722).
- **Machines (C5):** `service_logs.cost` by month of `log_date` (asset_id only, NULL = ₹0, as `totals_line`); `asset_cover.cost` by month
  of `from_day`, `asset_created_at = assets.created_at AND voided_at=''`; a cover with no `from_day` → the month of its `at`, flagged
  "no from-date" (R1's pick, stated). Never the purchase price. Non-ISO dates → "Date not read" at the top, no month (N2; the live
  database has 0 service_logs and 0 asset_cover rows today, 14 battery fittings all ISO).
- **Batteries:** `battery_fit.price` by `fitted_on`, `voided_at=''` (the brief says *price*; the old-battery amount Jasoria pays back is
  NOT subtracted — a decision for the chat if the net is wanted). A place with `active=0` still counts.
- **Each rupee once — the rule as built (C6, C7):** (1) every spend / cover / fitting of a ticked machine / place (all months) claims its
  paper(s): the bill, and for a fitting the warranty card too — only when `bills.created_at = bill_created_at`; `none:old-battery` is no
  paper; a mismatch → "paper link stale", claims nothing. The row's own cost counts; its paper is shown under it "its paper B-x" at no
  amount. (2) X-ray films: a claimed film paper is listed "(counted there)" and the fold says "The month shows ₹N … ₹M of it (B-x) is
  counted under <row>". (3) Marked papers: claimed → "its paper — counted under <row>"; already a film paper this month → "already counted
  under X-ray films"; else the C4 rule. One paper claimed by two rows → each row's cost counts, both flagged "one paper, two entries —
  check". A marked purchase paper of a machine counts, flagged "purchase paper of <machine>" (N3). **Not detectable:** a spend entered
  on a ticked machine AND as a battery fitting of a ticked place with no paper on either.
- **Marks:** table `xray_mark` exactly as §3.4, `CREATE UNIQUE INDEX xray_mark_live … WHERE removed_at=''`, every mark INSERT OR IGNORE, sums
  over live marks whose record still carries the fingerprint (a re-issued id inherits nothing). Unmark sets `removed_at/removed_by`. Every
  mark / unmark audited in `desk_audit` (`xray_mark`, `xray_unmark`; the seed `xray_mark_seed`). No write to bills, assets, battery_place,
  battery_fit (walk-checked).
- **Seed (B2, C8):** never at mount. Data step `python3 -B xray_costs.py --ensure <db>`: B-0163 by stamp (with `bills.created_at`), the
  places by EXACT names "Digital X-ray" and "X-ray detector (FDR) battery" (with `made_at`); each absent one → one printed line; no
  machine; any row of that key in `xray_mark`, live or removed, means "leave it" (read the table, not the audit). My reading of "if it is
  not found, seed nothing": the paper and each place are judged one by one (the brief's C8 wording) — a missing B-0163 does not stop the
  two places.
- "Total since <first month>": loops from the earliest candidate month to the current month through the same `month_view`, cached per
  request (N5); the label is the first month whose total is not ₹0.

### The walk — `walk_s582.py` (made-up rows; a scratch copy of the live assets.db on the box; 15:45:49–15:45:55 IST)
**14 checks: 14 GREEN.** W1 (structural), W2, Z1 (structural: the mount adds only `xray_mark` + `xray_mark_live`, 0 rows), X1 films by The
month's rule (₹1,900 = The month's own figure; receipt, awaiting challan, set-aside out; ₹400 film paper claimed by a cover → fold ₹1,500),
X2 marked Stationery paper counted ₹1,200 and its row unchanged, audit lines present, X3 not counted twice, X4 machine spend ₹2,500 +
cover ₹8,000 + no-from-date cover ₹50 = ₹10,550 (April spend, voided cover, ₹5,00,000 purchase price, unmarked machine out; "looks like
X-ray" listed first, never ticked by the system), X5 battery ₹20,000 (voided ₹9,999 out), X6 each rupee once (fitting's bill and
spend's paper claimed; stale link claims nothing; month total ₹33,900 = 1,500 + 1,850 + 10,550 + 20,000), X7 manager 403 on page and
POST, no menu item; owner's menu Machines · Batteries · X-ray costs · Renewals, X8 Personal paper markable, "not counted: in no section of
The month", never on a manager's page, X9 re-issued id inherits no mark, X10 the seed on a schema copy with made-up rows of the same
names (marks 3 · second run 0 · an unmarked seed left unmarked · absent paper / name skipped with one line each · two runs at once → one
live mark each), X11 FROM vs TO in fresh processes: manager's The month / Batteries / place / machine pages byte-identical; owner's
identical after removing exactly one bar element "X-ray costs" (and a changed word on the TO page is caught).
**Negative control** (`--expect-red`, FROM files): **12 of 12 MUST_RED red** (W2, X1–X11); W1 and Z1 structural, green on both.
**Browser** (`walk/browser_xray_s582.py`, PC headless Chrome, 15:46:05–15:46:09 IST): V1 GREEN at 1366 × 768 and 1366 × 620 (all six folds
open: no sideways scroll; 26/26 amount + paper cells, 70/70 tick boxes, the mark box and both Saves inside the width); its control (a
table forced to 1900 px) RED.
Full output: `deploy_kits/S582_XRAY_COSTS/walk/walk_results_s582.txt`.

### The rehearsal — `rehearse_s582.sh` on a made-up root (/tmp/s582reh), 15:40:24–15:44:03 IST — **REHEARSAL GREEN**
1 fresh install green: all walks inside the installer green — S582 14/14 + control 12/12 red · S575 8 · S571 12 (line 354 in S582's form) ·
S568 14 (see below) · S566 12 · S563 17 + tidy fetch (102 = 102, no difference) · S560 37 + pack 9 · S548 8 · S559 43 (M1 unchanged) · S557 41 ·
S555 19 · S551 87; backups `batteries.py.bak_S582_40eb8a91` and `assets.db.bak_S582_20261018_154025` (before the restart); both files
placed and read back at their pins; /healthz 200, /desk /batteries /xray 302; **the data step on the made-up root's copy of the live
database: "seed: paper B-0163 — marked for X-ray", "seed: battery place Digital X-ray — marked for X-ray", "seed: battery place X-ray
detector (FDR) battery — marked for X-ray", live marks 3**; database check: only `xray_mark` + `xray_mark_live` added, the 38 earlier
tables' rows unchanged (desk_audit only appended with 3 `xray_mark_seed` lines), the backup = the database before. 2 ALREADY INSTALLED.
3 forced red, 4 /desk 404, 5 /desk 200, 6 /xray 404 → each restored batteries.py to 40eb8a91 and moved xray_costs.py aside as
`.undone_S582`, healthz 200. 7 batteries.py moved, 8 sorting_desk.py moved, 9 batteries.py missing, 10 packs.py moved, 11 a foreign
xray_costs.py present, 12 a half install (batteries at TO, no xray_costs.py) → each REFUSED before any backup or placing. End guard: the
live scan app's and finance folder's program files unchanged.

### Backups made / services restarted
None on the live box (this run does not install). In the rehearsal only, under /tmp. No service restarted (the rehearsal's restart is
`true`).

### R1 items, how each was met
B1: `lines_s582.py` rewrites S571's line 354 (found exactly once) to accept Batteries · Renewals **or** Batteries · X-ray costs · Renewals.
Note: S571's walk copies only its own MODS (no `xray_costs.py`), so in that walk xray_costs is not mounted and the old order holds; the
rewrite is therefore defensive, and S582's own X7 checks the strict order with xray_costs mounted. S559's walk M1 was run as S575 runs it,
baseline on the FROM files and the walk on the S582 files — green (its MODS have no batteries.py, so its bar never had Batteries either);
no line of it changed. B2: unique index + INSERT OR IGNORE + seed only in the data step (X10 runs two at once). B3: the installer copies
S575's shape (all earlier walks, both pythons, DB backup before restart, auto-restore). C1–C9 as above. N1: the number gate passes (it
flags phone-shaped numbers only; "B-0163" is not one). N4: S560's pack walk is in the set. N6: the menu's endpoint = the page's endpoint
(`s582_xray`) — the bar marks it "on" (X7). N8: see "not done".

### Found outside the brief (not touched)
1. **S568's frozen walk is RED on today's database, before S582** — its I3 goes red on the FROM files exactly as on S582's (proven, both
   runs). Cause: since this morning the owner filled the live stationery list (13 items, including "A4 paper (75 gsm)"); S568's I3 makes a
   made-up "Walk A4 paper 75 GSM" and expects the desk's pre-match to offer that item, and the matcher rightly prefers the real one. This kit
   ships `s568_copy_s582.py`, which empties the four stationery tables in the /tmp scratch copy given to S568's walk only (its install-day
   shape; S575 did the same for S571), and S568's walk is then 14/14 on FROM and on S582. **Any later kit that runs S568's walk needs the
   same; S575's own installer would now refuse if run again** (it is already installed, so no harm today).
2. `/root/finance/purchase_app.py` is 98f7d9f0, not S575's read pin 147201dd (file time 07:03 today) — a Sanjeevni file; the installer only
   prints it (S575's rule), and S568's walk ran with it as it is, green.
3. B-0163's `bill_date` is stored as "14/10…" (not ISO); its `bill_month` is set, so The month reads it right. A joined challan shows
   "challan joined to B-x"; **its bill is not marked automatically** — when B-0163's bill arrives and is joined, the bill will need its own
   mark (or a later kit carries the mark across). That's for the owner to decide (what the page shows), so I didn't build it.
4. The live database has no service_logs or asset_cover rows yet, so the Machines fold stays empty until spends / covers are recorded. Two
   live machines, "FDR AMC" and "FDR battery", will be listed first as "looks like X-ray — tick to count" (not ticked).
5. Jasoria's old-battery amount is not subtracted from a battery's price (the brief says price) — the chat may want the net.

### Not done, and why
- **Not installed, not published** — the brief overrides CLAUDE.md for this run. PUBLISH_ALL.bat was not run.
- **The evidence note** in `ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S582\` (BUILD_NORM §6, R1 N8) was not written: CLAUDE.md forbids
  writing outside the repository and the server's /tmp. This report and `walk/walk_results_s582.txt` are the evidence; the chat may copy them.
- `DUTY_MAP` not changed — the kit adds no staff duty (an owner-only page).
- **Box /tmp left behind:** `/tmp/s582dev`, `/tmp/s582kit` and the empty `/tmp/s582reh` (code copies, walk outputs on made-up rows,
  one rendered page of the made-up month; no secret, no patient detail). My `rm -rf /tmp/s582kit` over ssh was **refused by the permission
  list**, so per the rulebook I did not try another way. Please remove them: `rm -rf /tmp/s582dev /tmp/s582kit /tmp/s582reh`. The
  installer's own scratch (`/tmp/s582_install_*`) is removed by the installer (checked in the rehearsal).
- One edit was blocked by the tool's own filter (it took shell text inside a PowerShell edit for a delete); the same edit was made with the
  editor.

### The server line (the owner's, after the chat's check and the publish)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S582_XRAY_COSTS/install_s582.sh`
**Undo:** `\cp -p /root/assetapp/batteries.py.bak_S582_40eb8a91 /root/assetapp/batteries.py && mv -f /root/assetapp/xray_costs.py /root/assetapp/xray_costs.py.undone_S582 && systemctl restart assetapp`

### Cost
About **US$ 9.7 of the run's US$ 40 budget** (read from the run's own budget counter when this report was written: $9.59 spent before
this line). The number gate (`NO_PHONE_NUMBERS.py --files-from`, 33 files: the kit and this report) is clean, `git check-ignore` drops no
kit file, and the kit has no `__pycache__`.
