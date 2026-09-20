# START HERE — SESSION 274 — written at the S272 close, 20-Sep-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project. Run `SANJEEVNI_START_HERE_PROMPT_v1_1` (the project's custom instructions) Phase 0 first, then this file. **Read `S272_BUILD_BRIEF.md` §0 for the mandate and §2 for what is live.**

*FIRST ACT: take your session number from the board document `board/_numbers` by a version-pinned write (`NUMBERS_PROTOCOL_v1.md`, in canon). 274 is reserved there for this chat; if the pinned write fails, re-read and take what it says. Every kit, D and F number is taken the same way, before the scratch folder is named and before the first canon file is written — never from this file, the Register or `deploy_kits\`.*

---

## 0 · HIS INSTRUCTION FOR THIS SESSION

> *"do seven number point and then start the build in your preferred order in a fresh chat in this session."* — 20-Sep, after the spine went live. Point 7 was this close. The order is D567:

1. **Shavez's morning tile** — `SHAVEZ_MORNING_TILE_PLAN.md`; a ✓ means the report re-added (the spine's readers).
2. **His overdue line** on the health card — salt list > 8 days, item / category lists > 35 days.
3. **Refused files kept in quarantine** by the one door, not deleted (Book 3d).
4. **The spine on the health page** (`spine_read.py status`, one line); name `spine.db` + `readings/` to the parent for the nightly backup.
5. **Ordering prepared offline** against the live spine, rehearsed every night — **not switched**.
6. **Near-expiry** from the archived expiry exports (D409).
7. **The Sanjeevni Book v1.5** — the spine as its §4; §11.4 item 3e's witness is now D566.

**Do not** move any screen onto the spine before seven clean nights of `gate 14/14` (D566) and his word. **Do not** touch the stock-check screens or tables until count #1 is closed — his standing rule, restated 20-Sep.

Each morning: read the spine's line first —
```
/root/wa/venv/bin/python3 -B /root/finance/spine/spine_read.py status
```
(it is his line to run; the nightly bundle carries `/root/finance/spine/` from 01:35 tonight if the parent widens the bundle — until then the compare file `spine_compare_latest.txt` is read from the box).

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_113_S272close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_110_S272close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_98.md` (F-0 … F-572) |
| Runbook | `HANDOFF_RUNBOOK_2026-09-20_Session272close_v193.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_4_S268.md` (v1.5 is item 7 above) |
| the contract · the reference | `MARG_REPORT_CONTRACT_v1.md` · `S270_CORE_DATA_VERIFICATION_REFERENCE.md` (in canon from this close) |
| the plan · the status | `S272_SPINE_ARCHITECTURE.md` · `S272_WHERE_WE_STAND.md` (project knowledge + working papers) |
| live pins | `live_pins_S272close.txt` |
| build brief | `S272_BUILD_BRIEF.md` |

**Next free: D568 · F-573 · A-D25 · kit S334 · Session 274 (this file) — the parent's next is 273 (`START_HERE_SESSION_273.md`).**

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

Seven files NEW under `/root/finance/spine/` (kit `S331_SPINE`, pins in the Register §S272) and two root crontab lines tagged `# S331_SPINE`. Nothing existing changed. The 06-Sep count: 373 rows, untouched, proven by the gate on every build.

## 3 · THE PIN CHECK AT YOUR OPEN

Hold the seven spine files against the 21-Sep 01:35 bundle **only if the parent has widened `code_bundle.py` to carry `root/finance/spine`** — otherwise they are ABSENT from the bundle by rule, not drift; say so. The VPS `signatures.json` is still `b2dcb211` against manojz `a987a08e` (known divergence, carried).

## 4 · LESSONS FROM THIS SESSION, kept short

1. The board's `nextFree` is not the whole truth — list `deploy_kits\` too (F-570).
2. An import check imports the way the code does (F-571).
3. A second commit to the same path lands old bytes — use the PC shell (F-572).
4. An audit keeps its derived inputs (F-569).
5. The bundle is 01:35 evidence; a folder added after it is absent by rule, never drift.
