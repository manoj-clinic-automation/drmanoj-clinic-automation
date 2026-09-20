# S272 BUILD BRIEF — the Sanjeevni close of 20-Sep-2026, and the mandate for S274

*Written 20-Sep-2026 at the close (08:01 IST, clock read). S272 opened 01:49 IST on `S270_BUILD_BRIEF` §0. Next Sanjeevni session: **S274** (273 is the parent's). Model: the session ran on the model the owner set at 02:31 IST and on no other after that.*

## 0 · THE OWNER'S MANDATE FOR S274 — his words, 20-Sep

> *"do seven number point and then start the build in your preferred order in a fresh chat in this session."*

Point 7 (this close) is done. The build order is D567 — see `START_HERE_SESSION_274.md` §0: Shavez's tile → his overdue line → quarantine → spine on the health page / backup → ordering prepared offline → near-expiry → Book v1.5. **No screen moves onto the spine before seven clean nights and his word. The 06-Sep stock check is not touched until it is completed.**

## 1 · WHAT S272 DID

| step | result |
|---|---|
| Phase 0 | board claimed v150; reports REBUILT/OK/FIXED (06:09 IST 19-Sep); clone 95d16d98, gate 664/664; Sanjeevni pins 38 match · 0 drift · 1 BLIND · 42 superseded |
| S270 verification re-run | 114/117 inputs byte-identical, same DB 9c3ac1da; `bf.pkl` rebuilt and reproduced (3,888); **14/16 keys identical**; the sweep widened to 104 inputs found the 31-Mar opening 40 units under its lines (F-564, F-565) |
| lineage trace | two pipelines, no shared tables; six copies of a fact; five Marg sources never loaded (F-566 … F-568) |
| `S272_SPINE_ARCHITECTURE.md` | the plan (D564), addendum §10 after the build; md5 29fd938e |
| the opening | his 20-Sep re-export (cc608ca2) row-identical to 27-Aug — Marg's own total; carried as exception (D565) |
| **kit S331_SPINE** | rungs 1–3 in one kit; offline gate 14/14 on the whole archive; selftest 39 with deliberate failures; installer rehearsed five ways; NO_PHONE_NUMBERS clean; `.gitignore` allow line |
| install | first line REFUSED at 2/8 (F-571), fixed, republished `c389737`; second line 8/8 green **07:19 IST**: 159 readings, gate 14/14, compare, 2 cron lines |
| `S272_WHERE_WE_STAND.md` | plain-language status by area (project + working papers) |

**Live pins (all NEW, read back from the box):** `marg_read.py 7ec9b325` · `spine_evidence.py 0fcf6c64` · `spine_build.py f5907fd4` · `spine_read.py ab55344e` · `spine_compare.py e4029460` · `spine_rules.json dd6c7616` · `selftest_spine.py bfa607b9` — all under `/root/finance/spine/`. Crontab: 2 lines `# S331_SPINE` (declared to the parent).

**The live compare at install:** `sale_bill` 779 vs spine 3,915 · `purchase_bill` 519 vs 517 · salts differ 23 (SANJEEVNI MEDICOS, live) · MRP off 43 · `stock_snapshot` latest 19-09. These are what rung 4 fixes by moving the screens.

## 2 · THE GATE, AS IT READS ON THE BOX

14/14 blocking: every export passes its witness or a sourced exception · every purchase line ties to one bill-wise bill · every sale export passes · no repeat bill number · closings witnessed; the opening declared, full, accepted · at least one closing checkable · **stock = Marg on every item at 2026-09-17** · count baseline 373 · salt/category/item-master exports pass · no salt is the shop's name · every sale and purchase name reaches a Marg item. Non-blocking notes: 1 purchase bill whose lines do not re-add (LKD 67025, Marg's own), the 10 Marg-side sale bills, 47 clip families, 144 timing differences all closed by a later closing.

## 3 · STANDING RULES CARRIED

His rules of §4 of the S270 brief, unchanged, plus: F-570 list `deploy_kits\` before claiming · F-571 import the code's way · F-572 second writes via the PC shell · F-564 the gate witnesses every input it uses · D566 seven clean nights before a lane moves · **the stock check untouched until completed (his word, 20-Sep)**.

## 4 · NUMBERS

Next free after this close: **D568 · F-573 · A-D25 · kit S334 · Session 274 (Sanjeevni) / 273 (parent)**. The board wins if later.

## 5 · OWED TO THE PARENT (one line each)

- `code_bundle.py`: carry `root/finance/spine` (`*.py`, `*.json`, `spine_compare_latest.txt`, `spine.db`) — and `spine.db` into the state backup.
- Two root crontab lines added by S331 (`# S331_SPINE`).
- F-570 is the parent's breach, owned on the board at 02:41; nothing further.

## 6 · WHERE THINGS ARE

Working papers `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S272\` (the two papers, `evidence\`, `rerun\`) · kit copy `02_SESSION_KITS\S272\S331_SPINE\` · project knowledge: `claude/S272_SPINE_ARCHITECTURE.md`, `claude/S272_WHERE_WE_STAND.md`, `claude/S272_BUILD_BRIEF.md` · the board keys `S272_progress`, `kit_S331`, `kit_S331_live` · this close's canon in `KB_canon_all\` (Register v5.113 · Archive v1.110 · Fault v2.98 · Runbook v193 · `START_HERE_SESSION_274`).

---
*S272_BUILD_BRIEF · close 20-Sep-2026 · the mandate is §0; the order is D567.*
