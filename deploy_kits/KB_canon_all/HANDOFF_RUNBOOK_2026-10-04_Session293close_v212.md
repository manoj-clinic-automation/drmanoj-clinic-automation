# HANDOFF RUNBOOK — v212 — S293 close (the parent), 04-Oct-2026

*Supersedes v211 (the parent's S292 close). For the next parent chat (session 294 if still free on the board — it is not reserved; 285 is the Sanjeevni chat's, open at this close). §1A, §1B and §1C are carried whole from v211. §1D is new: the statement road. §2B is the Sanjeevni chat's own backlog, carried whole from v211 with one more dated note.*

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

## §2B · The Sanjeevni chat's backlog — carried whole from v210 (its S283 close, 02-Oct)

*Dated note, 03-Oct, by the parent's S290 close: since this text was written S446_AMIR_STAGES_BILLS went live (02-Oct 06:15) and S452_AMIR_PANEL_FIXES went live (23:51); S454_BILL_REGISTER is written, not built, at the owner's word. The board's `_claude_status.sanjeevni` and `claude/S283_POSTCLOSE_HANDOFF.md` are current; the Sanjeevni close (session 285) rewrites this section.*

*Dated note, 03-Oct, by the parent's S291 close: the Sanjeevni chat is still in its S283 POST-CLOSE; since the note above it has taken D662 … D667, F-690, F-691, F-695, F-696 and kit S454 on the board. `S454_BILL_REGISTER` is a brief on the PC, on hold and re-opened more than once at the owner's word — read the board's newest Sanjeevni line before acting on it; nothing of it is built. D664 is his ruling for the parent's backlog (§2A item 7).*

*Dated note, 03-Oct evening, by the parent's S292 close: the Sanjeevni chat is still in its S283 POST-CLOSE and worked through the day beside this session (its Claude Code build held the build lock for most of the afternoon). **`S454_BILL_REGISTER` parts 1, 1B, 1C, 1D, 2 and 3 are LIVE** (HEAD `aa619298` at 18:21); the reception phone is set up for the supplier messages; it took D668, D669, D670 (reversed by the owner's later word), F-701, F-702, F-708 and F-711 … F-713. Its pins are DECLARED-PENDING on the board (`_claude_status.sanjeevni`). It touched no parent file today. **From the parent to it:** F-704 (above, §2A item 10) and the Marg apply-abort lead of the S291 whole read. Read the board's newest Sanjeevni line before acting on anything here.*

**What happened (25-Sep → 02-Oct):** 26 kits went live through Claude Code (D617):

- S399, S400, S402–S412, S414, S417, S418, S427, S428, S430–S432, S436, S437, S439, S440 and S444;
- of these, S408, S409, S411 and S412 are parent-owned and were built here on the owner's word;
- S444 moved three parent files, declared: `clinic_sso.py`, `portal.py`, `tile_grants.json`;
- S397 went onto the medical PC.

The 06-Sep count was closed by the owner on 27-Sep. S438 is HELD. S444 was built from an earlier text of its brief (F-679); the remainder is S446, written and waiting for the owner's line to Claude Code.

**Mental models earned:**

- a file handed to another builder is confirmed by its hash where it lands, and its report is read against the brief's section list (F-679);
- every duty is on the person's own home, and the staff-eye walk is the test of done (D648);
- an identity is normalised once where it enters (F-669);
- a refusal is a message to a person (F-674);
- open work is listed by state, never by "this month" (F-673, F-680);
- one figure has one calculation (F-641).

**In order:**

1. **S446_AMIR_STAGES_BILLS** — the owner's one line; then REPORT_S446 read against §3.1 … §3.5.
2. **The staff-eye walk, live**, for S444 and S446.
3. **Stage A → B → C of D649:**
   - Stage A: 7 orthotic vouchers, then verified;
   - Stage B: 22 renames, then verified, then live orthotic ordering;
   - Stage C: 30 medicine vouchers, 5 per visit.
4. **The 18 supplier messages** not leaving the reception phone since 26-Sep.
5. **The *Medicine bills* scan home**, after the staff's feedback on the walkthrough mock.
6. **The Marg purchase import**, after one photo of Marg's import screen.
7. **The spine rungs 4a–4f**, one kit each (`S283_SPINE_READINESS_27SEP.md`).
8. **The count PDFs spec** (`S283_COUNT_SHEET_AND_STATEMENT_PDF_SPEC.md`), carried into S438 when the owner releases it.

**Held:** S438_COUNT_BOOK.

**Brief:** `S283_BUILD_BRIEF.md`.

*Fifth dated note, 04-Oct, by the parent's S293 close: the Sanjeevni chat opened session 285 at 05:10 04-Oct (on manojz, beside the parent); it proved F-716, which the parent repaired the same morning (S474 — `finance_ingest.py`, `finance_returns.py`, `marg_backfill.py`, `finance_app.py` moved); it took F-715 … F-719, D672, D673 and kit S470_ORDER_ON_SPINE (PLANNED, all its own files); P4B's watcher is not delivered before 13:00 IST 04-Oct. The parent moved `packs.py` again (S471, S472 → `6099b525`), S452's edit kept. Thirteen of its S454 pins differ from the parent's S292 list (its build moved them after the list was cut) — its close re-pins them from the 04-Oct bundle.*

## §3 · Files

**Canon:** Register v5.132 · Archive v1.129 · Fault v2.117 · this Runbook v212 · `START_HERE_SESSION_294.md` · `S293_BUILD_BRIEF.md` · `live_pins_S293close.txt` · `S293_CLOSE_REPORT.md`; the Sanjeevni side's `S283_BUILD_BRIEF.md`, `SANJEEVNI_SYSTEM_BOOK_v1_10_S283.md`.

**Kits this session (all in `deploy_kits/`):** `S471_PACKS_SEPTEMBER` · `S472_MAHINE_KA_KAAM` · `S473_PHONE_KITS` (+ `PC_KITS/macrodroid/{foldphone,receptionmobile}/`) · `S474_FINANCE_TIDY` · `S475_YES_INTEREST_ROW`; `GAS_CURRENT/PersonalJanitor/Bank_Statement_Relay.gs` and `GAS_CURRENT/UPIReconciliation/Bank_Statement_Filer.gs` as placed. Each kit's README carries its own undo line.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S293\` (the Phase 0 note, the whole-read result, the plan brief, the bundle copies read, the kits' build folders, the close's assembly pieces). The raw phone exports: `D:\Downloads\margsync\_config\macrodroid\` (keys inside; never the repository).

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: **analysis first when he says so, then "take my yes" — the whole plan, no second round**; **a statement never passes through the staff-readable mailbox**; **the accountants get the pack, not the mail**; **a refused publish is cleared in the kit's own breath** (F-722). Carried: a yes/no question gets one word; an explanation is short and in his words; a category he has not finalised is not guessed; credentials, sign-ins, passwords on his pages and Apps Script authorisations are his hands; reception-PC work at 08:30.

## §5 · Read first

`START_HERE_SESSION_294.md` → `S293_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`.

*v212 · S293 close · 04-Oct-2026.*
