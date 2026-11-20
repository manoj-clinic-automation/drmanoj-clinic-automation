# S492 — THE FOLLOW-UP TRACKER MOVES TO THE SERVER — THE PLAN, FINAL (20-Nov-2026, the parent, reviewed by Fable)

*Supersedes `S491_TRACKER_TO_SERVER_PLAN.md` and `S492_TRACKER_TO_SERVER_PLAN_v2.md`. For the owner's OK; nothing is built before it (D1021). Counts only; no patient detail. Reviewed against the live PC folder (connected 20-Nov 14:5x IST), the repository, S443 §7, S442, S287 and his rulings in memory; §10 answers his word of 15:18 IST (the Clinical data report he cannot export daily; Docterz's longer-period CSV on request; the browser page's other functions). Technical choices are the assistant's and are stated, not asked.*

## 0 · What the review found — why v1 was not enough

v1 said "`processor.py`, byte for byte, moves". True, but less than half the story. On the PC, **three programs** make the daily result and **four separate sends** carry it to the readers:

| on the PC today | lines | in the repository? | what it does |
|---|---|---|---|
| `processor.py` (the engine) | 3,556 | yes | the rules: who came, who is due, the ladder, the call sheet, the ledgers |
| `docterz_pickup.py` (the orchestrator, S892) | 995 | **no — PC only** | every 5 min: finds the exports, cuts a multi-day report into days, decides RUN / skip / quarantine, picks the right follow-up log (S540), the "log alone" rule (S892), the Sunday rule, rebuilds `Day_Tenders.csv`, fires the sends |
| `push_patient_join.py` · `push_followups_today.py` · `push_patient_mirror.py` · `watch_and_push_followups.py` | ~1,000 | partly | the four sends |

**The four roads from the PC to the readers — each must be cut on the PC and re-made on the server, or the spare keeps feeding:**

