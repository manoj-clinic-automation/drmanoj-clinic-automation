# START HERE — SESSION 291 — written at the S290 close (the parent), 03-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz. Run `START_HERE_PROMPT_v10` (the project's custom instructions) Phase 0 first, then this file. **The work is §0 below; the list of everything pending is `claude/S288_PENDING_LIST.md`; the brief is `S290_BUILD_BRIEF.md`; the open incident is `claude/INCIDENT_2026-10-02_RECEPTION_PC_SECURITY.md`.**

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1). **291 is reserved there for this chat** (the S290 close, v183); 285 is the Sanjeevni chat's. If 291 is gone, take what the board says and say so in your first line. Kit numbers are claimed before the scratch folder is named (F-515). Read every PLANNED line on the board before touching a file it names (D646).*

*Connect `D:\Downloads`, `D:\dr-manoj-git` and `F:\ClinicBackup` (and `D:\clinic_writer`, and the two Drive folders `H:\My Drive\Clinic Data Archive\ToReception` and `…\FromReception` — these two do not mount in the PC shell; the file-transfer tools reach them). `device_bash` worked through S290 (the four disk folders mount). No git in the PC shell (F-511). The routine named in the custom instructions is v14; the canon folder holds `END_OF_SESSION_PROMPT_v16.md` and that is the one to run.*

---

## 0 · THE WORK — in the owner's order

1. **Verify this close's publish landed** (A16b: `.git/logs/HEAD`, `refs/remotes/origin/main`, the gate from inside `KB_canon_all` — 789 rows expected).
2. **The reception PC's side of the server door — the one thing between the owner's instruction and done.** Read the board first (`_claude_status.session`): the S290 chat has a check scheduled for 03-Oct 10:20 IST and records its result there. If job `20261002T220335_j13_server_door_hello.py` has answered through the server door, the door is proven. If not: is that PC on the clinic's own internet (its heartbeat on the health page; its LAN cable was out on the night of 02-Oct)? The job expires 04-Oct 22:03 — send a fresh one after that. How to send and read: Runbook v209 §1A.
3. **Then remove the Claude app from the reception PC by a job, with `"keep_claude_running": false` set in the same job** — his instruction 5 of 02-Oct. Not before step 2 is proven.
4. **The maintenance pass (§1.5):** `finance_app.py` is at the drift line — five kits since it was read whole on 27-Sep. Read it whole from the newest bundle before any backlog item. Then the three counts of the pin check against that bundle.
5. **Confirm** that the 01:50 encrypted run of 03-Oct carried `ring_outcomes.db` and the 22 Vitals sheets (its state file or `list`).
6. **The assistant's own, in order:** `secure_setup.cmd` into the reinstall kit · the build lock in the parent's installer (F-694) · F-692 (an IPv6 address for the server name) · F-693 (the reception PC and the clinic Wi-Fi, read at the desk) · the Medical PC's and Dr Manoj's PC's kits for the *Clinic PCs* tile.
7. **The owner's deferred decisions** (`claude/S288_PENDING_LIST.md` §C): the follow-up tracker move · contacts · the mail flood · the portal tiles · the "other works" for Tailscale. Build only what he says yes to.

**Held:** the Callback Tracker move (D634). **Owner-side, not ours:** the August accountant pack · the petty taps · the Docterz Clinical Data Report · the pharmacy lines on his board.

