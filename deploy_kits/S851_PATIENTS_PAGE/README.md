# S851_PATIENTS_PAGE — the Patients page on his console (D939 Part 1)

*The parent · S474 · 17-Nov-2026 · built from the newest bundle's live bytes (owner_console 9f4b284d) · mock-up v16.*

## What he gets
`https://followup.dr-manoj.in/finance/console/patients` — reached from the console's month section ("Patients — month by month …").

1. **At a glance** for the chosen month (month chips at the top; Jul 2026 onwards).
2. **Reading and suggestions** — fixed plain rules (who came, planned reviews, medicines not reviewed, groups, back after a gap, diagnosis typed, clinic money).
3. **Month by month** — patients, new / seen before, back within 30 days, clinic ₹.
4. **Follow-ups you gave** — within a week / planned review / medicines: kept, medicines only, late, still open, neither.
5. **By diagnosis group** — 8 main groups + other groups + no diagnosis typed.
6. **Back after a gap** — late returners by group.
7. **How much the diagnoses cover** + the diagnosis words still to place.
8. **Comes next** (Part 2 — calls and WhatsApp, Google, reviews, last year's history).

Every count taps open its list of patients (name, day, note) linking to the patient's record. Percentages only on a base of 20 or more. Rules are S433's (NEW = clinic ID above every earlier day's; diagnosis carried from the nearest written visit; kept = by due + 7 days).

## How it works
- `patients_page.py` reads the database into `/root/finance/patients_reading.dat` (private, 600) — rebuilt when older than an hour, or on the as-of chip's tap (not more than once a minute). It writes nothing to the database.
- `owner_console.py` gains: the three routes (via `patients_page.init`, inside a try — a fault there leaves the console as it was) and one line in the month section.
- Only the owner's login opens it (the console's own guard); others get a plain 403 page.

## Files
| file | pin |
|---|---|
| finance/owner_console.py | 9f4b284d → fe5e915c |
| finance/patients_page.py | NEW 595ce680 |
| finance/patients_page.html | NEW a2a8a17c |

## Proof
- `walk_s851.py` — made-up root (made-up patients 7001–7008, no real number): **WALK 34/34** on the new files; control on the live files **5/34 red**; a mutation (kept window +30 days) **31/34 red**.
- `shape_s851.py` — on a copy of the live database: every console section the same except the one new month line and the timing line; months Jul 2026 → this month; follow-up states add up; reading 0.1 s; file 600. **SHAPE OK 12/12.**
- Cold review (a fresh reader): no blocker; its 2 should-fix (a day's clinic money counted once per clinic ID and day, however many visit rows; the reading file private from its first byte) and 3 minor (a bad date skipped, not fatal; a lock released only by its owner; the live shape allows last month early in a month) built in. The real reading is unchanged by them.
- The page itself driven in a headless browser on the made-up and the real reading: no script errors, every section drawn, month switch, a tap opens its list.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s851kit && cp -rp /root/deploy/repo/deploy_kits/S851_PATIENTS_PAGE /tmp/s851kit && bash /tmp/s851kit/install_S851_PATIENTS_PAGE.sh
```
`DRY=1` before `bash` runs every gate and walk with nothing changed. `--undo` puts owner_console back and sets the two new files aside.
