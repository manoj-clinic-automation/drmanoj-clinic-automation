# S566_SCANAPP_LAST_FIXES — brief for the build runner (Agent SDK, the API credits)

*Written 16-Oct-2026 by the Scan App project (session 318). Kit **S566** claimed on the board `_numbers` (v441 → v442)
with its PLANNED line (D646) naming the four files below. **v2** — after the independent read
`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S566_BRIEF_R1.md` (md5 `9950b7d4…`, 4 BLOCKER · 6 CORRECTION · 9 NOTE). The owner's word, 05:20 IST 16-Oct: "check the scanner and then
find whatever needs to be done, then include these two small follow-ups ... use the Claude API credits". This file is the
whole scope. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S566_SCANAPP_LAST_FIXES`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** Kit in
`deploy_kits\S566_SCANAPP_LAST_FIXES\`, report `claude_code_briefs\REPORT_S566.md`, then stop. Nothing live placed or
restarted; no live row written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 0 · Where this comes from
- S563 (live 19:08 IST 15-Oct) and its independent kit review
  **`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S563_KIT_REVIEW_K1.md`** — notes **N5** and **N6** (items 1 and 2).
- A read-only live check as the owner, 05:2x IST 16-Oct (items 3-8). The scanner itself raised nothing new (no clinic
  scan since B-0164; B-0162/B-0163 were the double stamp S559 already repaired). **No change to `scanner_widget.js`.**
- No new feature, no new page, no new switch. Reception's screens unchanged.

## 1 · Read first
`claude_code_briefs\S563_SCANAPP_TIDY.md` (v2) and `REPORT_S563.md`; the K1 review above; `S560_RECEIPTS_STATEMENTS.md`,
`REPORT_S560.md`; `REPORT_S559.md`, `REPORT_S557.md`; `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`. Every rule and NEVER of
those briefs still binds. **Copy `deploy_kits\S563_SCANAPP_TIDY\`'s kit shape exactly** (installer `S566_*` variables, the
build lock, pins before anything moves, rebuild on the box from the live bytes, both pythons, the walks on a database copy,
backups, restart assetapp only, healthz, the undo line; the rehearsal on a made-up root; walk and control in separate
processes; made-up rows only; injected `today`).

## 2 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/sorting_desk.py` **`062ac43cf71b52faa16d0feee25126c5`** (S563)
- `/root/assetapp/clinic_papers.py` **`9a59f977226f901e06d91c312cd116b7`** (S563, consolidated)
- `/root/assetapp/asset_register.py` **`0828fbc307d400feff2fbc0872fef686`** (S563)
- `/root/assetapp/asset_machine.py` **`7d4fdffce01a28fd7e5cc2c4f2aeeb74`** (S563)
- Read only, **never edited**: `scanner_widget.js` `10a8bb29…`, the parent's `/root/finance/packs.py` `048d2ad8…`,
  `claude_reader.py` `3894dc23…`, `claude_reread.py` `d9b75e78…`, every finance-app, portal and Sanjeevni file.

## 3 · What to build (binding decisions; find the real cause of each in the code first and name it in the report)

**v2 — READ `S566_BRIEF_R1.md` WHOLE BEFORE BUILDING. Its replacement wording is binding and REPLACES the text below
where they differ:** point 1 → item 1 · point 2 → item 3's rule · point 3 → item 7 · point 4 → item 8 · point 5 → item 4's
rule · points 6, 7, 8 → item 5 · point 9 → item 6's last two sentences · point 10 → item 2's rule. Its § Causes are the
causes to confirm first. Its NOTES bind as follows: **12** — the walk seeds both possible B-0009 shapes; **13, 15** — keep
the D710-held and challan drafts as they are; item 1's duplicate check is the guard; **14** — report what leaves the home
card; **16** — the earlier walks whose counts move are adapted in `/tmp` copies only, each change named; **17** — the old
page's header count follows the same filters; **18** — `set_warranty` and `set_pe_who` on the old pages call the same
item-2 helper (a Personal paper: owner only); **19** — the home card's total takes no items loop.


