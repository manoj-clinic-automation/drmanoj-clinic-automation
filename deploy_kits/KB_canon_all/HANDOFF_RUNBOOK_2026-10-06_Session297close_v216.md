# HANDOFF RUNBOOK — v216 — S297 close (the parent), 06-Oct-2026 (the evening), on top of the parent's own S294 close of that morning

*Supersedes v215. **§0, §2A and §5 are rewritten here by the parent's S297 close; §1 has three models added at its head; §1F is new (the salary pages, and the System Board as data); §4 has what was earned at S297; §3 names this close's files.** §1A … §1E are carried whole; **§2B is the Sanjeevni chat's, whole and unchanged since v214** (its session 296 is open at this close and rewrites it at its own). For the next parent chat (**298**, next on the board, not reserved).*

*(v215's header, retained:)* Supersedes v214 (the Sanjeevni chat's S295 close). **§0, §1, §1D (corrected), §1E (new), §2A, §4 and §5 are rewritten here by the parent's S294 close**; §1A has its S292 paragraph brought up to date; §1B and §1C are carried whole; **§2B is the Sanjeevni chat's, whole and unchanged from v214**; §3 names this close's files beside the earlier ones. For the next parent chat (**297**, next on the board, not reserved) and the next Sanjeevni chat (296, reserved).*

*(v214's header, retained:)* Supersedes v213 (the Sanjeevni chat's S285 close). v213's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged since v212 (the parent's S294 is still open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S295 close**, §3 and §5 name this close's files beside the earlier ones. For the next parent chat (294, open; 297 after it) and the next Sanjeevni chat (**296, reserved on the board at this close**).

*(v213's header, retained:)* Supersedes v212 (the parent's S293 close). v212's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged (the parent's S294 is open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S285 close**, §3 and §5 name both closes' files. For the next parent chat (294, open; 296 after it) and the next Sanjeevni chat (**295, reserved on the board at this close**).

*(v212's header, retained:)* Supersedes v211 (the parent's S292 close). For the next parent chat (session 294 if still free on the board — it is not reserved; 285 is the Sanjeevni chat's, open at this close). §1A, §1B and §1C are carried whole from v211. §1D is new: the statement road. §2B is the Sanjeevni chat's own backlog, carried whole from v211 with one more dated note.

## §0 · What happened (06-Oct, one chat, the morning into the evening)

1. **The open:** session 297, claimed late at 08:49 IST because he stopped the ritual for a salary question. One slip of the assistant's own: `git status` in the PC shell left a lock file, moved out at once (F-755).
2. **His six rulings on the staff's *Aaj ka kaam* lists** (a switch per person and per line; the floor at 01-Oct on a line and its page; one line is one job; the order of turning on; September's leftovers) — a mock-up was to be shown first. **Paused at his word before it was begun.** The lists stay live and off.
3. **D681 and D682 — the salary pages.** Advances on Sheet 2 in two tables that never mix, one line per loan; Darpan back on the common sheet, his long-term loan on one private ledger page from April 2026; the amount the workbook added for the skipped April comes off.
4. **`S489_SALARY_LAYOUT` — built, reviewed twice, shown as September's real pages (a 7-page PDF), published `083260e0` at 10:51, installed 11:03 IST, nine of nine green.** `salary_policy.py` `92aecbe3` → `ac603874` (v1.17, a full file); new `loan_pages.json` `b7853638`; one correcting row appended to the staff ledger's data. Read live as the owner at 11:10.
5. **A total that had moved was his:** he had changed the late-charge settings that morning. **September locked by him at 12:21:48 IST on the new pages, and printed.**
6. **Two corrections said to him:** nothing carries a negative net to the next month — it is by hand (F-760); there is no door today to waive selected staff's late minutes or write off a carry. A panel was offered; he closed it: *"nothing more required"*.
7. **D683 — the close made lean** (*"such minor permissions need not be taken every time"*): the board written once, everything else finished first, the open's housekeeping left to the open. Routine v18.
8. **D684 — the System Board rebuilt:** open lines only, his notes quoted back and answered, the lists as data in `board/_page`. Eight notes of his answered — seven of them had waited since 24-Sep (F-762).

