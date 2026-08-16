# D297 CALL-INTELLIGENCE CONSOLE — PORTAL BUILD DOSSIER — v1 (S168)

**Tier 1 · self-contained build reference. Advanced Orthopaedic Surgery Centre, Bareilly.**
**Owner: Dr. Manoj Agarwal · built with Claude · created Session 168, 2026-08-11.**

> **What this is.** One place that holds *everything* the console/portal build needs — schema, the
> proven staff-attribution mechanism, the query rules, the display contract, the live-data findings,
> the install state, and the roadmap — so no future session has to re-probe MyOperator or re-derive
> any of it. Companion to the signed **`D297_Call_Console_Contract_v4_FINAL.md`** (the *what to build*)
> — this is the *how it was built and what we learned*. Everything below was proven against live data
> this session (D160/D188); numbers are pinned to their probe.
>
> **Masking:** patient numbers are last-4 only anywhere they appear. Agent `UserId`s below are internal
> MyOperator identifiers (they live in the `Agents` sheet), not secrets or PHI. The API bearer token
> lives only in the VPS `.env` and is never written here (F-31).

---

## 0 — THE SHAPE OF THE THING (one paragraph)

A **builder** (`portal_console.py`, on the VPS at `/root/wa/`) reads the two live Google Sheets +
MyOperator `/search` + Drive **read-only** and writes one SQLite file **`console.db`** (`/root/wa/`).
A **page** (`/portal/console`, served by `portal.py`, the doctor-gated portal on port 8099) reads
`console.db` **only** and renders the call log, conversation threads, staff performance, and new
leads. The builder is the **sole writer** of `console.db` (one-writer invariant, D235); the page never
computes analytics, it only *consumes* what the builder already reconciled (consume-don't-recompute,
D236/D296). `console.db` + `transcript_cache.db` carry full numbers + diagnosis + patient speech →
**F-31/F-49: gitignored, never in a repo or kit.**

```
Google Sheets (2)  ─┐
MyOperator /search ─┼─►  portal_console.py  ──writes──►  console.db  ──reads──►  /portal/console
Drive transcripts  ─┘        (builder,                    (SQLite,               (portal.py,
                              /root/wa/)                    /root/wa/)             doctor-gated, :8099)
```

---

## 1 — GROUND-TRUTH CONSTANTS (pinned; do not guess)

| Thing | Value |
|---|---|
| Builder | `/root/wa/portal_console.py` · VPS python **`/root/wa/venv/bin/python3`** (system python3 lacks gspread) |
| Live builder md5 (S167 Stage A) | `81581a6cec84b4414827dc71d35548d3` |
| Stage-2a builder md5 (S168, delivered-not-installed) | `00b2175fa11e7d046befa4531a5834b6` |
| DB written | `/root/wa/console.db` (SQLite; atomic tmp→replace, full-rebuild-idempotent) |
| Transcript cache (persistent, survives rebuilds) | `/root/wa/transcript_cache.db` |
| Portal app | `/root/portal/portal.py` · **port 8099** · systemd `clinic-portal.service` (the `8090` in-file is a dead dev-fallback) |
| Live portal md5 (console page rev2) | `7a862f748…` *(installed; a WinSCP overwrite briefly rolled it to `f0655abd…`, caught by the md5 gate — F-66)* |
| Portal rev3 md5 (delivered-not-installed) | `54c239a3c645860cfd2914e5262e9e08` |
| Source Sheet | "Clinic Callback Tracker" · ID `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` |
| **Join Key** (the spine of every join) | **`{phone10}_{call_start_unix}`** |
| MyOperator base | `https://publicapi.myoperator.co` · Company `68384350414b9847` · WABA `2101222617483538` |
| API credential | the **"Authentication" Bearer token** (APIs & Webhooks → Developer API → WhatsApp APIs), in VPS `.env` only — NOT the Calling-APIs `x-api-key` |
| Builder modes | `--selftest` (offline, 35/35) · `--dry-run` (reads live, writes nothing) · `--myop-probe` (read-only /search) · `--build` (writes console.db). Layers: `--with-myop-reconcile` · `--with-transcripts` · `--days N` |