| what the PC makes | who reads it today | the road today | after the move |
|---|---|---|---|
| `Staff_Action_Today_<day>.xlsx` (the call sheet) | Callback Tracker tab → Call Console → staff cards | (a) HTTPS `/fu-upload` → `/root/wa/followup-inbox/` → `push_followups_vps.py` → Sheet; **and** (b) the PC also writes the Sheet tab directly | the server writes the workbook straight into the inbox; `push_followups_vps.py` is the ONE Sheet writer; the PC's direct Sheet write ends |
| `Visit_Ledger_Join.xlsx` + `Patient_Ref` (salted fingerprints) | `patient_visit` / `patient_ref` → WhatsApp lists, Call ke baad, Patient records | `push_patient_join.py --push` → server; `finance_patient_sync.py` cron :20 past, 08–21 | a local write; the runner calls the sync the moment the join is written (the 21:20 race ends); the cron stays as backstop |
| the **Day Revenue** tab and `Day_Tenders.csv` | the command console's money line, the day page, the month views — **the revenue board** | the PC's `outputs\` is Drive-synced → `docterz_ingest.py` reads the Drive folder every 10 min; *"the file Drive modified later wins"* | `docterz_ingest.py` reads the server's outputs folder FIRST; Drive only for a day the server never made. **Without this one change the revenue board would read the PC spare's file forever** |
| the 08:00 `Patient_Master` mirror (Sheet tab) | the Callback Tracker's new-caller conversion | `run_patient_mirror.bat` nightly on the PC | the same script, cron 08:00 on the server, the server's own Sheet credential |

**Three more things v1 did not carry:**
1. **The state file.** `D:\Downloads\DocterzArchive\_pickup_state.json` (every export seen, every day's digest and patients, the "log alone" days) is what RUN / skip / quarantine rest on. It is seeded with the twelve data files, or the server's first pass sees every past day as new.
2. **The Call_Feed.** Every PC run pulls the Callback Tracker's published call feed from Google into `outbound_log.csv`; that drives the *reinstated callbacks* on the call sheet. A live input that changes by the hour — a naive replay of an old evening would fail for a reason that is not a code difference. The replay pins it (§4).
3. **The clock.** All three programs read the local clock and assume IST. The server runner pins its own clock to IST, whatever the server's setting — otherwise a next-morning run before 05:30 IST stamps the previous date.

## 1 · What moves

`/root/followup_tracker/` = the PC's live folder, byte for byte (the PC's bytes hashed first; the repository's `processor.py` is 10-Nov and may be behind), plus a server runner = `docterz_pickup.py` with its Windows parts replaced: it watches the server's own intake (§10), writes to the inbox and the finance folders locally, calls the syncs. Every rule stays: the 3-minute quiet wait so the two exports are taken together; cut per business day; RUN / skip / "newest wins" / QUARANTINE; S540; S892 "follow-up log alone"; Sunday emergency-only; `Day_Tenders` newest-export-wins. Input files are named exactly as the PC names them (the name is inside the ledgers).

**Seeded once from the PC:** the twelve data files, `_pickup_state.json`, `feed_url.txt`, the vacation calendar. The fingerprint salt the server already holds; the Sheet credential is the server's own.

It runs within minutes of each export arriving, every day, sitting or not. At 9:45 pm, if either evening report has not arrived, he gets one push (live from S808/S809; pointed at the server's run).

## 2 · What stays IDENTICAL for staff

The Call Console, its rows and sections, its Hindi, the ladder, the Callback Tracker's tab, the timings. Same workbook, same tabs — made on the server. Staff are told nothing because nothing they see changes.

## 3 · How the exports reach the server

As today: reception's agent puts the consultation report and the follow-up log on the server first. The PC fetches them back (`docterz_fetch.py`) — that fetch STAYS, because the spare needs the same inputs to stay current. What ends is the PC sending results back up. His own Clinical data report keeps leaving his PC by `docterz_clinical_send.py` when he exports (§10).

## 4 · The proof before any switch — the replay, twice

**Pairing rule.** For each of the past month's evenings (22 consultation evenings, 24 follow-up logs since 19-Oct; the archive's `index.csv` and the state file say which input made which run) the reference is the LAST run of that day, its workbook in `outputs\`, and the `data\backups\<date>_daily` snapshot taken just before it. The clock is pinned to that run's recorded time (as S287 did). The Call_Feed fetch is off and `outbound_log.csv` is taken from the NEXT snapshot — the state after that evening's fetch — so the feed is exactly what the PC saw.

**Replay 1 — on his PC** (D656; patient files never leave it): the server's code against the PC's own evenings. Pass = every `Staff_Action_Today` sheet identical cell for cell; the data files identical apart from the input file's name and its Revenue_ID.

**Replay 2 — on the server, after the seed, before the switch:** the same month again with the server's Python, libraries, clock and line endings — compared against the workbooks the PC uploaded on those evenings, which the server's inbox already holds. A replay that passes on the PC proves the code, not the environment; this closes that gap. The server holds patient data already; nothing new crosses.

Any difference is explained and fixed before the switch. Both replays are read-only on the live folders; scratch copies are removed.

## 5 · The spare — how the PC feeds nothing

One flag file on the PC, `D:\Downloads\DocterzArchive\_SPARE_MODE.txt` (the convention of `_server_fetch_OFF.txt`). With it present, `docterz_pickup.py` and the watcher skip the four sends and nothing else: the PC keeps fetching, running, archiving and making its list and ledgers, so it stays current as the undo. Its `outputs\` and `data\` stay Drive-synced — his backup copy of the spare. The server's live data folder goes into the nightly encrypted state bundle; one restore drill before the switch. This is a change to a live PC program — covered by this OK.

## 6 · The switch — in this order, so nothing changes until the evening he picks

1. **Before the evening (nothing visible changes):** `docterz_ingest.py` reads the server's outputs first, Drive second; `finance_patient_sync.py` callable by the runner; the 08:00 mirror cron installed, OFF; the runner installed with its OFF file present (`/root/followup_tracker/OFF`, the `_off/ALL_OFF` family); the intake door (§10) live but feeding only the archive.
2. **The evening:** after the PC's own run and sends, the seed goes up once by the join path the PC already uses. Then `_SPARE_MODE.txt` on the PC; the OFF file removed on the server. From the next export the server makes the list.
3. **The guard:** the server writes the inbox locally, so ANY arrival on `/fu-upload` after the switch means the PC sent — his console shows it in red, with the time.
4. **Next morning, for seven days:** the call list, the Sheet tab, the money line and `patient_visit` checked against the PC spare's own output, one line on his console ("server 63 · PC 63 · same").

## 7 · Nothing deleted — the undo

The PC tracker, its data, its browser page and the manual way all stay. **Undo = two files:** remove `_SPARE_MODE.txt` on the PC, put the OFF file on the server; the PC sends again from its own current ledgers. The PC's `/run` page sends — so it is used only with the server's OFF file in place, never alongside it.

F-1316 closes at the end of the watch week.

## 8 · Size

**The move: four sessions** — (1) the hash of the PC's bytes, Replay 1, the server kit and the PC's spare-mode kit, walked offline; (2) the install with everything OFF, the seed, Replay 2 on the server, the readers server-first, the intake door; (3) the switch evening; (4) the next-day check, the week's watch, the record. **Then §10's enrichment: two more** — (5) the Clinical data report and the patient list absorbed on arrival (advised periods, diagnosis groups, medicines days); (6) the browser page's surviving functions as server pages and the PC page's retirement from the tiles.

## 9 · What he does

Says OK (or what to change — a screen, a wording, the order, the evening). Picks the switch evening when session 2 is green. Exports the Clinical data report when he can — the console tells him up to which date the last one reached (§10). `C:\followup_tracker_local_test_kit` is already added. Nothing else.

---

## 10 · THE DOCTERZ REPORTS — ONE DOOR ON THE SERVER (his word of 15:18 IST)

**The finding.** Four kinds of Docterz CSV exist in the PC's own uploads (148 consultation reports, 72 follow-up logs, 3 clinical data reports, 3 patient lists "up to <date>"), and they enter by four different roads today: reception's agent, his PC's Downloads pickup, the PC browser page's upload box, and a by-hand run of the diagnosis seeder. On the server there will be **one door**, and every road leads to it.

**The door.** An owner-only page on his portal, *Docterz reports*, with one upload box and one list. Any Docterz CSV — any of the four kinds, any period (one evening or six months), any file name — is recognised by its columns, never its name; cut into business days; archived once under `/root/finance/docterz_exports/<KIND>/<YYYY-MM>/` with one index (the PC's archive, re-made on the server); and handled by the same RUN / skip / "newest wins" / QUARANTINE rules per day. The page answers in counts: days new and run, days already known and skipped, days quarantined (fewer patients than held — never silently), follow-up dates added, diagnoses added. The automatic arrivals (reception's agent; his PC's clinical send; the reception phone's pickup if ever) land in the same door, so there is one archive, one index, one set of rules, and the page shows them too: *last consultation report · last follow-up log · last clinical data report · last patient list — each with the date it reaches*. The PC browser page's upload box is the fallback, unchanged.

**The Clinical data report — never awaited, always absorbed.** He cannot export it every working day, so no list ever waits for it (S443 §7; F-1503 — the follow-up log is the source of dates). When it comes, for whatever period, it makes every list better, by the S443 §7 table: the exact advised period for each follow-up row (the tracker's weak spot when the prescribing day cannot be read); a follow-up the log missed, added; the diagnosis group on each calling row and the Patients page; drugs and dosage → the days of medicines given → the *on medicines* state (D919) with Sanjeevni's purchases; tests and procedures advised against *Report baaki* and the slips; a count of differences on his console. Weekly or monthly is enough: the page says *"clinical data reaches up to <date>"*, so he knows what period to ask Docterz for. His PC's Downloads pickup of it stays (he exports on that PC); the door is where it lands.

**The longer-period CSV on request — the same door.** A consultation report or follow-up log for a long period repairs the gaps by itself: a missed evening becomes a new day and runs; a known day with the same patients and money is skipped; a known day with more patients re-runs (newest wins) as the orchestrator already does for a re-export; a day with fewer is quarantined and shown. A long patient list runs the diagnosis seeder on arrival (today a by-hand step, last run 24-Oct), so the call sheet's priority letter stops going stale. Only the latest business day's list is ever re-sent to staff — an old day re-run never replaces today's call list (the orchestrator's own rule).

**The PC browser page's other functions — read from `app.py`'s routes, and what becomes of each:**

| the page offered | what it did | after the move |
|---|---|---|
| upload + *Run* | the two exports → the day's run | the door; automatic for the agent's files |
| *Diagnosis* (patient list / patients_detail) | the taxonomy seeder → `patient_diagnosis.csv` → the priority letter on the call sheet | automatic on arrival at the door |
| *Vacation* add / delete | the doctor's off-days, read by the ladder | one line on his console: off-days, add / remove (the data file moves; empty today) |
| *Confirm* | staff-confirmed appointments → `confirmations.csv` | the Callback Tracker's outcomes are the live source; the file moves, read-only |
| *Concessions* + export | the concession log from the money columns | written by the run as today; the export becomes a download on the status page |
| *Finance* (patient / period / lines), *Revenue* upload / review / promote | the June money pages; the review queue is dormant since 28-Jun | **retired** — money lives in `finance.db` and the finance pages |
| *Calls*, *Call audit*, *Called-in* | the Call_Feed pages | **retired** — the Call Console is their successor; the feed itself still feeds the reinstatements |
| *Lab*, *Procedure* add | June-era manual registers, no data since | **retired** — the lab door and the procedures page exist on the server |
| *Init master*, *Download* | one-time seeding; the day's workbook | the status page lists the day's workbook; init never again |

Nothing on the PC page is removed; it stays whole as the fallback (§7). The *Follow-up Tracker* tile retires at the end of session 6, when the console shows everything the page showed.

*S492 · 20-Nov-2026 · the parent · reviewed and finalised; nothing built.*
