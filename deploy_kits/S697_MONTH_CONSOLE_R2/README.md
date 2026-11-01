# S697_MONTH_CONSOLE_R2 — the console and the month page, round 2 (the parent, S377, 01-Nov-2026)

**His words.** The S376 close's list for this kit (D818; F-1079, F-1080) and, this evening, the Sanjeevni chat's list of his owner
pages for the console (S375) with his three answers (20:31 IST): the staff screens left out · a line at 0 stays grey · the build
order mine; and the look: *"instead of the red, amber dots how about making that particular line that coloured"*.

**What it changes — five files, placed whole, each pinned FROM → TO (the installer refuses a live file that is not at FROM):**

| file | FROM | what |
|---|---|---|
| `/root/finance/owner_console.html` | e0d7d62f | the bars as the month page's (small uppercase label, the pill tinted, the accent bar and summary when open); the colour off the dot onto the line (amber / rose strip, the figure bold at the end); the month chips; on a phone the chips take their own row |
| `/root/finance/owner_console.py` | 391823ad | VERSION S697 1.5; the review-queue line reads the Review & Approve page's own tile (open exceptions by kind, days awaiting); `L(... fig=)`; TARGET_DOOR `expiry` → the expiry page, `porders` → `?old=1`; the Sanjeevni section's pages with their figures (`_sanj_pages`) and ONE Marg-reports line, shown even when the approvals list cannot be read; The month's two chips and no second link |
| `/root/finance/month_read.py` | 9aa2e053 | VERSION S697 1.2; the IPD line by `voided_at` (F-1079); "due since <day>" (F-1080b); Bought = films + procedure room / others / stationery; `others()` — every other lane and section, the unsorted clinic bills amber, the pharmacy scans counted against `purchase_scan_link` (rupees never added); the running month's line second in the console section |
| `/root/finance/month_page.html` | 29db7c20 | the section "Other papers of the month" under "Bought for the rooms" |
| `/root/finance/xray_film.py` | 961e779a | VERSION S697-XRAY-FILM-1.2: a no-count day shows that day's slip films; "Mornings not counted in October 2026" (F-1080c) |

**Settled here (D818 (f)):** the purchase-orders `?old=1` line lives on the console's Sanjeevni section (daily), not on The month — one page, one link.

**Reads, never writes:** `supplier_msg.s454_card_facts`, `porders.shortage_summary`, `expiry_watch.newest/now_view`, `reports_tile.status`,
`stock_diff`, `upi_match`/`darpan_correction`, `sale_item_review`, `purchase_scan_link` — all on the console's COPY of finance.db;
`assets.db` mode=ro. No data step, no new table, no portal change. Restarts clinic-finance; the reading rebuilt once.

**Cold review (independent):** R1 NOT SAFE — the kit's sums were stale after the last edit (regenerated, re-rehearsed); the [7/8] gate relaxed to 'the month and the Sanjeevni section read', a page a reader cannot read being one grey line by design; the expiry wording. Then SAFE TO INSTALL.

**Proof.** `walk_s697.py` on made-up databases: 85 checks (S696's 53 carried, three rewritten by design) and 13 mutants; the control
on the live folder 33 red; the installer rehearsed (`rehearse_s697.sh`: dry · install · again · changed · half · corrupt · offon ·
stalelock · red at [7/8] · journal red · the old master's shutdown traceback NOT a red). The pages rendered at 1366 and 390 px
on made-up data and read by a sub-agent.

**Install (one server line, window 04:00–23:30 IST):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s697kit && cp -rp /root/deploy/repo/deploy_kits/S697_MONTH_CONSOLE_R2 /tmp/s697kit && bash /tmp/s697kit/install_S697_MONTH_CONSOLE_R2.sh
```
**Undo:** the installer prints it; the backups are `*.bak_S697_<from8>` beside each file.
