# S585_STATIONERY_ISSUE_MANY — many stationery items issued on one screen (D738)

**Why.** The owner, 14:41–15:10 IST 18-Oct-2026: *"develop a system where multiple items can be issued on one screen"*; *"in Shavez folder
there is an Excel file named stationery where you can find what all was issued, so you can populate that also, and we can edit it later on if
needed"*, with his mapping of that sheet. The brief: `claude_code_briefs/S585_STATIONERY_ISSUE_MANY.md` (v2), read whole with its independent
review `S585_BRIEF_R1.md` (md5 `706779ce…`, 2 BLOCKER · 9 CORRECTION · 10 NOTE) — the replacement wording of every BLOCKER and CORRECTION is
what was built, with the Scan App chat's C3 decision (the sheet's lines keep the opening count's day but are never "this month"). Board
`_numbers` v491 → v492. The owner's mock-up `claude_code_briefs/S585_MOCKUP_Main.dc.html` is the screen's specification.

**What changes.**
1. **Stationery diya, many items on one screen** (staff, Roman Hindi) — only while the new switch **`stationery.many`** is ON (absent = OFF):
   "1 · Kisko diya?" (Lab · Reception · Sanjeevni · Clinic · **X-ray**, big buttons), "2 · Kya aur kitna diya?" (every active item: its name,
   "shelf pe <stock> <unit>", **−**, the number — a box that can be typed in — **+**; a row with a number turns green), the line naming what will
   be saved, and ONE **Save karo (N)** — grey until a place and a number are chosen, disabled on the first tap. The Save goes to its own POST
   `/stationery/diya/many`: one issue per item through the existing `issue()`, then ONE commit (all or none); "Save ho gaya ✓ — <what> → <place>";
   a quantity above the shelf stock is saved and flagged on the owner's page as before. Refused (nothing written) while the switch is OFF, with
   no place, with no number. The **Ginti** card below is the one-item screen's own (cut from its template — the same bytes).
2. **Switch OFF = S568's one-item screen, byte for byte** (walk M1, and S568's own walk I4 / I4F unedited). ON, the one-item screen stays at
   `/stationery/diya?one=1` (its four places are frozen: `ONE_PLACES`, R1 B1).
3. **The switch** is a card at the top of the **owner's Stationery page** (`POST /stationery/many`, owner only, audited) — **not** on the
   Switches card, which lives in `sorting_desk.py` and is not touched (R1 C1).
4. **X-ray is a place** — `issue()`, the new screen, the stock table's "Issued this month (Lab · Reception · Sanjeevni · Clinic · X-ray)"
   (made from the places, R1 C2), This month's issues. (S582's X-ray costs page counts purchase papers, not issued stationery — unchanged.)
5. **Void** (owner only, `POST /stationery/void`): each line of This month's issues, of the new fold **"Show all issues"** (earlier months)
   and of the sheet's fold has Void — the line stays, struck through ("voided by …"), audited in `desk_audit`, and leaves the stock. *"Voiding an
   issue made before the latest count does not change the stock — the count stands."* (said on the page). No new column (R1 C5).
6. **Shavez's sheet** — the installer's data step (after health, R1 C4): `python3 -B stationery.py --history <assets.db>` writes the seven
   lines below in ONE transaction with the key `stationery.history_s585` (checked first; a second run writes nothing), each **1 s before its
   item's opening count** (day = that count's day, `stock_before` NULL, `by_whom` = `history (Shavez sheet)`), so the opening stock he gave
   stands exactly; items by their EXACT names among the active items; an absent item or one with no opening count is skipped with one line;
   the stock figures are compared before / after inside the transaction — any difference rolls it all back. On his page they are never in
   This month's issues or the per-place figures: they are in their own fold **"Earlier issues — from Shavez's sheet (no date)"**, each voidable.

   | item | qty | place |
   |---|---|---|
   | Register 72 pages | 6 | Reception (the OPD register) |
   | Register 104 pages | 6 | Reception (the lab register kept at reception) |
   | Register 192 pages | 3 | Lab (the lab register) |
   | Register 104 pages | 6 | Lab (the A/C register) |
   | Small notebook (copy) | 2 | Lab (the expense copy) |
   | Notebook (copy) 72 pages | 6 | Sanjeevni (Medical's daily detail) |
   | Small notebook (copy) | 2 | X-ray |

**Files and pins (FROM → TO).** `/root/assetapp/stationery.py` **`d11d7183` → `18268ff0`** (21 counted edits, each anchor exactly once —
`make_s585.py`). The only file changed. Read only, pinned, never edited: `asset_register.py c39c084e`, `sorting_desk.py 110335ea` (both at
drift 8, F-836), **`batteries.py 775471e6` and `xray_costs.py 22e59f5a` — S582's TO pins** (S582 is installed FIRST, R1 B2; the installer
checks them against `deploy_kits/S582_XRAY_COSTS/PIN_TO_*.txt` and refuses if S582's kit is absent), `clinic_papers.py 6db07c12`,
`asset_machine.py 7d4fdffc`, `scanner_widget.js 10a8bb29`, `claude_reader.py 3894dc23`, `claude_reread.py d9b75e78`, the parent's
`/root/finance/packs.py e46264b8`. **assets.db: additive, no DDL** — the data step's seven lines, its key and one audit line. The switch
`stationery.many` is **not written** (OFF). The database is backed up (`assets.db.bak_S585_<stamp>`, the backup API) BEFORE the restart.
Restarts **assetapp only**.

**Kit.** `make_s585.py` (the patcher) · `walk_s585.py` (W1, W2, M1–M9; `--expect-red` = the control on the FROM files; `--pages` = M1's fresh
process; `--save-pages` = the pages for the browser walk) · `s582_copy_s585.py` (S582's walk is given a scratch copy WITHOUT the table
`xray_mark` — its install-day shape: since S582 was installed the live table holds its three seed marks and S582's Z1, which expects the mount
to add the table with no row, is red on any copy of today's database; no line of S582's walk is changed) · `install_s585.sh` ·
`rehearse_s585.sh` · `walk/` (`browser_many_s585.py` at 390 × 844 and 1366 × 768 with its control, `walk_results_s585.txt`) · `PIN_*.txt` ·
`KIT_ID.txt` · `SUMS.md5`. S568's walk is run with S582's `s568_copy_s582.py`; S571's with S582's `lines_s582.py` (as S582 runs them).

**Proof (18-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC):** see `walk/walk_results_s585.txt` and
`claude_code_briefs/REPORT_S585.md`.

**Install (the owner, after publishing — S582 is already installed):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S585_STATIONERY_ISSUE_MANY/install_s585.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/stationery.py.bak_S585_d11d7183 /root/assetapp/stationery.py && systemctl restart assetapp`
— then `/healthz` 200 and `stationery.py` back at `d11d7183`. Shavez's seven lines stay: the old file never takes them off the stock, but
its page would list them among October 2026's issues and per-place figures. To take them out, BEFORE the undo line: `python3 -B /root/assetapp/stationery.py --history-void <assets.db>` — it voids
them (`voided_by` = `undo S585`), never deletes; the key stays, so a re-install writes nothing. Lines issued to X-ray while the kit was in
place show as "xray" on the old page. The database backup `assets.db.bak_S585_<stamp>` is needed only if the data change itself must be
reversed — say so before using it.
