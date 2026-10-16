# S571_BATTERIES — brief for the build runner (Agent SDK, the API credits)

*Written 16-Oct-2026 by the Scan App project (session 318). Kit **S571** claimed on the board `_numbers` (v454 → v455)
with its PLANNED line (D646). The owner's word, 11:57 IST 16-Oct: "AND THE BATTERY ONE ?". His rulings are **D730** (1).
Run by `D:\Downloads\_kbtools\agent_build\run_build.py S571_BATTERIES`.*

**v2 — READ `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S571_BRIEF_R1.md` (md5 `9fe1793b…`, 1 BLOCKER · 9
CORRECTION · 8 NOTE) WHOLE BEFORE BUILDING. Its replacement wording is binding and REPLACES the text below where they
differ.** In short:
- **B1** battery reminders are computed when read and shown as one **"Batteries"** card on Renewals, as the papers page
  does for personal-expense warranties (not rows in the reminders table);
- **C2** the `batteries.on` switch sits where S568's switch does;
- **C3** F-185 here means no phone, registration, serial or account number — the months are allowed;
- **C4** suppliers match on the first word (Jasoria, B.L.);
- **C5** an automatic place comes from a machine's name (UPS / inverter), plus the Vehicle category, and only for
  machines added after the install;
- **C6** the payer pre-selects the desk choice in the browser only, writing nothing until the desk's Save;
- **C7** the paper picker follows the desk's visibility rules, and owner-only places are refused on the server;
- **C8** warranty months are typed from the card (no new reading);
- **C9** every seeded place's payer is as the review lists;
- **C10** if the server is not yet at S568, the FROM files are built from the nightly bundle by the two-step chain.

