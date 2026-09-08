# HANDOFF RUNBOOK — v164 · Session 232 close · 08-Sep-2026

*Supersedes v163 (S231 close). Tier 0.*

---

## §0 · WHAT HAPPENED

**Attended, ~10 hours, six publishes. Two machines changed. Not one live VPS file moved.**

**Phase 0.** `D:\Downloads` was **not connected** at the open — named, requested, granted; the same
shape as S229 and S230. Manifest **413/413** from inside `KB_canon_all`, inverse check clean.

**The morning's task was one line of records housekeeping. It became F-369.** The pin the to-do list
said was stale **had no row to be stale in**: four live VPS files had been written only into a
per-session WAVE table below the `§12 STATE` heading, which `gen_live_pins.py` never reaches. They
were in **no** pin list and `verify_live_pins.py` had never held the box to one of them, from S230 to
S232. The same read found the manifest naming **two CURRENT Registers**. Repaired atomically; VPS
rows **95 → 99**; **the owner read all four back from the box and all four matched.**

**⭐1 · The secret gate.** `NO_PHONE_NUMBERS.py` widened — one gate, one place — to refuse a Bearer
literal, a private-key block and secret-shaped assignments. **Selftest 20/20 · 0 false alarms across
the whole repository · 1 true catch on the file that actually leaked.** Two false alarms were found
by measurement and killed, one of them `author`, which contains `auth`. `PUBLISH_ALL.bat`'s refusal
banner was a trap and was corrected.

**⭐2 · F-363.** On disk 7,589 bytes; the true document **exactly 7,607**. Six differing lines: five
ASCII flattenings **and `(D400-adjacent)` dropped** — sixteen bytes of meaning. S231's hand-retype
verdict confirmed by measurement.

**⭐3 · The staff advance policy, rebuilt from `staff_ledger.py` v3.6-S225-LOANS-D374**, verified
byte-identical to the live pin first. Both stored copies were byte-identical **and both wrong**.

**⭐5 · F-362** closed on the MEDICAL PC (captures start at boot; `WATCHER ALIVE, pid 9948`) and
**F-368** closed on the VPS (nine files quarantined, nothing deleted). **Tailscale closed both ends.**
The renewals and vendor register written with the name estate measured by DNS.

**The nightly task's eleven empty nights ended** — D426, a standing item, and an entry point that
cannot go stale.

**New fault codes:** F-369, F-370, F-371. **Decisions:** D425, D426, D427.
**No SOP change. No surveillance-scope change.**

---

## §1 · MENTAL MODELS — what changed in how to think about this system

**1 · A hash gate proves the rows it HAS. It says nothing about the rows it does not have.**
Every check in this estate is of that kind. **An absent row is a live file nobody is checking**, and
no green will ever show it. When you verify a set, ask what is *missing* from it.

**2 · A design document becomes a lie the day it ships.** The S190 advance policy was written to get
a build approved, ends *"nothing is built yet"*, and was still being quoted as policy five amendments
later. **Either it is re-issued as-built at the close that ships it, or it is banner-retired then.**

**3 · Two stores agreeing is not correctness.** Both copies of that policy were byte-identical. A
byte sweep is blind to a document that agrees with itself everywhere and has been overtaken by
reality. **Only a person who knows what the clinic does can catch that** — and the owner did, twice.

**4 · Count the bytes to find the fault; read the diff to name it.** F-363's eighteen bytes look like
a flattening in the count. The diff shows a lost parenthetical — which no encoding pass produces.
**The difference between an encoding event and a retype is visible only in whether anything was
LOST.**

**5 · Cadence, not recency, decides whether a silence means anything.** Two triggers both last ran
seven days ago; one is a fault and one is a healthy monthly job. **The page does not show the
schedule.** Ask what the thing's period is before calling a gap a stop.

**6 · A selftest that cannot fail is not a test.** One written this session read `hhmm(x) == hhmm(x)`
— true on any machine in any zone. Rewritten against constants, it failed on its first run and then
passed. **Make it fail once on purpose before you trust it.**

**7 · "Not mid-X" and "after X" are different instructions.** F-368 sat behind the WABA rotation for
sessions because *"not to be touched mid-rotation"* was read as *wait for the rotation*. Doing it
BEFORE was strictly safer. **The owner asked the question that surfaced it, and was right about four
of the five items held there.**