**Beside this chat:** the Sanjeevni chat's session 296, open since 06:05 IST — kits S488, S490 and S491, F-753, F-754, F-756, and the four publishes of the afternoon (the last `a0a3b8e6`, 16:51 IST). Its own close writes them; §2B below is its text, unchanged since v214.

## §1 · Mental models

**Added at S297 (the list below is v215's, whole):**

- **A page that must agree with a store is worked back from that store.** The private loan page takes its opening from the ledger on the box and a record that holds months and kinds only; it cannot disagree with the ledger, and the kit holds no person's figure (F-757).
- **On an append-only store the undo is an append** (F-758). A correction is one new row with a tag, a dated backup and a note; it is taken back by a second row.
- **A preview of money pages says which settings it was worked on, and the live page is read again just before he is asked to lock** (F-761). **A sentence printed for staff is a claim about the system — read it in the code first** (F-760).
- **His approvals are few and arrive together** (D683): finish everything that does not prompt, then ask once. **What he types on his board is answered at the next close, on the board** (D684).

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

## §1F · The salary pages and the System Board — where things are since S297

**The salary pages (D681, D682; kit S489).** The engine is `/root/staff_register/salary_policy.py` (v1.17-S489); it is served by `/root/staff_register/staff_register.py`, which this kit did not touch. The month's sheets:

```
https://followup.dr-manoj.in/register/salary
```

and a locked month's frozen sheets:

```
https://followup.dr-manoj.in/register/salary/locked?ym=2026-09
```

- **Sheet 2** has three tables: *this month's advances*, *instalment loans* (one line per person per loan; a group of advances that is one loan is named in `/root/staff_register/loan_pages.json` under *groups*), and one closing line per person.
- **A private loan** is named in `loan_pages.json` under *history* (months before the ledger began: skipped or paid — no figure). Its page opens at a balance **worked back from the ledger**; if the ledger's own adjustment for those months is not the one the record names, the page prints a *Check* note instead of a wrong opening.
- **A slip** is printed only for a person with a running instalment loan (`has_slip`).
- **`loan_pages.json` is made by the kit's `data_s489.py`** (`--write <path>`, `--check <path>`); change the record there and re-run, never by hand on the box.
- **The staff ledger** (`/root/staff_ledger.py`, data `/root/staff_ledger/ledger.jsonl`) is append-only. *Skip* adds a flat amount to a loan; *Defer* is free twice per financial year per person. **A skipped month is not yet one button** — his ruling is owed before the first skip (§2A item 4).
- **The late-charge settings are his** (`salary_policy_settings.json`, changed by him on 06-Oct; an audit file beside it). A sheet worked before a settings change will not match one worked after.
- **Nothing carries a negative net forward** — it is by hand until he asks for the panel.
- **No person's figure goes into the repository** (F-31; it is public, F-365). Tooling that needs real figures lives in `D:\Downloads\ClaudeCowork\02_SESSION_KITS\S297\` and never in `deploy_kits/`.

**The System Board (D684).**

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

- **The lists are one document, `board/_page`** — `yours` (what needs him; `when` = `now`, at most five, or `later`), `told` (what he typed, quoted, with the answer), `tell` (worth knowing, one sentence each), `plan` (the pharmacy build), `stamp`. `END_OF_SESSION_PROMPT_v18.md` A10c has the fields and the close's part.
- **A close changes `board/_page`, not the page.** The page is republished only when its code must change; its source, builder and browser test are in `D:\Downloads\ClaudeCowork\02_SESSION_KITS\S297\system_board_v2\`.
- **His ticks and notes** are item documents `board/<id>` (`done`, `doneAt`, `note`); a message is a document in `messages` (`read`). A note with text and a message with `read:false` show on the page as *Waiting for Claude* — **the open reads them before anything else, and the close answers every one.**
- **The parent owns the Clinic and Personal lines; the Sanjeevni chat owns the Pharmacy lines and `plan`.** Each writes only its own, pinned to the version it read.

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **The open's first work (v18 moved it here):** the three nightly reports · **the pin list against the 07-Oct bundle — this session's two rows (`salary_policy.py` `ac603874`, `loan_pages.json` `b7853638`) are DECLARED-PENDING until then** · the SSD mirror listed back · the sweep · the tranche and the measured project-knowledge size · the cold kit (due: the Register and the Archive bumped twice on 06-Oct) · the four numbers · what no store holds · the statement road's health row. **And the board: every waiting note and message, read first.**
3. **The *Aaj ka kaam* mock-up — PAUSED at his word; his word resumes it.** One person's list and his switch panel, on his six rulings of 06-Oct (a switch per person and per line; the floor at 01-Oct on a line and on its page; one line is one job; the order of turning on; September's leftovers). Nothing is built until he has seen it. Then the kits of D679 in the order he was told: (a) the morning step on punch; (b) stand-ins and *away*; (c) the Docterz-export lock; (d) the attendance month-end sheet flow; later (e) approving inside the console.
4. **His ruling on the skipped month, before Darpan's first skip:** today *Skip* adds the flat amount and *Defer* must be pressed on both long-term lines — one button is a small kit once he says which he means.
5. **From his board (answered there as *on my list*):** a set-up section in his portal for the biometric machine, Hostinger, CyberPanel, SSH and the websites — set-up notes and links to open each, **never a password on a page**; the MyOperator ticket's answer (in the clinic mailbox, 08–10 Sep: regenerating the WhatsApp API token) read and turned into exact steps — the rotation itself needs his credentials.
6. **Small, on the salary pages, older than S489:** Sheet 4 has no total row and no thousands separators; Sheet 3's fine footnote reads oddly while the card fine is zero in settings; the slip's line about a negative net (F-760) is corrected with the next change to `salary_policy.py`.
7. **Offered once, not chased:** a duty-timings page that takes a *from* date; the waiver and negative-carry panel (**closed by him — do not raise it again unless he asks**).
8. **`finance_app.py` stands at drift 4** since its whole read of 04-Oct — a whole read comes before its next patch. `salary_policy.py` 0.
9. **Wording seen live on the console, small:** *N min late* on a first punch far past the usual hour; Bhati's punch does not join a login; Amir on a non-visit day; names in lower case in the fact lines.
10. **The self-test suite's own kit (F-742):** `finance_app.py --selftest` aborts as the box runs and carries 58 stale expectations. Test code only.
11. **Small, by a job, on or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC (the next job number is j44; 08:30 on a clinic day); tell him in one line.
12. **A statement that reaches Drive after 07:30 waits until 05:40 the next day** (F-741). If he wants it sooner, ask once; do not build unasked.
13. **His, told once, not chased (they are on his board):** look at each person's list and tap *Turn on* · the two remaining Yes Bank passwords · the pack's send · Ranjeet's login · the clinic / MK expense split · the follow-up tracker on the server · the reception PC's Windows and its cabled port · the contact groups workbook · the Docterz Clinical Data Report export · the arms licence (renewal in December, to be submitted in November — his correction).
14. **Waiting on his word ("later"):** contacts steps 3–5 · the mail flood · the portal tiles · the "other works" for Tailscale.
15. **Handed on by the duty map, still open:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
16. **Kits owed, not urgent:** Shavez's PC and the lab PC setup kits · the F-712 reader · `asset_register.py`'s two dead items.
17. **Held at his word:** the Callback Tracker move (D634).
18. **Two small folders to delete, his (deletion is off for a session):** `D:\Downloads\_to_delete_S294\` (WHY_SAFE.txt inside) and `D:\dr-manoj-git\_to_delete\` (one empty lock file, F-755).
19. **For the Sanjeevni chat:** from its next close the Pharmacy lines and `plan` in `board/_page` are its own to refresh (v18 A10c) — the plan on the board is still as its S295 close left it; his three pharmacy notes of 24-Sep are quoted on the board as *on my list* and wait for its answer (the old Kedar balance to be closed by an adjustment entry; four appliances to be marked for Amir to correct in Marg; the name-check sheet into Amir's app); the seventeen extra duty lines of `aaj_duties.json` are still offered to `DUTY_MAP.json`.

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

**At the S297 close (the parent), on top of these:** Register v5.136 · Archive v1.133 · Fault v2.121 · this Runbook v216 · `START_HERE_SESSION_298.md` · `S297_BUILD_BRIEF.md` · `S297_CLOSE_REPORT.md` · `live_pins_S297close.txt` · `END_OF_SESSION_PROMPT_v18.md`. **Kit of the parent's S297:** `deploy_kits/S489_SALARY_LAYOUT` (its README carries its own undo line). **On the PC only, never the repository:** `D:\Downloads\ClaudeCowork\02_SESSION_KITS\S297\` (the kit's offline tooling with real figures, zipped; the System Board's source, builder and test) · `03_WORKING_PAPERS\S297\` (September's preview PDF, the brief, the close report, the routine) · `03_WORKING_PAPERS\_EVIDENCE\S297\` (the work note with the figures, the review findings, the board as it was before the rebuild).

## §4 · Rules at the boundary

**Earned at S297:** his approvals are few and arrive together — finish what does not prompt, then ask once; no board line mid-session unless a number is taken or a live file is protected; what he types on his board is answered on his board at the next close; a ticked line is gone from his list, not struck through; a list for him is short — five lines, one sentence each; a salary figure never enters the repository; a preview of money pages says what it was worked on; what he has closed (*"nothing more required"*) is not raised again. *(The text below is v215's, whole.)*

The owner's standing rulings (restated in START_HERE §0). **Earned at S294:** when he stops a build, it stops at once and he is shown what he asked about, in one line; **a new screen for staff is installed switched off and shown to him first** — he turns it on; **nothing stale is put in front of a person as theirs** (D679's floor); a figure for him is read on the page he will read it on; a refused publish is cleared in minutes and said plainly as the assistant's miss. Carried from v212: analysis first when he says so, then *"take my yes"* — the whole plan, no second round; a statement never passes through the staff-readable mailbox; the accountants get the pack, not the mail; a yes/no question gets one word; an explanation is short and in his words; a category he has not finalised is not guessed; credentials, sign-ins, passwords on his pages and Apps Script authorisations are his hands; reception-PC work at 08:30.

## §5 · Read first

Parent: `START_HERE_SESSION_298.md` → `S297_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md` (the *Aaj ka kaam* rulings: `S294_BUILD_BRIEF.md` and Runbook §1E). Sanjeevni: `START_HERE_SESSION_296.md` → `S295_BUILD_BRIEF.md` → `claude/S295_PENDING_BUILDS_05OCT.md` → `claude/S295_ORDER_MODEL_REPLAY.md` (before any word on S486).

*v212 · S293 close · 04-Oct-2026.*

*v213 · S285 close (the Sanjeevni chat) · 04-Oct-2026 — §2B, §3, §5.*

*v214 · S295 close (the Sanjeevni chat) · 05-Oct-2026 — §2B rewritten; §3 and §5 extended.*

*v215 · S294 close (the parent) · 06-Oct-2026 — §0, §1, §1E, §2A, §4, §5 rewritten; §1A and §1D brought up to date; §2B the Sanjeevni chat's, unchanged.*

*v216 · S297 close (the parent) · 06-Oct-2026 — §0, §2A, §5 rewritten; §1 and §4 added to; §1F new; §3 extended; §2B the Sanjeevni chat's, unchanged.*
