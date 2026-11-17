# S853_PATIENTS_PART2 — the Patients page, part 2 (D939 Part 2)

*The parent · S477 · 17-Nov-2026 · built from the live bytes of S851 (patients_page.py 595ce680, .html a2a8a17c) · mock-up v16.*

## What he gets — on `https://followup.dr-manoj.in/finance/console/patients`
1. **The same months a year before** — each month's 2025 twin beside this year's (patients, new, visits a day, consultation / X-ray / procedure rupees where Docterz holds them, planned reviews kept), and the usual ranges over 18 months.
2. **Before they reach you — Google** — searches, views, calls, directions, chats, website, all actions, beside the clinic's new patients and new patients per 10 direction requests; each month against the same month a year before (Google's own comparison).
3. **At the front desk — calls and WhatsApp** (the chosen month) — six tiles; calls with each caller counted once a day (first ring / rang again / called back / later day / never / no call-back); WhatsApp senders (answered / tried / nothing); when the phone rings; what answered calls were about (the AI's verdict); WhatsApp month by month from September.
4. **Google reviews** — reviewers, the low share, drafts made and shared, new reviewers since the last reading, asks per 100 patients; the complaint themes against other listings with where this page can look.
5. **The "Called" columns** — in Follow-ups you gave (called of the row's follow-ups; the tap opens them) and By diagnosis group (of the missed, called).
6. Readings at the head of each month: the never-reached callers, Google against the clinic door, the same month last year, planned reviews against 18 months, calling brings them back, reviews follow the asks.
7. Under Back after a gap: the late returns measured on the full record from January 2025, and how each review date was finally kept, by group.

## How it works
- `patients_part2.read2()` is called at the end of `patients_page.read()` inside a try; a fault leaves Part 1 whole and the block says "could not be read".
- Calls and WhatsApp are judged by the Call Console's own functions (`/root/portal/calls_console.py`, loaded read-only under another name). Stores are opened read-only: `/root/wa/console.db`, `/root/wa/wa_inbox/inbox.db`, `/root/portal/wa_awaiting.db`, `/root/portal/gmb_store.db`. Nothing is written anywhere but the page's own reading file.
- `patients_history.json` — counts only, worked out on manojz from the two Docterz exports (Jan-2025..Jun-2026) by S851's own `read()` rules; no patient in it.
- `patients_google.json` — Google's monthly mail figures (Jun–Oct 2026) and Google's year-on-year; a later month is added by the next session that reads the mail (until the server reads it by itself).

## Files
| file | pin |
|---|---|
| finance/patients_page.py | 595ce680 → (TO_PINS.md5) |
| finance/patients_page.html | a2a8a17c → (TO_PINS.md5) |
| finance/patients_part2.py | NEW |
| finance/patients_history.json | NEW |
| finance/patients_google.json | NEW |

## Proof
- `walk_s853.py` — made-up root (made-up patients, numbers 90000000xx, made-up call record, inbox, Review Assist store): **WALK 39/39**; control on the live files **2/39 red**; a mutation (later-day window 7 → 0) **34/39 red**.
- `walk_s851.py` (S851's own) on the new files: **34/34** — Part 1 unchanged.
- `shape_s853.py` on manojz's copy of the database (17-Nov 03:16): Part 1 the same in every block, history and Google read; on the box the installer runs it on copies of every live store and prints counts only.
- Cold review (a fresh reader): NOT SAFE on the first look — 3 MUST (a caller of the last 7 days counted "never"; a follow-up still open or not yet due counted "not called"; an ID with no number counted "not called"), 4 SHOULD (the chat rule worked out once per number, not once per month; each reading line guarded alone; a part month compared per open day; one bad review row costs only itself), LOW 8–13 — all built in, each with its own walk case. Second look: SAFE TO INSTALL; its 2 SHOULD (one percentage base for the calls table and the tile; a fault in one Part 2 card costs that card only) and LOW 3, 4, 6, 7 also built in.
- The page drawn for every month in a scripted harness on the made-up and the real reading: no error, no "undefined", every block drawn; the old page red on the same checks.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s853kit && cp -rp /root/deploy/repo/deploy_kits/S853_PATIENTS_PART2 /tmp/s853kit && bash /tmp/s853kit/install_S853_PATIENTS_PART2.sh
```
`DRY=1` before `bash` runs every gate and walk with nothing changed. `--undo` puts the two files back and sets the three new ones aside.