The review's NOTES bind as guidance (mounting as S568 did, the desk offer's place, battery "bill awaited" kept out of
Bills awaited, the control's structural allowance).

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** The kit goes in
`deploy_kits\S571_BATTERIES\` and the report in `claude_code_briefs\REPORT_S571.md`; then stop. Nothing live is placed
or restarted, and no live row is written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 0 · Sources — binding
- **The proposal:** `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S318_BATTERY_PROPOSAL.md` (v2).
- **The owner's mock-up:** artifact `https://claude.ai/artifact/HxgXR7jN6PHFvsgkXghKxR`, artboards `Main.dc.html` (the
  list) and `Fitted.dc.html` (New battery fitted). The build follows it.
  - Its files are also at `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\battery_mockup\` (copied there by the chat).
  - If you cannot open it, follow §2 below, which carries its content.
- **His words, 07:54–08:51 IST 16-Oct:**
  - The battery places are 3 cars (**Carnival, Wagon R, Vento**), a scooty, a bike, the generator, 2 inverters (clinic,
    home) with **2 batteries each**, 3 online UPS (**digital X-ray, NK Pathology, DTH lab**), the small UPS of 2 PCs, 1–2
    small UPS for the lab analysers, and one for the home DVR and router.
  - **Reception's flow is not touched.**
  - **UPS batteries come from B.L. Computers**, with a 1-year warranty; their bill will come **with** the battery (or
    late, as a fallback).
  - **Other batteries come from Jasoria**, with a bill and a **warranty card** with the battery, and they pay for the
    **old battery**.
  - New vehicles and UPS can be added by hand, and **a new asset adds its battery place by itself** if that is not in
    the flow.

## 1 · Read first
- The S568 brief and its R1, `REPORT_S568.md` (with its fix round), and the S566, S563, S560 and S557 briefs and reports.
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`. Every rule and NEVER of those still binds.
- **Copy `deploy_kits\S568_STATIONERY_STOCK\`'s kit shape exactly.** It is the newest, and it handles a NEW module file:
  how it is mounted, its tables, the installer's treatment of its absence, and the undo that removes it. Use the
  rehearsal script with K2's fix: compare `(cd "$LIVE_FIN" && md5sum -- *.py *.html 2>/dev/null) | md5sum`, never a
  directory listing.
- How S557's `asset_machine.py` does parts, cover, reminders into Renewals and the Switches card. Batteries copy those
  patterns: reminders go into the same Renewals list, ownership fingerprints included.

## 2 · Pins — FROM bytes, read on the box first
**These are S568's TO pins: S568 must be installed first. Any other byte = STOP and report.**
- `/root/assetapp/sorting_desk.py` **`695ba90b4b3652f0e087f29b7c25d706`**
- `/root/assetapp/asset_register.py` **`e5356e0c75f564085b20a059f76a4b48`**
- `/root/assetapp/clinic_papers.py` **`6db07c12a8ba5ab0123db2a5bee0fa7b`** — read; edit only if the Renewals or month
  wiring needs it.
- NEW `/root/assetapp/batteries.py`
- Read only, **never edited:**
  - `stationery.py` `d11d7183…`
  - `asset_machine.py` `7d4fdffc…` — a new UPS/inverter machine is seen from the batteries side, not by editing it
  - `scanner_widget.js` `10a8bb29…`
  - `packs.py` (S568 TO `e46264b8…`, the parent's)
  - every Sanjeevni and finance file

## 3 · What to build (the mock-up is the specification)
1. **The Batteries page** (owner's English; in the scan app's menu after Machines).
   - **Totals at the top:** due for replacement · warranty ends within 30 days · bill awaited · battery places.
   - **Four groups, as in the mock-up:**
     - **Online UPS** (B.L. Computers · warranty 1 year · bill with the battery);
     - **Small UPS** (B.L. Computers · warranty 1 year);
     - **Generator and inverters** (Jasoria · bill and warranty card come with the battery · old battery paid back);
     - **Vehicles** (Jasoria · bill and warranty card · yours only).
   - **One row per place:** place and sub-line · battery now · fitted · warranty till · a status badge (OK / Warranty
     ends in N days / Due for replacement / Bill awaited N days / Water top-up due) · **New battery fitted**.
   - **"+ Add a battery place"** under the groups.
   - **Tapping a place opens its history:** the re-order line (type · Ah · V · set of N · supplier · warranty · paid by),
     then every battery it has had (fitted · removed · lasted · cost · the bill's stamp, linked to the desk).
2. **Seeded places** (data step: rows of names only — no numbers of any kind, F-185):
   - **Online UPS:** Digital X-ray (clinic) · NK Pathology (paid by NK Pathology) · DTH lab.
   - **Small UPS:** Reception PC · Second PC · Lab analysers · Home DVR + router (home, owner only).
   - **Generator and inverters:** Generator (clinic) · Clinic inverter (2 batteries) · Home inverter (2 batteries, owner only).
   - **Vehicles** (owner only): Carnival · Wagon R · Vento · Scooty · Bike.
   - Each place carries:
     - its group;
     - its payer — clinic / NK Pathology / owner. The **DTH lab** place's payer is **"to confirm"**: show it as such,
       never guess;
     - its supplier preset (B.L. Computers or Jasoria);
     - its default warranty months (B.L.: 12; Jasoria: empty until read from the card);
     - its usual life in months for the reminder (car 42, two-wheeler 30, inverter 54, UPS 30, generator 30 — editable
       per place);
     - its owner-only flag.
3. **New battery fitted** (one form, as the mock-up's two examples).
   - The date is today; the supplier and warranty come from the place.
   - **B.L. places:** the bill is scanned with the battery, or the battery reads **"bill awaited"** until a bill is linked.
   - **Jasoria places:** the price, the **old-battery amount**, the net, and the warranty months read from the card or typed.
   - **Bill and warranty-card link:**
     - pick a paper from the same supplier's recent papers (any lane, shown by stamp · date · amount), or leave it
       awaited. The card can be a second paper;
     - on the **sorting desk**, a paper from B.L. Computers or Jasoria shows **"Battery fitted at <place> on <date> — this
       bill?"** when that place has a bill awaited. One tap links it;
     - **linking never changes the paper's lane, section or status** (D664). The desk's normal destinations still decide
       where the money goes; the place's payer only pre-selects, saved only on Save.
   - Saving puts the previous battery into the history with its removed date.
4. **Reminders into the existing Renewals list** (as S557's covers do, with ownership fingerprints):
   - warranty ends in 30 days;
   - usual life reached;
   - a B.L. bill still awaited after 30 days;
   - upkeep: inverter water every 3 months, UPS backup check every 3 months, generator start monthly — a "done" tap
     resets each one.
   - Owner-only places' reminders show to the owner only.
5. **A new UPS or inverter added in Machines** (an asset whose category or name says UPS or inverter) gets a battery
   place made by itself, linked to that machine, at the next page load (idempotent; never twice).
6. **Who sees what:**
   - the owner sees everything at once;
   - managers see clinic and lab places only, and only when the new switch **`batteries.on`** is ON (absent = OFF) — a
     row on the scan app's Switches card, owner only;
   - the reception login never sees it;
   - home and vehicle places, and their papers, are owner only, server-side.

## 4 · The walk, the controls, the rehearsal
- **`walk_s571.py`:** one named check per item 1–6, each **green on the TO files and red on the FROM files**
  (`--expect-red`, MUST_RED printed). Counts are printed into the log. It must include:
  - a B.L. place: fitted → bill awaited → a B.L. paper on the desk offered → linked → no longer awaited;
  - a Jasoria place: price, old-battery amount, net, and warranty from the card;
  - history after a second fitting;
  - the four reminder kinds, with "done" resetting upkeep;
  - an owner-only place refused to a manager;
  - a manager with the switch absent (refused) and set (clinic places only);
  - a new UPS machine making its place once;
  - **a linked paper's lane, section and status unchanged.**
- **The earlier walks green on the new files:** S568 (14), S566 (12), S563 (17 + the tidy fetch), S560 (37 + pack 9),
  S548 (8), S559 (43), S557 (41), S555 (19), S551 (87). Any adapted line goes in a `/tmp` copy only, with its reason.
- **The browser walks:** S560's desk layout (7) and S568's staff-screen checks, plus a Batteries page check at
  1366 × 768 that every group is reachable.
- **The installer:**
  - S568's shape, plus the new module, new tables and the seeded places (idempotent: a second run adds nothing);
  - **no existing row changed**;
  - `.bak_S571_<from8>` beside each replaced file, `assets.db.bak_S571_*`;
  - restart `assetapp` only (no finance file changes);
  - the undo line, which also removes `batteries.py`.
- **The rehearsal** on a made-up root. `.gitignore` last-match-wins, the contact-number gate (`SANJ_CONFIG_STORE` as
  before), SUMS, KIT_ID, README and the PIN files, all clean.

## 5 · NEVER (in addition to every earlier brief's)
- change reception's intake, its lanes or words, or `scanner_widget.js`; touch `packs.py`, `stationery.py`,
  `asset_machine.py`, or any finance or Sanjeevni file;
- move a paper, or guess its section or whose expense it is (D664); guess the DTH lab payer;
- write a number of any kind into the repository (F-185) — a vehicle registration, a phone number, a serial;
- install, restart or publish.

## 6 · The report
`REPORT_S571.md`, as S568's:
- the FROM pins as read; the counted edits; the TO pins;
- the walk, control and earlier-walk counts; the browser walks; the rehearsal;
- calls you made, with reasons; anything not done; anything seen outside the brief;
- the cost, **as the runner's own log states it**.

Last line: **nothing installed, nothing published.**

**If anything cannot be done as written, stop, write what was done and why, and end.**
