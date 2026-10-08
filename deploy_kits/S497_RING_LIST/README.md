# S497_RING_LIST — the after-call list (tile *Call ke baad*)

Session 302 (parent), 08-Oct-2026. D693 — the owner, 07-Oct-2026: *"what happens after they click the book appointment
button is nowhere visible to them … they get to see it as a list whose appointment was booked by whom at what time"*;
then *"tabular … updated from the Docterz exports confirming that these patient turned up, and persist for the no shows
distinctly"*; then *"full mobile numbers, weekdays in english, leave scope for whatsaap"*; then *"it is final"*.
**The specification is his final mock-up of 07-Oct; this kit follows it line for line.** Closes F-798, mends F-797.
Second build, 08-Oct: two reviews of the first build found two blocking faults and eleven smaller ones; all are mended
here and each is a check of the walk that is red on the first build (the walk's lines that begin `[B1 s1.py]` …).

## What it does

| who | where | what |
|---|---|---|
| alisha, shivani, shavez, reception | a tile **Call ke baad**, right after Call Tracker → `/portal/ring/list` | ONE table in three parts, Roman Hinglish, in the mock-up's words: ***Nahi aaye*** on top, set apart — shown whatever the span until the patient comes or a person presses **Phir call kiya — naya din** or **Ab nahi aayenge**; ***Aane baaki***; ***Aa gaye — Docterz ke export se pakka***, filled by itself. Spans *Aaj · 7 din · 30 din*. Full mobile numbers; English weekdays. |
| the same four | the card after **Appointment book ho gaya** | one OPTIONAL tap, *Kis din aayenge?* — Aaj · Kal · Parso · Aur din chuniye; the note stays and can be put right; a link *Aaj ki list dekho*. |
| the doctor | the same page | the staff's page exactly as they see it, with his own box on top (English): **the switch**, the two settings, up to which day Docterz visits are on the server. |

- **Installed switched OFF for staff.** Until the doctor presses *Turn it on for staff* on the page: no staff login is
  drawn the tile, the page says *Yeh list abhi band hai*, and their card after the tap is byte for byte the old card.
- **No old line meets the staff.** The list follows only appointments booked **on or after the day he first turns it
  on** (that India day is written once, `switch_on_day`; turning it off and on later never moves it). He may move that
  date **earlier** on his box, back to **01-Oct-2026 and no further**; emptied, it returns to the switch-on day. An
  appointment booked before the date is not shown, cannot be pressed, and its card is the old card.
- **Come or not, by itself.** A visit is a row of `patient_visit` in `/root/finance/finance.db`, opened **read-only**
  (`file:…?mode=ro`); no other table is read by the list and nothing is ever written there. The visit must be dated on
  or after the booking day (a visit on the booking day itself counts). A caller who was known is looked for by the
  clinic IDs the caller card showed, then by the same mobile's fingerprint; a number that was new, by the fingerprint —
  and it then carries the name and ID Docterz gave it. When the visit is another clinic ID's than the one filed (a
  family mobile) the page says whose: *Aaye · 06-Oct* / *Hari Lal · ID 6202 ki visit*.
- **No-show — only when Docterz can speak for that day.** A line is *Nahi aaye* only when (1) the day AFTER the
  promised day has come — with no day given, the booking day plus `wait_days` (3) have gone by — AND (2) the visits on
  the server are readable AND (3) they **reach that last day**. `patient_visit` keeps no record of *when* a row was
  brought in (`finance_patient_sync.py` writes no import time and keeps no log table), so "reach" is the newest visit
  date on file: `through >= last day`. Until then the line stays in *Aane baaki*, under every span, with no button
  and the words *Docterz se abhi pakka nahi hua*. If the finance database is absent, locked or unreadable **nobody**
  is *Nahi aaye*, the page has no button, and the amber line says so. A late arrival is still *come* (*Aaye · 06-Oct ·
  1 din baad*). Every day is worked in India time, whatever the server's clock is set to.
- **WhatsApp: room only.** A column, a place on the card, three empty fields in the store. Nothing is sent; no line of
  the program writes those fields.
- **Nothing is deleted.** *Ab nahi aayenge* marks the row; a new promised day keeps the old one in `appt_event`.

## Settings (table `kv` in `/root/portal/ring_outcomes.db`; the first three are on the doctor's box on the page)

| key | default | meaning |
|---|---|---|
| `list_on` | off | the list, its tile and the card's new part shown to staff |
| `wait_days` | `3` | a booking with no day waits this many days after the booking day before it is *Nahi aaye* (1–30) |
| `follow_from` | empty | his own first booking day. Empty = the switch-on day. Never before `2026-10-01` (refused). A Save that sends back the date the box was already showing pins nothing. |
| `switch_on_day` | — | written ONCE, the first time `list_on` becomes on (India date); never overwritten |