**CLOSED BY THE OWNER'S WORD OF 02-OCT — DO NOT RAISE WITH HIM AGAIN:** the technician who worked on the reception PC on 25-Sep (his trusted vendor's) · AnyDesk and UltraViewer on that PC (they stay) · changing passwords ("no need to change any Passwords") · the Windows activation there (his and the vendor's). No Windows Security scan is run on that PC and its exclusions are not changed.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami` — the browser profile is shared with the Sanjeevni chat, which signs in as staff for its walks.

**`packs.py` moved** (the Sanjeevni chat's S452, `23fda41a…`) — it is the parent's file; read it live before building on it.

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. One line per command; `\cp` past the alias.
4. Token-lean, never at the cost of verification.
5. Plain English, one step at a time, full-file replacements, ALL-CAPS = urgent.
6. Never print secrets. Patient numbers: full mobile numbers on screens for him and staff (21-Sep); none in the repository (F-185).
7. Nothing live rebuilt without his OK; the manual path stays.
8. Sub-agents read screens.
9. Do not hand him diagnostics — ask only for what nobody else can do, in one line.
10. When a screen is wrong, read its code first.
11. Do not hand him a step that is not his.
12. His board carries only what needs him and what he should know, and every close keeps its words current.
13. His own items are deferred unless urgent.
14. Never put technical choices to him — decide, say it in one line, proceed.
15. Keep chat short; collapsible pages, no long scroll.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_129_S290close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_126_S290close.md` (§S289 folded in, §S290) |
| Fault → Action Register | `Fault_Action_Register_v2_114.md` (§7.48 = F-683, F-684, F-685, F-688, F-689, F-692, F-693, F-694) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-03_Session290close_v209.md` (§1A: how to send a job to the reception PC) |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| live pins | `live_pins_S290close.txt` (DECLARED-PENDING 0; every VPS row a bundle carries = the 03-Oct 01:35 bundle) |
| build brief | `S290_BUILD_BRIEF.md` (the Sanjeevni side: `S283_BUILD_BRIEF.md`) |
| numbers | System Board `board/_numbers` — at this close (v183): **D663 · F-695 · A-D25 · kit S455 · session 291 reserved here, 285 the Sanjeevni chat's, 292 next** |

## 2 · WHAT IS LIVE FROM S289 + S290 — the short map

| what | where | state |
|---|---|---|
| The reception agent S453.1 + guard | `C:\ClinicAgent` on `receptionpc` (user `dell`); kit `deploy_kits/S448_RECEPTION_AGENT/` | live; restart test passed 02-Oct 22:44 |
| Direct upload | `/root/finance/reception_door.py`, health row *Reception PC* | live, proven both ends |
| The *Clinic PCs* tile and button | `https://followup.dr-manoj.in/finance/pcs` — `/root/finance/pc_kits.py`; serves `deploy_kits/PC_KITS/` | live; the setup file rehearsed on Windows |
| The server job door | five paths under `/finance/api/reception/jobs/` | server side proven; **PC side not proven** |
| Security on the reception PC | `C:\ClinicAgent\secure_setup.cmd` (run 02-Oct 22:26) | firewall on; held after the restart |
| Tailscale + the read-only share | `\\receptionpc\ReceptionC`, user `clinicview` | opens from his phone |

*Written at the S290 close, 03-Oct-2026.*

---

## SANJEEVNI · carried whole from START_HERE_SESSION_288 — appended at the S283 close (the Sanjeevni project), 02-Oct-2026 — for the next SANJEEVNI chat, not this one

*Carried whole from `START_HERE_SESSION_290.md` at the S290 close (03-Oct). Dated note by the parent: since this section was written S446_AMIR_STAGES_BILLS went live (02-Oct 06:15) and S452_AMIR_PANEL_FIXES went live (23:51); S454_BILL_REGISTER is written, not built, at the owner's word; S452 moved the parent's `packs.py`. The board's `_claude_status.sanjeevni` is current; the Sanjeevni close (session 285) rewrites this section.*

*The parent's chat may skip this section, except its first bullet: S444 moved three parent-owned files.*

- **For the parent — three of your files moved (S444, live 01-Oct 22:08 IST, declared).** `clinic_sso.py` → `6344e09c` (the sign-in name lower-cased at make and verify), `portal.py` → `ba61e35a` (a one-job login opens on its job; `?all=1`), `tile_grants.json` → v31 `392e6d89` (`users.amir.home`). Sanjeevni's `porders.py` → `3620b374`. All four equal the 02-Oct 01:35 bundle. Nine of §S287's eleven DECLARED-PENDING pins also equal that bundle; the other two are these (Register v5.127 §S283).
- **For the parent — two no-door findings of S444's duty map are yours:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only (13 clinic days with no first pass). `claude_code_briefs\DUTY_MAP.md`.
- **The next Sanjeevni chat — first act:** take its session number on the board. The `session_note` leaves **285** for it; take it if still free, otherwise what the board says.
- **Read:** `S283_BUILD_BRIEF.md`, then `REPORT_S444.md` and, when it exists, `REPORT_S446.md`.
- **The work:**
  1. S446_AMIR_STAGES_BILLS — the remainder of S444 (F-679). The brief is written and hash-verified on the PC; the owner pastes one line to Claude Code.
  2. Then the staff-eye walk live (D648).
  3. Then Stage A of D649: 7 orthotic vouchers → verified → renames → verified → live orthotic ordering.
- **Held:** S438_COUNT_BOOK.
- **PLANNED on the board for S446:** `amir_day.py`, `stock_app.py`, `sanjeevni_approvals.py`, `purchase_app.py`, `darpan_kal.py`; medical `marg_txt.py`, `marg_watch.py`. `packs.py` is read only.