---

## 2 — `console.db` SCHEMA (what the page can read)

The builder discovers every source column by **header name** at runtime and HALTs (printing the live
header) if a required column is missing — a filename/position is never trusted (D188). Tables:

| Table | Key columns | Notes |
|---|---|---|
| **`calls`** *(spine)* | `join_key`, `phone10`, `category`, `direction`, `status`, `answered`, `total_duration`, `ended_at_ist`, `captured_at_ist`, `recording_filename` | from `Call_Durations`; `status='probe'` row excluded from counts. **No agent column** — agent comes from joins (see §4). |
| **`verdicts`** | `join_key`, `agent`, `patient_name`, `claimed_outcome`, `not_filed`, `ai_outcome`, `verdict`, `outcome_tf`, `status`, `error`, `doctor_flag`, `doctor_note`, `final_outcome`, `conduct_note`, `match_confidence`, `recording_link`, `flag_postop/complaint/urgent/surgery/clinical/conduct` | from `Call_Verdicts`. **One call can have many verdict rows** (re-judged) → dedup before counting (§3). `not_filed` = blank Claimed Outcome. **AI Reason + Evidence columns exist in the sheet but the builder currently DROPS them** (roadmap item). |
| **`recordings`** | `myoperator_filename`, `join_key`, `recording_link` | bridge `recording_filename → MyOperator Filename → Join Key`; the recording-link fallback source. |
| **`transcripts`** | `join_key`, `text`, `transcribed_at` | merged from `transcript_cache.db`; **PHI (patient speech)**. |
| **`patients`** | `phone10`, `name`, `diagnosis`, `age`, `gender`, `last_visit`, `patient_uid`, `clinic_id` | from `Patient_Master`; diagnosis IS present live (F-70). |
| **`outbound`** | `phone10`, `agent`, `start_unix`, `date`, `time`, `duration_s`, `status` | from `Outbound_Log`; agent source for outgoing calls. |
| **`agents`** | `ext`, `name`, `userid`, `active` | the roster (see §4.2). |
| **`conversations`** | `phone10`, `attempts`, `miss_attempts`, `any_connected`, `net_missed_open`, `last_agent`, `resolved_by` | phone-grouped threads; `net_missed_open` corrected by the MyOperator reconcile. |
| **`daily_summary`** | `date`, `net_missed`, … | the MyOperator-`/search`-sourced authority the reconcile matches to. |
| **`myop_daily`** | `date`, `myop_net_missed`, `daily_summary`, `delta` | reconcile output (delta 0 on real days). |
| **`latency`**, **`unjudged`**, **`meta`** | — | latency mining; reasons-not-judged; `meta` holds `built_at` + row counts. |
| **`call_agent`** *(NEW, Stage 2a)* | `join_key`, `agent`, `department`, `matched_how` | **additive** table added by the Stage-2a builder change; the *reliable* per-call staff attribution (see §4). |

---

## 3 — QUERY & DEDUP RULES (the F-74 lesson, baked in)

**F-74 — never LEFT JOIN a one-to-many child straight into a counted spine.** The first console render
showed impossible totals (Incoming **2276** > all-calls **1651**) because `LEFT JOIN verdicts` fanned
each call out by its verdict count (**2195** verdicts across **1651** calls — re-judged calls have
several) and `LEFT JOIN patients` compounded it. The fix, now standing rule:

- **`_DV`** — collapse `verdicts` to **one row per `join_key`** via `MAX(id)` (**newest verdict wins**).
- **`_DP`** — collapse `patients` to one row per `phone10`.
- **`_DPHONE`** — number-recovery helper (see §5).
- After dedup, **a dimension's parts must sum to the spine total** — that sanity check is the tripwire.

The page's data helpers are: read-only `_console_conn` (opens `console.db` `mode=ro`), `_console_meta`,
`_console_filters`, the three dedup views above, `_AGENT_EXPR`, `_LOG_FROM/_LOG_COLS`, `_log_row`,
`_log_where`, and the query builders `_query_log / _facets / _query_conversations / _query_staff /
_query_leads`, plus `_group_by_day`.

