# S717_GMB_WATCH — "What patients say — for our clinic" on the GMB page · the parent · session 389 · 06-Nov-2026

**For the owner, in two lines.** Below the drafts, the GMB Review Assist page now shows three things:
- our patients' complaints, as a percent of our reviewers, with the trend from one reading to the next;
- the complaints where other clinics' patients complain more often than ours;
- the words patients use elsewhere that ours don't.

It is read every two weeks, read-only, and you can add a listing to read.

## Why
D832 Part C. The owner said "build" at 11:05 IST on 06-Nov, on mock-up v3, which he had narrowed at 10:18–10:20 IST:
> *"The comparison shd be as percent of reviewers who complained"* · *"Don't chase others fake or real reviews, narrow down on what is useful for us only."*

The section therefore shows no other listing's stars or counts, and makes no judgement on any listing's reviews.

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/portal_gmb.py` | a4606e4c (S713) | 5bd5318f | Two new tables in the S713 store. **snapshot** holds one row per reading: our reviewers counted, each complaint as a percent of ours and of the other listings' reviewers, the words, the listings read and a note. **watch** holds the listings to read. Three new doors, all behind the doctor gate: `GET /portal/gmb/api/watch` (the latest and previous reading, and the listings), `POST /portal/gmb/api/snapshot` (a reading, checked field by field: counts, percents 0–100, names up to 60, words up to 30, a note up to 300, any 7-digit run → `[number]`) and `POST /portal/gmb/api/watch` (the owner adds a listing; 20 at most). A reading can hold **no review text, no reviewer and no star average**: the check keeps only the allowed fields and drops any other. A date must be a real day, not in the future; each complaint may appear once; a number too large is refused. S713's doors are unchanged; `KIT = "S717"`. |
| `/root/portal/gmb.html` | 964f0288 (S713) | 47d38f4f | The new section after the Staff SOP, as in mock-up v3: (1) our complaints, largest first, with ▲ up / ▼ down / same since the previous reading, and the summary line; (2) only the complaints where elsewhere is higher, any that appear elsewhere and not yet at ours first; (3) the words as chips; then *Read from:* and *Add a listing*. If the server does not answer, the section stays hidden and the page works as before. **The S707 engine is untouched** (561 lines identical), and so is S713's keeping. |
| the store | — | one reading | `seed_s717.txt` holds the 5-Nov reading, made from the S385 research on the owner's PC: ours 167 reviewers, the five listings 146, nine figures, 16 words and no review text. It is put in **once**, only when the store holds no reading yet, together with the five listings. Its note says plainly that it counted only the 1★ and 2★ reviews, and only the newest reviews of the other listings. |

## The reading every two weeks (the assistant's work, not the owner's)
Read-only, through the assistant's browser: our listing and each listing on the watch list. It is worked out **on the owner's PC** and never in the cloud workspace. Each complaint is counted as a percent of each side's reviewers, now in **every** review, not only 1★ and 2★. The words come from their good reviews that never occur in ours, with no doctor's name and no typo. The reading is then saved through `POST /portal/gmb/api/snapshot` behind the owner's login. No review text leaves the PC. The next reading is due **19 Nov 2026**; the board carries it.

## Proven (session 389, the cloud workspace; the live files = S713's kit, installed and verified 09:34 IST 06-Nov)
- `walk_s717.py` (the installer runs it on the server) — on a made-up store: **18 of 18 green**. It checks:
  - before any reading, nothing shows;
  - the seed goes in once, and a second time writes nothing;
  - the first reading reads back right;
  - the five listings are on the list;
  - a second reading becomes the latest, with the first as previous;
  - seven bad readings are refused;
  - a reading without the page's header is refused;
  - adding a listing works, twice adds nothing, a phone number becomes `[number]`, and 20 is the limit;
  - a reading holds only the allowed fields;
  - S713's keeping still works and health says S717;
  - every door sits behind the gate;
  - nothing is written outside the store;
  - the seed itself is a valid reading.

  **Control** on the live S713 module: **18 S717 check(s) red . 0 green**.
- `browser_walk_s717.js` — the page in Chromium at PC and phone width, served over http: **38 of 38 green**. It covers the date line, our five complaints in order with their percents, the summary line, the trend wording with one reading and with two (▲ red, ▼ green, same), only staff tone and bills under "stay ahead of", the 16 chips, the *Read from* line, no star average and no "fake", adding a listing, no sideways scroll, no script error, and the server down (section hidden, Generate still works). **Control:** the live page goes red at once.
- S713's own page walk on the new page: **32 of 32 green**. S707's: **BROWSER OK 162/162**.
- The installer rehearsed on a made-up server (see the close report).

## Cold review (independent agent, S389)
**SAFE TO INSTALL**, no blocker. Its points, all built:
- the reading's date is a real day, not in the future;
- a huge number is refused, not a server error;
- a complaint that falls to 0 stays on the list, showing the fall;
- the store's copy before the install is made with SQLite's own backup, not a file copy;
- a failed first reading on the ALREADY path is reported, not passed;
- each complaint may appear once in a reading;
- the README now says that unknown fields are dropped.

Its XSS probes (`<img onerror>`, `<svg onload>` as a complaint and as a word) ran nothing.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s717kit && cp -rp /root/deploy/repo/deploy_kits/S717_GMB_WATCH /tmp/s717kit && bash /tmp/s717kit/install_S717_GMB_WATCH.sh
```
## Undo
```
\cp -p /root/portal/portal_gmb.py.bak_S717 /root/portal/portal_gmb.py && \cp -p /root/portal/gmb.html.bak_S717 /root/portal/gmb.html && systemctl restart clinic-portal
```