**8 · When a setting has a CLI, ask the CLI.** Two console hunts for Tailscale's key expiry failed;
one line of PowerShell answered in a second.

---

## §2 · THE LIVE BACKLOG — what S233 picks up

**The full plan, marked against what is done, is `claude/S232_ACTION_PLAN.md`. In order:**

**⭐1 · Back up the Apps Script projects and the live Sheets.** **The last way this estate can lose
data quietly.** Eleven projects (not nine) and seven Sheets are live databases with no backup of any
kind; Apps Script keeps history inside Google and nowhere else. **D426 makes it buildable
unattended.** The trigger read this session says which projects are actually armed, so it covers the
live ones first.

**⭐2 · Sanjeevni steps 2+3, clubbed** — derivation off the screens, the four lanes pointed at the
spine. **The spine was built at S229 and nothing reads it yet.** No screen changes behaviour; this is
the moment the screens stop being able to disagree. Every visible improvement is downstream of it.

**⭐3 · Step 4 — sections as jobs**, with the owner, screen by screen. Six role maps instead of
forty-two tiles; the roles are written concretely in `S230_SURFACE_AND_ROLES` §6. Three cheap fixes
ride with it: one Stock Check tile sending three people to the same wrong door · **no list of counts
and no "start a new count"**, though a count is the unit of work · six English money-tile names a
Hindi-first staff member cannot tell apart.

**⭐4 · The WABA rotation**, on MyOperator's reply — **the only thing genuinely blocked.** Then
self-hosted ntfy (D427) and Bitwarden (D421).

**⭐5 · Then:** the watchers and the three-month expiry window · the direct push (D402) · **the junk,
last and by evidence.**

**Also standing:** the morning digest is built and waiting (⭐6) · F-370 rides the next
`staff_ledger.py` kit · the orphaned Apps Script trigger is recorded and untouched · `git gc`, the
`/root` tidy and the KB retirement remain cheap Tier-3 work.

---

## §3 · INSTALL DISCIPLINE

Unchanged and still earned: build and test offline → `py_compile` → the owner installs. **A prepared
kit is proven only by a LIVE-SHAPE walk.** Verify a kit gate from **inside** its own folder. Never
run `py_compile` inside the repository — and note that `python3 -m py_compile` writes `__pycache__`
**even with `PYTHONDONTWRITEBYTECODE=1`**, because it writes the cache explicitly. Move it out and
name it in `WHY_SAFE.txt`.

**New this session, and it is the strongest proof-of-no-change available:** to show a source edit
changes no behaviour, **compile both files and compare their code objects** — name, argcount, names,
varnames and bytecode, walked recursively. `S232_F370_COMMENT` did this across **312** code objects
and matched exactly. **A diff shows what you changed; a code-object comparison shows what the machine
will do.**

**`GIT_OPTIONAL_LOCKS=0` is NOT an escape from F-233** — measured this session, `git status` still
takes the lock. The rename-aside remains the only remedy.

---

## §4 · THE BOUNDARY — what is live, what is not

**LIVE on the VPS:** the widened publish gate (in the repo, used at every publish) · the F-368
quarantine folder `/root/_quarantine_S232_F368_20260908_111131/`, mode 700 — **delete it after the
WABA rotation, not before.** `/root/finance/freshness.py` `66d93a63…` **read back from the box and a
pass**, together with `freshness_legs.json`, `clinic_state_backup.py` and `verify_restore.py`.

**LIVE on MEDICAL:** scheduled tasks `MargAgentBoot` and `MargAgentBootStop`. **The Startup folder
item is untouched** — that is deliberate, and the Drive leg depends on it.

**NOT live:** `deploy_kits/S232_MORNING_DIGEST/` and `deploy_kits/S232_F370_COMMENT/` — both built,
proven and staged. **`S232_F370_COMMENT/staff_ledger.py` is the new BASE** for the next kit that
touches that file; the live pin `80257711…` has not moved.

**HELD BY THE OWNER:** the PWA install, until the restructure exercise is done · the Sanjeevni/Marg
project split, until it is developed further · Apps Script work (read, never act — the ICICI → VPS
chain is load-bearing across three projects and the Callback Tracker is not to be touched at all).

**Owed to the owner:** nothing that blocks a session. One reply from MyOperator, and one look at
`Security _ Hostinger.pdf` when convenient.

---
*HANDOFF RUNBOOK v164 · S232 close · 08-Sep-2026. Next free: **D428 · F-372 · Session 233.***
