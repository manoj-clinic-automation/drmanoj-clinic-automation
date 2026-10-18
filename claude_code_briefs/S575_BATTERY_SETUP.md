# S575_BATTERY_SETUP — brief for the build runner (Agent SDK, the API credits)

*Written 18-Oct-2026 by the Scan App project (session 318). Kit **S575** claimed on the board `_numbers` (v462 → v463)
with its PLANNED line. The owner's ask, 06:02 IST 18-Oct: "Does the battery page offer me to link the existing batteries,
bills, and for many UPS, I only have a date when the batteries were renewed. So for the initial setup, that functionality
is also required. Online UPS has variable number of batteries, so I need a place where I can mention the number of the
batteries each online UPS is having." Run by `D:\Downloads\_kbtools\agent_build\run_build.py S575_BATTERY_SETUP`.*

**v2 — READ `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S575_BRIEF_R1.md` (md5 `99057249…`, 0 BLOCKER · 8
CORRECTION · 7 NOTE) WHOLE BEFORE BUILDING. Its replacement wording is binding and REPLACES the text below where they
differ.** In short:
- **C1** "Old battery — no bill" is stored as `bill_id=NULL`, `bill_created_at='none:old-battery'` (the card the same):
  no new column, no data step. All three "awaited" decisions — `place_view`, `page_place`, `desk_offer` — honour it;
- **C2** "Old battery — no card" is on the Jasoria form only (the B.L. form has no card select);
- **C3** a later link goes through the place page's "The battery now — its papers" box (`#s571links`), for the battery
  in use — not a new form on each history row;
- **C4** `candidates()` and `_pickable()` stay unchanged (S571's I7 depends on them); the wider list and the stamp
  lookup are separate, with a fixed order when more than one picker is filled;
- **C5** Find by stamp uses `sorting_desk._s566_stamp_form` and batteries' own lookup; one refusal line for every case,
  never revealing to a manager that a Personal paper exists;
- **C6** First setup lists places with **no battery recorded** (not by badge text); its date is required; it sends the
  place's warranty months; saves and refusals return to the fold;
- **C7** "How many batteries? — set" is owner-only and opens the place's edit form; "set of N" shows even before a
  battery is recorded;
- **C8** the 2024 walk: the warranty has passed, so it shows a date, not a reminder, and the badge is "Due for
  replacement"; use N=4.

The review's NOTES bind as guidance. Only the 15-year lower limit on the fitted date is new; past dates already save.

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** The kit goes in
`deploy_kits\S575_BATTERY_SETUP\` and the report in `claude_code_briefs\REPORT_S575.md`; then stop. Nothing live is placed
or restarted, and no live row is written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 1 · Read first
- `claude_code_briefs\S571_BATTERIES.md` (v2), its R1, `REPORT_S571.md` (with fix round 1), and the kit
  `deploy_kits\S571_BATTERIES\`. **Copy that kit's shape exactly.**
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`. Every rule and NEVER of S571 still binds.

## 2 · Pins — FROM bytes, read on the box first; a different byte = STOP and report
- `/root/assetapp/batteries.py` **`9a0054ac`** — S571's TO, the file this kit changes. Read the full md5 on the box.
- Read: `sorting_desk.py` `110335ea…` and `asset_register.py` `c39c084e…` (S571's TO). Edit them only if a change
  cannot be made in `batteries.py`, and then name the reason.
- Never edited: `stationery.py`, `asset_machine.py`, `clinic_papers.py`, `scanner_widget.js`, `packs.py`, and any
  finance or Sanjeevni file.

## 3 · What to build (all on the Batteries pages; reception untouched)
1. **An old battery, with only a date.** On **New battery fitted**:
   - "Fitted on" takes any past date (dd-mm-yyyy, the app's own date rule; up to 15 years back, never in the future).
   - The **Bill** choice gains **"Old battery — no bill"**, beside "Bill awaited". With "Old battery — no bill":
     - no "bill awaited" badge;
     - no "B.L. bill still awaited" reminder;
     - the warranty and usual-life reminders work from the fitted date, as now;
     - the history line reads "no bill (old battery)".
   - The **warranty card** gets the same choice.
   - A bill can still be linked to it later from the history line (below).
2. **Link existing papers, old ones too.**
   - The bill and warranty-card pickers (the fitted form, and the history line's link form) list:
     - the place's supplier's papers of the last 90 days, as now;
     - a **"Show older / other papers"** choice, which lists every paper the person may see (the desk's visibility rules;
       never pharmacy, set-aside or second scans), newest first, with stamp · supplier · date · amount;
     - a **"Find by stamp"** box (B-0162, B162, b-162 …, the S566 stamp normaliser), which links that paper if the person
       may see it, or else gives one plain refusal line.
   - **Linking never changes the paper's lane, section or status** (D664), as S571.
3. **Batteries in each online UPS.**
   - The count is already stored ("Set of" / "Batteries in the set").
   - Make it visible where the owner sets up: on the Batteries list, an online UPS row with no count shows **"How many
     batteries? — set"**, linking to its "Change this place".
   - The New battery fitted form shows "Batteries in the set" first for the three online UPS.
   - The list shows "set of N" once known (S571 already writes it into the battery line).
4. **First setup in one sitting.**
   - The Batteries page gets a small owner-only fold, **"First setup"**, listing the places still "Not recorded yet".
   - Each has a one-line form: fitted on · batteries in the set (UPS) · bill (Old battery — no bill / pick / find by
     stamp) · Save.
   - The full form stays available.

## 4 · The walk, the controls, the rehearsal (as S571's)
- **`walk_s575.py`:** one named check per item 1–4. Each must be **green on the TO file and red on the FROM file**
  (`--expect-red`, MUST_RED printed), with the counts printed. It covers:
  - an old UPS battery dated 2024 with "Old battery — no bill": no awaited badge, no bill reminder, warranty/life
    reminders from 2024;
  - an older paper linked by "Show older" and by stamp (B162 form);
  - a Personal paper refused to a manager by stamp;
  - a linked paper's lane, section and status unchanged;
  - an online UPS with no count showing the prompt, and after setting it, "set of N";
  - the First setup fold saving three places in a row.
- **Earlier walks green on the new file:** S571 (12), S568 (14), S566 (12), S563 (17 + tidy), S560 (37 + pack 9),
  S548 (8), S559 (43), S557 (41), S555 (19), S551 (87). Adapted lines go in `/tmp` copies only, with reasons.
- **Browser walk:** the Batteries page and the First setup fold at 1366 × 768.
- **The installer:**
  - S571's shape;
  - no data step (if one is needed, STOP and report);
  - `.bak_S575_9a0054ac`;
  - restart `assetapp` only;
  - healthz;
  - the walks on a database copy;
  - the undo line.
- **The rehearsal's end check** compares only program files (`*.py *.html`), never a folder listing (S568 K2).
- **Gates:** `.gitignore` last-match-wins, the contact-number gate, SUMS, KIT_ID, README, PIN files.

## 5 · NEVER
- Change reception's intake or any staff screen's words.
- Move a paper or guess its section (D664).
- Put any number of any kind (a registration, phone, serial or account number) into the repository.
- Install, restart or publish.

## 6 · The report
`REPORT_S575.md`, as S571's:
- pins, counted edits, TO pin;
- the walk, control and earlier-walk counts; the browser walk; the rehearsal;
- calls made, with reasons; anything not done; anything seen outside the brief;
- the cost **from the runner's own log**.

Last line: **nothing installed, nothing published.**

**If anything cannot be done as written, stop, write what was done and why, and end.**
