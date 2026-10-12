# START HERE — SESSION 311 — written at the S305 close (the parent), 12-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz. Run `START_HERE_PROMPT_v10` (the project's custom instructions) Phase 0 first, then this file. **The work is §0 below — its first build is THE PACK BUILD (D714), the owner's word at the close: *"eos, this build etc in a fresh chat in this project"*. The brief is `S305_BUILD_BRIEF.md`; the build norm is `BUILD_NORM_v1.md` (D704 — binding); the Runbook is v228 (§2A: the order; §1M: what S305 made live and the September pack's figures). The close routine is `END_OF_SESSION_PROMPT_v18.md` — read its first block before the close, not at it.**

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1). **311 is RESERVED for the parent at this close; 310 is the Sanjeevni chat's (open since 18:31 IST 11-Oct); 309 the Scan App chat's (open since 06:32 IST 12-Oct).** Take what the board says and say so in your first line. **Every kit number is claimed on the board before its folder is named (F-831, F-515).** At this close: D715 · F-872 · A-D25 · kit S537 · session 312 next.*

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`. `device_bash` worked through S305; **never run `git` in it (F-511, F-833)** — read `.git/logs/HEAD` and the refs. **A `.gitignore` check is last-match-wins (F-832); it blocks `*.json` — ship as `.json.kit`.** Before the number gate runs in the device shell, set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` (F-810). **`device_commit_files` can upload a cached older copy when a staged path is reused — always stage from a fresh `/mnt/user-data/outputs/<new dir>` and verify the md5 on the PC.***

