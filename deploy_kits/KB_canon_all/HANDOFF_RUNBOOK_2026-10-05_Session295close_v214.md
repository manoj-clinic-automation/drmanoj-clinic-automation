# HANDOFF RUNBOOK — v214 — S295 close (the Sanjeevni chat), 05-Oct-2026, on top of its own S285 close (04-Oct); the parent's sections are v212's, of its S293 close

*Supersedes v213 (the Sanjeevni chat's S285 close). v213's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged since v212 (the parent's S294 is still open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S295 close**, §3 and §5 name this close's files beside the earlier ones. For the next parent chat (294, open; 297 after it) and the next Sanjeevni chat (**296, reserved on the board at this close**).*

*(v213's header, retained:)* Supersedes v212 (the parent's S293 close). v212's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged (the parent's S294 is open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S285 close**, §3 and §5 name both closes' files. For the next parent chat (294, open; 296 after it) and the next Sanjeevni chat (**295, reserved on the board at this close**).

*(v212's header, retained:)* Supersedes v211 (the parent's S292 close). For the next parent chat (session 294 if still free on the board — it is not reserved; 285 is the Sanjeevni chat's, open at this close). §1A, §1B and §1C are carried whole from v211. §1D is new: the statement road. §2B is the Sanjeevni chat's own backlog, carried whole from v211 with one more dated note.

## §0 · What happened (03-Oct 22:17 → 04-Oct late morning, one sitting with a night's gap)

The maintenance pass done, the statement road rebuilt, five kits live; every publish verified. In the owner's order:

- **The §1.5 whole reads** (04-Oct 05:17–05:35, from the 04-Oct 01:35 bundle): `finance_app.py` and `asset_register.py` every line; drift 7 → 0 and 6 → 0; dead 3 and 2 found at the line; every S292 DECLARED-PENDING pin equals the bundle. The three dead blocks of `finance_app.py` were removed the same day (S474).
- **The September statements and the road** (no kit; D674, F-723): his personal Janitor and CC saver scripts had failed since 1-Oct (*Authorization is required*) — the relay was dead and the September statements sat in his personal inbox. The relay now files each statement straight into Drive from his personal account; the clinic-side Filer is retired; the accountants get the pack only; the old forwarded copies left the staff-readable clinic inbox at his yes. His two re-authorisations were his hand. First run after: 12 files at 09:31.
- **The accountant pack** (S471): consecutive cycle-dated ICICI statements stitched to the month; *partial* one word with the next due date; one password per Yes Bank account; row numbers that never repeat; the electricity words; the shelf fetches again at 07:30. **Open, his:** the four Yes Bank passwords (current ×3, HUF); the pack's send.
- **Shavez's *Mahine ka kaam*** (S472): due days on every item, *aaj ka kaam* first, *late* and *N baaki*, a hand-over ticked with a photo, the tile's live line, the owner's section late-only. No WhatsApp nudge — no approved staff template exists.
- **Both phones' MacroDroid setups** (S473; F-721, F-722): two cards on *Clinic PCs & phones*; a press makes the `.mdr` with the live key put in on the server; the templates in the repository carry placeholders and no stored value; the raw exports with keys live in `D:\Downloads\margsync\_config\macrodroid\` only. `.gitignore`'s `*phones*` swallowed the first folder name — renamed `macrodroid`.
- **The finance app** (S474): the dead three removed; **F-716 repaired** — the Marg apply paths commit once per day so their rollback is real; a refused md5 is parsed again.
- **The Yes Bank readers** (S475; F-720 closed): the bank's quarter-end interest row (posted 01-Oct, value date 30-Sep) no longer refuses a true statement; the two refused September rows were given back to the reader and read.
- Twelve server files changed; **DECLARED-PENDING 12**; nothing over the drift line.

## §1 · Mental models

1. **A page tells you where to look; the store tells you what is true** — and **a statement is read in its own bytes before its reader is judged** (F-720: the refusal's reason was the bank's own row, found by decoding the PDF the shelf served).
2. **A refused file is retried when its reader changes** — `process_inbox` never retries on its own; the installer that mends a reader gives the refused rows back (S475 step 7).
3. **An export of a program's configuration is read for every field it carries** (F-721), and **a new path is held against the un-anchored ignore rules before it is named** (F-722).
4. **A job that runs under someone's Google authorisation is watched by what it produces, not by its own failure mail** (F-723). His personal scripts' failure mails reach his personal inbox only.
5. **A store that staff can read is not a road for a bank statement** (D674). The relay goes to Drive; the clinic mailbox is out of the chain.
6. **"Take my yes"** — once he has corrected the plan, build the whole plan; do not come back with a second round of questions.
7. **Two chats, one working copy, one publish:** the Sanjeevni chat's Claude Code publishes sweep the parent's working-tree changes and the parent's sweep theirs; a file the other chat owns is read live before it is touched (packs.py was moved by both within a day — each on the other's pin, declared both ways).
8. **The board's one counter costs a full rewrite per line** (about 166 KB at this close): take numbers and record installs in as few writes as the protocol allows; trim before 200 KB (F-703).
9. Carried from v211: a walk is hermetic by construction (F-709) · a rule is walked with every value it names (F-710) · before a report's word is repeated to the owner, the screen it speaks of is read (F-714) · the gate is run as PUBLISH runs it · a made-up secret in a walk is made at run time · the reinstall question is "what would not come back" (F-705) · read `whoami` before an owner-only press · what his word closed is not raised again · the build lock binds every installer (F-694) · patient files never pass through the assistant's workspace (D656) · a system change on a PC is his hand.

## §1A · How to send a job to the reception PC

**Sign (both doors), in manojz's own shell — the secret never leaves that PC:**

```
cd <folder with the job> && python3 -B $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S448_RECEPTION_AGENT/reception_sign.py sign $HOME/mnt/Downloads/margsync/_config/reception_agent_key.txt <job file>
```

It writes `<IST time>_<job>` and `<IST time>_<job>.sig`. Job folders so far: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S290\reception_jobs\` (j01 … j21) and `…\_EVIDENCE\S291\reception_jobs\` (j22 … j40). Useful ones to copy: `j35_cable_and_wifi_read.py` (the cable and Wi-Fi from Windows' own records), `j33_setup_complete_check.py` (the whole setup), `j40_after_wifi_driver.py` (driver, scans, Windows Update, build).

**The Drive door (the usual road):** stage the stamped job and its `.sig`, copy both into a **fresh** folder under the cloud workspace's outputs, and commit **the job first, then the `.sig`, in two separate calls** to `H:\My Drive\Clinic Data Archive\ToReception\jobs\`. About two minutes later stage `H:\My Drive\Clinic Data Archive\FromReception\results\<stamped name>.out.txt` (a refusal is `<stamped name>.REFUSED.txt`). Those two folders are reached by the file-transfer tools only, not by the shell. A job that restarts the agent loses its own Drive result — read the next job instead.

**The server door:** from the assistant's browser, on any page of the clinic site, `fetch` a `POST` to `/finance/api/reception/jobs/submit` with JSON `{name, job (base64 of the stamped file), sig}`; read with `reception_sign.py read-token` → `POST /finance/api/reception/jobs/read`. Proven from the PC on 03-Oct (j13). Impractical for a job of several kilobytes — the Drive door is the working road. Full text: `deploy_kits/S453_RECEPTION_SERVER_DOOR/README.md`.

**Rules of both doors:** `.ps1`, `.cmd`, `.bat` or `.py`; first comment line `# timeout=NNN` changes the 600 s limit; a name is used once; older than 48 hours refused; runs as user `dell`, not elevated; ask for counts, never listings of patient folders. **A system change on that PC — a driver, a Windows setting — is the owner's hand at the PC, not a job.** **A rehearsal sends the installer's output to NUL and reads `install_log.txt`** (F-698).

**Added at S292:** job folder `…\_EVIDENCE\S292\reception_jobs\` holds j41 (run 03-Oct 10:52 — Windows' own currency, read only) and **j42 and j43, prepared and unsigned**: j42 puts agent S456.1 on that PC (S453.1 → S456.1, from the living kit), j43 reads the result. Sign and send both at **08:30 on a clinic day**, j42 first; a job that restarts the agent loses its own Drive result, so j43 is the read.

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
- **If no statement reaches Drive:** his personal scripts' authorisation has lapsed again (F-723) — the failure mail goes to his personal inbox; ask him for the one re-authorisation (his hand). The shelf's *re-read the shelf inbox* button on the packs page runs a fetch at once.
- **The locked e-statements:** opened by the shelf with the per-account Yes Bank passwords he sets on the packs page (*Statement passwords*, six account rows then three bank-wide); the branch's unlocked copies, when they come, win (a locked twin becomes *duplicate of branch copy*).
- **The hand-over photos** (S472) are under `/root/finance/statements/packs/handover/<month>/` — on the box only until named to the encrypted nightly's list (owed).
- **Undo lines:** each kit's README (`S471_PACKS_SEPTEMBER`, `S475_YES_INTEREST_ROW`); the Filer's trigger is re-made by its `setupStmtFiler()` only by hand, on purpose.

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **The maintenance pass:** hold the twelve DECLARED-PENDING pins against the 05-Oct 01:35 bundle; state the three counts. No file is over the drift line.
3. **Read at the open, mine:** the relay's 05-Oct run and the 07:30 fetch after it — new files in Drive's *Bank Statements / 2026*, the packs page's September cells (13 of 15 at this close).
4. **08:30 on a clinic day (Monday 05-Oct):** sign and send j42, then j43 (§1A).
5. **Rehearse both new PC setups in a scratch folder on Windows before either new button is pressed** — `deploy_kits/S458_MEDICAL_PC_KIT/` and `deploy_kits/S459_MANOJZ_PC_KIT/`.
6. **One small kit:** the hand-over folder into the encrypted nightly's list; the F-723 watch (no statement to Drive for N days) on the packs page and the health page.
7. **A full `--selftest` of `finance_app.py` on a scratch copy** — lead: the old Marg-push checks against S243's auto-apply; `import finance_app as _fa` under `__main__`.
8. **`END_OF_SESSION_PROMPT` v17:** the board-size line (F-703); the Google-authorised-job line (F-723). Owed.
9. **Small, by a job, on or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC; tell him in one line.
10. **Left on the box, counted:** 61 test scans in `/root/finance/finance_scans.test_scans_set_aside_S468` · one old self-test file in `yesbank_statements` · `/root/finance/ipv6_facts_s455.json`.
11. **His, told once, not chased:** the four Yes Bank passwords · the pack's send · the reception PC's cabled port · that PC's Windows (F-700) · "Connect automatically" for the clinic Wi-Fi on that PC · the clinic / MK expense split · the follow-up tracker on the server (C·2).
12. **Waiting on his word ("later"):** contacts steps 3–5 · the mail flood · the portal tiles (after the pharmacy move) · the "other works" for Tailscale.
13. **Handed on by the Sanjeevni chat's duty map:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
14. **Open, not urgent:** F-243 `clinic_users.json` in no store; `asset_register.py`'s two dead items (under the line).
15. **Held at his word:** the Callback Tracker move (D634).

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

**Canon:** Register v5.132 · Archive v1.129 · Fault v2.117 · this Runbook v212 · `START_HERE_SESSION_294.md` · `S293_BUILD_BRIEF.md` · `live_pins_S293close.txt` · `S293_CLOSE_REPORT.md`. **At the S285 close (the Sanjeevni chat), on top of these:** Register v5.133 · Archive v1.130 · Fault v2.118 · this Runbook v213 · `START_HERE_SESSION_295.md` (the Sanjeevni chat's) · `S285_BUILD_BRIEF.md` · `live_pins_S285close.txt` · `SANJEEVNI_SYSTEM_BOOK_v1_11_S285.md` (supersedes v1.10). **At the S295 close (the Sanjeevni chat), on top of these:** Register v5.134 · Archive v1.131 · Fault v2.119 · this Runbook v214 · `START_HERE_SESSION_296.md` (the Sanjeevni chat's) · `S295_BUILD_BRIEF.md` · `live_pins_S295close.txt` · `SANJEEVNI_SYSTEM_BOOK_v1_12_S295.md` (supersedes v1.11).

**Kits — the Sanjeevni chat (02 → 04-Oct):** `deploy_kits/S446_AMIR_STAGES_BILLS` · `S452_AMIR_PANEL_FIXES` · `S454_BILL_REGISTER` (folders P1 … P5, P4C; P4B kept as not delivered) · `S470_ORDER_ON_SPINE`; briefs and reports in `claude_code_briefs\` (`S454_BILL_REGISTER.md` d54d8c4d, `REPORT_S454.md` 898a05d2, `S470_ORDER_ON_SPINE.md` d1732c36, `REPORT_S470.md` 1ec791f4). Its papers: the Sanjeevni project's `claude/S285_*.md` and `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S285\` (the open findings, the ordering relook with its scripts, the generation analysis, the apply-lead proofs, the S470 brief, this close's files).

**Kits — the Sanjeevni chat (04 → 05-Oct, S295):** `deploy_kits/S480_MARG_TEXT_READERS` (a live dependency of manojz's `PUSH_STOCK_DAILY.bat`) · `S482_BILL_CHAIN` · `S483_SPINE_READS_TEXT` (built, not installed) · `S484_SPINE_BILL_TIES` · `S485_DARPAN_ORDER_TAB`; briefs and reports in `claude_code_briefs\` (`S480_MARG_TEXT_READERS.md` 39359a3c, `REPORT_S480.md` ed841814 · `S482_BILL_CHAIN.md` 7a61f8a8, `REPORT_S482.md` 65ac8e63 · `S483_SPINE_READS_TEXT.md` b576e802, `REPORT_S483.md` bda8022c · `S484_SPINE_BILL_TIES.md` 93765bcf, `REPORT_S484.md` 1628d78a · `S485_DARPAN_ORDER_TAB.md` 37af2209, `REPORT_S485.md` b047b522 · `S486_BUYING_MODEL.md` 774e227f — PARKED, with `S486_replay\`); `DUTY_MAP.json` v7 1595520d. Its papers: the Sanjeevni project's `claude/S295_*.md` and `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S295\` (the text-readers analysis, the renames checked, the calendar-glitch audit, the order-model replay with its scripts, the pending builds, the briefs and their drafts, the Darpan mock, this close's files).

**Kits of the parent's S293 (all in `deploy_kits/`):** `S471_PACKS_SEPTEMBER` · `S472_MAHINE_KA_KAAM` · `S473_PHONE_KITS` (+ `PC_KITS/macrodroid/{foldphone,receptionmobile}/`) · `S474_FINANCE_TIDY` · `S475_YES_INTEREST_ROW`; `GAS_CURRENT/PersonalJanitor/Bank_Statement_Relay.gs` and `GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs` as placed. Each kit's README carries its own undo line.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S293\` (the Phase 0 note, the whole-read result, the plan brief, the bundle copies read, the kits' build folders, the close's assembly pieces). The raw phone exports: `D:\Downloads\margsync\_config\macrodroid\` (keys inside; never the repository).

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: **analysis first when he says so, then "take my yes" — the whole plan, no second round**; **a statement never passes through the staff-readable mailbox**; **the accountants get the pack, not the mail**; **a refused publish is cleared in the kit's own breath** (F-722). Carried: a yes/no question gets one word; an explanation is short and in his words; a category he has not finalised is not guessed; credentials, sign-ins, passwords on his pages and Apps Script authorisations are his hands; reception-PC work at 08:30.

## §5 · Read first

Parent: `START_HERE_SESSION_294.md` → `S293_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`. Sanjeevni: `START_HERE_SESSION_296.md` → `S295_BUILD_BRIEF.md` → `claude/S295_PENDING_BUILDS_05OCT.md` → `claude/S295_ORDER_MODEL_REPLAY.md` (before any word on S486).

*v212 · S293 close · 04-Oct-2026.*

*v213 · S285 close (the Sanjeevni chat) · 04-Oct-2026 — §2B, §3, §5.*

*v214 · S295 close (the Sanjeevni chat) · 05-Oct-2026 — §2B rewritten; §3 and §5 extended.*
