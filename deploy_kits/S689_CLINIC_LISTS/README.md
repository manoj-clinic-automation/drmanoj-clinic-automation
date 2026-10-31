# S689_CLINIC_LISTS — the owner's X-ray & procedures page (D812)

*The parent, session 373, 01-Nov-2026. The owner's OK at 00:29 IST on mock-up v3 (https://claude.ai/artifact/EbXFK5Zeb4eUo5ok9wb9T6).*

## What it gives him

One page that only Dr Manoj can open: **Procedures** and **X-rays**, both starting 1-Oct-2026.
- **Layout:** grouped by day, newest first. Each day shows its counts (procedures by kind; X-ray films by size) and its rupee total. The month's tiles sit above.
- **Each row:** date, slip no., clinic ID, patient, procedure / X-ray, side, kind (or film size and films), paid (Cash / UPI / Free / Not marked paid), amount (with the discount shown when there is one).
- **Dates:** pick a month, or type a From–To range.
- **Search box:** finds a patient name, clinic ID, slip number, procedure or X-ray name. With no From–To typed it looks through everything since 1-Oct. Matches are highlighted.
- **Docterz only:** a charge in that day's Docterz report for a patient who has no slip line of that kind that day. Docterz names no procedure, so the line has no kind until the slip is written.
- **Excel:** downloads exactly what is on the screen.
- **Where it lives:** the tile **X-ray & procedures** in the **Patients** folder of his portal home.

## What it changes on the box

| file | from | to |
|---|---|---|
| `/root/finance/finance_app.py` | 2f604fee | one guarded mount block after S688's |
| `/root/finance/clinic_lists.py` | — (new) | the page |
| `/root/portal/portal.py` | 1a9b3a1b | one tile + its group line |

**Not changed:** `tile_grants.json`, because Dr Bhawna's "only" list already keeps the tile off her home. The staff X-ray list in the film log is not changed either. The database is not touched: the module has no INSERT, UPDATE, DELETE, CREATE or DROP, and walk check G1 proves every table's row count stays the same.

## Who reaches it

The paths start `/finance/slips/lists`, which is unit `slips`.
- **manoj:** the only login that gets in.
- **Every other slips login, the other doctor included:** 403.
- **No login:** turned away at the front gate.

## Rules decided while building (stated, not asked)

- **Slips not marked paid:** a line on an `ok` slip that the X-ray room has not marked paid is **listed, marked "Not marked paid"**, not hidden. That way no procedure that was done goes missing from his list. Void, cancelled and spoilt slips never show.
- **Rs 50 glucometer:** Docterz bills the ₹50 glucometer under X-ray (`clinic_money.HEAD_MOVES`). It is matched against a ₹50 procedure line of the same patient that day, so it does not show as a Docterz-only X-ray.
- **Kinds:**
  - Clavicle bandage is **Other** (the owner: not a cast or slab), even though the rate list groups it with casts.
  - Anything whose name starts with the word "ILI" is **ILI**, the knee included (not "Ilizarov…", not "iliac…").

## The gates

- **The walk:** **68 of 68 green** on a copy of the database. It covers:
  - who reaches what
  - every row rule (14 made-up lines, one with no name typed so the patient master's name is used; a name that only begins with "ili" such as Ilizarov is not ILI)
  - films matching the film log's own rule for every paid X-ray since 1-Oct
  - the search and the dates
  - the Excel
  - nothing written
  - October against an independent count of the real slips
  - every login's home under every role
  - the builder, which refuses a changed FROM file and its own output
  - **19 mutants, each caught**
- **The control on the live files:** `37 S689 check(s) red . 8 green`.
- **Made-up rows:** they use the days 10–12 Nov **2027**, clinic IDs `W689-nn` and slip numbers from 900001, all checked unused (F-1059).
- **Rehearsal** (`rehearse_s689.sh`, made-up root): DRY · install · ALREADY · a red at [8/9] restores all three files · a journal naming the module restores · a DOCTOR_AUTO_OFF someone else set is left in place · a lock and switch left by a killed run are cleared · a changed FROM refuses.
- **Cold review:** round 1 found two real faults, both fixed: "Ilizarov…" counted as ILI; the installer removing a DOCTOR_AUTO_OFF it had not set. Round 2: SAFE, with fixes taken anyway: a short search no longer lists Docterz-only rows by their placeholder words; "today" is IST whatever the box's zone; a lock or DOCTOR_AUTO_OFF left by a killed S689 run is cleared by the next run, a live run's lock is never taken over, an existing backup that is not the FROM bytes is never overwritten.
- **Cold review round 3:** SAFE. Its fixes were taken too: the 'ili' search check runs on the made-up days only (a real "Dilip" can no longer fail the install), a stale S689 switch is cleared on every exit once the lock is held, the ALREADY path leaves the switch alone while any lock exists and restarts both services after a stopped run, and a signal after the verified install no longer undoes it.
