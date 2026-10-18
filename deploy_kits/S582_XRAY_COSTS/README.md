# S582_XRAY_COSTS — the X-ray department's expenses, month by month (D736)

**Why.** The owner, 13:03 IST 18-Oct-2026, on B-0163 (500 X-ray envelopes, moved at his word to *Stationery & packaging*): "But it needs
to be also under the xray expenses section, so that I can assess expenses of the xray department also." The brief:
`claude_code_briefs/S582_XRAY_COSTS.md` (v2), read whole with its independent review `S582_BRIEF_R1.md` (md5 `d3e0fa69…`, 3 BLOCKER ·
9 CORRECTION · 8 NOTE) — the replacement wording of every BLOCKER and CORRECTION is what was built. Board `_numbers` v480 → v481.

**What changes (the owner's screens only — Shavez, reception and every staff word untouched).**
1. **A new menu item "X-ray costs"**, right after Batteries, for the owner only. It opens **"X-ray expenses — <Month YYYY>"** with the
   previous / next month (and a month box), and one line: *₹ this month · ₹ since <the first month with any X-ray cost>*.
2. **Four folds, each with its month total and its rows** (date · what · supplier · amount · the paper / machine / battery place):
   - **X-ray films** — The month's own "X-ray films" section, read through sorting_desk's own selection (`_s566_paid_rows`) and sum
     (`_s566_total`), with the subs taken from `MONTH_SECTIONS` by key (R1 C1, C2): receipts, statements, awaiting challans, set-aside
     papers, second scans and held doubles never count, exactly as on The month. The fold always shows The month's own figure; if a film
     paper is the paper of a counted cover / spend / battery, one line says how much of it is counted there.
   - **Papers marked for X-ray** — any paper he marks by its stamp ("+ Mark a paper for X-ray": B-0162, B162, b-162 or 162 — through
     `batteries.by_stamp`, the desk's visibility: never pharmacy, never a patient's paper, never set aside / a second scan / a page; R1 C3).
     A marked paper counts only when The month counts it in its own section, in the month The month gives it; otherwise it is listed
     "not counted: <why>" (rejected / set aside · second scan · a page of B-x · challan awaiting · challan joined to B-x · challan closed ·
     receipt · statement · held double (D710) · in no section of The month · not on the clinic lane — R1 C4). **A Personal paper shows but
     does not add** (it is in no section of The month). "Unmark" on each row.
   - **Machines marked for X-ray** — their service / repair spends (`service_logs.cost` by `log_date`, as `asset_machine.totals_line`)
     and their covers (`asset_cover.cost` by `from_day`, the machine's fingerprint, not voided; a cover with no from-date is counted in the
     month it was recorded, said "no from-date" — R1 C5). **Never the purchase price.** A spend / cover with a date that is not a full
     date is listed at the top ("Date not read"), counted in no month (R1 N2).
   - **Batteries of the X-ray places** — `battery_fit.price` by `fitted_on`, not voided (a place taken off the list still counts).
3. **The ticks** — "Machines — which count for X-ray" lists every machine with a tick; those whose name or room says X-ray / X ray / FDR /
   CR / digitiser come first as "looks like X-ray — tick to count" — **the system never ticks one** (D664). "Battery places — which count
   for X-ray" likewise.
4. **Each rupee once (R1 C7).** (1) a counted spend / cover / battery fitting claims its paper(s) — the bill, and for a fitting the
   warranty card too — only when the paper's fingerprint matches (`bills.created_at` = the row's `bill_created_at`; "Old battery — no bill"
   is no paper; a mismatch shows "paper link stale" and claims nothing — R1 C6); the paper is shown under the row "its paper B-x" at no
   amount; (2) X-ray films; (3) marked papers. One paper claimed by two rows: each row's own cost counts, both say "one paper, two
   entries — check". A marked machine's purchase paper, if he marks it, counts as a marked paper flagged "purchase paper of <machine>"
   (R1 N3). **Not detectable:** the same spend entered on a marked machine AND as a battery fitting of a marked place with no paper on either.