---

## 4 — STAFF ATTRIBUTION: THE MECHANISM (the big S168 discovery)

**Problem.** The console's "staff" column looked like it was *only Alisha*. That was a **verdict-attribution
artefact** — many answered calls were unjudged (e.g. 18/38 answered on 10 Aug were still unjudged at the
2:44 AM build), and many verdicts carry a **blank agent**. The verdict is the wrong place to read the handler.

**Where the handler actually lives (proven).** In each MyOperator `/search` record, `_source._us` is a
list of `{ky, vl}`. The entry whose **`vl == 'received'`** is the staff who handled/made the call, and its
**`ky` is that staff's MyOperator UserId**. Incoming-missed records carry only `vl == 'missed'` entries →
correctly **no handler**.

### 4.1 — `/search` record anatomy (probed S168, read-only)
- Top-level `_source` fields used: `caller_number_raw` / `caller_number` (→ phone10), `start_time`
  (unix; the join-key suffix), `status` (**numeric: 1=answered, 2=missed**), `event` (**1=incoming,
  2=outgoing**), `department_name` (`Appointments` / `Emergency` / blank on outbound), `filename` /
  `fileurl` (recording), and **`_us`** (the handler list above).
- `log_details[0]` carries `action` (`received`/`missed`), `_ds` (`ANSWER`/`BUSY`), `_did`, `received_by`,
  `transfered_to`, `start_time`, `end_time`, `duration` — useful context, but **`_us` is the source of truth
  for the agent**.
- Worked examples (masked):
  - *incoming answered* → `_us=[{ky:686cf557…, vl:'received'}]`, dept `Appointments` → **Shivani**.
  - *incoming missed* → `_us=[{…,'missed'},{…,'missed'}]`, dept `Emergency` → **no handler** (rang two, both missed).
  - *outgoing answered* → `_us=[{ky:69cfa941…, vl:'received'}]` → **Alisha** (she placed the call).

### 4.2 — The roster: `ky` → `Agents.UserId` → name (mapped 100%, 483/483, zero unmapped)
| UserId (`ky`) | Ext | Name |
|---|---|---|
| `6838435041f29988` | 10 | Dr Manoj Agarwal |
| `686cf49a692bb162` | 11 | Shavez Ahmed |
| `686cf557c4f09495` | 12 | Shivani Srivastava |
| `686cf5a29a97d527` | 13 | Manoj Bhati |
| `69cfa941359e1649` | 14 | Alisha Khan |
| `6a2017dd50280597` | 15 | Darpan Robert |
| `6a2018cda8975829` | 16 | Reception Mobile *(the reception backup mobile, kept as a named agent — leave as-is)* |
| `6a59b1b7a2f88134` | 17 | Awdhesh |

### 4.3 — Coverage numbers (14-day probe, S168)
- `/search` hits: **663** · with a `received` ky: **483** · of those mapped to a known name: **483 (100%)**.
- Real 14-day distribution (received): **Shivani 217 · Alisha 182 · Reception Mobile 54 · Shavez 28 ·
  Manoj Bhati 1 · Dr Manoj 1** — confirms "Alisha-only" was purely the artefact.
- Exact join-key match to `console.db` calls: **391/663** (misses = incoming-missed, which have no join key,
  plus a few answered calls whose recording start-unix differs from the `/search` `start_time` by seconds).
- `console.db` calls carrying a join key at that build: **988**.

### 4.4 — The backfill (Stage 2a, built + proven; `build_call_agent`)
Writes the additive **`call_agent(join_key, agent, department, matched_how)`** table:
1. Load `agents.userid → name`.
2. From the `/search` hits already pulled by `myop_reconcile_layer` (**no extra API call**), for each record
   with a `received` ky that maps to a name, index `{phone10}_{start_time} → (name, department)`.
3. For each `calls.join_key`: **exact** match first; else **proximity** — same phone, nearest `/search`
   start within **≤90 s** (recording start vs ring start can differ by a few seconds). Record `matched_how`.
