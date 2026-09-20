# START HERE — SESSION 275 — written at the S274 close, 20-Sep-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project. Run `SANJEEVNI_START_HERE_PROMPT_v1_1` (the project's custom instructions) Phase 0 first, then this file. **Read `S274_BUILD_BRIEF.md` §0 for where things stand and §2 for what is live.**

*FIRST ACT: take your session number from the board document `board/_numbers` by a version-pinned write (`NUMBERS_PROTOCOL_v1.md`). 275 is reserved there for this chat; if the pinned write fails, re-read and take what it says. Every kit, D and F number is taken the same way — never from this file, the Register or `deploy_kits\`. The parent's next chat takes 276.*

---

## 0 · WHERE THE WEEK STANDS

D567's seven items are done — six live on 20-Sep (S337 · S336 · S338 · S341 · S343) and the Book at v1.6. **The clock that matters now is D566/D572: seven consecutive nights of `gate 13/13`**, counted from 20-Sep, read from `/root/finance/spine/spine_state.json` (or the health page's *Marg spine gate* row). No screen moves onto the spine before that and his word.

**What to do in this order, none of it his:**

1. **Read the morning.** Shavez's tile — `/finance/reports/aaj` — with the first real morning behind it (21-Sep): did the tick arrive, and how long after the door's *aa gayi*? The walk prints the lag (`walk_s334.py` on a scratch copy). If the lag is hours, write the one-line proposal for the door running the reader at take time; do not build it without his word.
2. **Read the three nightly files** beside the spine: `orders/order_rehearsal_latest.txt` (the score begins 27-Sep), `expiry/near_expiry_latest.txt` (F-576: the 27 batches — the October export decides), `spine_compare_latest.txt`.
3. **The category-list signature to the VPS** — `signatures.json` `b2dcb211` → manojz's `a987a08e` (one data edit, a kit): S336's rescan then rescues the 18-Sep category export the VPS door refused, the first real rescue.
4. **The rung-4 plan for ordering onto the spine** as a paper, ready for the day the seven nights are up and he has ruled on `order_rules.json`.

**Do not** touch the stock-check screens or tables until count #1 is closed (his standing rule). **Do not** move any screen onto the spine before seven clean nights and his word.

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_114_S274close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_111_S274close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_99.md` (F-0 … F-578) |
| Runbook | `HANDOFF_RUNBOOK_2026-09-20_Session274close_v194.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_6_S274.md` |
| the contract · the reference | `MARG_REPORT_CONTRACT_v1.md` · `S270_CORE_DATA_VERIFICATION_REFERENCE.md` |
| live pins | `live_pins_S274close.txt` |
| build brief | `S274_BUILD_BRIEF.md` |

**Next free (a mirror — the board's `_numbers` is the source): D573 · F-579 · A-D25 · Session 275 (this file) / 276 (the parent).** Kit numbers: read `_numbers`.

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

`reports_tile.py 2798436712` (S337) · `marg_take.py 75b8056c` + `phi_scan.py` + `marg_rescan.py` + `marg_rescan_vps.py` (S336) · `spine_build.py 1378c87d` + `freshness_legs.json 9dfbef9c` (S338) · `order_rehearsal.py` + `order_rules.json` (S341) · `near_expiry.py` (S343) · three root cron lines. Pins in the Register §S274.

## 3 · THE PIN CHECK AT YOUR OPEN

The 21-Sep 01:35 bundle carries `/root/marg_ingest/*.py` and `/root/finance/*.py|*.json` — so `marg_take.py`, `phi_scan.py`, `marg_rescan*.py`, `reports_tile.py` and `freshness_legs.json` should MATCH. The spine folder (`spine_build.py`, `order_rehearsal.py`, `near_expiry.py`, `order_rules.json`) is **absent from the bundle by rule** until the parent widens `code_bundle.py` — say so, not drift. `signatures.json` still `b2dcb211` on the VPS (manojz `a987a08e`).

## 4 · LESSONS FROM THIS SESSION, kept short

1. A kit's login-gated `api/healthz` proves nothing to curl; import the placed module (F-573).
2. `py_compile` on copies, never in the kit folder (F-574).
3. Every Marg export carries the shop's phone and Marg's footer number; a PHI scan exempts exactly those (F-575).
4. The count the code runs (13) beats the count a decision remembers (14) (F-577).
5. A canon file corrected after its row is written is a new row (F-578).
6. The one counter works: five collisions, zero double-mints.