The first booking day in force = `follow_from` when he has set one (not before 01-Oct-2026); else `switch_on_day`;
else, while the list has never been on, today — so what he is shown before turning it on is what the staff would be
shown if he turned it on now. (The fix brief's "max(setting, switch-on day, 01-Oct)" and its "he may move it earlier
than the switch-on day" cannot both hold when his date is the earlier one; the second, his own choice, governs.)

## Files

| file | on the box | from → to |
|---|---|---|
| `ring_outcome.py` | `/root/portal/ring_outcome.py` | `495b0ada681cda359a1a621a22f4efa5` → `7cb60aad2df80f87fdc4a674ebe7ee45` |
| `portal.py` | `/root/portal/portal.py` | `63df9d49672e19e878245b30c0455bef` → `f8b059f61fa8b885f024f4f4ce73e4f2` |
| *(by `apply_s497.py`)* | `/root/portal/tile_grants.json` | `f9441311cd413bc4c12e9d4e23feb791` (v32) → `64f8b04937e8841c405cb9070b604aad` (v33) |
| `make_s497.py` | not placed | builds the two programs from the live bytes by anchored edits (each anchor exactly once), checks the result in memory, then writes; `--check` rebuilds and compares, writing nothing |
| `apply_s497.py` | not placed | the grants edit by exact text; pinned to v32; a file already v33 is left as it is |
| `walk_s497.py` | not placed | the walk the installer runs on the box before placing anything (0 checks, five more on a copy of the real ring store; `--control` is the same walk on the live files and must end RED) |
| `install_S497_RING_LIST.sh` | not placed | gates → pins → compile under both pythons → walk + control → backups → place → read-back → restart → health → restore on red; `DRY=1` places nothing |

**Touched:** the three files above, and the ring store `ring_outcomes.db` — it gains eleven columns on `outcome`
(`appt_day`, `appt_day_by`, `appt_day_at`, `appt_state`, `appt_state_by`, `appt_state_at`, `recalls`, `recall_at`,
`wa_state`, `wa_at`, `wa_ref`) and two small tables (`kv`, `appt_event`) the first time the new code runs. Nothing that
was there is changed; the old program reads the store as before (walked).
**Not touched:** `ring_common.py` (`4344b592`, read whole, held at its pin), `ring_hook.py`, `portal_push.py`,
`finance.db`, the tracker sheet, the tap itself (`file_outcome`), the mirror, the sweeper, the counts page.
**Restarts:** `ring-hook` and `clinic-portal` only.
**Backups:** `ring_outcome.py.bak_S497_495b0ada`, `portal.py.bak_S497_63df9d49`, `tile_grants.json.bak_S497_f9441311`,
and `ring_outcomes.db.bak_S497_<stamp>` (sqlite backup API), all in `/root/portal/`.

In `portal.py`: one tile entry, its section line, a small helper (`_s497_tile_on`) and one line in the tile filter
that keep the tile from being drawn for a staff login while the list is off. In `ring_outcome.py`: of the live file's 31 functions only `init_db`,
`render_page` and `install` change; everything else is added.

## Install (the VPS; one line)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S497_RING_LIST/install_S497_RING_LIST.sh

A dry run (every gate and the walk, nothing placed): the same line with `DRY=1 ` before `bash`.
Already installed → it says so and changes nothing. A live file that is not at its pin → refused, nothing placed.

## Undo

    cd /root/portal && \cp -p ring_outcome.py.bak_S497_495b0ada ring_outcome.py && \cp -p portal.py.bak_S497_63df9d49 portal.py && \cp -p tile_grants.json.bak_S497_f9441311 tile_grants.json && systemctl restart ring-hook clinic-portal && md5sum ring_outcome.py portal.py tile_grants.json

The three md5s must read `495b0ada…`, `63df9d49…`, `f9441311…`; `/portal/health` must answer 200. The added columns and
the two tables in `ring_outcomes.db` may stay — nothing reads them once the files are back. The store's own backup is
needed only if what the staff pressed must itself be taken back.

## The assistant's decisions where the mock-up was silent

1. **The card's new part is switched with the list.** While the list is off the staff's card after the tap is the old
   card; the day question appears with the tile. (His rule of 05-Oct: a new screen for staff is shown to him first.)
2. **The tile is hidden from staff while off**, not shown and refusing (a tile that only refuses is a trap, S223).
3. **No day given:** the booking day plus three FULL days are waited; the line turns on the fourth day after booking.
4. **Spans.** A line is under a span when it was booked or re-called within the span looking BACK, or its promised
   day falls from today up to as far AHEAD (*Aaj* = booked or re-called today, or due today — this is what the card's
   link opens). *Nahi aaye*, and a line whose day has gone by but cannot yet be judged, ignore the span.
5. **Phir call kiya — naya din** opens the card's own four choices (Aaj · Kal · Parso · Aur din chuniye); a day is
   required, today or later. **Ab nahi aayenge** asks once (*Ab nahi aayenge?*) and removes the line from all three
   parts — but if Docterz later shows the visit, the line is in *Aa gaye*: the export is the truth, not the button.
   There is no other undo. Both buttons are taken by the server **only for a line standing in *Nahi aaye* at that
   minute**; anything else is answered 409 with *Yeh line ab “Nahi aaye” mein nahi hai. List dobara dekhein.* and the
   page reloads — so a press sent twice is written once. A day given **from the card** to a line standing in *Nahi
   aaye* is written as the re-call it is (`recall_at`, `recalls`), so the line is in *Aane baaki* and not nowhere.
6. **A known caller** is matched by every clinic ID the caller card showed for that mobile, then by the mobile's
   fingerprint (a family member registered at that visit has a new ID). Wider than "by clinic ID" alone, on purpose:
   a false *Nahi aaye* sends staff to call someone who came.
7. **The doctor reads the staff's page as they read it** (Roman Hinglish, his own mock-up); only his box is English.
8. **Two settings and one fact on his box** beyond the switch: `wait_days`, `follow_from`, and the day up to which
   Docterz visits are on the server.
9. **Words not on the mock-up**, used only when something is off: *Yeh list abhi band hai. Dr sahab chalu karenge.* ·
   *Yeh list aapke login ke liye nahi hai.* · *Docterz ka record abhi padha nahi ja saka — kaun aa gaya, yeh abhi pakka
   nahi ho sakta. Thodi der mein dobara dekhein.* · *List abhi padhi nahi ja saki …* · *Yeh din nahi chalega — aaj ya
   aage ka din chuniye.* · *Yeh appointment nahi mila.* · *1 din ho gaya* (the mock-up shows only *N din ho gaye*) ·
   *Aur din · 12-Oct (Mon)* on the card once such a day is chosen · the tile's line *Appointment list · kaun aaya, kaun
   nahi* · an empty part shows one line with *—*. **Added 08-Oct, each for one fix:** *Docterz se abhi pakka nahi hua*
   (under the day of a line that cannot yet be judged) · *Is number se Docterz ki visit nahi mil sakti* (under a
   number that is no mobile — a landline, none, withheld — when there is no clinic ID either; that line only, the page
   is not blinded; once its days are gone it is *Nahi aaye* like any other, so a person can deal with it) · *… ki
   visit* (whose visit it was) · *Yeh line ab “Nahi aaye” mein nahi hai. List dobara dekhein.*
10. **The mock-up's two label lines** (*FINAL MOCK-UP (7 Oct) · …*) are not on the real screens.
11. **A date more than half a year away carries its year** (*pichhli visit 02-Sep-2024*), so an old visit is not read
    as this year's.
12. **Seen and mended in the same line as F-797:** the page's id is written so that an address carrying `</script>`
    cannot close the page's script early. The doctor's counts page now writes the day from its address as text.
13. **A login is shown as a name** under *Kisne book kiya*, on the card and in his box: the name filed with the row;
    else the name the call system holds for the login (`ring_agents.json` — the portal's own user store keeps no
    display name); else the login with its first letter made a capital.
14. **A tile masked for one login** (Manage Users) is not held by that login: no page, no press, no day question.
15. **On a phone (820 px and under)** the *Mareez* column stays at the left while the table slides sideways; the
    table itself is the mock-up's. On a wider screen nothing is different.
16. **The *Aur din* date box** sends only a whole date from today to a year ahead; a part-typed one is not sent.
17. **Left as they are, by decision (08-Oct):** the wider visit match of point 6; a visit on the booking day counts
    as *come*; no undo for *Ab nahi aayenge* beyond a later Docterz visit; the old card's own title and Devanagari
    button while the list is off (that page is the live page, byte for byte).

## To know

- **"Reaches that day" is the newest visit DATE on file**, because no import time is recorded. If an export is taken
  in the middle of a clinic day, a patient promised for that day who comes after the export can stand under *Nahi
  aaye* the next morning until the next export lands; the line then moves to *Aa gaye* by itself. On a day the
  clinic is shut no visit carries that date, so lines due that day are judged when the next working day's visits
  arrive. The doctor's box shows the day up to which visits are on the server.
- **On the first morning the staff's list holds only what is booked from that day on.** Earlier appointments are
  shown only if he moves the date back on his box (to 01-Oct-2026 at the earliest). The installer's last lines print
  how many lines that would be.
- **On a phone the table slides sideways inside each part** — it is drawn as the mock-up is (a wide table); the
  *Mareez* column stays in place.
- **No line was added to the duty map** (`DUTY_MAP.json` / `aaj_duties.json`) for *Nahi aaye*; that is not in this
  kit's brief.