4. Coverage is printed inside `--dry-run --with-myop-reconcile`, so it is **measured before install**.
- Proof: builder `--selftest` **35/35** (existing paths intact) + `build_call_agent` unit **6/6** (exact,
  proximity, missed-skip, unmapped-skip).
- **Window caveat:** `/search` is time-windowed, so `call_agent` covers the pulled window. Recent calls are
  covered by the cron window; the back-catalogue needs a one-time larger pull (`--days 60/90`) — decide from
  the dry-run coverage number.

### 4.5 — How the page should read the agent (portal rev4, next)
Prefer **`call_agent.agent` → `verdict.agent` → `outbound.agent`**. `call_agent` fills in the answered calls
the verdict left blank, so staff shows on essentially every answered call. (This is the one remaining wiring
step; the page currently reads verdict/outbound only.)

---

## 5 — LIVE-DATA FINDINGS / PUNCH-LIST (folded into rev2/rev3)

| Finding | Fix |
|---|---|
| Timestamps are ISO with `+05:30` (e.g. `2026-07-03T16:52:03+05:30`) | `_split_dt` strips the tz and splits date/time for display. (Kin F-72: normalise tz before any datetime math.) |
| `phone10` blank on **505** outbound rows (0 incoming) | recover the number from the join-key prefix + the verdict's patient number; names then resolve on the recovered number. |
| AI-verdict column looked alarmingly "pending" | show `ai_outcome` with **fail-loud semantics**: "pending" ONLY when there is no verdict; "error" when `verdict.status`/`error` set; "no outcome" when a verdict exists but `ai_outcome` is blank (**919/2195** verdicts have a blank `ai_outcome`). |
| Recording link often blank on the call row | fall back to the `recordings` table by join_key. |
| Transcripts | render inline in the Call-Detail panel (PHI — behind the doctor gate). |
| Diagnosis / last-visit / clinic-id / your-review | surfaced everywhere (diagnosis IS live in `Patient_Master`, F-70). |

**A1 join sanity (from Stage A, still true):** `Call_Durations` spine = 1651 (+1 probe = 1652); of the
~1010 *recorded* calls **99.9%** matched a recording (the scary "61%" is just missed-calls-have-no-recording);
`unjudged` reconciles to the row (641 no-recording + 1 unmatched + 36 verdict-error + 4 judge-pending = 682).
**A2b:** `Daily_Summary` is `/search`-sourced → the reconcile reproduces it **14/14 real days** and corrected
the net-missed-open list **154 → 134**.

---

## 6 — THE PAGE (`/portal/console`, portal.py)

- **Routes:** `GET /portal/console` (doctor-gated via `doctor_required`) + `GET /portal/console.csv` (export).
- **Shell:** the existing `PAGE_HEAD` CSS tokens (`--bg/--card/--line/--muted/--blue`); a **🎧 Call Console**
  tile added to the Clinic tile group.
- **Views (4):** Call log · Conversations (phone-grouped threads) · Staff (performance summary) · New Leads
  (unknown incoming).
- **Filters (cascading, live counts):** Direction → Answered/Missed/Net-missed → Agent → Flag → Date + a
  free-text box.
- **Call Detail (unified expandable macro, rev3):** number · name · diagnosis · last-visit · clinic-ID ·
  staff · outcome · AI-verdict · your-review (doctor_flag/note/final_outcome) · flags · note · recording ·
  transcript. Used in log / threads / leads. The log is **day-grouped and collapsible** (nested `<details>`).
- **Delivery gate (F-63):** every route gets a Flask **test-client hit** (200 + expected content) before
  install — not just `py_compile`. rev3 passed 19/19.

---

## 7 — INSTALL STATE & THE EXACT NEXT SEQUENCE

**Live now:** portal console page **rev2 `7a862f74…`** (installed). **Delivered, NOT installed:** portal
**rev3 `54c239a3…`** (unified Call-Detail + day-grouped log) and the Stage-2a **builder `00b2175f…`**.

