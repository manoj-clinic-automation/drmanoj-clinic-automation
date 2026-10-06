# START HERE — SESSION 297 — written at the S294 close (the parent), 06-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz. Run `START_HERE_PROMPT_v10` (the project's custom instructions) Phase 0 first, then this file. **The work is §0 below; the list of everything pending is `claude/S288_PENDING_LIST.md`; the brief is `S294_BUILD_BRIEF.md`; the Runbook is v215 (§1E: where the console and the staff's lists live).**

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1). **297 is next for the parent and is not reserved; 296 is reserved for the Sanjeevni chat.** Take what the board says and say so in your first line. A kit number is claimed before the scratch folder is named (F-515); D and F numbers before the first canon file of a close. At this close: D681 · F-753 · A-D25 · kit S488.*

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup` and the tracker's live folder `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker`; the two Drive folders `H:\My Drive\Clinic Data Archive\ToReception` and `…\FromReception` are reached by the file-transfer tools only (they never mount in the shell — that is not "unreachable"). `device_bash` worked through S294 on `D:\Downloads` and `D:\dr-manoj-git`; never run `git` in it (F-511) — read `.git/logs/HEAD` and the refs.*

---

## 0 · THE WORK — in the owner's order

1. **Verify this close's publish landed** (A16b: `.git/logs/HEAD`, `refs/remotes/origin/main`, the gate from inside `KB_canon_all`).
2. **Read whether the staff lists are on** — `https://followup.dr-manoj.in/finance/aaj/api/switch` as the owner (the browser pane). **At this close they were OFF**: S487 is live and waits for him to look at each person's list from his console and tap **Turn on**. If he has turned them on: read each list once (`https://followup.dr-manoj.in/finance/aaj?as=<login>`), the taps recorded (`duty_tick`), and what the staff's first day showed. If he has asked for wording changes: the map's lines are the Sanjeevni chat's (`claude_code_briefs/DUTY_MAP.json`); the parent's seventeen are in `/root/finance/aaj_duties.json` — a change there is a kit.
3. **The maintenance pass (§1.5):** the pin list against the newest bundle. At this close, on the 06-Oct 01:35 bundle: **215 match · 0 mismatch · 16 not in the bundle; DECLARED-PENDING 2** (two files the bundle does not carry: `/root/portal/NotoSansDevanagari-Regular.ttf`, `/root/wa/vitals/vitals_page.html`). **`finance_app.py` stands at drift 4** since its whole read of 04-Oct — a whole read comes before its next patch. `asset_register.py` 0.
4. **The next kits of D679, in the order he was told** (Runbook v215 §1E, *not built*): (a) the morning step that must be answered before the other tiles open, triggered by the day's punch; (b) stand-ins and *away*; (c) the Docterz-export lock; then (d) the attendance month-end sheet flow; later (e) approving inside the console — Shavez first, then the owner. **Build only what he says yes to; show him the screen first and install it switched off.**
5. **Small wording on the console, seen live:** *N min late* on a first punch far past the usual hour; Bhati's punch does not join a login; Amir on a non-visit day; names in lower case in the fact lines.
6. **The self-test suite's own kit (F-742)** — `finance_app.py --selftest` aborts as the box runs and carries 58 stale expectations. Test code only.
7. **The statement road, read at the open (mine):** the health row *Bank statements reaching Drive* on `https://followup.dr-manoj.in/finance/health`; the packs page's September cells (13 of 15 — NK Pathology's and the Clinic's current accounts wait on his passwords); the two Yes Bank monthly statements that reached Drive at 07:53 on 05-Oct should have been fetched at 05:40 on 06-Oct.
8. **On or after 09-Oct:** delete `DriveFS_old_2026-10-02` on the reception PC by a job (the next job number is j44; 08:30 on a clinic day); tell him in one line.
9. **The owner's deferred decisions** (`claude/S288_PENDING_LIST.md` §C): the clinic / MK expense split (D664 — *not finalised*; never guessed) · the follow-up tracker on the server · contacts · the mail flood · the portal tiles · the "other works" for Tailscale.

**Held:** the Callback Tracker move (D634). **Owner-side, not ours:** the two remaining Yes Bank passwords on the packs page · the September pack's send · the reception PC's cabled port · "Connect automatically" for the clinic Wi-Fi on that PC · his decision on that PC's Windows (F-700) · one small folder to delete, `D:\Downloads\_to_delete_S294\` (the two EMPTY `_v.db` files of F-752, one more empty file and one `.pyc`; `WHY_SAFE.txt` inside).

**CLOSED BY THE OWNER'S WORD OF 02-OCT — DO NOT RAISE WITH HIM AGAIN:** the technician who worked on the reception PC on 25-Sep · AnyDesk and UltraViewer on that PC (they stay) · changing passwords · the Windows activation there.

**CLOSED BY HIS WORD OF 04-OCT:** the accountants get statements only inside the pack (D674) · a bank statement never passes through the clinic mailbox · the 61 test scans stay where they are (*"let it be your call"*).

