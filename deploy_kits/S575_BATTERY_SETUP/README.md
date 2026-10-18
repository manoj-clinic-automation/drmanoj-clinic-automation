# S575_BATTERY_SETUP — setting up the batteries: an old battery with only a date, older papers and find by stamp, the set count, First setup

**Why.** The owner, 06:02 IST 18-Oct-2026: "Does the battery page offer me to link the existing batteries, bills, and for many UPS, I
only have a date when the batteries were renewed. So for the initial setup, that functionality is also required. Online UPS has
variable number of batteries, so I need a place where I can mention the number of the batteries each online UPS is having." The brief:
`claude_code_briefs/S575_BATTERY_SETUP.md` (v2), read whole with the independent review `S575_BRIEF_R1.md` (md5 `99057249…`, 0 BLOCKER ·
8 CORRECTION · 7 NOTE) — its replacement wording for every CORRECTION is what was built. Board `_numbers` v462 → v463.

**What changes (the Batteries pages only — reception, the sorting desk's screens and every staff word untouched).**
1. **An old battery, with only a date.** New battery fitted: "Fitted on" takes any past date (dd-mm-yyyy, the app's own date rule),
   up to 15 years back, never in the future (R1 N4). The Bill choice gains **"Old battery — no bill"** beside "Bill awaited" (both
   forms); on the Jasoria form the Warranty card gains **"Old battery — no card"** (the B.L. form has no card select — R1 C2). It is
   stored as the id NULL and created_at `none:old-battery` in S571's own columns — **no new column, no data step** (R1 C1). Such a
   battery is never "bill awaited": no badge, no "B.L. bill still awaited" reminder, not in the "B.L. bill awaited" total, and the
   sorting desk does not offer it a new B.L. paper as "this bill?". The warranty and usual-life dates count from the fitted date as
   before. The history reads **"no bill (old battery)"** / **"no card (old battery)"**; the audit line carries `no_bill`. A bill can
   still be linked later from the place's box "The battery now — its papers" (the battery in use — R1 C3); linking replaces the marker.
2. **Link existing papers, old ones too.** The usual picker is unchanged (the place's supplier, the last 90 days — `candidates()` and
   `_pickable()` untouched, R1 C4). Beside it, a closed fold **"Show older / other papers"** holds a second list — every paper the person
   may see by the desk's own rules (never pharmacy, a patient's paper, a set-aside paper, a second scan or a page of another paper;
   Personal to the owner only), any supplier, any date, newest first, "stamp · supplier · date · amount" (at most 300) — and a box
   **"Find by stamp"** (B-0162, B162, b-162 … through the desk's `_s566_stamp_form`). On the fitted form and in "The battery now — its
   papers". The order is stamp, then the wider list, then the usual list; two filled with different papers are refused ("Pick the bill in
   one place only."). Every refusal by stamp is ONE line, "No paper B-0162 that you may link here. Nothing was linked." — it never tells a
   manager that a Personal paper exists (R1 C5). **Linking never changes the paper's lane, section or status** (D664).
3. **Batteries in each online UPS.** An online UPS with no count shows the owner **"How many batteries? — set"** in its row, opening the
   place's "Change this place" (`?edit=1` opens that fold — R1 C7); a manager sees no prompt. "set of N" shows once known, even before a
   battery is recorded. On New battery fitted an online UPS has "Batteries in the set" as its first field.
4. **First setup in one sitting.** An owner-only fold **"First setup"** on the Batteries page lists every place with no battery recorded
   (decided by `current_fit`, not by the badge's words — R1 C6), one line each: Fitted on (required), Batteries in the set (online UPS),
   Bill (Old battery — no bill, the default / the supplier's papers / or find by stamp), Save. Each line carries the place's supplier and
   warranty months. The save and any refusal come back to the open fold with the message. The full form stays on every row.

**Files and pins (FROM → TO).** `/root/assetapp/batteries.py` **`9a0054ac` → `40eb8a91`** (31 counted edits, each anchor exactly once,
`make_s575.py`; S571's TO is this kit's FROM). Read only, pinned, never edited: `sorting_desk.py 110335ea` and `asset_register.py c39c084e`
(S571's TO — nothing needed them), `clinic_papers.py 6db07c12`, `stationery.py d11d7183`, `asset_machine.py 7d4fdffc`, `scanner_widget.js
10a8bb29`, `claude_reader.py 3894dc23`, `claude_reread.py d9b75e78`, the parent's `/root/finance/packs.py e46264b8`. **No data step**
(R1 N3: S571's `--ensure` line is dropped; the tables exist and the mount's own ensure is a no-op on them). The database is still backed
up (`assets.db.bak_S575_<stamp>`, the backup API) before placing. Restarts **assetapp only**.

**Kit.** `make_s575.py` (the patcher) · `walk_s575.py` (W1, W2, Z1, I1–I5; `--expect-red` = the control on the live FROM file;
`--save-pages` = pages for the browser walk) · `s571_copy_s575.py` (S571's walk is given a scratch copy at its own install-day shape —
S571's three tables and `batteries.since` taken out, which its mount makes again; no line of S571's walk changed) · `lines_s575.py` (S571's
browser walk B3 in S575's form: the fields outside the closed fold) · `install_s575.sh` · `rehearse_s575.sh` · `walk/`
(`browser_batteries_s575.py` at 1366 × 768 with its control, `walk_results_s575.txt`) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Proof (18-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC):** see `claude_code_briefs/REPORT_S575.md` — the walk
8/8 green; the control 6 of 6 MUST_RED red (W1, Z1 structural, green on both); every earlier walk green in the rehearsal's outcome 1
(S571 12 · S568 14 · S566 12 · S563 17 + its tidy fetch · S560 37 + pack 9 · S548 8 · S559 43 · S557 41 · S555 19 · S551 87); the
browser walks (S575 3/3, its control red; S571 3/3, its control red; S560 desk layout 7/7; S568 staff screen 2/2); the rehearsal GREEN.

**Install (the owner, after publishing):** `bash /root/deploy/repo/deploy_kits/S575_BATTERY_SETUP/install_s575.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/batteries.py.bak_S575_9a0054ac /root/assetapp/batteries.py && systemctl restart assetapp`
— then `/healthz` 200 and `batteries.py` back at `9a0054ac`. Nothing in the database needs undoing: a battery saved as "Old battery — no
bill" keeps its marker, which S571's file reads as a battery whose bill is not linked (on a B.L. place it then shows "bill awaited"
again). The database backup `assets.db.bak_S575_<stamp>` is needed only if rows saved after the install must be removed — say so before
using it.