**Next-session step 1 (measure before installing anything):**
```
# WinSCP the delivered portal_console.py to the VPS as a STAGING copy — do NOT overwrite the live builder:
#   /root/wa/portal_console.new.py
md5sum /root/wa/portal_console.new.py            # expect 00b2175fa11e7d046befa4531a5834b6
/root/wa/venv/bin/python3 /root/wa/portal_console.new.py --dry-run --with-myop-reconcile --days 30
#   → read the "-- Stage-2a agent backfill … --" block: tagged / exact / proximity / coverage %.
#   (Consider a one-time --days 60/90 for the back-catalogue; /search is time-windowed.)
```
**Then, if coverage is good:**
1. Install the builder: `.new` → `md5sum` in place → `cp portal_console.py{,.bak-S169}` → `mv` → run
   `--build --with-myop-reconcile --with-transcripts` to populate `call_agent`.
2. Install portal **rev3** (`54c239a3…`) the same `.new`→md5→`mv`→`systemctl restart clinic-portal.service` way.
3. Build + deliver portal **rev4** = read `call_agent` (prefer `call_agent.agent > verdict.agent >
   outbound`); F-63 test-client gate.

**Install discipline (F-66, always):** `.new` upload → `md5sum` in place → `mv`; keep a timestamped `.bak`
before replacing; a filename is not provenance — trust the hash. A new/altered table needs the builder run
(or `--init`) before the page queries it (F-65).

---

## 8 — ROADMAP (staged, D300) — what's next, in order

1. **Stage 2a coverage measure → builder install → portal rev4** (reads `call_agent`). *(top task)*
2. **Capture AI reason/evidence** — `Call_Verdicts` has AI Reason + Evidence columns the builder currently
   drops; carry them into `verdicts` so the console shows *why* the AI ruled + feeds training.
3. **Follow-ups tab** — Settled (due − seen) + a **booked-not-visited no-show flag**, from the tracker's
   `Followups_Settled`.
4. **Track R — enter your-verdict** via curated dropdowns + free text → a new `console.db.dispositions`
   table (**one writer**) + an AI-training feed; retire the AppScript referee + `verdict_review.py`.
5. **Push-back to the staff callback tracker** — write to its **own calling-list tab** (never clobber
   `push_followups_today.py`, D235), two sections: auto "Appointment booked, not visited" + manual "Call
   list from Dr Manoj".
6. **B2** — recording proxy `/portal/rec/<join_key>` (local-first) + **Track K** `rec_cache/` (60-day / 1 GB,
   oldest-pruned; Drive never deleted). *(deferred)*
7. **B3** — arm the refresh cron `*/10 9–21 IST` running **`--build --with-myop-reconcile --with-transcripts`**
   (NOT plain `--build`, or the 154→134 correction + new transcripts + `call_agent` are lost each rebuild). *(deferred)*
8. **Gist metric 5** — verdicts pending referee, from `console.db`. No-shows → **Track N**.

**Owner input owed:** red-pen `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only, last).

---

## 9 — DECISIONS & FINDINGS THIS DOSSIER ENCODES

- **D299** — staff attribution: the handler is `/search` `_us[vl='received'].ky` → `Agents.UserId` (proven
  100%, 483/483); backfilled into the additive `call_agent` table (exact + ≤90 s proximity); the console
  prefers `call_agent > verdict.agent > outbound`. Extends D246 (new table, no rework).
- **D300** — console display/dedup rule (one-verdict-per-join_key `MAX(id)`, one-patient-per-phone, before
  any count — F-74; AI-verdict fail-loud) + the staged build order in §8.
- **F-74** — LEFT JOIN one-to-many fan-out inflated counts; dedup subqueries; sanity-check that a dimension
  sums to the spine.

*Full narrative: KB History Archive §S168. Backlog authority: HANDOFF_RUNBOOK §2 (v106). Contract of record:
`D297_Call_Console_Contract_v4_FINAL.md`. This dossier is the consolidated build reference — if it and the
contract disagree on a target, the contract wins; if it and the live code disagree on a fact, PROBE the live
source (D160/D188).*

**END OF D297 CONSOLE PORTAL BUILD DOSSIER v1 (S168).**
