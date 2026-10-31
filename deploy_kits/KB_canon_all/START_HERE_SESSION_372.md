# START HERE — SESSION 372 — written at the S371 close (the parent), 31-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, linked to manojz. IPD kit 4 was given to Claude Fable (D807); use it when he has answered the mock-up.
1. Follow `OPEN_ROUTINE_v1` (read it from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The project's custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work: the open (§0 A); then IPD KIT 4 once he has answered the mock-up's three questions (§0 B).** If he has not, ask them once, in one message, and take whatever he names next.
   - The Runbook is v284 (§2A). The Register §S371 holds D809 (the consent's ankle and staged plan); §S370 holds D806–D808; §S368 D804 (the IPD design v2).
   - The live IPD module: `/root/finance/surgery_cases.py` 89a668a9 (S681, `S681-IPD-3.0`, CONFIRMED by the 31-Oct bundle). Its kit: `deploy_kits/S681_IPD_PAPERS_BILL/`. The mock-up: `https://claude.ai/artifact/D4BQUWfNKqoXHt5uZBJmcw` (file in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S371\`).

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **372 is RESERVED for the parent.** 369 (Sanjeevni) was open at this close; 363 (Scan App) and 365 (NK Pathology) reserved.
- At this close: D810 · F-1059 · A-D25 · kit S686 · session 373 next. **Kit S682 is already taken** for kit 4 and PLANNED on `surgery_cases.py` 89a668a9 (30-Oct 15:05); the line goes stale on 6-Nov — after that, write a fresh PLANNED line on the newest bundle's bytes.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* The standing rules of `START_HERE_SESSION_357.md`'s connection list stand whole: never `git` in the device shell; every commit to the PC read back by hash; a published kit folder never changes.

***Every time you write is read first: the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

**Learned this session (S371):**
- **A real patient's case is the best test of a generator.** His proximal humerus + bimalleolar-with-subluxation consent showed four gaps at once; the answer was ticks, not more fixed procedures.
- **Never swap shared state for the length of a call (F-1058).** Compute it where it is read (a getter); a second run then cannot see a half-restored value.
- **A step that reports success counts what it changed (F-1057).** "0 places" is never a tick; a search for text must look for the text as it is printed, after every tidy-up.
- **The consent page:** `/root/wa/casepack/casepack_page.html`, served per request by `casepack_portal.py` (`/portal/casepack`, no restart). Kits on it carry a `make_sXXX.py` that the installer re-runs on the box's live file and must match byte for byte; the walk runs on `file://` in Chromium with every non-file request aborted. `walk_s684.py` holds the page helpers (`open_page`, `reset`, `gen`); `walk_s685.py` imports them.
- **The device VM:** `/tmp` is wiped overnight; rebuild from the newest bundle. Run walks in the foreground. `pkill -f` can kill its own shell (exit 144): harmless.

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN (`OPEN_ROUTINE_v1`).**
1. **The board:** every note, every message with `read:false`. **Remind him of the packs page (D713).**
2. **The day's checks:** read or run `day_open.py`; `UNREAD_LISTS_LATEST.txt`. **The finance restore drill** should be fresh after its first run (Sunday 1-Nov 02:10); if not, it is the first work.
3. **The newest bundle against `live_pins_S371close.txt`:** `casepack_page.html` f95d186d. When the 01-Nov bundle carries it, the DECLARED-PENDING 3 becomes 2. Any other change is a halt; re-read the file whole (F-472).
4. **The rest (first open of the day only):** project knowledge measured once, never-cited %, what no store holds, the cold kit when DUE.

**B · IPD KIT 4: THE IMPLANT BILLS DESK, THE CHEQUE, THE VENDORS' LEDGER (D807; Runbook v284 §2A item 2; kit S682).**
- **His three answers first** (asked 30-Oct 15:10, on the mock-up's last board): the five steps' words · does Shavez write the cheque from the desk (number, date, amount) · old cases settled only by him on the vendor's page.
- **Read first, whole:** `surgery_cases.py` 89a668a9 from the newest bundle: the vendors' pages, the vendor ledger, the hospital payments (receipts), `IMPL_PAY` and `_follow_implants` (S681), the old-case exclusion from the vendors' balances and the awaiting-cheque list, and `surg_bill`'s credit line (`COALESCE(payable, bill)`, the implant's actual cost, owner-only).
- **What it is for (D804, D807):** Shavez enters or scans each vendor's bill against its case's implant (the scanner widget the papers use); the hospital's cheque is recorded; the vendor is paid and confirms. Each implant's step moves and the case's step follows the least advanced. A vendor's page shows its ledger (bills, payments, balance). The old cases' implants are settled there, one by one, and join the balances only once settled.
- **Who sees what (D804):** Shavez sees and enters everything except the implant's actual cost; the actual cost and the amounts paid to vendors are Dr Manoj's (checker).
- **Every S681 gate:** carry walk_s681's 254 checks and add a section; the control on the live module; the probe as manoj, shavez, bhawna, darpan; mutants; a cold review by a sub-agent (two rounds); the real screens sent before placing; the rehearsal (DRY · install · ALREADY INSTALLED · red after placing restores 89a668a9). Then the publish and the one server line.
- **No phone number, name or clinic ID in the repository (F-185); no patient file in the cloud workspace (D656).**

**C · THEN, in order (Runbook v284 §2A):** the Hostinger kernel update when its fix is out (a read-only OS check in the next server line first) · kit 5 when the hospital has explained the credit heads (D808) · kit 6 · the X-ray film log (D805; a mock-up first) · F-1051 (three closes) · his three board items of 27-Oct · F-1031 · D786's first month from 1-Nov · the rest.

**On Monday 2-Nov:** the newest `claude/AUDIT_RUN_*` (slice 5) and its *For the builder* lines; the close answers each.

**Owner-side, on his board:** the publish (Y182) · the packs page (shops and passwords) · Y106 · the glucometer line · his IPD share % · the hospital's word on the credit heads (Y181) · from 1-Nov *Approve & save* · the Marg engineer's restore test · the SBI downloads · Raghav's Zerodha papers · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence in November.

**Standing owner rulings:** rules 1–51 of `START_HERE_SESSION_360.md`, 52–53 of `START_HERE_SESSION_368.md`, 54–56 of `START_HERE_SESSION_370.md` and 57–59 of `START_HERE_SESSION_371.md` stand whole. Added:

60. **The consent's ankle is built from ticks; any closed fracture can be "external fixator now, fix later"; an extra fracture can be "plan later"; definitive fixation is never assumed to be a plate (D809).** Plaster/slab-now only with its own wording, at his word.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_204_S371close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_201_S371close.md` (§S371) |
| Fault → Action Register | `Fault_Action_Register_v2_188.md` (§7.122) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-31_Session371close_v284.md` (**§2A the order**) |
| open / close / prompt | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` · `COMMON_START_HERE_PROMPT_v1.md` |
| live pins | `live_pins_S371close.txt` |
| build brief | `S371_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers`. At this close: **D810 · F-1059 · A-D25 · kit S686 · session 373 next; 372 RESERVED for the parent** |

*Written at the S371 close, 31-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (369 open):** the Marg spine gate has failed since 29-Oct 09:40 — the evidence is on the board for it (`parent_S371_1`). D803 / F-1048 (the PC set-up kits) remain the parent's, queued after the IPD build.
- **The Scan App (363 reserved):** unchanged by this session. **NK Pathology (365 reserved):** unchanged.
- **For all:** `/root/wa/casepack/casepack_page.html` moved twice this session (f95d186d). A chat touching it builds on these bytes.
