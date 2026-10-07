# REPORT S494_AMIR_JOBS_NOTICE_FLAGS — installed 07-Oct-2026 12:33 IST, verified, published

**For the owner**
- **Reception is now told when Darpan's order sheet arrives.** The message used to fail on every phone. It now goes out at the next ten-minute check, the same day. Yesterday's sheet was too late to announce, so it was not sent.
- **Amir's page now carries his one-time Marg jobs.** They sit under "Ek baar ke kaam" on his Marg sudhar card. Today there are three: scan a bill from RAMA MEDICOSE, scan one from KUSHAGRA MEDICAL AGENCY, and enter Kedar's ₹310 cash payment. Each line goes when it is done. The four orthotic category lines will appear when he reaches his rename list.
- **Your list shows the spot-count line once**, not once for each day.
- **The stock flags fell from 81 to 10** at the newest closing (06-10). 178 flags across the last three closings were sales or purchase reports that reached the server after the closing. They now clear themselves.
- **What needs you:** type the bank details for **AGARWAL SURGICALS AND MEDICALS**. Its bill is already scanned. The line on your list goes once the details are saved.

---

## For the chat

Kit `deploy_kits/S494_AMIR_JOBS_NOTICE_FLAGS/` · D686 · F-765, F-767, F-771. Kit published as `ae650b7` (PUBLISH_ALL verified it on origin).
- **Build lock:** taken 12:32:54 IST by the installer itself, released after this report.
- **Installer run:** from `/tmp/s494kit/repo/` (a repository-shaped copy of the kit and the v9 map), 12:32:54 → exit 0 at 12:33:52 IST.
- **A DRY run came first** (12:28–12:31, green, nothing written).
- **After the publish:** `git pull` on the box, then `diff -r` of the clone's kit against the kit that ran shows no difference. SUMS.md5 is b4d7be7c on both, and the clone's `DUTY_MAP.json` is byte-equal to the one the walk read. Run from the repository, the installer answers **ALREADY INSTALLED**.

### Part A's cause, proved on the box first
- `/usr/bin/python3 -c "import pywebpush"` → `ModuleNotFoundError: No module named 'pywebpush'`
- `/root/wa/venv/bin/python3 -c "import pywebpush"` → imports (`/root/wa/venv/lib64/python3.9/site-packages/pywebpush/`)

This is the expected result, so Part A was built.

### Pins — FROM → TO, md5 read back on the box (12:33:52, and again 12:34:36 from the repository's run)

