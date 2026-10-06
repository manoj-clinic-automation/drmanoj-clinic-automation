# HANDOFF RUNBOOK — v215 — S294 close (the parent), 06-Oct-2026, on top of the Sanjeevni chat's S295 close (05-Oct)

*Supersedes v214 (the Sanjeevni chat's S295 close). **§0, §1, §1D (corrected), §1E (new), §2A, §4 and §5 are rewritten here by the parent's S294 close**; §1A has its S292 paragraph brought up to date; §1B and §1C are carried whole; **§2B is the Sanjeevni chat's, whole and unchanged from v214**; §3 names this close's files beside the earlier ones. For the next parent chat (**297**, next on the board, not reserved) and the next Sanjeevni chat (296, reserved).*

*(v214's header, retained:)* Supersedes v213 (the Sanjeevni chat's S285 close). v213's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged since v212 (the parent's S294 is still open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S295 close**, §3 and §5 name this close's files beside the earlier ones. For the next parent chat (294, open; 297 after it) and the next Sanjeevni chat (**296, reserved on the board at this close**).

*(v213's header, retained:)* Supersedes v212 (the parent's S293 close). v212's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged (the parent's S294 is open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S285 close**, §3 and §5 name both closes' files. For the next parent chat (294, open; 296 after it) and the next Sanjeevni chat (**295, reserved on the board at this close**).

*(v212's header, retained:)* Supersedes v211 (the parent's S292 close). For the next parent chat (session 294 if still free on the board — it is not reserved; 285 is the Sanjeevni chat's, open at this close). §1A, §1B and §1C are carried whole from v211. §1D is new: the statement road. §2B is the Sanjeevni chat's own backlog, carried whole from v211 with one more dated note.

## §0 · What happened (04-Oct 15:56 → 06-Oct before dawn, one chat across two nights)

1. **The open (04-Oct 15:56):** session 294 on the board; `_numbers` trimmed to forty claims, the whole kept in evidence; the twelve S293 pending pins reproduced from the bundle and the kits' own applies. His word at 16:10: *"I would like you to do what all is possible for you in your list."*
2. **`finance_app.py --selftest`, whole, on a scratch copy:** 666 of 724 with auto-apply off; it **aborts as the box runs**. No live fault; the suite is out of date (F-742) and wants its own kit.
3. **S476_STATEMENT_WATCH (live 04-Oct):** the health row *Bank statements reaching Drive*; the owner-only text door `/finance/packs/api/text/<id>`; `clinic_users.json`, the hand-over photos and `spine/orders` into the encrypted nightly.
4. **S477 + S478 (manojz):** the two PC setup kits rehearsed on a real Windows by the nightly itself — first run 05:06 05-Oct, GREEN, 46 checks — after a reading found and S478 repaired the bare-`python` defect (F-743). The *Medical PC* and *Dr Manoj's PC* buttons are released.
5. **S479_YES_MONTHLY_READER (live 04-Oct evening):** the bank's e-mailed monthly statement read (F-725 repaired); one row key across the three Yes Bank readers (F-744); the pack hands on the unlocked copy (F-745). The page read 13 of 15 for September.
6. **Monday 05-Oct 08:15:** every pending pin equal to the 05-Oct bundle; the statement road ✓; **j42 and j43 served — the reception PC's agent is S456.1.**
7. **His morning ask (05-Oct):** the daily, weekly and monthly duties of Shavez and reception, settled with him over two rounds; and a tile at the top of his app leading to a command console. The mock-up: *"mock-up seems okay to build. Go ahead."* (D680).
8. **S481_COMMAND_CONSOLE (live 18:22 05-Oct):** paused once at his word over which model was working, resumed at *"Build it"*. A reading layer on a copy of the database. Its first server run stopped red at its own walk and placed nothing (F-746); the walk corrected, the second run green.
9. **S487_AAJ_KA_KAAM (live 21:35 05-Oct, switched OFF for staff):** his word — *"dont populate old stale data, use from current month only, and the leftovers of September"* (D679). One Hinglish list per login; nothing before 01-Sep-2026 shown or counted; the console now reads the same lines. Its first publish was refused for a missing allow line (F-751).
10. **The close (06-Oct):** the nightly of 03:12 read; **the pin list held against the 06-Oct 01:35 bundle: 215 match · 0 mismatch · 16 not in the bundle; of the fifty rows that say DECLARED-PENDING, forty-eight equal the bundle (the Sanjeevni chat's eighteen among them) and two are files the bundle does not carry** (`/root/portal/NotoSansDevanagari-Regular.ttf`, `/root/wa/vitals/vitals_page.html`). The lists were still off at 05:00.

**Beside this chat:** the Sanjeevni chat's S295 (04-Oct 18:06 → 05-Oct 20:25) — S480, S482, S484, S485 live, S483 built and not installed, S486 briefed and parked. Its own close wrote v214; §2B below is its text, unchanged.

## §1 · Mental models

1. **A reading layer computes nothing.** The console asks each owning module on a COPY of the database (`FINANCE_DB` pointed at the copy before any module loads) and writes one file; the service only reads the file. A new figure for the owner goes into the module that owns it, then into the console — never the other way.
2. **One list engine, two readers.** `aaj_kaam.build_all` feeds the staff's page (live, through a `mode=ro` connection) and the console's builder (on the copy). A change to a duty's wording or count is made once — in `DUTY_MAP.json` (the Sanjeevni chat's) or `aaj_duties.json` (the parent's) — and both screens follow.
3. **The floor is laid under the SQL, not written into it.** TEMP views named like the floored tables on the engine's own connection; the map's SQL runs unedited. A `main.<table>` or a `rowid` in a `due_sql` steps around it (the walk's check A3c is red on that).
4. **A list that is not whole says so** (F-750) — and **a guarded piece of a reading says it could not be read; it is never simply absent** (F-748).
5. **A walk is run on data shaped unlike the box it was written on, and on more than one clock** (F-746); **a negative control that survives is a finding about the check** (F-747).
6. **The login gate answers before routing** — a door answering 302 without a login proves nothing about whether it is mounted. The proof is to load the placed app on a copy and ask the app for its routes (`reading_s487.py mounted`).
7. **A figure for the owner is read where he will read it** (F-724).
8. **A database copy is made only under the session's own home; a scratch box is hashed against the live pins before the first walk** (F-752). **After a kit is placed, `.gitignore` is read against every file of it before the publish is named** (F-751).
9. **When he stops a build, it stops at once and he is shown what he asked about** — the model question of 05-Oct: paused, the session's setting shown, resumed at his word.
10. Carried from v212: a page tells you where to look, the store tells you what is true · a refused file is retried when its reader changes · an export of a program's configuration is read for every field (F-721) · a job under someone's Google authorisation is watched by what it produces (F-723) · a store that staff can read is not a road for a bank statement (D674) · *"take my yes"* — once he has corrected the plan, build the whole plan · two chats, one working copy, one publish: a file the other chat owns is read live before it is touched · the board's one counter costs a full rewrite per line: trim before 200 KB (F-703) · a walk is hermetic by construction (F-709) · a rule is walked with every value it names (F-710) · the gate is run as PUBLISH runs it · read `whoami` before an owner-only press · what his word closed is not raised again · the build lock binds every installer (F-694) · patient files never pass through the assistant's workspace (D656) · a system change on a PC is his hand.

## §1A · How to send a job to the reception PC

**Sign (both doors), in manojz's own shell — the secret never leaves that PC:**

```
cd <folder with the job> && python3 -B $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S448_RECEPTION_AGENT/reception_sign.py sign $HOME/mnt/Downloads/margsync/_config/reception_agent_key.txt <job file>
```

It writes `<IST time>_<job>` and `<IST time>_<job>.sig`. Job folders so far: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S290\reception_jobs\` (j01 … j21) and `…\_EVIDENCE\S291\reception_jobs\` (j22 … j40). Useful ones to copy: `j35_cable_and_wifi_read.py` (the cable and Wi-Fi from Windows' own records), `j33_setup_complete_check.py` (the whole setup), `j40_after_wifi_driver.py` (driver, scans, Windows Update, build).

**The Drive door (the usual road):** stage the stamped job and its `.sig`, copy both into a **fresh** folder under the cloud workspace's outputs, and commit **the job first, then the `.sig`, in two separate calls** to `H:\My Drive\Clinic Data Archive\ToReception\jobs\`. About two minutes later stage `H:\My Drive\Clinic Data Archive\FromReception\results\<stamped name>.out.txt` (a refusal is `<stamped name>.REFUSED.txt`). Those two folders are reached by the file-transfer tools only, not by the shell. A job that restarts the agent loses its own Drive result — read the next job instead.

**The server door:** from the assistant's browser, on any page of the clinic site, `fetch` a `POST` to `/finance/api/reception/jobs/submit` with JSON `{name, job (base64 of the stamped file), sig}`; read with `reception_sign.py read-token` → `POST /finance/api/reception/jobs/read`. Proven from the PC on 03-Oct (j13). Impractical for a job of several kilobytes — the Drive door is the working road. Full text: `deploy_kits/S453_RECEPTION_SERVER_DOOR/README.md`.

**Rules of both doors:** `.ps1`, `.cmd`, `.bat` or `.py`; first comment line `# timeout=NNN` changes the 600 s limit; a name is used once; older than 48 hours refused; runs as user `dell`, not elevated; ask for counts, never listings of patient folders. **A system change on that PC — a driver, a Windows setting — is the owner's hand at the PC, not a job.** **A rehearsal sends the installer's output to NUL and reads `install_log.txt`** (F-698).

**The S292 jobs, done at S294:** job folder `…\_EVIDENCE\S292\reception_jobs\` holds j41 (03-Oct, Windows' own currency, read only) and **j42 and j43, signed and served at 08:30–08:35 on Monday 05-Oct**: j42 put agent **S456.1** on that PC (`reception_agent.py` `d3d4b67b`, S453.1 kept as `.prev`), j43 read it back. The heartbeat now carries the Windows build and the last cumulative update. The next job number is j44.

## §1B · The Docterz reports — by the server road since S457 (F-697 closed)

Reception exports both reports each evening (the consultation report and the follow-up log); the reception PC posts them to the server by itself. On manojz the tracker's five-minute task now runs `docterz_fetch.py` first: it asks the server at most every 10 minutes, compares by md5 with what is already in `D:\Downloads`, fetches what is missing and checks it. The pickup then works as before. **Nothing is the owner's to run.**

- **Its record:** `D:\Downloads\DocterzArchive\_server_fetch_last.txt` (one line per pass).
- **Its switch:** a file `D:\Downloads\DocterzArchive\_server_fetch_OFF.txt` (or the PC-wide `D:\Downloads\margsync\_off\ALL_OFF.txt`).
- **It depends on manojz being awake.** A day reaches his portal the next time that PC is on.
- **The fallback, if the fetch is ever off** — his old line still works and is safe on any day (identical files are skipped by content):

```
cmd /c copy /y "H:\My Drive\Clinic Records\Docterz exports\*.csv" "D:\Downloads\"
```

- **Undo:** put `DOCTERZ_PICKUP.bat.bak_S457_90f45531` back in the tracker's folder. Full text: `deploy_kits/S457_DOCTERZ_SERVER_PATH/README.md`.

## §1C · The clinic papers (D664) — where things are

- **The list to sort:** `https://followup.dr-manoj.in/scanapp/papers` — a suggestion per paper (Yes / Change / Skip), three groups (Procedure room · X-ray films, two sizes · Others), *join pages* with an undo that names the papers.
- **The warranty:** on a Dr MK expense paper, *Keep the warranty*; his card on `https://followup.dr-manoj.in/scanapp/renewals`; the Renewals row of `https://followup.dr-manoj.in/finance/health` names one inside its window (info; warn inside 7 days; never red).
- **Code:** `/root/assetapp/clinic_papers.py` (whole in `deploy_kits/S466_EXPENSE_WARRANTY/built/`), mounted by one guarded import in `asset_register.py`; every template hook sits behind `is defined`.
- **Open, his:** the split between clinic expenses and MK expenses — *"overlapping category, so not finalised yet"*. No rule suggests anything for electrical or plumbing papers. **Do not guess it.**
- **Not built:** a warranty date offered from the scan.

## §1D · The statement road (D674) — where things are since S293

- **The road:** bank → the owner's **personal** Gmail → `Bank_Statement_Relay.gs` (his personal Janitor project, trigger 07:00 daily, label `stmt-relayed`) → **Drive / Clinic Data Archive / Bank Statements / `<YYYY>`** (folder `1wGzaXnCoKcILw1VSv3UGYfQlVTl78UgT`; 2026 = `1-vrRDEZd0l53DKbZp3N51Laef5U759te`) → `stmt_shelf.py run` on the box at **05:40 and 07:30** (fetch + identify) → the packs page. Nothing passes through the clinic mailbox; nothing is mailed to the accountants until the owner presses *Send to accountants* (the pack).
- **The scripts:** repository copies in `deploy_kits/GAS_CURRENT/PersonalJanitor/Bank_Statement_Relay.gs` (S293 v2) and `…/UPIReconciliation/Bank_Statement_Filer.gs` (RETIRED; its trigger removed). The Janitor project is the owner's personal account's, shared to the clinic account as editor — the clinic browser pane edits it at `script.google.com/u/1/`; the clinic account's own `gas_export.py` drift check does not cover it.
- **If no statement reaches Drive:** his personal scripts' authorisation has lapsed again (F-723) — the failure mail goes to his personal inbox; ask him for the one re-authorisation (his hand). **Corrected at S294 (F-741):** the packs page's *re-read the shelf inbox* button only re-identifies files already on the shelf — it does **not** fetch; the fetch from Drive is the cron's alone (05:40 and 07:30), so a statement that reaches Drive after 07:30 is read the next morning.
- **The locked e-statements:** opened by the shelf with the per-account Yes Bank passwords he sets on the packs page (*Statement passwords*, six account rows then three bank-wide); the branch's unlocked copies, when they come, win (a locked twin becomes *duplicate of branch copy*).
- **The hand-over photos** (S472) are under `/root/finance/statements/packs/handover/<month>/` — in the encrypted nightly state bundle since S476.
- **The watch (S476):** the health page's row *Bank statements reaching Drive* — from the 3rd of a month, amber while no bank file was fetched this month and last month's cells are empty or partial. It measures the shelf's fetch, not the relay. **Read it at every close** (v17).
- **The readers:** `finance_yesbank.py` (the net-banking download), `yes_branch.py` (the branch's statement), `yes_monthly.py` (the e-mailed monthly statement, S479) — one row key across the three (F-744). The owner-only text of a shelf file: `/finance/packs/api/text/<id>` (S476), in his browser only.
- **Undo lines:** each kit's README (`S471_PACKS_SEPTEMBER`, `S475_YES_INTEREST_ROW`); the Filer's trigger is re-made by its `setupStmtFiler()` only by hand, on purpose.

## §1E · The Today tile, the command console and the staff's lists (D679, D680) — where things are since S294

- **The owner's pages:** the *Today* tile at the top of his Clinic app → `https://followup.dr-manoj.in/finance/console` — seven sections (Needs you · Money · Today's work · Attendance · Sanjeevni · Scans & papers · System). Under *Today's work*: the *Staff lists* line with **Turn on / Turn off**, then one block per list with **List** beside the name → `https://followup.dr-manoj.in/finance/aaj?as=<login>` (that person's list as they will see it; taps off).
- **The staff's page:** `https://followup.dr-manoj.in/finance/aaj`, from the *Aaj ka kaam* tile on their home — shown only when the lists are on and the login has a list.
- **Code on the box:** `/root/finance/owner_console.py` (1.1) and `.html`; `/root/finance/aaj_kaam.py`, `aaj_kaam.html`, `aaj_duties.json`; the mounts in `finance_app.py` (two guarded blocks after packs); the two tiles in `portal.py`. The reading: `/root/finance/console_reading.dat` (+ `.lock`, `.err`, `console_build.log`) — derived, rebuilt when older than five minutes and asked for.
- **The switch and the taps:** setting `aaj.staff_on` = `<ISO time>|<login>` (empty = off) and `aaj.staff_first_on` (kept once); table `duty_tick` (one row per line and period; made on the first tap). **At the S294 close: off, no tap table.**
- **The floor:** `aaj_duties.json` `from` (2026-09-01); the setting `duties.from` overrides it. Floored tables: `clinic_day_revenue` (from the first counter sheet, 12-Sep), `clinic_money_flag`, `day_entry`.
- **Who works which queue:** the map's `shared` and `aaj_duties.json` `works` — Alisha and Shivani each see Alisha's and the reception's queue; the shared Reception login sees the reception's only.
- **To change a line:** the map's lines are the Sanjeevni chat's (`claude_code_briefs/DUTY_MAP.json`, pulled to `/root/deploy/repo/…` by any install line); the parent's seventeen are in `aaj_duties.json` — a change to that file is a kit (it is pinned).
- **'late'** is the map's own rule: late on the day its allowed days are used up — the same on the list and on the console. A weekly tap line is late from the Tuesday, a monthly from the 4th.
- **Not built (agreed with him on 05-Oct, D679):** the morning step that must be answered before the other tiles open, triggered by the punch; stand-ins and *away*; the Docterz-export lock; the night list's carry-over wording; the attendance month-end sheet flow; approving inside the console.
- **Undo lines:** each kit's README (`deploy_kits/S481_COMMAND_CONSOLE/`, `deploy_kits/S487_AAJ_KA_KAAM/`).

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **His, the one thing waiting on S487:** look at each person's list from the console and tap **Turn on** (or say what wording to change). Until then the staff see nothing new.
3. **The maintenance pass at the next open:** the pin list against the newest bundle (at this close: 215 · 0 · 16; two rows pending because the bundle does not carry them). `finance_app.py` stands at **drift 4** — the next patch to it reaches the line and a whole read comes first.
4. **The next kits of D679, in the order he was told:** (a) the loud line on punch — the morning step answered before the other tiles open; (b) stand-ins and *away*; (c) the Docterz-export lock; then (d) the attendance month-end sheet flow (reception prints, staff tick and sign, reception enters the changed days, Shavez checks, the owner approves changed days only); later (e) approving inside the console, Shavez first and then the owner.
5. **Wording seen live on the console, small:** *N min late* on a first punch far past the usual hour (Shavez 149, Darpan 31 on 05-Oct); Bhati's punch does not join a login; Amir on a non-visit day; names in lower case in the fact lines (*entered by shivani*).
6. **The self-test suite's own kit (F-742):** bring `finance_app.py --selftest` current — 58 expectations describe pages changed on purpose, and the run aborts as the box runs. Test code only.
7. **For the Sanjeevni chat (on the board's 20:3x line of 05-Oct):** the seventeen extra lines of `aaj_duties.json` are offered to `DUTY_MAP.json`; a duty ships with its table (an unreadable line now gives that person a *list not whole* banner); F-749's order (`returns.pending_ok` is true only after the approvals tree is built).
8. **Small, by a job, on or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC; tell him in one line.
9. **A statement that reaches Drive after 07:30 waits until 05:40 the next day** (F-741; seen 05-Oct, two files at 07:53). If he wants it sooner: a third fetch, or the button made to fetch — ask once, do not build unasked.
10. **Left on the box, counted:** 61 test scans in `/root/finance/finance_scans.test_scans_set_aside_S468` (his word: they stay) · one old self-test file in `yesbank_statements` · `/root/finance/ipv6_facts_s455.json`.
11. **His, told once, not chased:** the Yes Bank passwords for NK Pathology's and the Clinic's current accounts (September reads 13 of 15) · the pack's send · the reception PC's cabled port · that PC's Windows (F-700; its build and last update now ride the heartbeat) · "Connect automatically" for the clinic Wi-Fi on that PC · the clinic / MK expense split · the follow-up tracker on the server (C·2).
12. **Waiting on his word ("later"):** contacts steps 3–5 · the mail flood · the portal tiles (after the pharmacy move) · the "other works" for Tailscale.
13. **Handed on by the duty map, still open:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only. (The lists now name these jobs to the reception's people; the tiles are still to be granted.)
14. **Kits owed, not urgent:** Shavez's PC and the lab PC setup kits · the F-712 reader · `asset_register.py`'s two dead items (under the line).
15. **Held at his word:** the Callback Tracker move (D634).
16. **One small folder to delete, his (deletion is off for a session):** `D:\Downloads\_to_delete_S294\` — the two EMPTY `_v.db` files of F-752, moved there at the close from `…\_EVIDENCE\S294\s487_build\visual\`, with one more empty file and one `.pyc`; `WHY_SAFE.txt` inside.

The living list: `claude/S288_PENDING_LIST.md`.

## §2B · The Sanjeevni chat's backlog — rewritten at its S295 close (05-Oct-2026, 20:xx IST)

*Supersedes the §2B of v213 (the S285 close). The next Sanjeevni chat is **session 296 (reserved on the board at this close, `_numbers` v289)**; it starts from `START_HERE_SESSION_296.md`, then `S295_BUILD_BRIEF.md`, then `claude/S295_PENDING_BUILDS_05OCT.md` (what is still to build by the decided architecture — the owner's ask of 05-Oct).*

**What happened (04 → 05-Oct):** four kits live from the owner's paste lines to Claude Code, each read back against its brief. **S480_MARG_TEXT_READERS** (05-Oct 07:25; the medical PC 07:59) — every Marg report the shop exports is read as text by one cutter and a spec per report; an empty report is an answer (D675); the salt reader no longer files items under the firm's name (F-730). **S482_BILL_CHAIN** (09:44) — the chain of Marg's bill numbers, `mi_bill_chain`, says what export is missing; one gap found (08/09-Sep) and shown on Shavez's tile and the owner's line; seven rename rows set to the compulsory spellings (D676). **S483** stopped itself on its own walk (built, not installed); **S484_SPINE_BILL_TIES** (11:35) mended the spine's reader and its tie rules — the spine, frozen since about 08:10 by two text-made sheets, built again at 11:37 (gate 13/13). **S485_DARPAN_ORDER_TAB** (15:24) — Darpan's tab *आज का ऑर्डर* on *Kal ka hisaab* (D677); it went live the same afternoon on a list he had not been shown (F-740, the assistant's), and the owner put `order.source` back on `marg_sheet` himself about 17:3x. **S486_BUYING_MODEL** (D678) was briefed, refined on a replay of the shop's own five months, and **PARKED at the owner's word** — not started.

**Mental models earned:**

- an empty report is an answer, and the chain of Marg's bill numbers — never the calendar — says what is missing (D675);
- a new road for a sheet is proved against every reader of that sheet, the spine's gate among them, before it goes live (F-734);
- when two records are equal on the key that orders them, the tie-break is a stated rule about what they are (F-736);
- a brief that changes what a staff member sees says WHEN it becomes visible, from a state read at install (F-740);
- an approval step is enforced at every route that can do the approved act, old pages included (F-738);
- an ordering rule is chosen on the shop's own months before it is built: the engine as it stood was worse than the sheets it was to replace (the replay: 246 empty-shelf item-days against the shop's 173; the refined model 100);
- the order of an install is fixed: Claude Code builds and publishes, then the server line — the owner is never given the server line first;
- a kit that stops on its own walk is the system working (S483).

**In order:**

1. **The morning after, read only:** the 18 server pins of §S295 against the 06-Oct 01:35 bundle (DECLARED-PENDING; each equals its predecessor in the 05-Oct bundle 1e0721c9); the first `spine/orders/order_score_latest.json` (the night of 05-Oct) and the weekly line on the owner's card; Amir's count board — *26 of 28*, two to correct (ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST) — then the proof and the 22 renames; that Darpan's Marg sheet arrives by itself (`order.source = marg_sheet`).
2. **The small kit — the owner's *"Go"* of 05-Oct**, one kit number from the board, its brief read by an independent agent against that morning's bundle. Display: dates compared as dates on three stock and pipeline lines (`stock_app.py`, `darpan_app.py`, `owner_sheets.py` — the audit's items 16 … 18); Amir's waiting card says since when and for what, and a refusal is kept past midnight (items 19, 20 — not the four flow gates of items 2, 3, 8, 9, which are the later *calendar-safe* build); the owner's own overdue line (the salt list over 8 days, the item / category list over 35); a wrongly learnt item name can be struck on the Items check. Pipeline: a refused text with patient detail is kept off Drive's `FromMedical\refused_text`; F-733's two collector lines read in the code to confirm S482 closed both (the pending paper carries them as owed in error). **It touches none of the twelve parked files:** `order_rules.py`, `porders_s454.py`, `porders.py`, `porders.html`, `darpan_kal.py`, `darpan_kal.html`, `order_sheet.py`, `order_sheet_pdf.py`, `finance_approvals.html`, `spine/spine_read.py`, `spine/order_rehearsal.py`, `spine/selftest_spine.py`. F-726 a (an answered salt reaches Amir's sheet): its wording is shown to the owner first.
3. **S486_BUYING_MODEL — PARKED.** Not pasted, not built, until it has been analysed again on Fable 5.1 after the limit resets (Saturday 10-Oct night). `claude_code_briefs\S486_BUYING_MODEL.md` 774e227f (37,852 B), `claude_code_briefs\S486_replay\`, `claude/S295_ORDER_MODEL_REPLAY.md`. For the re-read: the replay's limits (its §4), the two-day delivery case, safety 4 or a higher minimum order, whether Part A (F-738, F-739, the owner's cards on his approvals page, F-717) goes alone. Its PLANNED lines stand on the board and lapse by D646's seven-day rule unless renewed — renew them before 12-Oct.
4. **K4 — the switch** of `order.source` off the Marg sheet only after K2 is live and the bar (D673) is met three weeks running. S485's tab stays installed and unused until then.
5. **Waits for Fable:** F-737's ruling (a one-supplier purchase print taken as the whole); the chain replacing the calendar on every screen that still says *missing* by weekday (the audit's items 4 … 7, 10, 11, 13 … 15, 21); the next medical-PC kit (the cutter's column rule — F-734's root; one capture second per text; a re-export not dropped — item 24; *overtaken* across Excel and text); rungs 4b … 4e, 4f after count #1, rung 5, P4/P5.
6. **A person's, named only:** the two days of the chain's gap (08-Sep, 09-Sep — one sale bill and one credit note number missing) exported again in Marg; Darpan's phone signed up for alerts (his 09:30 notice reaches nothing until then).
7. **Still open from earlier closes:** F-708 with F-702; F-701; the PDF at `_scratch\S454_BILL_REGISTER\view\sheet_p1c.pdf` on the PC (never published; to remove); F-717 (written into S486 Part A, parked); F-719 / F-727 (the 22 renames close the orthotic families; DOLOGESIC SP is a merge in Marg); Amir's Stage C after B.

**Left on the server, scratch only:** `/tmp/s482kit`, `/tmp/s482probe`, `/tmp/s483kit`, `/tmp/s483probe`, `/tmp/s484kit`, `/tmp/s484probe`.

**Held:** S438_COUNT_BOOK (the owner's word).

**For the parent, one line each:** `order.source` has a third value `darpan`, and `claude_code_briefs/DUTY_MAP.json` is v7 (two new duties: `shavez.bill_chain_gap`, `darpan.order_review`) · the finance upload route should take an EMPTY sale day as a day with no bills (F-731; manojz no longer sends it) · the `finance_app.py` hops 56eb421b → 47a83382 (S476) → ef1382d2 (S481) and `portal.py` d9b7685f → 10a675e7 (S481) are yours to write — no kit of this session touched either · `finance.db` has two new tables, `mi_bill_chain` and `order_darpan_edit` · `D:\Downloads\margsync\PUSH_STOCK_DAILY.bat` now runs `push_expected.py` from the published folder `deploy_kits\S480_MARG_TEXT_READERS\` in the PC clone — that folder is a live dependency, never pruned · `/root/finance/spine/orders/` into the state backup (still owed from S285).

**Brief:** `S295_BUILD_BRIEF.md`. **Book:** `SANJEEVNI_SYSTEM_BOOK_v1_12_S295.md`.

## §3 · Files

**Canon:** Register v5.132 · Archive v1.129 · Fault v2.117 · this Runbook v212 · `START_HERE_SESSION_294.md` · `S293_BUILD_BRIEF.md` · `live_pins_S293close.txt` · `S293_CLOSE_REPORT.md`. **At the S285 close (the Sanjeevni chat), on top of these:** Register v5.133 · Archive v1.130 · Fault v2.118 · this Runbook v213 · `START_HERE_SESSION_295.md` (the Sanjeevni chat's) · `S285_BUILD_BRIEF.md` · `live_pins_S285close.txt` · `SANJEEVNI_SYSTEM_BOOK_v1_11_S285.md` (supersedes v1.10). **At the S295 close (the Sanjeevni chat), on top of these:** Register v5.134 · Archive v1.131 · Fault v2.119 · this Runbook v214 · `START_HERE_SESSION_296.md` (the Sanjeevni chat's) · `S295_BUILD_BRIEF.md` · `live_pins_S295close.txt` · `SANJEEVNI_SYSTEM_BOOK_v1_12_S295.md` (supersedes v1.11). **At the S294 close (the parent), on top of these:** Register v5.135 · Archive v1.132 · Fault v2.120 · this Runbook v215 · `START_HERE_SESSION_297.md` (the parent's) · `S294_BUILD_BRIEF.md` · `live_pins_S294close.txt` · `END_OF_SESSION_PROMPT_v17.md` (the routine from this close on) · `S294_CLOSE_REPORT.md`.

**Kits — the Sanjeevni chat (02 → 04-Oct):** `deploy_kits/S446_AMIR_STAGES_BILLS` · `S452_AMIR_PANEL_FIXES` · `S454_BILL_REGISTER` (folders P1 … P5, P4C; P4B kept as not delivered) · `S470_ORDER_ON_SPINE`; briefs and reports in `claude_code_briefs\` (`S454_BILL_REGISTER.md` d54d8c4d, `REPORT_S454.md` 898a05d2, `S470_ORDER_ON_SPINE.md` d1732c36, `REPORT_S470.md` 1ec791f4). Its papers: the Sanjeevni project's `claude/S285_*.md` and `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S285\` (the open findings, the ordering relook with its scripts, the generation analysis, the apply-lead proofs, the S470 brief, this close's files).

**Kits — the Sanjeevni chat (04 → 05-Oct, S295):** `deploy_kits/S480_MARG_TEXT_READERS` (a live dependency of manojz's `PUSH_STOCK_DAILY.bat`) · `S482_BILL_CHAIN` · `S483_SPINE_READS_TEXT` (built, not installed) · `S484_SPINE_BILL_TIES` · `S485_DARPAN_ORDER_TAB`; briefs and reports in `claude_code_briefs\` (`S480_MARG_TEXT_READERS.md` 39359a3c, `REPORT_S480.md` ed841814 · `S482_BILL_CHAIN.md` 7a61f8a8, `REPORT_S482.md` 65ac8e63 · `S483_SPINE_READS_TEXT.md` b576e802, `REPORT_S483.md` bda8022c · `S484_SPINE_BILL_TIES.md` 93765bcf, `REPORT_S484.md` 1628d78a · `S485_DARPAN_ORDER_TAB.md` 37af2209, `REPORT_S485.md` b047b522 · `S486_BUYING_MODEL.md` 774e227f — PARKED, with `S486_replay\`); `DUTY_MAP.json` v7 1595520d. Its papers: the Sanjeevni project's `claude/S295_*.md` and `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S295\` (the text-readers analysis, the renames checked, the calendar-glitch audit, the order-model replay with its scripts, the pending builds, the briefs and their drafts, the Darpan mock, this close's files).

**Kits of the parent's S293 (all in `deploy_kits/`):** `S471_PACKS_SEPTEMBER` · `S472_MAHINE_KA_KAAM` · `S473_PHONE_KITS` (+ `PC_KITS/macrodroid/{foldphone,receptionmobile}/`) · `S474_FINANCE_TIDY` · `S475_YES_INTEREST_ROW`; `GAS_CURRENT/PersonalJanitor/Bank_Statement_Relay.gs` and `GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs` as placed. Each kit's README carries its own undo line.

**Kits of the parent's S294 (all in `deploy_kits/`):** `S476_STATEMENT_WATCH` · `S477_PC_KITS_REHEARSAL` (manojz) · `S478_MANOJZ_SETUP_PYTHON` (+ `PC_KITS/manojz/kit.zip` repacked) · `S479_YES_MONTHLY_READER` · `S481_COMMAND_CONSOLE` · `S487_AAJ_KA_KAAM`. Each kit's README carries its own undo line. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S294\` (the Phase 0 note, the Monday checks, the duties analysis, the work note, each kit's build folder with its walk maker, negative controls and rehearsal logs).

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S293\` (the Phase 0 note, the whole-read result, the plan brief, the bundle copies read, the kits' build folders, the close's assembly pieces). The raw phone exports: `D:\Downloads\margsync\_config\macrodroid\` (keys inside; never the repository).

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). **Earned at S294:** when he stops a build, it stops at once and he is shown what he asked about, in one line; **a new screen for staff is installed switched off and shown to him first** — he turns it on; **nothing stale is put in front of a person as theirs** (D679's floor); a figure for him is read on the page he will read it on; a refused publish is cleared in minutes and said plainly as the assistant's miss. Carried from v212: analysis first when he says so, then *"take my yes"* — the whole plan, no second round; a statement never passes through the staff-readable mailbox; the accountants get the pack, not the mail; a yes/no question gets one word; an explanation is short and in his words; a category he has not finalised is not guessed; credentials, sign-ins, passwords on his pages and Apps Script authorisations are his hands; reception-PC work at 08:30.

## §5 · Read first

Parent: `START_HERE_SESSION_297.md` → `S294_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`. Sanjeevni: `START_HERE_SESSION_296.md` → `S295_BUILD_BRIEF.md` → `claude/S295_PENDING_BUILDS_05OCT.md` → `claude/S295_ORDER_MODEL_REPLAY.md` (before any word on S486).

*v212 · S293 close · 04-Oct-2026.*

*v213 · S285 close (the Sanjeevni chat) · 04-Oct-2026 — §2B, §3, §5.*

*v214 · S295 close (the Sanjeevni chat) · 05-Oct-2026 — §2B rewritten; §3 and §5 extended.*

*v215 · S294 close (the parent) · 06-Oct-2026 — §0, §1, §1E, §2A, §4, §5 rewritten; §1A and §1D brought up to date; §2B the Sanjeevni chat's, unchanged.*
