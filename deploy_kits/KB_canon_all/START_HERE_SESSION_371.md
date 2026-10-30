# START HERE — SESSION 371 — written at the S370 close (the parent), 30-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, **on Claude Fable** (his word, 30-Oct 13:47: kit 4 *"seems a complex one? so how about giving it to fable"*), linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (read it from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The project's custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work: the open (§0 A), then IPD CASES KIT 4: THE IMPLANT BILLS DESK, THE CHEQUE AND THE VENDORS' LEDGER (§0 B).**
   - The Runbook is v283 (§2A item 2). The Register §S370 holds D806 (full mobiles, the IVR call), D807 (the kits' order) and D808 (the hospital statement; the share both ways). D804 (the design v2) is in §S368.
   - The live module: `/root/finance/surgery_cases.py` 89a668a9 (S681, `S681-IPD-3.0`, 3,136 lines). Its kit, with the walk, probe and installer to build on: `deploy_kits/S681_IPD_PAPERS_BILL/` (= `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S370\S681_kit\`).

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **371 is RESERVED for the parent.** 369 (Sanjeevni) was open at this close; 363 (Scan App) and 365 (NK Pathology) reserved.
- At this close: D809 · F-1056 · A-D25 · kit S682 · session 372 next. Kit 4 takes a NEW kit number (S682 or the board's next), PLANNED on `surgery_cases.py` 89a668a9 before the scratch folder is named.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.* The standing rules of `START_HERE_SESSION_357.md`'s connection list stand whole: never `git` in the device shell; every commit to the PC read back by hash; a published kit folder never changes.

***Every time you write is read first: the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

**Learned this session (S370):**
- **Show the real screens first, then the cold review, then the installer.** Both kits were rendered from the real module with made-up patients and sent to him before placing. The screen review found a nested form (F-1054); the cold review found phone numbers in page addresses (F-1055) and a guessed pin (F-1052).
- **No phone number in a page address, ever.** Searches post; links carry the patient's UID; the server looks the mobile up. `NO_PHONE_NUMBERS.py` blocks phone-shaped literals in the repository, so test numbers in a walk are split into adjacent string literals.
- **Every pin is pasted from an `md5sum` of the real bytes in the same run (F-1052).**
- **A re-commit of a device path goes from a NEW staged folder, read back by hash (F-1053; third time).**
- **The device VM:** `/tmp/s370/` held the bundle (`code/`) and a database copy (`db.sqlite`); `/tmp` is wiped overnight, so rebuild from the newest bundle. Run walks in the foreground.
- **The call service:** `call_api.py` on 127.0.0.1:8097 `/call`, the key from `/root/wa/.env` (never shown), the agents from `/root/portal/ring_agents.json`. The walks use a stand-in; no test ever reaches MyOperator.

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN (`OPEN_ROUTINE_v1`).**
1. **The board:** every note, every message with `read:false`. **Remind him of the packs page (D713).**
2. **The day's checks:** read or run `day_open.py`; `UNREAD_LISTS_LATEST.txt`.
3. **The newest bundle against `live_pins_S370close.txt`:** `surgery_cases.py` 89a668a9, `portal.py` 1a9b3a1b, `tile_grants.json` 64305c5f, `casepack_page.html` 26cba6b1. When the 31-Oct bundle carries them, the DECLARED-PENDING 6 becomes 2. Any other change is a halt; re-read the file whole (F-472).
4. **The rest (first open of the day only):** project knowledge measured once, never-cited %, what no store holds, the cold kit when DUE.

**B · IPD KIT 4: THE IMPLANT BILLS DESK, THE CHEQUE, THE VENDORS' LEDGER (D807; Runbook v283 §2A item 2).**
- **Read first, whole:** `surgery_cases.py` 89a668a9 from the newest bundle: the vendors' pages, the vendor ledger, the hospital payments (receipts), `IMPL_PAY` and `_follow_implants` (S681), the old-case exclusion from the vendors' balances and the awaiting-cheque list (S680, F-1055's round), and `surg_bill`'s credit line (`COALESCE(payable, bill)`, the implant's actual cost, owner-only).
- **What it is for (D804, D807):** the implant bills arrive from the vendors. Shavez enters or scans each bill against its case's implant (the scanner widget the papers already use). The cheque from the hospital is recorded; the vendor is paid and confirms. Each implant's step moves (not raised · bill raised · cheque received · paid to the vendor · vendor confirmed) and the case's step follows the least advanced. A vendor's page shows its ledger: bills, payments, balance. **The old cases' implants (backfill) are settled here**, one by one on the vendor's page, and join the balances only once settled.
- **Who sees what (D804):** Shavez sees and enters everything except the implant's actual cost; the actual cost and the amounts paid to vendors are Dr Manoj's (checker).
- **The order:** a mock-up of Shavez's desk and a vendor's page (PC and phone), sent to him first; his word; then the build. Every S681 gate: carry walk_s681's 254 checks and add a section; the control on the live module; the probe through the real app as manoj, shavez, bhawna, darpan; mutants; a cold review by a sub-agent (two rounds); the real screens sent before placing; the rehearsal (DRY · install · ALREADY INSTALLED · red after placing restores 89a668a9). Then the publish and the one server line.
- **No phone number, name or clinic ID in the repository (F-185); no patient file in the cloud workspace (D656).**

**C · THEN, in order (Runbook v283 §2A):** kit 5 when the hospital has explained the credit heads (D808) · kit 6 · the X-ray film log (D805; a mock-up first) · F-1051 · his three board items of 27-Oct · F-1031 · D786's first month from 1-Nov · the rest.

**On Monday 2-Nov:** the newest `claude/AUDIT_RUN_*` (slice 5) and its *For the builder* lines; the close answers each.

**Owner-side, on his board:** the packs page (shops and passwords) · Y106 · the glucometer line · **his IPD share % (Settings; until then "your formula" is not worked)** · **the hospital's word on the credit heads** · from 1-Nov *Approve & save* · the Marg engineer's restore test · the SBI downloads · Raghav's Zerodha papers · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence in November.

**Standing owner rulings:** rules 1–51 of `START_HERE_SESSION_360.md`, 52–53 of `START_HERE_SESSION_368.md` and 54–56 of `START_HERE_SESSION_370.md` stand whole. Added:

57. **Full mobiles on the IPD pages, and the call from the case through MyOperator's IVR (D806).** No phone number in a page address.
58. **The IPD kits' order (D807):** kit 4 on Claude Fable in a fresh chat; kit 5 after the hospital explains the credit heads; kit 6 after.
59. **The share both ways (D808):** the hospital's (the four heads × the statement's %, 50) beside his formula; the amount due his to choose.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_203_S370close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_200_S370close.md` (§S370) |
| Fault → Action Register | `Fault_Action_Register_v2_187.md` (§7.121) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-30_Session370close_v283.md` (**§2A the order**) |
| open / close / prompt | `OPEN_ROUTINE_v1.md` · `CLOSE_ROUTINE_v1.md` · `COMMON_START_HERE_PROMPT_v1.md` |
| live pins | `live_pins_S370close.txt` |
| build brief | `S370_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers`. At this close: **D809 · F-1056 · A-D25 · kit S682 · session 372 next; 371 RESERVED for the parent** |

*Written at the S370 close, 30-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (369 open):** D803 / F-1048 (the PC set-up kits) remain the parent's, queued after the IPD build. F-1051 is still the parent's.
- **The Scan App (363 reserved):** the IPD papers use its scanner widget (unchanged by both kits). **NK Pathology (365 reserved):** unchanged.
- **For all:** `/root/finance/surgery_cases.py`, `/root/portal/portal.py`, `/root/portal/tile_grants.json` and `/root/wa/casepack/casepack_page.html` moved this session (the pins above). A chat touching them builds on these bytes.