**THE MODEL (his word of 05-Oct):** he stopped a build because it was not running on the model he wanted — *"Either you do with Opus or you pause this task."* If he asks which model is working, say what the session is set to in one line and stop at his word; do not argue it.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami` — the browser profile is shared with the Sanjeevni chat, which signs in as staff for its walks. The pane was signed in as manoj (checker) through S294. **The console's Health line, filled in his browser, can show a personal licence number — never repeat it or write it anywhere.**

**The assistant does not type credentials for him** — a sign-in, a password on the packs page, an Apps Script authorisation are his hands. **A system change on a PC (a driver, a Windows setting) is his hand at that PC, not a job.** **Patient files never pass through the assistant's workspace (D656); a copy of the database is made only under the session's own home, never in a mounted folder (F-752).**

**Before a publish, run the gate as PUBLISH runs it:** `python3 -B deploy_kits/NO_PHONE_NUMBERS.py --files-from <list> <repo>`. **And read `.gitignore` against every file of a new kit** — it blocks `*.json` wholesale and several un-anchored names (`*phones*`, `*contacts*`, `*secret*`); a kit's `.json` needs its exact-path `!` line in the same breath (F-751, F-722).

**Standing owner rulings (restated):**

1. Publishing is his double-click — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
2. Full paths always, URLs too, each in its own copy block.
3. One line per command; `\cp` past the alias. A server line carries its own pull: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/<KIT>/<installer>.sh`.
4. Token-lean, never at the cost of verification.
5. Plain English, one step at a time, full-file replacements, ALL-CAPS = urgent. IST only.
6. Never print secrets. Patient numbers: full mobile numbers on screens for him and staff (21-Sep); none in the repository (F-185).
7. Nothing live rebuilt without his OK; the manual path stays.
8. Sub-agents read screens.
9. Do not hand him diagnostics — ask only for what nobody else can do, in one line.
10. When a screen is wrong, read its code first.
11. Do not hand him a step that is not his.
12. His board carries only what needs him and what he should know, and every close keeps its words current.
13. His own items are deferred unless urgent.
14. Never put technical choices to him — decide, say it in one line, proceed. He weighs in on what he can SEE: a screen, a wording, a workflow, a priority.
15. Keep chat short; collapsible pages, no long scroll. A list for him is short and readable.
16. Work on the reception PC is timed for 08:30, when the receptionist is in.
17. A yes/no question gets one word (03-Oct). An explanation is brief and in his words.
18. Analysis first when he says so, then "take my yes" — build the whole plan without a second round of questions.
19. **A new screen for staff is shown to him first and installed switched off; he turns it on (05-Oct). Staff pages are Roman Hinglish; his pages are English.**
20. **Nothing stale is put in front of a person as theirs (05-Oct: "dont populate old stale data").**

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_135_S294close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_132_S294close.md` (§S294) |
| Fault → Action Register | `Fault_Action_Register_v2_120.md` (§7.54 = F-741 … F-752; F-724, F-725 recorded) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-06_Session294close_v215.md` (§1A the job doors; §1B the Docterz server road; §1C the clinic papers; §1D the statement road; §1E the console and the staff's lists) |
| close routine | `END_OF_SESSION_PROMPT_v17.md` |
| live pins | `live_pins_S294close.txt` (**DECLARED-PENDING 2**, both files the bundle does not carry) |
| build brief | `S294_BUILD_BRIEF.md` (the Sanjeevni side: `S295_BUILD_BRIEF.md`) |
| numbers | System Board `board/_numbers` — at this close: **D681 · F-753 · A-D25 · kit S488 · session 297 next for the parent (not reserved), 296 reserved for the Sanjeevni chat** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| The owner's Today tile and command console | `https://followup.dr-manoj.in/finance/console` (tile at the top of his Clinic app) | live since 18:22 05-Oct; 1.1 since 21:35 |
| The staff's *Aaj ka kaam* lists | `https://followup.dr-manoj.in/finance/aaj` (staff) · `https://followup.dr-manoj.in/finance/aaj?as=<login>` (his preview) | live, **switched OFF for staff** — waits on his preview and tap; nothing before 01-Sep-2026 |
| The watch on the statement road | the health page's row *Bank statements reaching Drive* | live; ✓ at this close |
| The Yes Bank monthly statement reader | `/root/finance/yes_monthly.py`; the packs page | live; September 13 of 15 |
| The nightly state backup, wider | `clinic_users.json`, the hand-over photos, `spine/orders` | live |
| The PC setup kits, rehearsed | `D:\Downloads\_kbtools\PC_KITS_REHEARSAL_LATEST.txt` (GREEN, 46 checks, 05:06 05-Oct) | the *Medical PC* and *Dr Manoj's PC* buttons released |
| The reception PC | agent **S456.1** since 08:31 05-Oct (j42); guard S448.1 | the heartbeat carries how current its Windows is |

*Written at the S294 close, 06-Oct-2026.*

---

## SANJEEVNI — a pointer, not a carried section

The Sanjeevni chat has its own entry point since its S285 close: **`START_HERE_SESSION_296.md`** (session 296 reserved for it), with `S295_BUILD_BRIEF.md` and Runbook v215 §2B (its own text, unchanged from v214). The dated notes this section used to carry are in the Archive (§S283, §S285, §S295). **For the Sanjeevni chat, from this close:** `/root/finance/finance_app.py` is now `bff362c3…` and `/root/portal/portal.py` `63df9d49…` — rebuild any kit that was cut on `ef1382d2` / `10a675e7` or earlier; the staff's lists read `DUTY_MAP.json` as it is on the box (a duty ships with its table; a `main.<table>` or `rowid` in a `due_sql` steps around the floor); the seventeen extra lines of `aaj_duties.json` are offered to the map. **For the parent, still open from the duty map:** the Reception login has no Docterz collection / Morning match / Check karein tile; Morning match opens on yesterday only.
