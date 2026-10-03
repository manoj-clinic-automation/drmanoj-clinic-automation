# HANDOFF RUNBOOK — v211 — S292 close (the parent), 03-Oct-2026

*Supersedes v210 (the parent's S291 close). For the next parent chat (session 293 if still free on the board — it is not reserved). §1A is carried from v210 with this session's additions. §1B is rewritten: the Docterz reports now come by the server road. §2B is the Sanjeevni chat's own backlog, carried whole from v210 with one more dated note.*

## §0 · What happened (03-Oct, 10:20 → the evening, one sitting)

Fourteen kits, S456 … S469, all live or placed; every publish verified. In the owner's order:

- **How current the reception PC's Windows is, on the health page** (S456, F-700's remedy): `reception_door.py` gained the row; agent S456.1 is in the living kit and in `kit.zip`. **The agent on that PC is still S453.1** — job j42 is prepared, unsigned, for 08:30 on a clinic day. The Wi-Fi driver line is in `README_REINSTALL.txt` (A.1a).
- **The Docterz reports by the server road** (S457, F-697 closed): two signed read doors on the server; `docterz_fetch.py` and one line in `DOCTERZ_PICKUP.bat` on manojz, placed by the assistant. Proven by the scheduled task's own pass at 11:35:02. **His evening copy line is retired.** The first real evening is read at the next open.
- **Two more PC kits and their buttons** (S458 Medical PC, S459 manojz, S460 the page): three buttons on *Clinic PCs*. **Neither new setup has been rehearsed on Windows; neither new button is pressed before that.** manojz's own state now goes to the SSD every night (`pc_state_backup.py`, step 2b of `NIGHTLY.bat`; F-705) — the first copy was taken on the day.
- **The finance app** (S461, S462, S463, S468, S469): four tidy-ups from the S291 whole read; a salary advance reaches the Staff Ledger once (F-706); the checker's figures answer the checker (F-707), and the clinic tile and exceptions answer a non-checker only what reception's page reads; the self-test no longer writes into any live folder. **D671:** the negative-cash check on save is deliberately left as it is. The Marg apply-abort lead went to the Sanjeevni chat.
- **D664 built in three slices at his word "build."** (S464 … S467): the clinic papers to sort with a suggestion, three groups, the month by group; one purchase, one PDF, with an undo; *Keep the warranty* on a Dr MK expense paper, his card on *Renewals & warranties*, and the Renewals row of the health page. 30 real papers are on the list. `/api/due` untouched — nothing goes out on WhatsApp.
- **Faults of my own, on the record:** S464's walk was red on the box (F-709); S464's supplier rule never matched its own supplier (F-710); a read-only report said an advance was reversed when it was not (F-714) — corrected and told to him in the same hour.
- Five server files changed; **DECLARED-PENDING 5**. `finance_app.py` (7 kits since its whole read) and `asset_register.py` (6) are **over the drift line**.

## §1 · Mental models

