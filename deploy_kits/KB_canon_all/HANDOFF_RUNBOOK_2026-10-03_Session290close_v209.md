# HANDOFF RUNBOOK — v209 — S290 close (the parent), 03-Oct-2026

*Supersedes v208 (the parent's S288 close). For the next parent chat (session 291, a fresh chat on manojz). Session 289 (the reception-PC chat) is folded into this close. §2B is the Sanjeevni chat's own backlog, carried whole from v208 with one dated note.*

## §0 · What happened (02 → 03-Oct, the parent and the reception-PC chat)

- **The reception PC has an agent** (session 289, D658, kit `S448_RECEPTION_AGENT`): heartbeat every five minutes, repairs for Google Drive and Chrome's download folder, and jobs that arrive signed. Google Drive runs again there; Tailscale is on; the PC is shared read-only to the owner.
- **It reports straight to the server** (D659, `S449_RECEPTION_UPLOAD`): heartbeat and the two Docterz reports, no Google Drive needed. Both reports of 02-Oct reached the server this way at 21:13.
- **The PC kits are on the server behind the tile *Clinic PCs*** (D660, `S450_CLINIC_PCS_TILE`, `S451_CLINIC_PCS_BUTTON`): one button sets the reception PC up after a Windows reinstall. Rehearsed on that PC: six steps, 41 seconds.
- **A second job door through the server** (D661, `S453_RECEPTION_SERVER_DOOR`): live and proven from the server's side. **The PC's side is not proven** — that night the PC was on the owner's phone hotspot, from which the server cannot be reached (F-692).
- **The owner asked whether the setup was complete; it was not** (F-688, F-689). His word closed the vendor / remote-control / password / activation questions. Done with him at the PC: the firewall run, and a restart test that passed.
- **Every VPS pin of S288 and S290 equals the 03-Oct 01:35 bundle.** DECLARED-PENDING 0.

## §1 · Mental models

1. **The server relays, the PC decides** (D661). A job runs on the reception PC only if that PC's own key list accepts its signature. The signing secret lives on manojz alone and is used only in manojz's own shell.
2. **Two roads are two only where they do not share a failure** (F-692). Drive door: needs Google Drive on that PC. Direct road and server door: need the clinic's own internet (IPv4). Each failed once on a night the other worked.
3. **"Starts by itself" is proven only by a real restart** (F-689).
4. **A check an agent makes is written against what its own account can read** (F-683).
5. **A button is proven by one press through the real front server** (F-684) — and read `/finance/api/whoami` first: the assistant's browser profile is shared with the Sanjeevni chat.
6. **An installer that gives a machine an identity asks which machine it is on** (F-685).
7. **What a trusted vendor did on the owner's machine is told to him once; his word closes it** (F-688). Not to be raised again: the 25-Sep technician, AnyDesk and UltraViewer, passwords, the Windows activation. No Windows Security scan is run on that PC and its exclusions are not changed.
8. **A rule about the shared server binds whoever installs on it** (F-694): the build lock.
9. Carried: patient files travel browser → server, never through the assistant's workspace (D656); a chat reaches one PC — but the reception PC is now reached from manojz by signed jobs.

## §1A · How to send a job to the reception PC

**Sign (both doors), in manojz's own shell — the secret never leaves that PC:**

```
cd <folder with the job> && python3 -B $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S448_RECEPTION_AGENT/reception_sign.py sign $HOME/mnt/Downloads/margsync/_config/reception_agent_key.txt <job file>
```

It writes `<IST time>_<job>` and `<IST time>_<job>.sig`. Job folder used so far: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S290\reception_jobs\` (jobs j01 … j21).

**The Drive door (the usual road):** stage the stamped job and its `.sig`, copy both into a **fresh** folder under the cloud workspace's outputs, and commit **the job first, then the `.sig`** to `H:\My Drive\Clinic Data Archive\ToReception\jobs\`. About two minutes later stage `H:\My Drive\Clinic Data Archive\FromReception\results\<stamped name>.out.txt` (a refusal is `<stamped name>.REFUSED.txt`). Those two folders are reached by the file-transfer tools only, not by the shell. A job can be withdrawn by overwriting its file — the agent then refuses it. A job that restarts the agent loses its own Drive result.

**The server door:** from the assistant's browser, on any page of the clinic site, `fetch` a `POST` to `/finance/api/reception/jobs/submit` with JSON `{name, job (base64 of the stamped file), sig}`. To read: `reception_sign.py read-token <key file> <stamped name>` gives one line of JSON, good for 15 minutes, to `POST` to `/finance/api/reception/jobs/read`. No login is needed. Neither manojz's shell nor the cloud workspace can reach the server; the browser can. Full text: `deploy_kits/S453_RECEPTION_SERVER_DOOR/README.md`.

**Rules of both doors:** `.ps1`, `.cmd`, `.bat` or `.py`; a name is used once; older than 48 hours refused; runs as user `dell`, not elevated (an elevated step needs one "Yes" at that desk); default limit 600 s (`# timeout=900` in a comment line changes it); ask for counts, never listings of patient folders.

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **The reception PC's side of the server door.** Job `20261002T220335_j13_server_door_hello.py` waits in the server's queue until 04-Oct 22:03 and runs when that PC is on the clinic's own internet (its LAN cable was out on 02-Oct night — on his board). A check is scheduled in the S290 chat for 03-Oct 10:20 IST and records on the board as S290 POST-CLOSE; if the board does not show it, read j13 by the server door. If j13 has expired, send a fresh one.
3. **Then, and only then: remove the Claude app from the reception PC by a job, and set `"keep_claude_running": false` in `C:\ClinicAgent\config.json` in the same job** (his instruction). The Claude app was not running after the 02-Oct restart; the agent restarts it while that setting is true.
4. **The maintenance pass: read `finance_app.py` whole** from the newest bundle — drift is at the line (5).
5. **`secure_setup.cmd` into the reinstall kit** (`deploy_kits/S448_RECEPTION_AGENT/`, then `PC_KITS/reception/kit.zip` and `KIT_INFO.txt`), with one line in `README_REINSTALL.txt`. A changed kit reaches the server at the next publish plus any install line.
6. **The build lock in the parent's installer** (F-694), from the next kit.
7. **F-692** — an IPv6 address for the server name. Read the server's network first.
8. **F-693** — the reception PC and the clinic Wi-Fi: read at the desk, in range.
9. **The Medical PC's kit and Dr Manoj's PC's kit for the tile** — each its own rehearsed kit; the Medical PC's with the Sanjeevni side.
10. **Confirm** that the 01:50 encrypted run of 03-Oct carried `ring_outcomes.db` and the 22 Vitals sheets.
11. **`packs.py` was moved by the Sanjeevni chat's S452** (`23fda41a…`) — read it live before building on it.
12. **Small, on the reception PC, by a job:** clear `C:\ClinicAgent\rehearsal_S451\` if still there; the old `DriveFS_old_2026-10-02` folder may go after a clean week (from 09-Oct) — tell the owner then, in one line.
13. **Waiting on his word ("later"):** the follow-up tracker move C·2 (yes/no and the evening) · contacts steps 3–5 (his workbook) · the mail flood (low) · the portal tiles (after the pharmacy move) · the "other works" for Tailscale.
14. **Handed on by the Sanjeevni chat's duty map:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
15. **Open, not urgent:** F-243 `clinic_users.json` in no store.
16. **Held at his word:** the Callback Tracker move (D634).

The living list: `claude/S288_PENDING_LIST.md` (brought current at this close).

## §2B · The Sanjeevni chat's backlog — carried whole from v208 (its S283 close, 02-Oct)

*Dated note, 03-Oct, by the parent's S290 close: since this text was written S446_AMIR_STAGES_BILLS went live (02-Oct 06:15) and S452_AMIR_PANEL_FIXES went live (23:51); S454_BILL_REGISTER is written, not built, at the owner's word. The board's `_claude_status.sanjeevni` and `claude/S283_POSTCLOSE_HANDOFF.md` are current; the Sanjeevni close (session 285) rewrites this section.*

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

**Canon:** Register v5.129 · Archive v1.126 · Fault v2.114 · this Runbook v209 · `START_HERE_SESSION_291.md` · `S290_BUILD_BRIEF.md` · `live_pins_S290close.txt` · `S290_CLOSE_REPORT.md`; the Sanjeevni side's `S283_BUILD_BRIEF.md`, `SANJEEVNI_SYSTEM_BOOK_v1_10_S283.md`.

**Kits this session, all live:** `deploy_kits/S449_RECEPTION_UPLOAD` · `S450_CLINIC_PCS_TILE` · `S451_CLINIC_PCS_BUTTON` · `S453_RECEPTION_SERVER_DOOR` · the living kit `S448_RECEPTION_AGENT` and what the page serves, `PC_KITS/`.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/INCIDENT_2026-10-02_RECEPTION_PC_SECURITY.md` · `claude/RECEPTION_PC_WORK.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S290\`.

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: read `whoami` before an owner-only press; never raise again what his word closed; no scan and no exclusion change on the reception PC; the Claude app stays there until the server door is proven from that PC.

## §5 · Read first

`START_HERE_SESSION_291.md` → `S290_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md` → `claude/INCIDENT_2026-10-02_RECEPTION_PC_SECURITY.md`.

*v209 · S290 close · 03-Oct-2026.*