***Every time you write is read first — from the clock tool, a commit stamp, a file's time or a program's own line (F-791, F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK — v18 moved these here from the close; they are not optional.**

1. **Read the System Board before anything else:** every item document with a `note`, every message with `read:false`. Say in one line how many are waiting. **Remind him of the packs page (name the 25 card shops; type the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S305 close's publish landed** (`.git/logs/HEAD` = `refs/remotes/origin/main`; this close's canon files in the tree; `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count).
3. **What the S305 chat's own 08:15 IST task did on 12-Oct** (`Mon 08:15 IST: follow-up log check, j45, j46`): the F-837 answer (Monday's call list against Saturday's log; if right, S507's short-log rule corrected — a kit), **j45's result** and **j46's result** in `H:\My Drive\Clinic Data Archive\FromReception\results\`. **Read before acting; do not re-sign j45 if its result exists.** If the S305 chat said nothing (it may not have woken), do the three yourself: j45 at 08:30 on a clinic day (Runbook §1A), the job first, then its `.sig`.
4. **The three nightly reports** — exists · clock time · verdict, each. manojz is often off at 03:10; read the clock time, not the date.
5. **The pin list `live_pins_S305close.txt` against the newest bundle (13-Oct 01:35 or later). DECLARED-PENDING at this close: 2** — `/root/attlistener_v2.py` `52b26645…`, `/root/att_source_summary.py` `2aa34b88…` (S535, 06:00:50 IST 12-Oct). The six `/root` files of S522/S525/S527/S529 are equal to the 12-Oct bundle (STEP D's five *mismatches* of 12-Oct were only unnamed rows). The website's two files (`.htaccess` 4eac17e6, `save/index.php` f6496578) are not in any bundle. State the three counts and the pending count.
6. **The punch watch (S535):** `root/finance/punch_sources_summary.json` inside the newest `D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz` — its `verdict`, `addresses_on_punches`, `one_mark_headers`, `punches_csv_rows_without_source_line`. Say it in one line. Step 2 is not before about 19-Oct, and only on a steady ONE MARK with nothing missing.
7. **The SSD mirror listed back** · **the sweep into `_to_delete_S311\`** · **the reduction tranche** with the measured project-knowledge size before and after · **the cold kit — DUE** (this close bumps the Register and the Archive; the last was `COLD_KIT_S304close_2026-10-11.zip`) · **the four numbers** (`packs.py` — a whole read owed before its next patch; `setup_notes.py` 2) · **what no store holds** (the website's `.htaccess` has no off-box copy but its `.bak` and the S534 block) · **the statement road's health row** — and the health page's two rows of 10-Oct: *UPI evidence* (09-Oct, −10,163) and *Cash position* (last count 54+ days) — read each from its store, one line each to him; on

```
https://followup.dr-manoj.in/finance/health
```

**B · THE WORK ITSELF**

8. **THE PACK BUILD (D714; F-867, F-868, F-869) — first.** `packs.py` (368aa68c) read whole first; then one kit:
   - the income sheet: each split by its real parts (Docterz's `Cash: … , Online Payment: …` on the line — the server holds them in `clinic_day_tender`); no "split" lump;
   - *Wallet* counts as a booking only on a **consultation** line carrying a **Razorpay number**; any other *Wallet* is a reception entry error, shown as such and decided against the bank;
   - the portal (Razorpay → Yes Bank) part is the consultation fee only — another line of the same visit is expected in ICICI (F-869; 29-Aug ₹800);
   - the day-by-day check: the ICICI card-machine settlement credited on D+1 against D's Docterz online + card, every disagreeing day listed for reception (September: 9 days exact — 11, 14, 17, 19, 22, 23, 24, 25, 29; ~₹14,700 bank-over across 3–29 Sep; 12 Sep ₹2,950 short) — the walk must reproduce these;
   - the payment digest: one row per charge when a renewal/confirmation mail and a receipt of the same vendor and amount fall within a few days (Apple ₹24,900 and ₹699 in September); labelled *payment papers found in mail — these overlap the card spends*;
   - **show him the new income sheet for September before the install (F-761).** Wallet and the split are also read by `clinic_money.py`, `finance_clinic_day.py`, `clinic_register.py`, `clinic_day_pdf.py` — the kit says which it changes and which it leaves (the Clinic money page is the Sanjeevni chat's neighbour — check the board's PLANNED lines first, D646).
9. **Passports 12 months (D713 (1))** — I told him on 12-Oct it would be done that day; find where the 45-day lead is applied (S513 on the server; Renewal_Nag v3 in his personal Apps Script — change that only at his word, record it in `GAS_CURRENT/PersonalJanitor/` the same hour, D583) and make passports 12 months, everything else unchanged.
10. **The X-ray test shortcut (D713)** — first prove nothing reads the *X-ray test* Drive folder (the server's code, the reception PC's tasks); then a reception job (j47) at 08:30 on a clinic day removes *X-ray test – Shortcut* from the desktop; the folder stays. One line to him after.
11. **The assistant's, in the background:** F-808's loud line for a stale hand-made backup (agent S499.2 — delivered by the kit channel, a person double-clicks at the medical PC, D697) with `verify_medical.py`'s one sentence · F-742 the finance self-test suite · the reception login's Morning match read once (a sub-agent, reads only) · the 148 transcription-only documents.
12. **Ask him once this week:** the follow-up tracker on the server (*"Ask next week"*). Nothing moves until his yes.

**PARKED AT HIS WORD — NOT TO BE RAISED; he raises it:** the staff's WhatsApp alerts made loud (D692 — a topic name is a key: never in the repository, a kit, a page, the board or a chat line) · club C — the mailbox clean-up (D702). **Dropped:** Tailscale (D713). **Held:** the Callback Tracker move (D634); D679's later steps.

**Waiting on his word:** MyOperator's WhatsApp key · the contacts workbook · the mail flood · the portal tiles · kits for Shavez's PC and the lab PC · the WhatsApp appointment message (D693 item 6).

**Owner-side, on his board:** the publish · **the packs page (shops and passwords — remind every session)** · the Marg engineer test-restores Marg's automatic backup · a hand-made pen-drive backup about weekly · what the staff say about their lists and the after-call list · Ranjeet's login (his password) · the reception PC's Windows · the Docterz report export · the arms licence (submit in November).

**For the Scan App chat (its own, on the board):** *"make MK to MK personal if category is not there"* (D713 (2)).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** the technician of 25-Sep, AnyDesk and UltraViewer, passwords, the Windows activation on the reception PC (02-Oct) · the accountants get statements only inside the pack; no statement through the clinic mailbox; the 61 test scans stay (04-Oct) · a panel to waive selected staff's late minutes (06-Oct) · the daily health mails and Daily Clinic Reports in Trash — he deletes them himself (D698) · the accountants do not get his renewals list (D700) · no Docterz patient PDF is in his personal mail (10-Oct) · **his Fold's Contacts notification permission — skipped (12-Oct)** · **no email capture of Razorpay bookings (D714)**.

**THE MODEL (his word of 05-Oct):** *"Either you do with Opus or you pause this task."* If he asks which model is working, say what the session is set to in one line and stop at his word.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami` — the browser profile is shared with the Sanjeevni chat; his personal Google account and GoDaddy are signed in in the built-in pane. **The console's Health line and the personal RENEWALS list can show a personal licence or document number — never repeat it or write it anywhere.**

**The assistant does not type credentials for him.** **A system change on a PC is his hand at that PC, not a job.** **Patient files never pass through the assistant's workspace (D656); a copy of the database is made only under the session's own home and deleted after the read (F-752).** **No person's salary, advance or loan figure goes into the repository (F-31, F-365, F-757).** **An open door is described in the repository only after it is shut (F-773) — the punch listener is still open; its step 2 is described in the kit, its detail stays off the repository until shut.** **The reception job key stays on manojz and is never printed; a job is committed first, then its `.sig`.**

**Before a publish, run the gate as PUBLISH runs it:** `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`. **Walk a kit in the server's time zone too (F-772), from where it is packed (F-776). An edit script builds the new text in memory first (F-792). A read does not write (F-793). A feature whose point is what a phone does is proved on a phone (F-871). A gap between two figures is explained from the rows behind both (F-870).**

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. One line per command; `\cp` past the alias. A server line carries its own pull: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/<KIT>/<installer>.sh`.
4. Token-lean, never at the cost of verification.
5. Plain English, one step at a time, full-file replacements, ALL-CAPS = urgent. IST only.
6. Never print secrets. Patient numbers: none in the repository (F-185).
7. Nothing live rebuilt without his OK; the manual path stays.
8. Sub-agents read screens.
9. Do not hand him diagnostics — ask only for what nobody else can do, in one line.
10. When a screen is wrong, read its code first.
11. Do not hand him a step that is not his.
12. His board carries only what needs him and what he should know; every close keeps its lists current in `board/_page` and answers what he typed there (D684).
13. His own items are deferred unless urgent — **except the packs page, which he asked to be reminded of every session until done (D713).**
14. Never put technical choices to him — decide, say it in one line, proceed.
15. Keep chat short. A list for him is short: five lines, one sentence each.
16. Work on the reception PC is timed for 08:30, when the receptionist is in — except a repair the staff have just asked for.
17. A yes/no question gets one word. An explanation is brief and in his words.
18. Analysis first when he says so (*"do not build or code anything right now"*), then the test he asks for, then the build at his word.
19. A new screen for staff is shown to him first and installed switched off; staff pages are Roman Hinglish; his pages are English.
20. Nothing stale is put in front of a person as theirs (D687). A ticked line is gone from his list.
21. His approvals are few and arrive together (D683). No board line mid-session unless a number is taken or a live file is protected.
22. A page of money shown to him before an install says which settings it was worked on (F-761).
23. A set-up is written so that a new machine can be set up from the card alone (D688).
24. A build he parks stays parked and is not raised again.
25. His hold is honoured to the minute (D695).
26. **A door he wants closed "only if safe" is closed in two steps — record first, refuse only on evidence (D713).**

**THE BUILD NORM (D704) — `BUILD_NORM_v1.md`, binding:** a correction is part of the build (the code heals the data it governs, idempotently, every run); find the real cause first; exact counted edits on md5-pinned live bytes; a walk with made-up rows and a negative control that must go red; the installer's order (gates → pins → rebuild → walk → backups → place → restart only what it touches → health → data step → his words → undo line); rehearsed on a made-up root (green, ALREADY INSTALLED, red-after-placing restores); SUMS, `.gitignore` (last match wins) and the number gate before the publish is named.

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_148_S305close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_145_S305close.md` (§S305; D713 and D714 in full) |
| Fault → Action Register | `Fault_Action_Register_v2_133.md` (§7.67 = F-849, F-855, F-867 … F-871) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-12_Session305close_v228.md` (**§2A the order; §1M what S305 made live and the pack's figures**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S305close.txt` (DECLARED-PENDING 2) |
| build brief | `S305_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D715 · F-872 · A-D25 · kit S537 · session 312 next; 311 RESERVED for the parent; 310 the Sanjeevni chat's, 309 the Scan App chat's, both open** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| The one-button skipped loan month; Sheets 3–4; the slip's negative net (S522) | the staff ledger's Advances page; the salary sheets | live 11-Oct |
| The spine's health leg red as soon as a build fails (S525) | the health page; the hourly collector | live 08:0x 11-Oct |
| The medical PC's setup kit current (S526) | the Clinic PCs page's kit | repacked 11-Oct |
| The five set-up cards (S527, S529) | `https://followup.dr-manoj.in/finance/pcs` | live 11-Oct |
| The pack's Send answers under itself (S529) | `https://followup.dr-manoj.in/finance/packs` | live 11-Oct |
| The save-contact page; the old card address led to it (S529, S534) | `https://drmanojagarwal.com/save/` · `https://save.dr-manoj.in` | live; his Fold opens the page (12-Oct 05:05) |
| The punch listener records who sends each punch (S535, step 1 of 2) | the server; the nightly summary in the code bundle | live 06:00:50 12-Oct |

*Written at the S305 close, 12-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

**Sanjeevni (310, open):** its kits S533 (Amir's page rebuilt) and S536 (Amir's board and D712) — its entry point and backlog are its own (Runbook §2B). **For it, from this close:** `packs.py`, `clinic_money.py`, `finance_clinic_day.py` are the parent's and the pack build may touch the latter two — the parent writes a PLANNED line on the board before it does (D646). **Scan App (309, open):** D713 (2) is on the board for it in his words.