| file | FROM (brief = live before) | TO, read back |
|---|---|---|
| /root/finance/order_sheet.py (Part A) — **S486's parked file: re-pin S486 on this** | 16f21a6515a1317e1f6e31cb0a280513 | **012e21c92233d0eec4c828e15f7912e1** |
| /root/finance/stock_watch.py (Part B, one block, +5 lines) | 4fc0f6017825975e75ebacfdc2f122d2 | d78c902e0d3258fd0c615cd9715346b6 |
| /root/finance/shelf_figure.py (Part C) | 0d836de54672f3e624fcc763311ab22c | a1e87d1ff758e8f9a8206205a457b875 |
| /root/finance/amir_day.py (Part D) | 08d058a765278d6e119e70f8f0adeedd | 59b035da84a6648b94c1977d0c810b9d |
| claude_code_briefs/DUTY_MAP.json (v8 → v9) | f27423b61e50857875bb8f7ba4e5c57c | 2016244829b4c70c00f1c59b0250ee35 (the server's clone, read back) |
| claude_code_briefs/DUTY_MAP.md | cb78fe54f4d09fb4733dc1bac268cf9e | 7400e9ff2b047df82c81e897a06ea5ac (the server's clone, read back) |

**Read only, the same before and after, each at the brief's pin:**
- order_rules.py ee17c187, stock_app.py cc06dac9, purchase_app.py c29050c1, sanjeevni_approvals.py 792f4a9a
- spine/spine_read.py 712a1e4e, /root/portal/ring_common.py 4344b592, /root/assetapp/asset_register.py e774be89
- **Also unchanged (installer step 14):** finance_app.py, portal.py, tile_grants.json, aaj_kaam.py (e8517623, live as read: it has moved since S488's d65e0bf4, through S493/S495; walk §5 read these live bytes), aaj_kaam.html, aaj_duties.json, owner_console.py, packs.py, porders_s454.py, darpan_kal.py, and the crontab.

**Backups** (in /root/finance):
- `finance.db.bak_S494_20261007_123254`: 32,501,760 bytes, made with the backup API **before the empty table**, which was the first data write.
- `order_sheet.py.bak_S494_16f21a65`, `stock_watch.py.bak_S494_4fc0f601`, `shelf_figure.py.bak_S494_0d836de5`, `amir_day.py.bak_S494_08d058a7`. Each was read back at its FROM md5.

**Service:** `clinic-finance` was restarted once, at 12:33:41 IST.
- `/finance/healthz` answers 200.
- `/finance/amir`, `/finance/amir/step/6`, `/finance/approvals` and `/finance/porders` answer 302. That is the login gate, as expected.
- The journal has no Traceback since the restart. Its only `[ERROR]` lines are gunicorn's own "Worker … was sent SIGTERM!" at 12:33:41, the normal shutdown during the restart.

### The order of the install (the brief's 4.7)
The installer's order was: lock → DB backup → `CREATE TABLE IF NOT EXISTS amir_job` on the live database → gates, pins, build, compile on both pythons, and the walk on copies taken after that → place.
- I ran it from /tmp **before** publishing. So the v9 map reached the server's clone (at 12:34) only after the table existed (12:32:54), and **the "Not read just now" window never opened**.
- The installer's table statement and the code's `S494_DDL` are one statement, letter for letter (the walk checks this).

### The walk (`walk_s494.py`), as it ran inside the installer — 64 checks, GREEN

Its rows are keyed W494, and it ran on backup-API copies. Every Python it started carried `ORDER_PUSH_STUB` and a scratch `RING_PORTAL_DIR`, and so did the installer's own.

```
ok   the v9 map less S494's one duty reads back as the v8 map byte for byte (md5 f27423b6 = the brief's pin f27423b6)
ok   the installer's CREATE TABLE amir_job (step 3, before the gates) is the code's S494_DDL letter for letter
-- 1  the arrival notice (F-767)
ok   load_file with ORDER_PUSH_NONE (the web process): the W494 sheet's notice is pending and the stub is empty (0 payloads)
ok   control OLD (it ignores the switch): the stub holds one payload per login of order.notice_to at load (alisha, darpan, shavez, shivani)
ok   cron_pass (the tick, no switch): one payload per login carrying the stored text; pending false, sent filled, first_at kept; notices 1
ok   a second cron_pass sends nothing (0 payloads; notices 0)
ok   the real rows of an earlier day in the failed shape (the 06-Oct sheet) are marked lapsed at the first tick and never sent (1 row)
ok   W494 rows in the 06-Oct shape: taken now -> retried once; dated yesterday -> lapsed, not sent; taken 75 minutes ago (setting 60) -> lapsed, not sent
ok   a pending row whose first send fails on every phone becomes the failed shape and is tried once more at the next tick (retried, 4 payloads);
     the retried row is not sent again (0)
ok   order.source moved off marg_sheet -> dropped ('source'), not sent (0 payloads)
ok   without the switch, _sheet_notice sends at once as today (4 payloads)
ok   the setting row order.sheet_notice_max_min is seeded by order_sheet.ensure() itself with its note: 60
-- 2  one spot-count line (F-771)
ok   three W494 spot_missed notices on three days of the last week: Needs-you carries exactly one spot line, the newest
ok   control OLD gives three W494 spot lines (3; with the box's own two: 5)
ok   two trace_unexplained notices still make two lines
-- 3  the re-judge (F-765)
ok   before the sale reaches the spine nothing explains G1: record_gaps (NEW: re-judge first) leaves every W494 row as it was
ok   the window's sale added to the scratch spine after the flag: G1's first flag is cleared, its two copies with it ([0, 0, 0]);
     why: 'explained by a report that arrived later (first flagged 03-03 10:40; judged again 07-10 12:32)'
ok   control OLD: the three rows stay flagged after record_gaps is called again ([1, 1, 1])
ok   a second call writes nothing (rows 0, the table's checksum unchanged)
ok   the sale removed from the scratch spine again: nothing changes (cleared stays cleared)
ok   a later W494 closing recorded by record_gaps after the clear does not carry the flag (flagged 0; control OLD carries it: 1)
ok   a first flag nothing explains stays, byte-equal (G2); a carried flag whose origin lies before the window stays, its origin too (G3,
     explained by the spine and untouched); an unflagged row is never flagged (G4); an approximate row is untouched (G5, flagged and explained)
ok   with the spine absent nothing changes and nothing raises
ok   the re-judge ran on the copy of the live rows and only cleared (no closing gained a flag)
-- 4  his card (D686)
ok   stage None: the card shows the heading, the vendor block (each vendor with its newest bill's number and date) and the tap line, and not the category line
ok   stage A: the same
ok   control OLD: none of them (stage None, A and B)
ok   stage B (his rename list): 'In 2 item ki category Marg mein ORTHOTIC kijiye', 'W494 ORTHO ONE · W494 ORTHO TWO', 'Marg mein is category ka naam: ORTHOTICS'
ok   the hidden row (show_from NULL) is never on the card
ok   the owner's view of Amir's day says it in English: '... ; one-time Marg jobs: 5 open'
ok   the day closes exactly as before with jobs open: GATE_STEPS [2, 4, 5, 6]; the close POST NEW = OLD; step 7's list = OLD
ok   posted from step 4: 'Kar diya' on the tap line lands (303 -> /finance/amir/step/4); the line is gone, the row done by tap
ok   posted from step 5: 'Kar diya' on the category line lands (303 -> step 5); the line is gone, the rows said
ok   a category list received EARLIER the same day than his tap (11:00 < 12:00; as raw text it reads later) reopens nothing
ok   a W494 category list received later the SAME day that still shows another category: back on his card ('Is item ki category ...');
     the item absent from it stays said and the owner's line is there ("W494 ORTHO TWO is not on Marg's category list of 06-10 -- ...")
ok   one that shows the label: done, 'seen in Marg' -- a list whose export day is earlier than the day it was received is honoured (by md5)
ok   the owner's 'not done' line: absent at 9 days, one line at 11 ("Amir's one-time Marg jobs not done: 1 -- since 26-09 (11 days): W494 VENDOR B");
     the map's own owner line is not raised a second time (coded)
ok   posted from step 7: 'Scan ho gaya' lands (303 -> step 7); that vendor's line is gone, the other's head is singular;
     the owner's line: 'Bank details to type for W494 VENDOR A -- Amir says its bill is scanned'
ok   with a (non-numeric) account and IFSC on the copy the row is done, 'bank details on record', and the line is gone
ok   'Bill nahi mila' (posted from step 6): the line is gone and the owner's 'could not find' line is there
ok   a W494 scan link: done, 'scan linked', and the owner's 'its bill is scanned' line
ok   a job value for a row not shown, of the wrong kind, a made-up id, a non-number, a done row or a junk value changes nothing
ok   each tap left one audit row (who, 'job', the row's key)
ok   with no open job every step's page equals the OLD file's (steps equal: 1-7)
ok   _s494_jobs with the table broken ([]) and with it dropped: every step still renders (200 on all seven, both ways)
-- 5  the duty (DUTY_MAP v9)
ok   the duty as the brief writes it (id, person, tile, door, door_marker, allowed_days 10, coded, duty_hi, owner_line, due_sql letter for letter)
ok   due_sql on the copy: [0, None] on the empty table; two shown open of five W494 rows -> [2, '2031-01-05']; all said -> [0, None]
ok   control: with the v8 map the duty is absent
ok   the v9 map loads in aaj_kaam.load_defs ([None, 9, None]) and in owner_console's reader ([9, {'amir.marg_jobs': [0, None]}, 0]) without an error
ok   for every login but amir (darpan, shavez, alisha, shivani, reception, bhati, sukhveer, manoj) the list cut with v8 and with v9 is identical
-- 6  staff-eye (D648): amir, darpan, shavez, reception and the owner, signed in on scratch copies (a walk-only store and secret)
ok   NEW seeded, refreshed and re-judged on its own copy as the install and the first tick will; OLD the copy as it is
ok   the duty's due_sql after the seed and one refresh: [3, '2026-10-07']
ok   amir: signs in, 3 tiles; 10 pages compared; differences: /finance/amir and steps 1-7 (his card: the jobs)
ok      amir: 10 duties in the map, 3 due now -- each visible (tile on the home, marker on its door)
ok   darpan: 5 pages; differences: none · shavez: 5 pages; none · reception: 3 pages; none   [each with every due duty visible]
ok   manoj: 54 tiles; 13 pages; differences: /finance/amir/day (_s446_left's line), /finance/sanjeevni/api/needs-you
ok   Amir's home shows the tile and step 6 shows 'Ek baar ke kaam' while the duty is due (due 3)
WALK_S494 GREEN -- 64 checks
```
The log lines above are the walk's own, shortened where they repeat. The full log is at `/tmp/s494kit/install.log` on the box until /tmp is cleared.

**Each section's named control went red on the OLD files:**
- §1: OLD sends at load, whatever the switch says.
- §2: OLD shows three spot lines.
- §3: OLD keeps all three G1 rows flagged, and carries the flag into the next closing.
- §4: OLD shows none of the jobs.
- §5: the v8 map has no such duty.
- §6: compared NEW against OLD.

### The re-judge (Part C)

**Per closing, on the walk's copy of the live rows.** The window runs from 2026-09-29 (the newest closing less `stock.gap_rejudge_days` = 7).

| closing | first flags before → after | carried before → after | flagged before → after | cleared |
|---|---|---|---|---|
| 2026-10-02 | 0 → 0 | 0 → 0 | 0 → 0 | 0 |
| 2026-10-04 | 52 → 15 | 0 → 0 | 52 → **15** | 37 |
| 2026-10-05 | 55 → 0 | 22 → 7 | 77 → **7** | 70 |
| 2026-10-06 (newer than the brief's bundle) | 34 → 4 | 47 → 6 | 81 → **10** | 71 |

- **The late-keyed purchase count (counted only, mended nowhere):** 19 first flags remain with move > 0. For **15** of them, the spine holds a PURCHASE of the same item, dated within the seven days up to and including that flag's own prev, whose units equal the move within one pack. These look like bills keyed later than their date.
- **The first live tick, 12:40:02 IST**, did the same on the live database. Its log line: `{"slot": "none", "s454": {"sheets": 0, "notices": 0, "withdrawn": 0, "refresh": 0, "ties": 0, "marg_lines": 0, "gaps": 0}, ...}`. `notices` is new, and it is 0 because the 06-Oct row lapsed rather than being sent.
- **On the live database after that tick:** **178** rows have a `why` beginning "explained by a report that arrived later". The counts are 04-10 15 flagged (37 cleared), 05-10 7 (70), 06-10 10 (71), all "judged again 07-10 12:40". This is the walk's table exactly.
- **The 06-Oct order sheet (row 3) now reads `lapsed: true, pending: false`.** It was never sent.

### The data, as written (12:33)
- **The three settings:**

  | key | value | note | seeded by |
  |---|---|---|---|
  | `order.sheet_notice_max_min` | 60 | "Order sheet arrived: minutes after which the arrival notice is no longer sent" | `order_sheet.ensure()` itself (called once by the installer; every tick calls it too) |
  | `stock.gap_rejudge_days` | 7 | "Stock flags: days a first flag is judged again as later reports arrive" | the installer, INSERT OR IGNORE |
  | `amir.job_wait_days` | 10 | "Amir's one-time Marg jobs: days before your Needs-you list names them" | the installer, INSERT OR IGNORE |

  The notes are the brief's words, with no "S494:" prefix. The owner's settings card (`porders_s454.py`, parked by S486) lists only the keys it knows; these three rows join it when that file is next opened.
- **The eight jobs after the first refresh.** All eight were seeded and none was missing: every name was read on the box first. The four items are in `stock_item_section` (Orthotics), and the three vendors and Kedar are in `purchase_bill`.

  | key | shown | state |
  |---|---|---|
  | cat:BRACE TYLOR UNISON · cat:SKIN TRACTION HOPE · cat:TENNIS ELBOW L HOPE · cat:TENNIS ELBOW M HOPE | no (stage A today) | open |
  | vbill:AGARWAL SURGICALS AND MEDICALS | yes | **done — scan linked** (its bill of 07-Sep, linked 30-Sep) |
  | vbill:RAMA MEDICOSE · vbill:KUSHAGRA MEDICAL AGENCY | yes | open |
  | pay:KEDAR-JULY | yes | open |

- **The orthotic label read from the spine: `ORTHOTICS`**. It rests on 65 names: the Orthotics names less the four job items, all 65 "ORTHOTICS" in the 05-10 list (f62cc9e3). So Amir's category line will carry "Marg mein is category ka naam: ORTHOTICS".
  - Today BRACE TYLOR UNISON reads COMMON in that list. SKIN TRACTION HOPE and both TENNIS ELBOW items carry no category fact at all.
- **The map's `due_sql` on the live database: `(3, '2026-10-07')`**, as the brief expected. It was read once after the seed, and again from the clone's map at 12:34.
- **The owner's S494 line live now:** "Bank details to type for AGARWAL SURGICALS AND MEDICALS -- its bill is scanned" (warn, checks-marg). This was expected at install.

### Staff-eye differences, each named
- **Amir:** his card on `/finance/amir` and on steps 1–7 carries "Ek baar ke kaam" and today's three jobs. His Marg sudhar summary line on step 7 follows by itself.
  - His own `/finance/aaj` list did **not** change (see finding 1).
- **The owner:**
  - Needs-you gains the AGARWAL bank-details line.
  - The shelf-gap line falls from 81 items to 10.
  - The spot-count line is shown once. The box has two identical `spot_missed` notices this week (05-10 and 07-10), so the walk's NEW-only/OLD-only diff cannot show it. §2 proves it.
  - `/finance/amir/day` and the visit summary now end with "one-time Marg jobs: 3 open".
  - `/finance/console`'s page rendered equal on the copy, because it draws from its own reading snapshot. Its reader (`read_duties`) carries `amir.marg_jobs` under Amir, which the walk's §5 confirms. **Not verified live:** the console's next build is its own schedule.
- **Darpan:** the spot-count roster reads the shelf-gap flags at the newest closing, 81 → 10, so far fewer "flagged" reasons. `/finance/stockmatch` itself rendered equal, because its list is drawn by script.
- **Shavez, reception:** no difference.

### What I did NOT do, and why
- **Did not build or move:**
  - No ordering logic, no `order.source` write, no count page, no gate of Amir's day.
  - Nothing written into Marg, and no money row. Kedar's ₹310 entry is Amir's job in Marg, and the vendor sheet's own entry is the owner's.
- **Not opened:** none of the parent's files, and no line of `aaj_seed.py` / `aaj_kaam.py` (S493 is in flight on them).
- **The live re-judge** was left to the first tick, as the brief says. The installer only seeded the setting.

### Outside the brief — noticed, or decided on the way
1. **Amir's `/finance/aaj` list does not carry the new duty.**
   - Since S487/S493, each person's Aaj list is cut from his panel in `aaj_seed.py` (the clinic's file). That panel has no line for `amir.marg_jobs`, so the list is identical under v8 and v9.
   - The duty does have its door: his Marg sudhar card on every step, which is the brief's own door. But his Aaj line needs a seed line, owned by the clinic chat's S493 files.
   - **A finding for the clinic chat, not done here.**
2. **`first_at`:** for a retried row it keeps the earliest stamp (`first_at` if already there, else the old `at`). For the 06-Oct shape these are the same thing. For a pending row whose first send failed, it keeps the moment the notice was first written, rather than the failed send's moment. That is the "first" the field name promises.
3. **`Kar diya` on the category line** writes one audit row per category row it says (`ref` = that row's key). The other taps write one row each.
4. **The "not on Marg's category list" owner line follows 4.3's reopen rule.** It appears only once a list received after his tap shows the item absent, not for the list that was already the newest when he tapped. Today SKIN TRACTION HOPE and both TENNIS ELBOW items are absent from the 05-10 list. If he taps *Kar diya* and the next list still lacks them, you get that line for each.
5. **A sheet taken after the day's last tick (21:50) lapses unsent**, true to rule 2. So does any sheet the tick sees more than 60 minutes after it was taken.
6. **The installer has a `DRY=1` mode.** It runs every gate, the build and the whole walk on copies, with no lock, no backup and no live write; the table is made on the copy only. I used it once before the real run.
7. **Publishing.** PUBLISH_ALL was run as `cmd /c "<full path>\PUBLISH_ALL.bat < NUL"` so its closing `pause` returns at once. Its own gate ran clean: 9 staged files.
8. **S486 re-pins (its parked files):**
   - `order_sheet.py` 16f21a65 → **012e21c9**.
   - Also moved here: `stock_watch.py` 4fc0f601 → d78c902e, `shelf_figure.py` 0d836de5 → a1e87d1f, `amir_day.py` 08d058a7 → 59b035da. S486's re-read should take these.