1. **N5 [R1 point 1 governs] — a restored paper never counts twice blind.** S563's `_s563_restore` on a lane whose fresh status is
   `captured` (filed straight: Construction work, Personal expense / `owner_expense`, other documents) puts the paper back
   in front of a person instead of straight into a total or a pack: it returns as **waiting on the desk** (the same state a
   clinic paper gets, or the lane's own "to be sorted" state if one exists), so the normal Save — with the app's own
   duplicate check (`_dup_by_triple` or the lane's equivalent) — files it. If a lane has no waiting state at all, the
   restore runs the duplicate check itself and refuses with "This looks like B-xxxx — open it instead" when it matches.
   Audited as today.
2. **N6 [R1 point 10 governs] — the old challan doors check on the server.** In `clinic_papers.py`, the old Bills awaited page's **close, delete
   and join** POST routes (and any other POST that takes a challan or paper id on that page) refuse — with a plain message,
   nothing written — a challan with `subgroup='patient_paper'` for anyone, and one with `subgroup='personal'` for a
   non-owner, exactly the filters S563 put on the page's lists. One helper, used by every such route.
3. **B-0009 [R1 point 2 governs] — no paper waits where nobody sees it.** B-0009 (Construction work, a 3-way switch, status shown as "Waiting"
   since 11-Sep, no supplier or amount read) is on no desk list and no Bills awaited list. Find why the desk's waiting list
   leaves it out. Rule: **every live paper that is not on the pharmacy lane, not set aside, not a joined page and not a
   double scan, and whose status reads as waiting anywhere, appears in the desk's waiting list** (a Personal one for the
   owner only; a patient's paper only as today). The desk's waiting count on the menu and the home page follow the same
   list. Do not change the paper's lane, section or status (D664) — only make it reachable.
4. **The Bills awaited [R1 point 5 governs] count and the page agree.** The menu read "Bills awaited (2)" while the page listed one challan
   (B-0163). Find the two queries; make the count come from **the same helper that builds the page's list**, for the same
   viewer (owner / manager), so the number always equals the rows shown.
5. **A date [R1 points 6-8 governs] is never stored half-read.** B-0163's bill date is stored as the text "14/10". Find the writer (the intake, the
   reading step that fills an empty date, or the desk). Rule: a date field is written only as a full `yyyy-mm-dd`, or left
   empty; a partial or unparseable reading stays only in the reading (Claude's or Sarvam's) for the desk's "Claude read: …
   — use it" line, and the desk's misread flag still shows. **No data step:** B-0163's stored text stays; every page that
   shows a bill date shows a stored non-ISO value as written with the misread flag, never crashes, never sorts it wrongly.
   **Also on the old bill page:** a paper whose status is waiting (`draft`) never prints "approved by system …" beside it;
   the approval line shows only when the status is approved.
6. **The home page [R1 point 9 governs]'s "Spend this month" equals The month's total.** Home read ₹25,215 while The month's sections added to
   ₹26,705 (the gap = Others ₹850 + an Implant estimate slip ₹640). **The month page is the reference.** Home calls the same
   function The month uses for its grand total, for the same month and the same viewer — one source, no second sum. If The
   month itself counts something that is never spend by an earlier ruling (a receipt, a statement, an awaiting challan, a
   patient's paper, a pharmacy paper — D722, D728), report it and leave both as they are for that part.
7. **Machines list [R1 point 3 governs]: the Contract column shows a blank, never the word "None"** (36 of 39 rows did). Any other column on
   the Machines list and a machine's own page that prints `None` for an empty value gets the same blank.
8. **`/desk?open=` [R1 point 4 governs] accepts the stamp as well as the record number** (`?open=B-0162` and `?open=162` open the same paper;
   an unknown value opens the desk with a short "No paper B-xxxx" line, never an error). Every link the app itself makes
   keeps working.

## 4 · The walk, the controls, the rehearsal
- `walk_s566.py`: one named check per item 1-8, each **green on the TO files and red on the FROM files** (`--expect-red`
  with the MUST_RED list printed); counts printed into the log. Item 3 seeds a made-up paper shaped like B-0009; item 4 a
  made-up Personal / patient / plain challan mix seen as owner and as manager; item 5 a made-up "14/10" date; item 6 a
  month with Others and an estimate slip.
- The earlier walks green on the new files: S563 (17, and the tidy fetch), S560 (37 + pack 9), S548 (8), S559 (43),
  S557 (41), S555 (19), S551 (87 through `s551_lines_s559.py`) — each in its own process, any line a TO pin forces adapted
  in a copy in `/tmp`, never in a frozen kit. The S560 desk-layout browser walk (7) on the PC's headless Chrome, since the
  desk's waiting list may grow.
- The installer as S563's (no scratch step needed): pins checked; `.bak_S566_<from8>` beside each replaced file and
  `assets.db.bak_S566_*`; **no data step and no new column** (if one turns out necessary, STOP and report);
  `systemctl restart assetapp` once; `/scanapp/healthz` 200; the walks on a copy of the database; the undo line in the
  README. `clinic-finance` is not restarted.
- The rehearsal on a made-up root, its refusals and outcomes as S563's. `.gitignore` last-match-wins and the
  contact-number gate clean (`SANJ_CONFIG_STORE` as before); SUMS, KIT_ID, README, the PIN files.

## 5 · NEVER (in addition to every earlier brief's)
- change reception's intake or any staff screen; touch `scanner_widget.js`, `packs.py`, any finance, portal or Sanjeevni
  file, DUTY_MAP;
- guess a section, a sub-section or whose expense a paper is (D664); move a paper a person placed; change a stored row;
- copy a patient's file or a live database row into the kit, the report or the PC;
- install, restart or publish.

## 6 · The report
`REPORT_S566.md`: the FROM pins as read; the real cause of each item; every counted edit (anchor matched exactly once on
the live bytes); the TO pins; the walk and control counts; the earlier walks; the rehearsal; calls you made where this
brief left room, each with its reason; anything not done and why; anything seen outside the brief (not touched); the cost
**as the runner's own log states it** (the log exists: `D:\Downloads\_kbtools\agent_build\logs\`). Last line: **nothing
installed, nothing published.**

**If anything cannot be done as written, stop, write what was done and why, and end.**
