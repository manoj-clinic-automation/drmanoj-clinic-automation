# HANDOFF RUNBOOK — v213 — S285 close (the Sanjeevni chat), 04-Oct-2026, on top of the S293 close (the parent), 04-Oct morning

*Supersedes v212 (the parent's S293 close). v212's text stands whole — §0, §1, §1A … §1D, §2A and §4 are the parent's, unchanged (the parent's S294 is open at this close and rewrites them at its own); **§2B is rewritten here by the Sanjeevni chat's S285 close**, §3 and §5 name both closes' files. For the next parent chat (294, open; 296 after it) and the next Sanjeevni chat (**295, reserved on the board at this close**).*

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

## §2B · The Sanjeevni chat's backlog — rewritten at its S285 close (04-Oct-2026, 16:xx IST)

*Supersedes the §2B carried since the S283 close and the five dated notes the parent added to it. The next Sanjeevni chat is **session 295 (reserved on the board at this close)**; it starts from `START_HERE_SESSION_295.md`, then `S285_BUILD_BRIEF.md`, then `claude/S285_NEXT_BUILD_PLAN.md` (the plan the owner asked for — "plan the next build in the fresh chat of this project").*

**What happened (02 → 04-Oct):** S446 and S452 went live on 02-Oct (Amir's staged count, his panel's fixes); **S454_BILL_REGISTER** went live in parts across 03-Oct and was finished on 04-Oct 13:23 by its corrected watcher P4C (the register of a month's bills with their papers, D662; reception's one-task screen and the order from Darpan's Marg sheet, D665/D666; the count-carried shelf figure, D667; the printed sheet, the reception phone's messages, the owner's Items check and learnt item names, the medical PC's refusal note). **S470_ORDER_ON_SPINE** went live 04-Oct 15:04 — the ordering engine reads the spine (rung 4a finished), its constants are settings, the nightly rehearsal scores the list the engine really made (F-718), one score line a week on the owner's card from the night of 05-Oct. The Marg apply lead (F-716) was proven here and repaired by the parent (S474). The S283 POST-CLOSE's canon lines (D662 … D670, F-686 … F-713) are written at this close for the first time.

**Mental models earned:**

- the generator reads the spine, or it is not the designed system (rung 4a; S470);
- an engine is judged against what was bought and what ran out, never against one other list (F-696 re-read; D673);
- a counter day is read as it happens — the owner's "stock report" was a valuation, Amir's "both became zero" was half right by Marg's own closing;
- an answer given on one person's page lands on the page of the person who acts on it (F-726);
- a kit packed for another machine is read in full before its delivery hour (F-715);
- a departure from the design is written down the day it is found (F-719, F-727).

**In order:**

