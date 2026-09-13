# START HERE — SESSION 255

Hi Claude. Continuing my clinic-automation project — **Session 255**. *(The session before this one was
244; it issued kits S244 … S254 and the counters are re-aligned here — F-463. There were no sessions
245–254.)*
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.

## §0 · THE STANDING OWNER RULINGS — read before anything

1. **Publishing is HIS double-click.** Name one file, full path.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the `cp -i` alias. **Every VPS install line carries
   `cd /root/deploy/repo && git pull --ff-only &&` (F-464).**
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. ONE step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) in chat and the repository; never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's code FIRST.**
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line.
12. **A published kit is immutable (F-460).** Any change takes the next kit number, built on the live pin.
13. **Decision and finding numbers come from the Register's reserved line, read at minting (F-463).**
14. **Staff pages Hindi/Hinglish; owner pages and chat English. Keep chat short.**
15. **If a second chat is open, name the live file both will touch before either builds (F-462), and
    fold that chat into the close under a name he can add to its title.**

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · Check and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` · the
assistant's browser. ⚠ The device shell on manojz has been dead since 8-Sep (F-443) — say so in one
line, work through the file tools. ⚠ `F:` never mounts in that shell and is reachable anyway.

**2 ·** Open `CANONICAL_MANIFEST.md`. **3 ·** Verify rows by md5 — stage and hash; halt on a MISMATCH
only. Run the folder's own gate from inside `deploy_kits/KB_canon_all`:

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt | grep -vc ': OK$'
```

It must print 0. For every document family exactly one manifest row reads CURRENT (F-449).
**4 ·** Read only Tier 0: manifest · the project prompt · KB Register **v5.94** · Runbook **v175** ·
`OWNER_TODO_LIVE.md`. **5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read
`03_WORKING_PAPERS\S244\S244_BUILD_BRIEF.md`. **6 ·** Confirm, then ask which backlog item to start.

**7 · TWO PINS TO RE-HASH ON THE BOX at the open, in one line, before any kit touches either file —
the Register carries them as not-passes:**

```
md5sum /root/finance/amir_day.py /root/staff_master.csv
```

Expected: `amir_day.py` **a9f2062267ebac59e02fdb0f88e775de** (S246 installed) — if it reads
`79eb701f…`, S246 is published and NOT installed, and its one line is still owed;
`staff_master.csv` begins **e48ae0b0** (S248). Correct the two Register rows from what the box prints.

## CURRENT STATE — carried into S255

| | |
|---|---|
| **Archive** | `KB_History_Archive_v1_91_S244close.md` |
| **Fault Register** | `Fault_Action_Register_v2_76.md` |
| **KB Register** | `KB_Register_v5_94_S244close.md` |
| **Runbook** | `HANDOFF_RUNBOOK_2026-09-13_Session244close_v175.md` |
| **The map** | `SANJEEVNI_SYSTEM_BOOK_v1_1_S243close.md` (unchanged this session) |
| **Build brief** | `claude/S244_BUILD_BRIEF.md` |
| **Live pins** | `live_pins_S244close.txt` — `register_pin_verified: yes` |
| **Next free** | **D510 · F-465 · Session 255** |

**Live pins moved at S244** (printed by the box unless marked): `amir_day.py` bf7d9826 → aad400fa →
79eb701f → **a9f20622 (predicted — re-hash)** · `staff_ledger.py` **eacd7154** · `staff_master.csv`
**e48ae0b0 (SHORT — re-hash)** · `finance_clinic_day.py` **b2b7ff7d** · `clinic_register.py` **eaaea278** ·
`finance_app.py` **1fc62335** · NEW `clinic_money.py` **d5c3a845** · `portal.py` **d0f126a3** ·
`tile_grants.json` **v16 d7edf850** (v15 `932f7bd0` was the second chat's S250).

## WHAT IS TRUE THAT WAS NOT BEFORE

- The morning match is a screen, not a ritual: reception answers flags, Shavez checks, the owner sees
  four things. Flags never disappear until reconciled. The checker is `setting clinic_money.checker`.
- The float (₹2,500) is on the counter sheet and is never revenue; a normal day costs no taps.
- *Paid to another UPI* is a box on the sheet; physiotherapy is its own unit and table.
- Amir's step 4 tells him *processing* and lets him carry on; a closed day can be reopened.
- An advance can be collected against a closed month from the ledger card.
- **Not yet true:** the Razorpay / Yes Bank channel (Docterz Wallet / Patient APP / Net Banking) is
  still untracked — the plan is three steps in `claude/S244_BUILD_BRIEF.md`.

```
https://followup.dr-manoj.in/finance/clinic/match
```

```
https://followup.dr-manoj.in/finance/clinic/money
```

```
https://followup.dr-manoj.in/finance/physio
```

## WHAT NEEDS HIM

1. Bhati's login at `/portal/users` (parked by him). 2. Tell reception and Shavez about *Morning
match*; Saturday 12-Sep's first pass is still open. 3. Reprint August and LOCK it. 4. Amir's password.
5. Rotate the F-456 keys. 6. Delete `/root/_retired/S243_…` after a cycle.

## WHAT TO START ON

**⭐1 · The Razorpay / Yes Bank channel** (D507): stop expecting channel 4 in the ICICI file → the
payment-email relay from his personal Gmail into `portal_payment` → Yes Bank settlement recognition
through the 07:00 statement relay. Then Bhati's itemising and the learning step when he asks; then the
S243 carry-overs (D493 phase 2, the F-458 gate, the pin rows, F-451).

---
*START_HERE_SESSION_255 · written at the S244 close, 13-Sep-2026.*
