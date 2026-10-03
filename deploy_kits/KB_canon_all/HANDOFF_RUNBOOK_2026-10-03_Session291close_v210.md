# HANDOFF RUNBOOK — v210 — S291 close (the parent), 03-Oct-2026

*Supersedes v209 (the parent's S290 close). For the next parent chat (session 292 if still free on the board — it is not reserved). §1A is carried from v209 with this session's additions. §2B is the Sanjeevni chat's own backlog, carried whole from v209 with one more dated note.*

## §0 · What happened (03-Oct, 04:33 → 08:2x IST, one sitting)

- **The reception PC is finished, by signed jobs, with nobody at that desk:** the server job door proven from the PC (j13); the Claude app removed with its data (j22, j24); the agent's Chrome repair proven live; the full setup check clean (j33).
- **The firewall step is in the reinstall kit** (F-688 closed): `secure_setup.cmd` in `S448_RECEPTION_AGENT`, the installer puts it beside the agent, the README names it; rehearsed on the PC; published `5506531a` (05:51); the *Clinic PCs* page serves `kit.zip` `994871f3…`.
- **The server is reachable over IPv6** (F-692 closed): no server change; the owner entered one AAAA record at GoDaddy. Kit `S455_IPV6_FACTS` is a reader and took the build lock.
- **A Docterz day was missing from his portal** (F-697): reception's exports reach the server, but the tracker that feeds Day Revenue runs on manojz and watches only `D:\Downloads` there. His copy line fixed the day; the cause stands until the tracker moves (C·2).
- **The reception PC's Wi-Fi** (F-693 rewritten): the clinic Wi-Fi is `Airtel_Airtrl_mano_8080`, Wi-Fi 6; the PC's 2016 Intel driver could not list it. The owner installed driver 18.33.17.1 from Windows Update; the PC is on the clinic Wi-Fi. **The cabled port is dead** (media disconnected).
- **That PC's Windows 10 is at the November-2025 level** (F-700) — told to him with the options.
- `finance_app.py` read whole: drift 0. No server file changed; DECLARED-PENDING 0.

## §1 · Mental models

1. **The name of a network is taken from a screen that is on it** (F-693). Two diagnoses were built on a name nobody had checked.
2. **A record explains the events it holds, not the ones nobody looked for** (F-693). The cable's blinks explained every "disconnected while associating"; they did not explain why the clinic's name was never on the screen.
3. **A step on a screen is given to the owner only after that screen has been read** (F-693: *Hidden Network*).
4. **When one half of a chain moves, the walk runs to the screen the owner reads** (F-697).
5. **A question about what the world sees is asked from outside the machine** (F-699).
6. **A rehearsal of something that starts a long-lived process sends its output to NUL** (F-698).
7. Carried from v209: the server relays, the PC decides (D661) · two roads are two only where they do not share a failure (F-692) · "starts by itself" is proven only by a real restart (F-689) · read `whoami` before an owner-only press · what his word closed is not raised again (the 25-Sep technician, AnyDesk and UltraViewer, passwords, the Windows activation; no scan and no exclusion change on that PC) · the build lock binds every installer (F-694) · patient files never pass through the assistant's workspace (D656).

## §1A · How to send a job to the reception PC

**Sign (both doors), in manojz's own shell — the secret never leaves that PC:**

```
cd <folder with the job> && python3 -B $HOME/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits/S448_RECEPTION_AGENT/reception_sign.py sign $HOME/mnt/Downloads/margsync/_config/reception_agent_key.txt <job file>
```

It writes `<IST time>_<job>` and `<IST time>_<job>.sig`. Job folders so far: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S290\reception_jobs\` (j01 … j21) and `…\_EVIDENCE\S291\reception_jobs\` (j22 … j40). Useful ones to copy: `j35_cable_and_wifi_read.py` (the cable and Wi-Fi from Windows' own records), `j33_setup_complete_check.py` (the whole setup), `j40_after_wifi_driver.py` (driver, scans, Windows Update, build).

**The Drive door (the usual road):** stage the stamped job and its `.sig`, copy both into a **fresh** folder under the cloud workspace's outputs, and commit **the job first, then the `.sig`, in two separate calls** to `H:\My Drive\Clinic Data Archive\ToReception\jobs\`. About two minutes later stage `H:\My Drive\Clinic Data Archive\FromReception\results\<stamped name>.out.txt` (a refusal is `<stamped name>.REFUSED.txt`). Those two folders are reached by the file-transfer tools only, not by the shell. A job that restarts the agent loses its own Drive result — read the next job instead.

**The server door:** from the assistant's browser, on any page of the clinic site, `fetch` a `POST` to `/finance/api/reception/jobs/submit` with JSON `{name, job (base64 of the stamped file), sig}`; read with `reception_sign.py read-token` → `POST /finance/api/reception/jobs/read`. Proven from the PC on 03-Oct (j13). Impractical for a job of several kilobytes — the Drive door is the working road. Full text: `deploy_kits/S453_RECEPTION_SERVER_DOOR/README.md`.

**Rules of both doors:** `.ps1`, `.cmd`, `.bat` or `.py`; first comment line `# timeout=NNN` changes the 600 s limit; a name is used once; older than 48 hours refused; runs as user `dell`, not elevated; ask for counts, never listings of patient folders. **A system change on that PC — a driver, a Windows setting — is the owner's hand at the PC, not a job.** **A rehearsal sends the installer's output to NUL and reads `install_log.txt`** (F-698).

## §1B · The Docterz reports, until the tracker moves (F-697)

Reception exports both reports each evening; they reach the server by themselves. The owner's portal shows the day only after the tracker on manojz has seen the files in `D:\Downloads`. His one line on manojz (identical files are skipped by content, so it is safe to run on any day):

```
cmd /c copy /y "H:\My Drive\Clinic Records\Docterz exports\*.csv" "D:\Downloads\"
```

The tracker's task runs every 5 minutes and the server reads its sheet every 10. The assistant cannot run this copy: the Drive folder does not mount in the PC shell and patient files do not pass through its workspace (D656).

## §2A · The parent's backlog — in order

1. **His publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — this close's record only; no server line follows.
2. **Read the board for S291 POST-CLOSE:** the 08:40 job (the signal at the reception desk). If it is not there, send a copy of `j35_cable_and_wifi_read.py` in clinic hours.
3. **F-697 — stop the owner having to run a line each evening.** Either the tracker on the server (C·2, `claude/S287_TRACKER_MOVE_PLAN.md`, his yes/no and one evening) or, sooner, the manojz tracker reading the clinic Drive's *Docterz exports* folder as well as `D:\Downloads` (a change to a live tool: his OK first). Put to him as one yes/no.
4. **`README_REINSTALL.txt`: one line for the Wi-Fi driver** — after a Windows reinstall, install *Intel - net - 18.33.17.1* from Windows Update's optional updates before joining the clinic Wi-Fi. A changed living kit means `kit.zip`, `KIT_INFO.txt`, `MD5SUMS.txt` again and a rehearsal by a job.
5. **The reception PC's cabled port** (F-693): a different cable or socket (his hands), then the Realtek driver `10.19.627.2017` from optional updates at a quiet hour; a good cable with no link is the PC's socket — the vendor's.
6. **F-700 — how current each PC's Windows is, on the health page** (the agent's heartbeat can carry the build and the newest fix date). His decision on enrolment and on a new reception PC is his; told once.
7. **D664 — a short plan and a mock** for the clinic-consumables groups, one PDF per purchase and the *Dr MK expense* lane; the join of B-0105/6/7; the battery's warranty date. **Plan first; no build until he says.** His text is on the board (`_numbers` v188) and in the Sanjeevni chat's record.
8. **The build lock in the parent's installers** (F-694) — from the next kit that places a file; S455's reader shows the pattern (`mkdir /root/deploy/.claude_code_build.lock` + an `owner` file, released on every exit).
9. **The Medical PC's kit and Dr Manoj's PC's kit for the *Clinic PCs* tile** — each its own rehearsed kit; the Medical PC's with the Sanjeevni side.
10. **The tidy-up leads in `finance_app.py`** (`_EVIDENCE\S291\FINANCE_APP_WHOLE_READ_S291.md`): unescaped row text on the health page, routes without a role check, the ledger post inside the approve loop, the negative-cash guard, the apply-abort rollbacks, a selftest that writes into the live scan folder. One kit, his OK first.
11. **Small, by a job, on or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC; tell him in one line.
12. **Optional:** a `listener Default IPv6` on port 80 if a certificate renewal ever stumbles (the certificate is good to 08-Dec-2026); `/root/finance/ipv6_facts_s455.json` may go after the next 01:35 bundle.
13. **Waiting on his word ("later"):** contacts steps 3–5 (his workbook) · the mail flood (low; the health mails land in Gmail's Trash) · the portal tiles (after the pharmacy move) · the "other works" for Tailscale.
14. **Handed on by the Sanjeevni chat's duty map:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
15. **Open, not urgent:** F-243 `clinic_users.json` in no store.
16. **Held at his word:** the Callback Tracker move (D634).

The living list: `claude/S288_PENDING_LIST.md` (brought current at this close).

## §2B · The Sanjeevni chat's backlog — carried whole from v209 (its S283 close, 02-Oct)

*Dated note, 03-Oct, by the parent's S290 close: since this text was written S446_AMIR_STAGES_BILLS went live (02-Oct 06:15) and S452_AMIR_PANEL_FIXES went live (23:51); S454_BILL_REGISTER is written, not built, at the owner's word. The board's `_claude_status.sanjeevni` and `claude/S283_POSTCLOSE_HANDOFF.md` are current; the Sanjeevni close (session 285) rewrites this section.*

*Dated note, 03-Oct, by the parent's S291 close: the Sanjeevni chat is still in its S283 POST-CLOSE; since the note above it has taken D662 … D667, F-690, F-691, F-695, F-696 and kit S454 on the board. `S454_BILL_REGISTER` is a brief on the PC, on hold and re-opened more than once at the owner's word — read the board's newest Sanjeevni line before acting on it; nothing of it is built. D664 is his ruling for the parent's backlog (§2A item 7).*

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

**Canon:** Register v5.130 · Archive v1.127 · Fault v2.115 · this Runbook v210 · `START_HERE_SESSION_292.md` · `S291_BUILD_BRIEF.md` · `live_pins_S291close.txt` · `S291_CLOSE_REPORT.md`; the Sanjeevni side's `S283_BUILD_BRIEF.md`, `SANJEEVNI_SYSTEM_BOOK_v1_10_S283.md`.

**Kits this session:** `deploy_kits/S455_IPV6_FACTS` (a reader, run once) · the living kit `S448_RECEPTION_AGENT` and what the page serves, `PC_KITS/`.

**Papers:** `claude/S288_PENDING_LIST.md` · `claude/S448_RECEPTION_AGENT.md` · `claude/RECEPTION_PC_WORK.md` · `claude/S287_TRACKER_MOVE_PLAN.md`. Evidence: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S291\`.

## §4 · Rules at the boundary

The owner's standing rulings (restated in START_HERE §0). Earned here: his reception-PC work is done at 08:30 when the receptionist is in, not later in the morning; a list for him is short; credentials and sign-ins are his hands (the GoDaddy record, the Wi-Fi password), and so is any system change on a PC.

## §5 · Read first

`START_HERE_SESSION_292.md` → `S291_BUILD_BRIEF.md` → `claude/S288_PENDING_LIST.md`.

*v210 · S291 close · 03-Oct-2026.*
