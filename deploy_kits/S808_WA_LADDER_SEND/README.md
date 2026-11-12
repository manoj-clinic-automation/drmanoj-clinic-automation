# S808_WA_LADDER_SEND — the sending from the WhatsApp messages page

**Session S442, 13-Nov-2026, the parent.** The owner's words: D940 ("proceed with the build for sending to real patients"), D946 ("Keep the templates as such and proceed"), D947 ("Timings ok" · "Ok" to a ceiling of 150, all five automatic messages built together, each with its own switch, every switch his). The spec is `S440_WA_SENDING_PLAN.md`; the page follows the mock-up v2. Build 3.1 — after three passes of a cold review by a second reader (three must-fix in all, each closed in code and walked; the third pass: SAFE TO INSTALL; see the end).

## What it does
- `/root/portal/wa_ladder.py` (cb197293 → the kit's): the page gains a switch for each of the five automatic messages, "Send a test to my phone" / "It arrived" for each of the six, tick boxes and "Send to the ticked names" for long overdue, "Stop all sending", and "What went today". It still holds **no send code** — one new door hands a list's key and row tokens to the sending file.
- **NEW** `/root/portal/wa_ladder_send.py`: the sending. It calls the portal's one sender (`portal_wa.send`), once a message, and writes everything down in `/root/portal/wa_ladder.db` (in the encrypted nightly since S806).
- **ONE cron line** (`# S808_WA_LADDER_SEND`, every 5 minutes at :01, :06 … — a minute after the STOP listener's own pass): the timed run. A list "at 6:00 pm" therefore starts at 6:01. With every switch OFF it does nothing. One timed run at a time (a lock taken inside the run).
- **Every switch is OFF at install. The installer sends nothing — not even a test.** The doctor turns the first switch on.

## The timings (D947)
follow-up tomorrow 6:00 pm the day before · after today's visit 9:00 pm · appointment reminder 6:00 pm the evening before · date passed yesterday 10:00 am · date passed 5 days ago 10:00 am · long overdue only the names he ticks, on his press (8 am – 9 pm, at most 60 at a time).

## The plan's thirteen rules — where each is walked (`walk_s808.py`, 68 checks)
1 OFF sends nothing: 01, 28, 29 · 2 the lists' own holds: 07, 16 · 3 the replies read first; a deaf or stale listener, or one whose Inbox reader did not run, holds everything; the stop list read again per row: 14, 15, 45, 46, 47, 48, 63, 67 · 4 one number a day, across pages: 16, 17, 18, 57 · 5 never twice for a date, across pages: 17, 19, 20, 21 · 6 written ahead, never retried: 09, 10, 11, 12, 53 · 7 the one sender, one request: 07, 38, 40 · 8 once a day, a 90-minute window, nothing starts after it: 07, 08, 23, 24, 52, 56, 62, 64 · 9 the ceiling of 150, every try counted: 25, 58 · 10 a confirmed test first, read again at sending: 02, 03, 04, 32, 50, 54 · 11 TEST mode, read again per row: 05, 51 · 12 everything on record: 35, 42, 68 · 13 ALL_OFF and Stop all: 06, 28, 29, 60.
Also: only the doctor's own login, and nothing a request adds is believed (34, 36, 61, 65) · nothing that comes back from outside is kept or shown (49, 66) · the ticked names (30–33, 55).

## Added to the plan, on the safe side (said to the owner in the build brief)
- **The reminders wait for the visit records.** A day's visits reach the server in the evening, sometimes later. A "date passed" reminder sent before they arrive would tell a patient who came that he did not. So a list waits inside its 90 minutes until visits of the last clinic day (Sunday skipped) are on record; if they are not, that day is skipped and the page says why (26, 27, 59). "After today's visit" waits for today's visits the same way.
- **A batch stops at a refusal that would repeat** (HTTP 401/403/429, a gateway error, no clear answer, the sender breaking) and after two refusals in a row — so one fault cannot use up every row's one try. The rest of that day's list is then not sent, and the page says so (10–13, 53).
- **The timed run is its own process (cron), not a door of the portal.** The plan preferred a localhost-only door; a door that sends with no login is the larger risk, and a long run would hold one of the portal's two workers. The run and the page read the portal's settings file by the portal's own rule (the file's value, else the environment), the file itself every time. The installer stops if a setting this kit reads sits in the environment instead of the file (the shell's, cron's bare one, or the portal service's own — and it stops if the service's process cannot be found to look at). **The rest of the portal reads the file once, at its start** — after an edit of the file this page follows it at once, the other pages after the portal restarts.

## Known and left (nothing is sent wrongly by the first three; the fourth and fifth can send a reminder that is wrong for that patient)
- The "morning notice" line of rule 9 (the ceiling reached): said on the page and in `/root/portal/wa_ladder_send.log`; no notice is sent anywhere else.
- A row the lists hold because an earlier list "has" the number gets nothing that day when that earlier list's switch is OFF.
- After a weekday holiday every dated list is skipped that morning (the records cannot reach "yesterday").
- **The visit check proves that visits of the last clinic day have arrived, not that ALL of them have.** If reception exports at midday and not again in the evening, an evening patient can still be told his date passed.
- A patient told today to come tomorrow is not on the 6 pm list (today's follow-up dates arrive after 9 pm); a patient who came today, a day early, may still be reminded at 6 pm.
- Not in this kit: leaving out patients who bought medicines meanwhile (D919); the Hindi call-back recording and the busy step (parked, D940); the helpline on the Google profile and the contact page (F-1287).

## Install (the owner's one line; his own mobile typed at the end)
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s808kit && cp -rp /root/deploy/repo/deploy_kits/S808_WA_LADDER_SEND /tmp/s808kit && bash /tmp/s808kit/install_S808_WA_LADDER_SEND.sh <his own 10-digit mobile>`

The number is kept in the store only — never in the repository, an output or a log. While the installer runs it is on its own command line, and it stays in root's shell history on the server. `DRY=1` runs every gate and writes nothing. `--undo` sets every switch OFF, waits for a timed run in flight, puts `wa_ladder.py` back, sets the sending file aside and takes the cron line out; the store keeps its record.

## The cold review (S442) and what builds 2 and 3 changed
**Pass 1, on build 1: NOT SAFE** — **M1** a deaf or stale STOP listener did not hold the sending (a number that had replied STOP could be messaged); **M2** the words of a gateway's refusal went into the store and onto the page (they could carry anything). **Pass 2, on build 2: NOT SAFE by one case** — **M1b** when the Inbox's own reader failed, the listener still looked healthy. Closed in code and walked: the replies are read before every batch; a deaf or stale listener (46–48), or one that notes its Inbox reader did not run (63, 67), holds the batch; only fixed sentences and the HTTP number are ever kept (49).

Also built from the two passes: a confirmed test is not undone by a later failed one (54) · TEST mode, the window and the ticked hours read again for every row (51, 52, 55) · a visit dated in the future does not count (59) · every try counts toward the ceiling (58); the count and the written-ahead row are one transaction (by reading — the walk cannot show a race) · the timed run's own lock (58) · a gateway error is "may have gone" (53, 57) · an ambiguous date in another page's row is read both ways (the self-test) · "Stop all" says when it could NOT stop (60); the page is told when the switches cannot be read and keeps the button (65 for the flag; the button was seen in the browser, not walked) · the true reason on a skipped day (23, 46, 63) · a late or repeated ON press (62, 64) · the installer — a dead run's lock cleared, a live one respected; the live files read again once the lock is held, and a good backup never written over; a run cut short after placing is finished by the next run (restart, the gates, the cron line); `--undo` as above; the settings' place checked.

**Pass 3, on build 3: SAFE TO INSTALL, no must-fix** (a fuzzer of 2,700 made-up worlds and about 21,000 requests found no wrong send). Build 3.1 adds its three optional points, and a fourth short look by the same reader followed: the Inbox reader's one silent failure — its log folder cannot be listed — is looked for before every batch (67); a row another run wrote first is held and on record (68); the installer puts everything back when a run cut short is finished by the next run and the gates then fail.

The installer's control line ("the live files, which cannot send: red 68 of 68") is an import failure by construction — the live files have no sending part.

## Files
`make_s808.py` (remakes `wa_ladder.py` from the live bytes; `parts/page.html` is the page) · `portal/wa_ladder.py` · `portal/wa_ladder_send.py` · `walk_s808.py` · `install_S808_WA_LADDER_SEND.sh` · `SUMS.md5` · `KIT_ID.txt`.
