# S571_BATTERIES — Batteries: battery places, their history, "New battery fitted", the bill on the desk, reminders on Renewals

**Why.** The owner's rulings D730 (1) (his word, 11:57 IST 16-Oct-2026: "AND THE BATTERY ONE ?"; his words 07:54–08:51 IST and the
mock-up `Main.dc.html` / `Fitted.dc.html`). The brief: `claude_code_briefs/S571_BATTERIES.md` (v2), read whole with the independent
review `S571_BRIEF_R1.md` (md5 `9fe1793b…`) — its replacement wording for the BLOCKER and every CORRECTION is what was built. Board
`_numbers` v454 → v455, PLANNED line D646.

**What changes.**
1. **The Batteries page** (the owner's English; the scan app's menu, right after Machines). Totals: due for replacement · warranty
   ends within 30 days · B.L. bill awaited · battery places. Four groups as the mock-up — Online UPS (B.L. Computers · warranty 1 year ·
   bill with the battery), Small UPS, Generator and inverters (Jasoria · bill and warranty card · old battery paid back), Vehicles
   (Jasoria · yours only). One row per place: place and sub-line · battery now · fitted · warranty till · a badge (OK / Warranty ends in
   N days / Due for replacement / Bill awaited N days / Water top-up due, Backup check due, Start test due / Not recorded yet) · **New
   battery fitted**. **+ Add a battery place.** Tapping a place opens its history: the re-order line (type · Ah · V · set of N ·
   supplier · warranty · paid by), every battery it has had (fitted · removed · lasted · battery · cost · the bill's and the warranty
   card's stamps, linked to the desk), the current battery's paper picker, upkeep "Done today", and (owner) change the place / link it
   to a machine / take it off the list (its history kept).
2. **15 seeded places** (names only — no contact or identity number, F-185 as R1 C3): Digital X-ray (clinic), NK Pathology (NK
   Pathology), DTH lab ("to confirm" — shown so, never guessed); Reception PC, Second PC (clinic), Lab analysers (NK Pathology), Home
   DVR + router (yours only); Generator, Clinic inverter (2 batteries) (clinic), Home inverter (2 batteries, yours only); Carnival,
   Wagon R, Vento, Scooty, Bike (yours only). B.L. places warranty 12, Jasoria empty until typed from the card; usual life car 42,
   two-wheeler 30, inverter 54, UPS 30, generator 30 months (editable per place); upkeep inverter water 3, UPS backup check 3,
   generator start 1 month.
3. **New battery fitted** (one form, the mock-up's two kinds; two columns so every field and Save are on one 1366 × 768 screen). The
   date is today; supplier and warranty from the place. B.L.: the bill picked if scanned, else **bill awaited** until it is linked.
   Jasoria: price, old-battery amount, the net shown, the warranty months **typed from the card** (no reading, no Claude call — R1 C8),
   bill and warranty card picked or left for later. The picker: the place's supplier's papers (first word of the supplier key — R1 C4),
   the last 90 days, by the desk's own visibility rules (never a pharmacy or a patient's paper; a Personal paper to the owner only —
   R1 C7). Saving puts the previous battery into the history with its removed date. **On the sorting desk** a B.L. Computers / Jasoria
   paper shows "Battery fitted at <place> on <date> — this bill?" while that battery's bill is awaited; one tap links it (its own POST,
   never the desk's Save). **Linking never changes the paper** (D664): its lane, section and status stay as they are. A linked paper
   still waiting on the desk has "Where does it go?" pre-selected **in the browser only** from the place's payer (clinic → Clinic
   equipment, NK Pathology → NK Pathology, owner → Personal; "to confirm" → nothing) — nothing is written until the desk's own Save.
4. **Reminders, computed when read** (R1 B1): one **Batteries** card on Renewals beside the personal warranties card (it also counts
   toward "Nothing due"; `?all=1` shows every upcoming date): warranty ends within 30 days; usual life reached (amber 30 days before);
   a B.L. bill still awaited after 30 days; upkeep due — with a "done" tap that resets it. Nothing is written to `expiries`; S557's heal
   is not touched. They do not reach the home dashboard's due list or `/api/due` (R1 note 14).
5. **A new machine's place, by itself** (R1 C5): a machine added in Machines after the install (`assets.created_at` later than
   `batteries.since`) whose name holds the whole word UPS or inverter, or whose category is exactly Vehicle, gets one place at the next
   Batteries page load — at most one per (asset_id, asset_created_at), a unique index; Online UPS when the name says online, else Small
   UPS; owner-only when the machine is hidden, its location owner-only, or a Vehicle; payer from its entity (else "to confirm").