1. **The morning of 05-Oct, read only:** the sale export → the 04-10 expected feed → *"Orthotic: sab sahi ✓"* on Amir's card and the 22 renames open (Stage B). If the proof names a wrong item, read the voucher lines against Marg's 10:22 closing of 04-Oct first (one line was voided by the owner; BAMBOO M's −1 stands).
2. **The six S470 pins against the 05-Oct 01:35 bundle** (Register §S285, DECLARED-PENDING); the first `orders/order_score_latest.json` after the night of 05-Oct; the card's weekly line.
3. **The next kit — the brief is not written** (`claude/S285_NEXT_BUILD_PLAN.md` is the plan): text readers for every Marg report the shop exports (17 types, 20 signature shapes; readers exist for the sale, the closing stock and the order sheet; samples captured as refused on 04-Oct: purchase bill-wise, supplier/item-wise, salt-wise, category-wise; the owner exports the rest from his copy block) · F-726 (an answered salt moves to Amir's sheet; the Excel header; the page says which name it could not find) · F-717 (one rollback) · a learnt item name struck · *overtaken* judged on a same-kind Excel export too · the printed sheet's small remarks · `shelf_figure.py` onto `spine_read` · the five constants still inside `plan_line`.
4. **K2 — the buying model (D672),** its own kit number when its brief is written, after the first weekly score: a review interval per supplier from its bills, each medicine's level and usual lot from its own history, scheme included; the owner's settings as overrides; a rising or new medicine seen in its first week; the 39 *no supplier* medicines (purchases before April — the owner's word; LEUKOCREPE ordered this year, to check against the bills); ROSIKA FORTE's missing Mannat bill.
5. **K3 — Darpan's screen** (the system's list with *add a medicine* and *not needed*), mock first for the owner and Darpan. **K4 — the switch** of `order.source` when the bar (D673) is met three weeks running.
6. **The spine's own kit:** F-727 (12 keys twice in `sp_item`), F-719 (the 20-letter key) as a recorded departure; the remaining rungs 4b–4f (`S283_SPINE_READINESS_27SEP.md`).
7. **Still open from S283:** F-708 (the phone's blind *sent*) with F-702; F-701 (the medical agent's compile-only install); the PDF with the phone book's numbers at `_scratch\S454_BILL_REGISTER\view\sheet_p1c.pdf` on the PC (never published; to remove); Darpan shown once how to save the order report as text; Amir's Stage C after B.

**Held:** S438_COUNT_BOOK (the owner's word).

**For the parent, one line each:** `/root/finance/spine/orders/` into the state backup (S470 writes there nightly) · F-712 is the reader's (two bills in one scan; `asset_register.py`) · F-704 (`marg_report.py`'s two real numbers) stays with the Sanjeevni chat.

**Brief:** `S285_BUILD_BRIEF.md`. **Book:** `SANJEEVNI_SYSTEM_BOOK_v1_11_S285.md`.

## §3 · Files

**Canon:** Register v5.132 · Archive v1.129 · Fault v2.117 · this Runbook v212 · `START_HERE_SESSION_294.md` · `S293_BUILD_BRIEF.md` · `live_pins_S293close.txt` · `S293_CLOSE_REPORT.md`. **At the S285 close (the Sanjeevni chat), on top of these:** Register v5.133 · Archive v1.130 · Fault v2.118 · this Runbook v213 · `START_HERE_SESSION_295.md` (the Sanjeevni chat's) · `S285_BUILD_BRIEF.md` · `live_pins_S285close.txt` · `SANJEEVNI_SYSTEM_BOOK_v1_11_S285.md` (supersedes v1.10).

**Kits — the Sanjeevni chat (02 → 04-Oct):** `deploy_kits/S446_AMIR_STAGES_BILLS` · `S452_AMIR_PANEL_FIXES` · `S454_BILL_REGISTER` (folders P1 … P5, P4C; P4B kept as not delivered) · `S470_ORDER_ON_SPINE`; briefs and reports in `claude_code_briefs\` (`S454_BILL_REGISTER.md` d54d8c4d, `REPORT_S454.md` 898a05d2, `S470_ORDER_ON_SPINE.md` d1732c36, `REPORT_S470.md` 1ec791f4). Its papers: the Sanjeevni project's `claude/S285_*.md` and `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S285\` (the open findings, the ordering relook with its scripts, the generation analysis, the apply-lead proofs, the S470 brief, this close's files).

**Kits this session (all in `deploy_kits/`):** `S471_PACKS_SEPTEMBER` · `S472_MAHINE_KA_KAAM` · `S473_PHONE_KITS` (+ `PC_KITS/macrodroid/{foldphone,receptionmobile}/`) · `S474_FINANCE_TIDY` · `S475_YES_INTEREST_ROW`; `GAS_CURRENT/PersonalJanitor/Bank_Statement_Relay.gs` and `GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs` as placed. Each kit's README carries its own undo line.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S293\` (the Phase 0 note, the whole-read result, the plan brief, the bundle copies read, the kits' build folders, the close's assembly pieces). The raw phone exports: `D:\Downloads\margsync\_config\macrodroid\` (keys inside; never the repository).

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: **analysis first when he says so, then "take my yes" — the whole plan, no second round**; **a statement never passes through the staff-readable mailbox**; **the accountants get the pack, not the mail**; **a refused publish is cleared in the kit's own breath** (F-722). Carried: a yes/no question gets one word; an explanation is short and in his words; a category he has not finalised is not guessed; credentials, sign-ins, passwords on his pages and Apps Script authorisations are his hands; reception-PC work at 08:30.

## §5 · Read first

Parent: `START_HERE_SESSION_294.md` → `S293_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`. Sanjeevni: `START_HERE_SESSION_295.md` → `S285_BUILD_BRIEF.md` → `claude/S285_NEXT_BUILD_PLAN.md` → `REPORT_S470.md`.

*v212 · S293 close · 04-Oct-2026.*
