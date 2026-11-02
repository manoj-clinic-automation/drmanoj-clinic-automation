# S698_CALLS_R1 — the Call Console, round 1 (the parent, S379, 02-Nov-2026)

**His words.** The approved mock-up v12 (D819, D820; his "build" 10:00 IST 02-Nov): the Call Console in the month page's look — icons in
place of words with a legend, one timeline per person (unknown numbers first), full numbers and clinic IDs, recordings and transcripts
in place, Needs-you as icon chains; and the doubled call rows (F-1083) mended. The WhatsApps in the timelines, the sanitised follow-up
list and Call ke baad come with S699; the Staff performance section with S700; Patients on the command console with S701.

**What it changes — three live files edited on the box by `make_s698.py` (counted edits, the result pinned to this kit's TO), one new:**

| file | FROM | what |
|---|---|---|
| `/root/portal/calls_console.py` | NEW | the page at `/portal/console` (reads `console.db` only; the click-to-call through call_api.py as the owner's own agent, one call per number a minute; the transcript on tap; the owner's verdict posts to the old review route) |
| `/root/portal/portal.py` | 4ff31351 | the old console moves to `/portal/console/old` (the fallback; its views redirect there); the digest's "last build" filled (F-1084); the new module registered behind the doctor gate |
| `/root/wa/portal_console.py` | 552135b5 | the builder FOLDS the rows that describe one call (MyOperator's uuid, the recording, the session id, the exact end-second) — the fuller row wins; the fold's counts in the meta; five selftest checks |
| `/root/wa/call-hook/call_hook_capture.py` | b8a1a293 | v3.2: the appended row's number from the API's own answer (never `len(index)+2`), the key columns re-read on a miss, the row's key cells verified before an update, `ref_id` as a second key; eight selftest checks on a fake sheet |

**The cause (F-1083).** Since 29-Oct midday the tab `Call_Durations` held a gap, so the receiver's `len(index)+2` named the row ABOVE the
one really appended; every `call.summary` then overwrote the PREVIOUS call's row — the new call twice, the older call gone. Three layers:
the receiver (above), the builder's fold (every reader of console.db), and `repair_call_durations_s698.py` — run once by the installer:
the affected region of the tab rebuilt from the raw webhook log (the truth), a CSV backup first (owner-only), verified, restored on a
failure. `trace_s698.py` (read-only, counts) is printed before it. The console cron runs 07:00–22:50 (was 09–21); `console.db` is rebuilt once.

**Reads, never writes:** `console.db` (mode=ro), `/root/wa/.env` (the call key, never printed), `ring_agents.json` through `ring_outcome.ivr_agent`.
Writes: the Call_Durations tab (the repair, once), the crontab (one line), `console.db` (the builder, as the cron does).

**Proof.** `walk_s698.py` on made-up data: 82 checks, 9 mutants caught; the control on the live files 82 red; the three selftests
(builder 54, hook 69, repair tool); the page rendered at 1366 and 390 px and read by a sub-agent (no sideways scroll); an independent
cold review; `rehearse_s698.sh` on a made-up root: dry · install · again · changed · half · corrupt · someone else's switch · journal red ·
red at [9/9] · the repair's failure branch · SKIP_REPAIR.

**Install (one server line, window 04:00–23:30 IST; about three minutes — the rebuild of console.db is the long part):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s698kit && cp -rp /root/deploy/repo/deploy_kits/S698_CALLS_R1 /tmp/s698kit && bash /tmp/s698kit/install_S698_CALLS_R1.sh
```
**Undo:** the installer prints it; the backups are `*.bak_S698_<from8>` beside each file; the tab's CSV under `/root/wa/call-hook/backups/`;
the crontab as it was at `/root/wa/crontab.bak_S698_<stamp>`.