6. **Who sees what.** The owner: everything. A manager: the clinic and lab places only, and only while **`batteries.on`** is ON
   (absent = OFF; one row "Batteries for Shavez" on the owner's Switches card — R1 C2) — **installed OFF**. Reception: never. An
   owner-only place, its fittings, links, upkeep, history, reminders and desk offers are refused to anyone but the owner, server-side.

**Files and pins (FROM → TO).** `/root/assetapp/sorting_desk.py` `695ba90b` → `110335ea` (9 counted edits) · `asset_register.py`
`e5356e0c` → `c39c084e` (4) · **new** `batteries.py` (absent → `9a0054ac`; round 0 was `872a3ff3`). Read only, pinned (never edited): `clinic_papers.py
6db07c12` (no Renewals or month wiring needed it), `stationery.py d11d7183`, `asset_machine.py 7d4fdffc`, `scanner_widget.js 10a8bb29`,
`claude_reader.py 3894dc23`, `claude_reread.py d9b75e78`, the parent's `/root/finance/packs.py e46264b8` (S568's TO). Every edit is an
anchor found exactly once in the live bytes (`make_s571.py`). **Data step** (batteries.py's own `ensure`, additive, idempotent, after the
database backup): tables `battery_place`, `battery_fit`, `battery_upkeep`, indexes `battery_place_asset` (unique, the machine link) and
`battery_fit_place`, the 15 seeded places by `seed_key`, and one settings row `batteries.since` — no existing row changed; a second run
adds nothing. `batteries.py` is mounted by one guarded hook at the foot of `asset_register.py` after the S568 block; absent, the app runs
as before. Restarts **assetapp only** (no finance file changes).

**Fix round 1 (S571_FIX1, 16-Oct-2026 — the kit review K1, CORRECTION 1 and NOTE 2; only `batteries.py` changed, sorting_desk.py and
asset_register.py stay at their TO pins).** (1) `desk_offer`: a manager gets no battery offer and no pre-selection on the sorting desk
while `batteries.on` is absent or OFF (`if not owner and not switch_on(db): return {}` — the same rule as `may_see`). (2) A place's
history shows a paper's amount and its stamp link only when the viewer may see that paper (the desk's own `_visible`); otherwise the
line reads "a paper you do not see" with no amount and no link. Walk checks **I8** and **I9** added: green on the FIX1 file, RED on the
round-0 kit (`--expect-red --must-red I8,I9`: those two red, every other check green).

**Kit.** `make_s571.py` (the patcher) · `batteries.py` · `walk_s571.py` (W1, W2, Z1, I1–I9; `--expect-red` = the control on the live
FROM files; `--must-red I8,I9` with it = the round-0 control; `--save-pages` = the Batteries pages for the browser walk) · `install_s571.sh` · `rehearse_s571.sh` · `walk/`
(`browser_batteries_s571.py`, the Batteries page at 1366 × 768 with its control, and `walk_results_s571.txt`: that walk, S560's frozen
desk-layout walk in S568's one-line form, and S568's staff-screen walk, all on the final build) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Proof (16-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC):** see `claude_code_briefs/REPORT_S571.md` (its "Fix round 1"
section) — the walk 12/12 green; the control 10 of 10 MUST_RED red (W1, Z1 structural, green on both); the round-0 control I8, I9 red,
the other 10 green; every earlier walk green through the rehearsal's
outcome 1 (S568 14 · S566 12 · S563 17 + its tidy fetch · S560 37 + pack 9 · S548 8 · S559 43 · S557 41 · S555 19 · S551 87); the browser
walks (Batteries 3/3, its control red; S560 desk layout 7/7; S568 staff screen 2/2); the rehearsal GREEN.

**Install (the owner, after publishing):** `bash /root/deploy/repo/deploy_kits/S571_BATTERIES/install_s571.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S571_695ba90b /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/asset_register.py.bak_S571_e5356e0c /root/assetapp/asset_register.py && mv -f /root/assetapp/batteries.py /root/assetapp/batteries.py.off_S571 && systemctl restart assetapp`
— then `/healthz` 200 and the md5s back at the FROM pins; `batteries.py` is out of the app (moved aside, as S568's undo). The three new
tables, the seeded places and `batteries.since` stay (read by nothing the old files run); the database backup `assets.db.bak_S571_<stamp>`
is needed only if their rows must be removed — say so before using it.
