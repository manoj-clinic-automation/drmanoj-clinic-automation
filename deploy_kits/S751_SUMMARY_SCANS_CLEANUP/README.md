# S751_SUMMARY_SCANS_CLEANUP — the sixteen summary scans removed so staff rescan them properly (08-Nov-2026, Sanjeevni session 407)

**What happened.** Shivani scanned the October month summaries of fourteen dealers between 11:54 and 12:04 IST on 08-Nov-2026 — sixteen papers, B-0274 … B-0289 — without the **DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?** tick. The server read every one as an ordinary bill: nine landed as Pharmacy bills with no bill number (filed under November), five on the Clinic lane's sorting desk, two were set aside as duplicates of a single October bill (Daanshi, Drug Deal — the month total equals the one bill). Row 7 of the purchase check still read *20 awaited*.

**The owner's word (13:25 IST):** staff rescan them properly, for the practice; these sixteen are removed.

**What this kit does — one owner line, no code change, no restart.** `cleanup_s751.py` removes exactly those sixteen papers the way the app's own *Delete* button does (`asset_register.bill_delete`, S563): one `paper_deleted` audit row per paper (kept for ever, with the stamp, the time, the vendor and the amount), `assets.bill_id` cleared, `bill_items` and the `bills` row deleted. It also removes the rows **derived from each paper and keyed by its id alone** — `claude_reading`, `scan_check_s441`, `scan_question`, `scan_lie` — so a later paper that happens to get a reused id inherits nothing; and on `finance.db` the pairing scratch rows `purchase_scan_state` / `purchase_scan_link` / `purchase_sarvam_check` for those scan ids. A later paper's *second scan of B-02xx?* question (`dup_cand`) about one of them is cleared with the paper it asks about — the paper itself is kept. Both databases are backed up first (`assets.db.bak_S751_<stamp>`, `finance.db.bak_S751_<stamp>`). The stamp counter is untouched — the next paper is B-0290; stamps are never reused (A-D21). The stored PDFs stay on disk, as after the app's own Delete.

**All or nothing.** Every one of the sixteen must be the paper that was read on the screen — id, stamp, amount to the rupee, scanned on 08-Nov-2026 by Shivani, the vendor as read — or nothing is changed. It **refuses** when anything a person decided or paid points at one of them: `paper_payment_bill` / `paper_payment`, `proc_paper` / `proc_line` / `proc_photo`, `stationery_line`, `d664_warranty` / `d664_join`, an outside paper's `dup_of` / `challan_of` / `rescan_of`, finance's `s736_decision` / `s749_act` / `s750_dealer_of`, or a person's decision on a `purchase_scan_state` row (confirmed, vendor chosen, dup ok). A learned vendor spelling (`purchase_scan_alias`) is kept and reported.

**Walked** (`walk_s751.py`, on made-up databases built by the real app's own init — never a live file): DRY reads all sixteen and writes nothing; REAL removes exactly the sixteen (19 → 3 papers), writes sixteen audit rows, clears the derived and scratch rows, keeps the older papers, their readings, the audit history and the counter; a second REAL run refuses (not found). **CONTROL:** seven databases each broken one way — an amount off by ₹2, a paper scanned by someone else, an outside `dup_of` pointing in (two cases), a payment proved by one, a finance `s750_dealer_of` decision, a person's decision on a scratch row — each refuses with nothing changed and no backup made.

**Cold review (independent, before packing): SAFE TO INSTALL, no must-fix; its should-fixes built** — the person-decided scratch rows refuse, `purchase_sarvam_check` removed with the paper, `proc_photo` / `d664_join` refuse, the later paper's `dup_cand` question cleared instead of refusing, the audit time in the history column's own shape, the counter read-back cannot raise after the commit. **Known, as with the app's own Delete:** `bills.id` has no AUTOINCREMENT, so the next scans take ids 274 … again; their `bill_audit` history will also show the old `paper_deleted` row (it names the old stamp and time), as after any Delete of the newest paper.

**Order matters:** run this BEFORE staff rescan — a rescan made while the old paper is still there can be set aside as its duplicate (same picture), and the kit then refuses (an outside `dup_of`).

## The two lines (the owner's, after his publish)

The DRY read first — paste its output (F-1153), then the real line:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s751kit && cp -rp /root/deploy/repo/deploy_kits/S751_SUMMARY_SCANS_CLEANUP /tmp/s751kit && DRY=1 bash /tmp/s751kit/install_S751_SUMMARY_SCANS_CLEANUP.sh
```

```
bash /tmp/s751kit/install_S751_SUMMARY_SCANS_CLEANUP.sh
```

**Then staff:** each dealer's October summary rescanned under **Pharmacy** with the SUMMARY tick; Gunina's two pages together; Mannat once. Row 7 reads them as summaries.

**Touches the Scan App's data** (`assets.db` rows; no file of the Scan App's) — the Scan App chat is told at the close. Not a PLANNED file (D646 is about files).

**Finding for the close:** the intake takes a dealer's summary as a bill without a word when the tick is missed — the reader could notice a statement-shaped paper (several bill lines, a month total, no single bill number) and ask; the Scan App's backlog.