5. **Marks never change a paper, machine or battery place** — only the new table `xray_mark` is written (kind, ref_id, ref_created_at —
   the record's fingerprint, so a mark never passes to a new record that re-uses a deleted one's id; the unique index `xray_mark_live`
   allows one live mark per record; INSERT OR IGNORE — R1 B2). Every mark / unmark is audited in `desk_audit`.

**Files and pins (FROM → TO).** `/root/assetapp/batteries.py` **`40eb8a91` → `775471e6`** (2 counted edits, each anchor exactly once,
`make_s582.py`: E1 `menu_items` appends `xray_costs.menu_items(role)` after Batteries, guarded; E2 the end of `init` mounts `xray_costs`,
guarded — a failure prints to stderr and the Batteries pages run exactly as before). **NEW** `/root/assetapp/xray_costs.py` **`22e59f5a`**.
Read only, pinned, never edited: `asset_register.py c39c084e`, `sorting_desk.py 110335ea` (both at drift 8, F-836 — not touched),
`clinic_papers.py 6db07c12`, `asset_machine.py 7d4fdffc`, `stationery.py d11d7183`, `scanner_widget.js 10a8bb29`, `claude_reader.py
3894dc23`, `claude_reread.py d9b75e78`, the parent's `/root/finance/packs.py e46264b8`. **assets.db: additive** — the table `xray_mark`
and its index, made by the mount (CREATE … IF NOT EXISTS; no seed at mount, two gunicorn workers — R1 B2); **the data step** (after
health): `python3 -B xray_costs.py --ensure <assets.db>` seeds the owner's own words — the paper **B-0163** by its stamp, the battery
places named exactly **"Digital X-ray"** and **"X-ray detector (FDR) battery"** (C8; each absent one skipped with one line); no machine
is seeded; a seed he unmarked is never marked again. The database is backed up (`assets.db.bak_S582_<stamp>`, the backup API) BEFORE
the restart. Restarts **assetapp only**.

**Kit.** `xray_costs.py` (the new file) · `make_s582.py` (the patcher; also copies `xray_costs.py` at its pin) · `walk_s582.py` (W1, W2,
Z1, X1–X11; `--expect-red` = the control on the FROM files; `--pages` = X11's fresh process; `--save-pages` = the page for the browser
walk) · `lines_s582.py` (S571's walk line 354 in S582's form — R1 B1) · `s568_copy_s582.py` (S568's walk is given a scratch copy with
the stationery list EMPTY — its install-day shape: since this morning the live list holds the owner's real items, one of them 'A4 paper
(75 gsm)', and S568's I3 — which makes 'Walk A4 paper 75 GSM' and expects the pre-match to offer it — goes red on any copy of today's
database, on the FROM files exactly as on S582's; no line of S568's walk is changed; S575 did the same for S571) · `install_s582.sh` ·
`rehearse_s582.sh` · `walk/` (`browser_xray_s582.py` at 1366 × 768 with its control, `walk_results_s582.txt`) · `PIN_*.txt` · `KIT_ID.txt` ·
`SUMS.md5`.

**Proof (18-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC):** the walk 14/14 green; the control 12 of 12 MUST_RED
red (W1, Z1 structural, green on both); every earlier walk green in the rehearsal's outcome 1 (S575 8 · S571 12 · S568 14 · S566 12 ·
S563 17 + its tidy fetch · S560 37 + pack 9 · S548 8 · S559 43 · S557 41 · S555 19 · S551 87); the browser walk V1 green at 1366 × 768 and
1366 × 620, its control red; the rehearsal GREEN (12 outcomes). Details: `walk/walk_results_s582.txt` and `claude_code_briefs/REPORT_S582.md`.

**Install (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S582_XRAY_COSTS/install_s582.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/batteries.py.bak_S582_40eb8a91 /root/assetapp/batteries.py && mv -f /root/assetapp/xray_costs.py /root/assetapp/xray_costs.py.undone_S582 && systemctl restart assetapp`
— then `/healthz` 200 and `batteries.py` back at `40eb8a91`. The table `xray_mark` stays (additive, read by nothing else); the marks in it
come back if the kit is installed again. The database backup `assets.db.bak_S582_<stamp>` is needed only if the table itself must go —
say so before using it.
