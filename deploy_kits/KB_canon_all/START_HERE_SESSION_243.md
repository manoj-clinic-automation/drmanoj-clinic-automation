# START HERE — SESSION 243

Hi Claude. Continuing my clinic-automation project — **Session 243**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.

## §0 · THE STANDING OWNER RULINGS — read before anything

1. **Publishing is HIS double-click.** Name one file, full path.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the `cp -i` alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. ONE step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4); never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Do the background work; ask for the one action nobody
   else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line.
    He weighs in on what he can SEE: a screen, a wording, a workflow, a priority.

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · Check and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` ·
the assistant's browser.

⚠ **`F:` never mounts in the device shell — that does NOT mean unreachable.** The file-transfer
tools read and write it perfectly.

⚠ **THE DEVICE SHELL HAS BEEN DEAD SINCE 8-Sep** (Windows update, F-443). Check it once. If it is
still dead, say so in one line and work through `device_list_dir` / `device_stage_files` /
`device_commit_files`, which work normally.

✅ **BUT — F-447, and this changes what you may promise.** `gen_live_pins.py` and `MD5SUMS_ALL.txt`
**never needed that shell**: the first is a script over two files, the second is md5 over a folder
of files, and both ran in the workspace at the S242 close. **Stage the files and run them here.**
Only a step that genuinely needs a shell ON manojz is blocked by F-443. When a blocker survives a
close, re-ask which resource it actually needs.

⚠ **F-448 — RUN THE FOLDER'S OWN GATE AT PHASE 0, EVERY TIME.** It had been exiting 1 since the S241
close and nobody ran it. It is one command and it is the cheapest verification in this project:

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt
```

**It must exit 0.** At the S242 close it was rebuilt to 495 rows and does. Also run the inverse
check — files on disk = rows listed + `MD5SUMS_ALL.txt` itself.

✅ **The assistant's browser signs in and reads live pages.** Use it to verify a live page rather
than asking him what it says. Site access granted for `followup.dr-manoj.in` and
`attendance.dr-manoj.in`.

**2 ·** Open `CANONICAL_MANIFEST.md` (Tier 0 · the linchpin).
**3 ·** Verify rows by md5 — stage and hash; halt on a MISMATCH, never on absence from one store.
Verify a kit gate from INSIDE its own folder.
**4 ·** Read only Tier 0: manifest · the project prompt · KB Register **v5.92** · Runbook **v173** ·
`OWNER_TODO_LIVE.md` · any open incident.
**5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read `03_WORKING_PAPERS\S242\S242_BUILD_BRIEF.md`.
**6 ·** Confirm, then ask which backlog item to start.

## CURRENT STATE — carried into S243

| | |
|---|---|
| **Archive** | `KB_History_Archive_v1_89_S242close.md` |
| **Fault Register** | `Fault_Action_Register_v2_74.md` |
| **KB Register** | `KB_Register_v5_92_S242close.md` |
| **Runbook** | `HANDOFF_RUNBOOK_2026-09-12_Session242close_v173.md` |
| **Build brief** | `claude/S242_BUILD_BRIEF.md` |
| **Live pins** | `live_pins_S242close.txt` — **`register_pin_verified: yes`** |
| **Next free** | **D485 · F-449 · Session 243** |

**Live pins moved at the S242 close** — each predicted before the install and printed by the box:
`/root/finance/clinic_register.py` **`c6b87682ccbfb03734a39ad33c26f2a3`** ·
`/root/portal/portal.py` **`d08721f69bc7c3e3a79a50192b20affb`** ·
`/root/portal/tile_grants.json` **`7e7445a37ace9ea7c8218d598a05b81d`** (v12).

## WHAT IS TRUE THAT WAS NOT BEFORE

**The staff app is in use.** Shavez signed in; **Alisha made the first entry the daily register has
ever carried** on 12-Sep at 21:26 IST; Amir's single tile was verified in an incognito window.

```
https://followup.dr-manoj.in/finance/clinic/register
```

```
https://followup.dr-manoj.in/finance/amir
```

**⛔ D484 — DO NOT FLAG THE EMPTY DRAWER COUNT.** The nine boxes are the record and they reconcile
against the overnight report and the bank MPR. The notes-and-coins count is a convenience, offered
and never demanded. **A day with the boxes filled and that section blank is COMPLETE.**

**Amir carries exactly one tile** (D483). Forms & Downloads, Scan Purchase, Marg Purchases, Order
Medicines and Stock Check are **parked for him, not removed** — one line each to bring back, and
unchanged for everybody else. Do not "restore" them; he will say when.

## WHAT NEEDS HIM

1. **Reprint August and LOCK it** — still the only thing standing on his side.
2. **Reset Amir's password** (login `amir`); nobody can look the old one up.

```
https://followup.dr-manoj.in/portal/users
```

3. **One line on the VPS — A8c, the deploy clone, owed at every close:**

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```

## WHAT TO START ON

**⭐1 · Darpan's claim queue.** States `open → contacted → settled`; settled must name an outcome;
self-closes on a matching purchase return; ages to the top at fourteen days (D471). Amir's page has
been writing `amir_claim` rows since it went live and **none has been raised yet**, so the queue
opens quiet — build it for the first one, not for a backlog.

Then `OWNER_TODO_LIVE` ⭐1 in order.

---
*START_HERE_SESSION_243 · written at the S242 close, 12-Sep-2026.*
