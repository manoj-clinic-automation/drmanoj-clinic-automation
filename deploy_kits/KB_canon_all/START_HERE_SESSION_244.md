# START HERE — SESSION 244

Hi Claude. Continuing my clinic-automation project — **Session 244**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.

## §0 · THE STANDING OWNER RULINGS — read before anything

1. **Publishing is HIS double-click.** Name one file, full path.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the `cp -i` alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. ONE step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4) in chat and the repository; never print secrets or tokens.**
   (D493: full numbers may be SHOWN on staff desks on the server — the repository rule is untouched.)
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Do the background work; ask for the one action nobody
   else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line.
12. **13-Sep-2026 mandate:** *"I have to depend upon you and your skills. Whatever you think, say first
    and best to arrange everything properly and everything remains stable and working."* Decide,
    build, prove, hand him one line. Read `SANJEEVNI_SYSTEM_BOOK` and the rulings in its §13 first.

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · Check and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` · the
assistant's browser. ⚠ The device shell on manojz has been dead since 8-Sep (F-443) — check once, say
so in one line, work through the file tools. ⚠ `F:` never mounts in that shell and is reachable anyway.
✅ The browser signs in and reads live pages as the owner.

**2 ·** Open `CANONICAL_MANIFEST.md`. **3 ·** Verify rows by md5 — stage and hash; halt on a MISMATCH
only. **Run the folder's own gate (F-448) from inside `deploy_kits/KB_canon_all`:**

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt | grep -vc ': OK$'
```

It must print 0. **Also check F-449's rule: for every document family exactly one manifest row reads
CURRENT.** **4 ·** Read only Tier 0: manifest · the project prompt · KB Register **v5.93** · Runbook
**v174** · `OWNER_TODO_LIVE.md` · any open incident. **5 ·** Open
`D:\Downloads\ClaudeCowork\00_INDEX.md` and read `03_WORKING_PAPERS\S243\S243_BUILD_BRIEF.md`.
**6 ·** Confirm, then ask which backlog item to start.

## CURRENT STATE — carried into S244

| | |
|---|---|
| **Archive** | `KB_History_Archive_v1_90_S243close.md` |
| **Fault Register** | `Fault_Action_Register_v2_75.md` |
| **KB Register** | `KB_Register_v5_93_S243close.md` |
| **Runbook** | `HANDOFF_RUNBOOK_2026-09-13_Session243close_v174.md` |
| **The map** | `SANJEEVNI_SYSTEM_BOOK_v1_1_S243close.md` (§11.4 plan of record · §12 residue · §13 rulings) |
| **Build brief** | `claude/S243_BUILD_BRIEF.md` |
| **Live pins** | `live_pins_S243close.txt` — `register_pin_verified: yes` |
| **Next free** | **D496 · F-459 · Session 244** |

**Live pins moved at S243** (all printed by the box): `finance_app.py` **912398e9** · `finance_approvals.html`
**aa79b181** · `purchase_app.py` **ad1fc004** · `stock_app.py` **aa6d9cd9** · `amir_day.py` **bf7d9826** ·
`portal.py` **06f1b378** · `tile_grants.json` **0efad736 (v14)** · `clinic_watchdog.py` **35e40626** ·
NEW `darpan_kal.py` · `reports_tile.py` · `accountant_upi_cash.py` · `salts_refresh.py` · `code_bundle.py`.
Full table: `claude/S243_LIVE_PINS_AFTER_INSTALLS.md`.

## WHAT IS TRUE THAT WAS NOT BEFORE

- Sale reports **apply themselves** on arrival (D488). The salt list **refreshes itself** (D489).
- `/root/finance` holds the live system and its logs; 495 residue files sit in `/root/_retired/S243_…`
  with `UNDO.sh` — **do not delete; the owner does, after a cycle.**
- The live code is **byte-exact in a private zip** (`D:\Downloads\ClaudeCowork\02_SESSION_KITS\` and the
  SSD) and shipped nightly to Drive — `finance_app.py` is rebuildable. Use the capture as the base for
  any finance_app patch; gate installers on lineage markers + `count==1` anchors.
- New screens: **Kal ka hisaab** (Darpan) · **Aaj ki reports** (Shavez, Amir) · accountant report ·
  "Darpan — needs you" and "Amir's visit" on the hub.

```
https://followup.dr-manoj.in/finance/darpan/kal
```

```
https://followup.dr-manoj.in/finance/reports/aaj
```

```
https://followup.dr-manoj.in/finance/accountant/upi-cash/2026-09
```

## WHAT NEEDS HIM

1. Tell Darpan (Kal ka hisaab, each morning) and Shavez (Aaj ki reports, before the first sale).
2. The procedure-medicine customer word in Marg.
3. Reprint August and LOCK it · Amir's password.
4. Rotate the F-456 keys with the MyOperator rotation.

## WHAT TO START ON

**⭐1 · D493 phase 2** — patient mobile written at Apply for patients not in the master; then the
claim tab on Darpan's page; then Phase 3 of the plan (Book §11.4) in order. The owner has said: decide
and proceed; bring him one line per change in a quiet window; read pages yourself after.

---
*START_HERE_SESSION_244 · written at the S243 close, 13-Sep-2026.*
