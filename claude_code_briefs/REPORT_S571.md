# REPORT_S571 — S571_BATTERIES (built, walked, rehearsed; not installed, not published)

## Fix round 1 (S571_FIX1, 16-Oct-2026, 13:26–13:45 IST)

**For Dr Manoj (plain English):**
- Two fixes from the independent check, both in the Batteries part only. **Nothing on the server was changed.**
- While "Batteries for Shavez" is OFF, his sorting desk now shows **no battery question and no pre-ticked place**. Before this fix
  it showed them, and the button then failed.
- When Shavez looks at a battery's history, a paper he is not allowed to see (your Personal paper) now shows only as "a paper".
  It has **no amount and no link**. You still see everything.
- Every test is green again. The two new tests fail on the old kit, which shows they really check the fix.

**For the chat.**

*Read first (13:26–13:29 IST):* the brief `S571_FIX1.md`; `S571_BATTERIES.md` (md5 read `10a7d3c6…`, = the review's); the review
`S571_KIT_REVIEW_K1.md` — **md5 read `5b3a50bec327d53ea46859e7dfb3c651` = the brief's `5b3a50be…`** — CORRECTION 1 and NOTE 2 with their
lines; this report; the kit. The round-0 kit was kept byte-for-byte in `_scratch\S571_FIX1\round0\` (batteries `872a3ff3`, walk `459f6a2d`)
for the control.

*What changed (only `batteries.py`; `make_s571.py`, `install_s571.sh`, `rehearse_s571.sh` untouched; sorting_desk / asset_register at their TO pins):*
1. **CORRECTION 1** — `desk_offer`, right after `if not paper_visible(b, owner): return {}`: `if not owner and not switch_on(db): return {}`
   (the review's line; the same rule as `may_see`). A manager gets no `bat` at all — no offer, no `linked`, no `pre` — while `batteries.on`
   is absent or OFF.
2. **NOTE 2** — `page_place`: Cost from the bill only `elif bv and b["total_amount"] is not None` (bv = the desk's `_visible` via
   `paper_visible`); PLACE_TPL bill and card cells: `{% if h.bill_href %}<a …>{% elif h.bill %}{{h.bill}}{% elif h.awaited %}…` (card the
   same). A hidden paper: its words, no amount, no link (the `<a href="">` is gone).
   *Call:* the words stay "a paper you do not see", as the review gives the fix (the brief's "a paper" read as that line, not new wording).
   This keeps I7's existing assertion unchanged.
3. **Walk:** two new named checks rather than growing I6 (the brief allows "or a new check"). **I8** is the manager's desk JSON for a made-up
   B.L. paper and for the already-linked, unsorted Digital X-ray paper, with the switch absent, then "off", then "on". The owner's
   offers are read alongside each time. **I9** is the Generator (clinic place) fitted with a made-up Personal bill (₹7,350, no price
   typed, so Cost would come from the bill) and a Personal card. The manager's history is checked, then the owner's. `MUST_RED` gains I8
   and I9. New `--must-red I8,I9` with `--expect-red` passes only if those are red **and every other check is green**.

*Pins (FROM → TO), rebuilt on the box from the live bytes at 13:37:44 IST:*
| file | FROM (live, read) | TO (built = PIN_TO) |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `695ba90b4b3652f0e087f29b7c25d706` | `110335eac5a9792ebe52620ee676a13c` (unchanged from round 0) |
| `/root/assetapp/asset_register.py` | `e5356e0c75f564085b20a059f76a4b48` | `c39c084eabf52daa0da9cc6720fc7aa7` (unchanged from round 0) |
| `/root/assetapp/batteries.py` (new) | absent | **`9a0054ac073ccaa1252b426c5a9d408f`** (round 0 `872a3ff3…`) |
Read-only pins held: clinic_papers `6db07c12`, stationery `d11d7183`, asset_machine `7d4fdffc`, scanner_widget `10a8bb29`, claude_reader
`3894dc23`, claude_reread `d9b75e78`, packs.py `e46264b8`. Compiles on `/usr/bin/python3` and `/root/wa/venv/bin/python3`. Re-written:
`PIN_TO_batteries.txt`, `SUMS.md5` (29 files), `README.md` (a "Fix round 1" paragraph, pins, I1–I9), `KIT_ID.txt` (batteries `9a0054ac`),
`walk/walk_results_s571.txt` (this round's browser walks). Every other PIN file is unchanged; FROM and TO were re-checked on the box.

*The walk and its controls (box, backup-API copy of the database, made-up rows only; final kit bytes, 13:37:44–13:37:48 IST):*
- **`walk_s571.py` on the FIX1 files: 12 checks: 12 GREEN, 0 RED.** New counts:
  - `I8 counts: manager's desk, B.L. paper / the linked paper -- switch absent: bat False / False (offers 0, pre None); OFF: bat False /
    False (offers 0, pre None); ON: offers 3 (owner-only among them False), pre clinic_equipment; the owner's offers 4 each time (4/4/4),
    Home DVR among them True`
  - `I9 counts: … Personal bill (₹7,350) and card linked True; manager's history: amount shown False, stamps shown False, 'a paper'
    lines 2, links in the table 0; the owner's: amount True, stamps True, links 2`
- **Control on the live FROM files (`--expect-red`): 12 checks: 2 GREEN, 10 RED — "CONTROL must-be-red: W2, I1, I2, I3, I4, I5, I6, I7,
  I8, I9 -- all RED"**; W1, Z1 structural GREEN (as before).
- **Round-0 control: the FIX1 walk on the round-0 kit** (same sorting_desk / asset_register, batteries `872a3ff3`;
  `--expect-red --must-red I8,I9`): **12 checks: 10 GREEN, 2 RED (I8, I9) — "CONTROL must-be-red: I8, I9 -- all RED"; "CONTROL every
  other check GREEN: yes".** The round-0 counts:
  - I8: `switch absent: bat True / True (offers 3, pre clinic_equipment); OFF: bat True / True (offers 3, pre clinic_equipment)`. This is
    the review's fault, reproduced.
  - I9: `manager's history: amount shown True … links in the table 2`.

*The earlier walks (the rehearsal's outcome 1, final kit bytes, 13:37:48–13:41:35 IST):* S568 **14/14** · S566 **12/12** · S563 **17/17** +
its tidy fetch (102 answers each side, **none differing**) · S560 **37/37** + pack **9/9** · S548 **8/8** · S559 **43/43** · S557 **41/41** · S555
**19/19** · S551 **87/87**. Same adapted lines as round 0, nothing new.

*Browser walks (the PC's headless Chrome, 13:31:46–13:32:04 IST; pages rendered on the box from the FIX1 build, made-up rows):* Batteries
**3/3** (its control: **B1 RED**, as it must be) · S560 desk layout **7/7** · S568 staff screen **2/2**. Recorded in `walk/walk_results_s571.txt`.

*Rehearsal:* **`REHEARSAL GREEN`** (13:37:48–13:41:35 IST). All 10 outcomes as round 0: 1 green (+15 places, three tables, two indexes,
`batteries.since`, no other row changed) · 2 ALREADY INSTALLED · 3–6 restored · 7–10 REFUSED.
**A first attempt (13:33:04–13:36:44) gave every outcome as above but ended `REHEARSAL RED: the live finance folder's program files
changed during the rehearsal`.** The cause, read on the box: the hourly cron job `freshness.py --shout` (S525_FRESH_HOURLY, minute 35)
rewrote `/root/finance/freshness.html` at 13:35:01. That is a generated page, but the end guard counts every `*.html` there. Nothing
of this kit touched it. The rehearsal was re-run unchanged, between two :35 runs, and was GREEN. Both logs were kept in `_scratch\S571_FIX1\`.

*Box scratch cleared (13:42:16 IST):* `/tmp/s571dev` (2.6M), `/tmp/s571dev2` (3.4M), `/tmp/s571fin1`, `/tmp/s571reh`, `/tmp/s571probe1.sh`
and this run's `/tmp/s571fix1` were all removed — **0 `/tmp/s571*` left**. These held the database copies with made-up rows. The removal
was a script on the box limited to `/tmp/s571*` paths whose parent is `/tmp`. Lock and live files were read after: no build lock; sorting_desk
`695ba90b`, asset_register `e5356e0c`, no `batteries.py`, assetapp active.

*Cost (read from the runner's own logs):* round 0 **$11.51** (`S571_BATTERIES_20261016_1221.log`, "12:55:29 DONE · cost $11.51"). This
run's cost is not in its log yet. `S571_FIX1_20261016_1326.log` started 13:26:50 and the runner writes the DONE / cost line when the run
ends, so the total is $11.51 + that line.

*Not done / outside the brief (named, not touched):*
- **Not installed, not published.** No live file placed, no service restarted, no live row written, no build lock taken. (The lock was
  free throughout. The rehearsal uses its own made-up lock path.)
- The rehearsal's end guard (`rehearse_s571.sh:196`, `*.py *.html` in `/root/finance`) trips on `freshness.html` whenever a run crosses
  minute 35. The installer has no such guard. A later kit (or S571 at install time) could leave `freshness.html` out of that guard. It
  was not changed here, because the brief limits the change to `batteries.py`.
- The review's other notes stand as it judged them (N1, N3, N4, N6, N7, N8: no change). **N5** (install:267 wording "until he switches"
  → "until you switch") was not applied because it is outside this brief's two items. N9 (box scratch) is done above.

**Gates (FIX1, run last on the PC, 13:43 IST; re-run after this line was written, same words)** were run over 33 files: the 30 kit
files, this report, `S571_FIX1.md` and `S571_BATTERIES.md`.
- `.gitignore` (last match wins): `git check-ignore -v --no-index --stdin` (GitHub Desktop's git) found **none ignored** (exit 1).
  There is no nested `.gitignore` and no `__pycache__` / `.pyc` in the kit.
- Contact-number gate: `NO_PHONE_NUMBERS.py --files-from` (a copy in `_scratch\S571_FIX1`, md5 = the repository's) printed
  **`NO_PHONE_NUMBERS: clean -- 33 staged file(s) checked (numbers and credentials).`**
- `SUMS.md5`: 29 of 29 OK on the box (`/tmp/s571fix1/kit`, the bytes that walked and rehearsed) and on the PC.

**nothing installed, nothing published.**

---

# Round 0 (12:21–12:55 IST) — as first written

**For Dr Manoj (plain English):**
- The Batteries kit is built, tested and ready in `deploy_kits\S571_BATTERIES\`. **Nothing on the server was changed.**
- When installed, the scan app's menu gets **Batteries** after Machines: your 15 battery places in four groups (online UPS, small UPS,
  generator and inverters, vehicles), each with the battery now, its warranty, a status, **New battery fitted**, and its full history.
- B.L. Computers batteries show **"bill awaited"** until the bill is linked; when their bill reaches the sorting desk it asks
  "Battery fitted at <place> on <date> — this bill?" and one tap links it. The paper itself is never moved or changed.
- Jasoria batteries keep the price, the old-battery money and the net; you type the warranty months from the card.
- Reminders (warranty ending, battery due, a late B.L. bill, inverter water / UPS check / generator start) appear as one **Batteries**
  card on Renewals. Home and vehicle batteries are yours only; Shavez sees nothing until you switch **"Batteries for Shavez"** ON.
- Every test is green, and every new test goes red on today's files, as it must.

---

## For the chat

**Read first (12:21–12:35 IST):** the brief (v2) whole, `S571_BRIEF_R1.md` whole (md5 read `9fe1793bf1f0309395b13819ab323fd5` = the
brief's `9fe1793b…`), the proposal v2, both mock-up artboards (`battery_mockup\Main.dc.html`, `Fitted.dc.html` — the local copies; the
claude.ai artifact was not opened, the copies carry it), REPORT_S568 (with its fix round), S568's README / installer / rehearsal / patcher /
walk harness, S568 K2, BUILD_NORM_v1, and the live code the build touches (renewals(), d664's warranty card, `_s559_items`, the S568 mount,
the desk's SWITCHES / switch_states / paper_json / script, `_supplier_key`, `_s563_who_sees`, `_visible`).

### The FROM pins as read (12:21:46 IST, srv1746119 — S568 is installed; C10's two-step chain was not needed)
| file | live | brief |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `695ba90b4b3652f0e087f29b7c25d706` | same |
| `/root/assetapp/asset_register.py` | `e5356e0c75f564085b20a059f76a4b48` | same |
| `/root/assetapp/clinic_papers.py` | `6db07c12a8ba5ab0123db2a5bee0fa7b` | same (read only — not edited) |
| `/root/assetapp/batteries.py` | absent | new |
| read only: `stationery.py d11d7183` · `asset_machine.py 7d4fdffc` · `scanner_widget.js 10a8bb29` · `claude_reader.py 3894dc23` · `claude_reread.py d9b75e78` · `/root/finance/packs.py e46264b8` | all as pinned | same |
Read again at 12:54:04 IST after every run: unchanged, `batteries.py` absent, the build lock free.

### The counted edits (`make_s571.py`, each anchor exactly once on the live bytes)
- **sorting_desk.py — 9:** SD1 the mark `BATTERY = "S571"` · SD2 `("batteries.on", "Batteries for Shavez")` appended to SWITCHES (R1 C2) ·
  SD3 its key in `switch_states()` · SD4 `**_s571_paper(db, b, owner)` in paper_json's tail (R1 note 12) · SD5 the offer's box under the
  stationery panel · SD6 `s571init(j)` when a paper opens (the payer's pre-select, browser only) · SD7 `s571paint(j)` · SD8 the script's
  S571 part (the offer, "Yes — link it" = its own POST to `/batteries/link`, never the desk's Save) · SD9 `_s571_bt` / `_s571_paper`.
- **asset_register.py — 4:** AR1 renewals(): `s571b = s571_battery_card(show_all)` behind `is defined`, counted in "Nothing due" (R1 B1) ·
  AR2 `{{ s571b }}` next to `{{ d664w }}` · AR3 the menu: Batteries right after Machines (R1 note 11) · AR4 the mark `BATTERY_S571` and the
  guarded `import batteries; batteries.init(...)` after the S568 block.
- **clinic_papers.py — 0** (no Renewals or month wiring needed it). **New `batteries.py`** (the kit's own file).

### The TO pins (rebuilt on the box from the live bytes; = the kit's PIN_TO files)
| file | TO |
|---|---|
| `sorting_desk.py` | `110335eac5a9792ebe52620ee676a13c` |
| `asset_register.py` | `c39c084eabf52daa0da9cc6720fc7aa7` |
| `batteries.py` (new) | `872a3ff32b03e4fa323d0f751c82af42` |
All three compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.

### The walk and the control (box, backup-API copies of the database, made-up rows only; final bytes in the rehearsal 12:50 IST)
**`walk_s571.py` on the TO files: 10 checks: 10 GREEN, 0 RED.** Counts printed (the final run's):
- **W1** the app imports from the scratch folder on the copy · **W2** the S571 marks, batteries.py mounted, every earlier mark kept.
- **Z1 (structural)** new objects exactly `battery_fit, battery_fit_place, battery_place, battery_place_asset, battery_upkeep`; every old
  table's row count kept; settings added only `batteries.since`; every old setting kept.
- **I1 (item 1)** page 200; 15 "New battery fitted"; the four totals and four groups with their notes; menu `… Stationery . Machines .
  Batteries . Renewals …`; a place's history 200 with the re-order line; "+ Add a battery place" → 302, small UPS, B.L. Computers, warranty 12;
  "16 Battery places" after it.
- **I2 (item 2)** 15 seeded places, none wrong (group, payer, supplier first word, warranty, life, owner-only); DTH lab shown "paid by: to
  confirm"; a second ensure 15 → 15; `batteries.since` kept; upkeep inverter (water, 3), UPS (backup, 3), generator (start, 1), car none.
- **I3 (item 3)** B.L. form (warranty 12, "bill awaited"); fitted → "Bill awaited 0 days"; a made-up "B.L. Computers WALK571" paper on the
  desk: exactly one offer "Battery fitted at Digital X-ray on 15-06-2031 — this bill?"; linked (200, "The paper itself is unchanged"); bill
  id + created_at stored; badge then OK; the desk then says "Linked …" and pre-selects `clinic_equipment`. Jasoria (Wagon R): price
  ₹5,000, old ₹800 → **net ₹4,200** shown, warranty 24 typed → till 10-06-2030, bill and card linked; a second fitting → 2 fittings, the
  first removed 15-06-2031, "36 months", "— in use"; a future date refused.
- **I7 (D664)** the linked paper's lane clinic → clinic, section None → None, status draft → draft, **whole row unchanged**; picker owner 3 /
  manager 2 — Personal: owner yes, manager no; pharmacy, patient and older-than-90-days: never; a manager linking a Personal paper 400, the
  owner 200; the manager's history shows it as "a paper you do not see".
- **I4 (item 4)** badges "Warranty ends in 20 days" / "Due for replacement" / "Bill awaited 45 days" / "Water top-up due"; due-soon
  reminders 14, all upcoming 25; the four kinds present on Renewals' Batteries card; totals due 1, warranty 1, awaited 3; "done" → OK, next
  15-09-2031, its reminder gone; `expiries` row count unchanged.
- **I5 (item 5)** manager (switch absent) 403, made 0; then: the online UPS 1 place (Online UPS, B.L., payer clinic), the stabilizer 0, the
  machine from before the install 0, the car 1 (Vehicles, yours only), the hidden inverter 1 (yours only); a second load made none.
- **I6 (item 6)** manager, switch absent: page 403, a place 403, no Renewals card, no menu item; the owner's Switches card has "Batteries
  for Shavez"; switched ON (302, on); manager then: page 200 with the clinic and lab places only (no vehicle / home name), menu Batteries
  after Machines, Renewals card without owner-only places; owner-only place / its fit / its upkeep / a link to it: 403 each; desk offers for
  a Jasoria paper: owner 3 (Carnival among them), manager 1; a manager's added place is never owner-only nor "owner" payer; his edit 403;
  reception 403 / 403 / 403.

**Negative control on the live FROM files (`--expect-red`): 10 checks: 2 GREEN, 8 RED — "CONTROL must-be-red: W2, I1, I2, I3, I4, I5, I6,
I7 -- all RED"; structural W1 GREEN, Z1 GREEN** (R1 note 15's allowance: named, green on both).

### The earlier walks (rehearsal outcome 1, on the final TO files, scratch copy, 12:50–12:53 IST)
S568 **14/14** · S566 **12/12** · S563 **17/17** + its tidy fetch (102 answers each side, **none differing**) · S560 **37/37** · S560 pack
**9/9** · S548 **8/8** · S559 **43/43** · S557 **41/41** · S555 **19/19** · S551 **87/87**. Lines adapted only in `/tmp` copies, all
inherited, nothing new: S563 F4 and S559 O3/O4 in S566's form, S560 K2 and S559 J1/J3 in S563's form, S560 pack P2/P8 in S568's form, S551's
three lines (S559). **One call, no line edit:** S568's walk I8 compares the bundles before / after S568's pack fix; now that S568 is live,
`/root/finance/packs.py` is the *after*. The installer gives S568's walk a scratch `--fin` folder holding the four Sanjeevni readers and
`packs.py.bak_S568_048d2ad8` as its *before* (pinned `048d2ad8`), and the live `packs.py` as its *after* — exactly the pair it was proven on.

### The browser walks (the PC's headless Chrome, 12:48:17–12:48:43 IST; pages rendered on the box from the final build, made-up rows)
- **New `walk/browser_batteries_s571.py`: 3 browser checks: 3 GREEN** — B1 the owner's page at 1366 × 768 (viewport 1342 × 669) and 1366 ×
  620: the four totals on the first screen, every group's heading reachable and every row's "New battery fitted" inside the width (4 / 6 /
  4 / 6 rows), "+ Add a battery place" reachable, nothing wider than the screen; B2 the manager's page (4 / 5 / 2 / 0 rows); B3 both forms,
  every field and Save on one screen. **Its control** (a made-up broken layout): **B1 RED**, as it must be. (A first form layout had Save
  below the fold at 1366 × 768; the form was made two-column, as the mock-up's paired fields, and re-walked — the final bytes are the
  two-column ones.)
- **S560's desk-layout walk** (one line in S568's form: 16 buttons — S571 adds no destination): **7/7 GREEN**.
- **S568's staff-screen walk** (Stationery diya, 390 × 844, unchanged): **2/2 GREEN**.
All three results are in the kit's `walk/walk_results_s571.txt`.

### The rehearsal (made-up root `/tmp/s571reh/root`, 12:50:09–12:53:55 IST on the final kit bytes) — `REHEARSAL GREEN`
1 fresh install green (backups; the database backed up before the data step; the data step twice, 15 → 15; grown by exactly three
tables, two indexes, 15 seeded places and `batteries.since`, **no other row changed**; read-only files and packs.py untouched; nothing in
the finance folder backed up; the lock released) · 2 ALREADY INSTALLED · 3 forced red → every file restored, batteries.py removed · 4 `/desk`
404 → restored · 5 `/desk` 200 → restored (302 only) · 6 `/batteries` 404 → restored · 7 a moved live file → REFUSED · 8 a moved read-only
file (stationery.py) → REFUSED · 9 a foreign batteries.py → REFUSED · 10 a moved packs.py → REFUSED. The end guard is K2's: program files
only, `(cd "$LIVE_FIN" && md5sum -- *.py *.html 2>/dev/null) | md5sum`, and the same over the live scan app's `*.py *.js` — unchanged.
An earlier full rehearsal on the first kit (batteries `4b27e05f`, 12:40–12:44 IST) was also GREEN with the same counts.

### Kit identity
`deploy_kits\S571_BATTERIES\` (30 files: 29 + `SUMS.md5`). The same 29 files were sent to `/tmp/s571fin1/kit` on the box,
`md5sum -c SUMS.md5` **29 of 29 OK**, and the final rehearsal ran from there; the repository copy re-checked against SUMS on the PC: none
differing. Installer `install_s571.sh`, rehearsal `rehearse_s571.sh`; undo line in the README (moves `batteries.py` to `.off_S571`, as S568's).

### Calls made where the brief left room (with reasons)
- **"Bill awaited" is a B.L. state** (the badge, the "B.L. bill awaited" total — the mock-up's word, R1 note 17 — and the 30-day reminder):
  the brief gives it to B.L. places, whose bill comes late. A Jasoria battery left without its bill shows "none linked" in its history; the
  desk still offers it to a Jasoria paper ("or leave it awaited").
- **Upkeep counts from the later of: the last "done", the battery fitted now, the day the place was made.** So on install day nothing is due;
  generator start falls due after 1 month and UPS / inverter checks after 3, even before a battery is entered — say if he wants upkeep only
  for places with a battery recorded.
- **Usual life:** "Due for replacement" when reached; on Renewals it turns amber 30 days before (the proposal: "plan a replacement before it fails").
- **A manager may add a place** (clinic / lab: never owner-only, never "owner" payer); changing a place, linking a machine and taking a place
  off the list are the owner's only. A place is never deleted (taken off the list, history kept).
- **Cost in the history** = price − old battery when typed, else the linked bill's amount.
- **The auto-made machine place for a vehicle** takes its payer from the machine's entity per R1 C5 (Personal → "to confirm"), not "owner".
- **The undo moves batteries.py aside** (`.off_S571`), the brief's "removes it" in S568's form.
- **No build lock taken:** this run installs nothing; the rehearsal uses a made-up lock path. The real lock was free throughout.
- **DUTY_MAP not changed:** no staff duty is created at install (Shavez's switch is OFF; reception never sees it). **Finding:** once the
  owner turns "Batteries for Shavez" ON, upkeep "done" taps (inverter water, UPS check) could become Shavez's duty — if wanted, a later kit
  adds it to DUTY_MAP with its `due_sql` and door (the Batteries page / Renewals card).

### Not done, and why
- **Not installed, not published** (the brief overrides CLAUDE.md for this run). No live file placed, no service restarted, no live row written.
- **Cost:** the runner's own log `D:\Downloads\_kbtools\agent_build\logs\S571_BATTERIES_20261016_1221.log` was empty (0 bytes) when this
  report was written; the runner writes its cost line there when the run ends — read it there.
- The owner's claude.ai artifact itself was not opened; its local copies in `battery_mockup\` were followed.

### Seen outside the brief (not touched)
- R1 note 14: computed-when-read battery reminders do not reach the home dashboard's due list or `/api/due` (the WhatsApp digest).
- S569 and S570 kits are in `deploy_kits\` (another chat's builds this morning); the S570 runner log ended 12:13:57, before this run.
- Box scratch left: `/tmp/s571dev`, `/tmp/s571dev2`, `/tmp/s571fin1` (kit copies, built files, made-up-row walk copies of the database) and
  `/tmp/s571reh` (emptied by the rehearsal) — the permission list refused a remote `rm -rf`, so they were not removed; safe to delete.

### Gates (run last, finished 12:55:08 IST on the PC clock), over 32 files — the 30 kit files, this report and the brief
- `.gitignore` (last match wins): `git check-ignore -v --no-index` (GitHub Desktop's git) — **none ignored** (exit 1); no nested
  `.gitignore`, no `__pycache__` / `.pyc` in the kit.
- Contact-number gate (`NO_PHONE_NUMBERS.py --files-from`, run from a copy in `_scratch\S571_BATTERIES`, the default store as before):
  **`NO_PHONE_NUMBERS: clean -- 32 staged file(s) checked (numbers and credentials).`**
- `SUMS.md5`: 29 of 29 on the box and on the PC. (This report's gate line was added after the gate ran; the gate's words are unchanged.)

**nothing installed, nothing published.**