1. **A walk is hermetic by construction** (F-709): every store the code under test can reach is named and pointed at scratch. "Green offline" met a box that has a finance database.
2. **A rule is walked with every value it names** (F-710), and **a report that names a state is walked with a row that is nearly that state** (F-714).
3. **Before a report's word is repeated to the owner, the screen it speaks of is read** (F-714). That is what caught it.
4. **A loop that posts to another store validates everything first, then posts** (F-706).
5. **A role gate on the page is not a role gate on the data** (F-707, F-127's sentence again).
6. **The gate is run as PUBLISH runs it** — `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`. His publish was refused once, rightly, because my own check had run in another mode.
7. **A made-up secret in a walk is made at run time**, never written as a literal — the gate cannot tell a made-up token from a real one, and should not have to.
8. **The reinstall question is "what would not come back"**, asked of the machine itself (F-705).
9. **A shared counter that only grows is trimmed on a schedule** (F-703).
10. **With the build lock held by the other chat, build and walk; publish together when it is free.** His words.
11. Carried from v210: the name of a network is taken from a screen that is on it · a step on a screen is given to him only after that screen has been read · when one half of a chain moves, the walk runs to the screen he reads · a rehearsal of a long-lived process sends its output to NUL (F-698) · the server relays, the PC decides (D661) · read `whoami` before an owner-only press · what his word closed is not raised again (the 25-Sep technician, AnyDesk and UltraViewer, passwords, the Windows activation; no scan and no exclusion change on that PC) · the build lock binds every installer (F-694, now in every parent installer) · patient files never pass through the assistant's workspace (D656).

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

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **First work, the maintenance pass (two files over the line):** read `finance_app.py` and `asset_register.py` whole from the 04-Oct 01:35 bundle — unless he waives it in one line. In the same pass hold the **five DECLARED-PENDING pins** against that bundle and state the three counts.
3. **Read at the open, both mine:** `D:\Downloads\_kbtools\PC_STATE_BACKUP_LATEST.txt` (the first scheduled run of step 2b — it did not exist at this close) and the first real Docterz evening in `D:\Downloads\DocterzArchive\_server_fetch_last.txt` against his portal's Day Revenue.
4. **08:30 on a clinic day (Monday 05-Oct):** sign and send j42, then j43 (§1A). Then the health row *Reception PC* shows Windows' build and last update by itself.
5. **Rehearse both new PC setups in a scratch folder on Windows before either new button is pressed** — `deploy_kits/S458_MEDICAL_PC_KIT/` and `deploy_kits/S459_MANOJZ_PC_KIT/` (each has its own offline test; neither has met Windows). The Medical PC's with the Sanjeevni side.
6. **A full `--selftest` of `finance_app.py` on a scratch copy** — S468's change is proven by the self-test's first block only.
7. **`END_OF_SESSION_PROMPT` v17:** one line — the size of both board documents is read at every close (F-703). Owed.
8. **Small, by a job, on or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC; tell him in one line.
9. **Left on the box, counted:** 61 test scans in `/root/finance/finance_scans.test_scans_set_aside_S468` (not data; may be deleted at his OK) · one old self-test file in `yesbank_statements`.
10. **F-704 is the Sanjeevni chat's:** a retired file on the Medical PC (and its mirror on manojz) carries two real numbers with names. On the board for it. Not raised with him.
11. **His, told once, not chased:** the reception PC's cabled port (another cable or socket) · that PC's Windows (F-700) · "Connect automatically" for the clinic Wi-Fi on that PC · the clinic / MK expense split · the follow-up tracker on the server (C·2; less pressing now that F-697 is closed).
12. **Optional:** a `listener Default IPv6` on port 80 if a certificate renewal ever stumbles (good to 08-Dec-2026); `/root/finance/ipv6_facts_s455.json` may go.
13. **Waiting on his word ("later"):** contacts steps 3–5 (his workbook) · the mail flood · the portal tiles (after the pharmacy move) · the "other works" for Tailscale.
14. **Handed on by the Sanjeevni chat's duty map:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
15. **Open, not urgent:** F-243 `clinic_users.json` in no store.
16. **Held at his word:** the Callback Tracker move (D634).

The living list: `claude/S288_PENDING_LIST.md` (brought current at this close).

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

## §3 · Files

**Canon:** Register v5.131 · Archive v1.128 · Fault v2.116 · this Runbook v211 · `START_HERE_SESSION_293.md` · `S292_BUILD_BRIEF.md` · `live_pins_S292close.txt` · `S292_CLOSE_REPORT.md`; the Sanjeevni side's `S283_BUILD_BRIEF.md`, `SANJEEVNI_SYSTEM_BOOK_v1_10_S283.md`.

**Kits this session (all in `deploy_kits/`):** `S456_WINDOWS_CURRENCY` · `S457_DOCTERZ_SERVER_PATH` · `S458_MEDICAL_PC_KIT` · `S459_MANOJZ_PC_KIT` · `S460_CLINIC_PCS_TWO_MORE` · `S461_FINANCE_TIDY` · `S462_ADVANCE_POST_ONCE` · `S463_ROLE_LOCKS` · `S464_CLINIC_PAPERS` · `S465_PAPERS_JOIN` · `S466_EXPENSE_WARRANTY` · `S467_WARRANTY_ON_HEALTH` · `S468_FINANCE_SMALLS` · `S469_CLINIC_TILE_FIELDS` · the living kit `S448_RECEPTION_AGENT` and what the page serves, `PC_KITS/` (reception, medical, manojz). Each kit's README carries its own undo line.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/RECEPTION_PC_WORK.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S292\` (the D664 plan with his answer on the expense split; the build folders; the unsigned jobs).

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: **a yes/no question gets one word**; an explanation is short and in his words (*"tell me each briefly"*); a category he has not finalised is not guessed; when the other chat holds the build lock, the work goes on and the publish waits — together. Carried: reception-PC work at 08:30; a list for him is short; credentials, sign-ins and any system change on a PC are his hands.

## §5 · Read first

`START_HERE_SESSION_293.md` → `S292_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`.

*v211 · S292 close · 03-Oct-2026.*
