# HANDOFF RUNBOOK — Session 100 (v53) — 2026-07-07

**Canonical set (NOW FULLY CONSOLIDATED — no more delta chains):**
- **KB `Clinic_Master_KB_SystemsRegister` v1.42** (consolidated, self-contained) — WINS on any conflict.
- **Umbrella Architecture v1.31** (consolidated, self-contained).
- **This Runbook v53** (self-contained; supersedes v52 / Session 94).

Prior: Session 94 v52.

> **Documentation policy (owner directive, S100):** from here on, canonical docs are built as
> **single fully-consolidated files, not delta chains.** Deltas stacked over many sessions caused
> the missing-file confusion that Sessions 95–99 had to clean up. Each new canonical version folds
> everything into one self-contained master with one changelog. This Runbook, KB v1.42, and
> Umbrella v1.31 are all single-file masters.

---

## §0 — WHAT HAPPENED (Sessions 95–100: the documentation-consolidation arc)

**All EOS-light. NO live code touched in any of these sessions.** This was a records-cleanup arc
that turned the fragmented delta chains into clean consolidated masters and recovered missing files.

### 1. KB consolidated → v1.42 (Session 95)
The KB had become "v1.38 base + v1.39 + v1.40 + v1.41 delta" — four files to read as one. Folded
them into a **single self-contained master, v1.42**, with one unified Decisions Index (D121–D145),
merged surveillance notes, and one changelog. Verbatim fold-in — no content altered or invented.
Confirmed along the way that **KB v1.37 has no standalone file in project knowledge**; its content
was already absorbed into the v1.38 base (present in §73), so nothing was lost.

### 2. Missing-file hunt + cold-kit recovery (Sessions 96–97)
Mapped exactly what was missing vs. what GitHub / cold-kits held:
- **GitHub `docs/` folder** turned out to hold an older full-history archive — including
  **KB v1.37 delta** and **Umbrella v1.27 delta** (both recoverable there, not lost).
- The one true gap was the **Umbrella v1.28 consolidated base** (GitHub's Umbrella chain skips
  from v1.27 to v1.29). Owner **recovered `Umbrella v1.28` (CONSOLIDATED through S73) and the deep
  `Umbrella v1.19` delta from cold-backup kit** and uploaded both. Gap closed.
- Confirmed GitHub is BEHIND project knowledge on several docs (it lacks KB v1.38/v1.40/v1.42,
  Umbrella v1.29/v1.30/v1.31, Call_Console v1.5, the API card, and this whole cleanup arc). That is
  a **commit-to-GitHub task**, not a lost-file problem.

### 3. Umbrella consolidated → v1.31 (Session 99)
With v1.28 in hand, folded **v1.28 (consolidated base) + v1.29 (S75) + v1.30 (S93)** into a
**single self-contained master, Umbrella v1.31**, with a consolidated Track-1 decisions note
(D121–D142) and one changelog. Verbatim fold-in. Companion to KB v1.42.

### 4. Runbook refreshed → v53 (Session 100, this session)
The Runbook was still v52 (Session 94) and predated the whole arc — its "canonical set" line still
pointed at the old fragmented docs. This v53 records the arc, **repoints the canonical set to
KB v1.42 + Umbrella v1.31**, and carries the full live backlog forward unchanged (below). A small
KB history-close (v1.43) folds this arc into the KB's own changelog.

**Net effect:** the three governing docs are now clean single-file masters —
**KB v1.42 · Umbrella v1.31 · Runbook v53** — and every previously-missing version is either in
hand (cold kit) or safely in GitHub `docs/`.

---

## §1 — STATE / MENTAL MODELS

> **No live-systems state changed in Sessions 95–100.** The live picture below is carried forward
> verbatim from the Session 94 (v52) close. It is still current.

**Track 2 live systems:**
- **Duration gate LIVE and healthy** — `call-hook.service` (:8098) up, `Call_Durations`
  filling, outcome unlock working. The S94 403 outage is CLOSED.
- **Dashboard** — `OutcomeLog.gs` updated (D143) and redeployed as a New version; URL stable;
  Today outcome view works.
- Everything else unchanged: WABA sends still BLOCKED vendor-side (D120); `wa_approve`
  still nohup (not systemd); watchman / health report / attendance / follow-up push live;
  key rotations overdue.

**Track 1:** unchanged. Step 5 COMPLETE; Step 7 (reconciliation) not started;
Hindi spelling task still open.

**Mental models (reinforced S94, still true):**
- **The duration gate depends on a fragile chain:** MyOperator Call webhook → OLS `/mo-callhook`
  → `call-hook` receiver → secret gate → `Call_Durations` tab → dashboard poll. A break
  *anywhere* shows up to staff as a permanent "Checking…". First diagnostic when tiles stick:
  check for today's `YYYY-MM-DD.jsonl` raw-log file and the panel webhook status.
- **`.env` is edited by hand and can silently merge lines** — always `grep` to verify a repair
  landed on separate lines before restarting; keep a timestamped backup first.
- **Duplicates are PC-side, not dashboard-side** — fix at generation, not display.
- **Docs are consolidated single files now (S100 directive)** — build the next canonical version
  as a full fold-in, never a delta to stack.

---

## §2 — BACKLOG (what to pick up next)

> The consolidation arc (S95–S100) is COMPLETE. The real project work resumes at the six-item
> agenda below, exactly where S94 left it. **Item 1 (duplicates) is still the next execution item.**

### THE SIX-ITEM AGENDA (owner-set S94) — recommended order
**Item 0 — DONE at S94** (isGenericAgent_ fix; Today console works).

1. **Duplicate patient entries (NEXT, SAFE).** PC-side de-dupe. Before building, see today's
   `Staff_Action_Today_*.xlsx` (or two duplicate rows) to learn *why* a patient doubles —
   same section twice, or two different sections. That decides the collapse rule.
2. **Reconcile "didn't pick up but visited"** — auto-settle on a real Docterz visit. Design
   together with **Track-1 Step 7** (shared Clinic-ID + mobile match). Needs design decisions.
3. **Trim the >200 staff list** — needs an OWNER POLICY call (caps; where the 124 dropouts
   go). Partly pre-designed as D66 "Living Staff List."
4. **Live staff-activity summary on doctor dashboard** — today live + yesterday audited.
   Audited half depends on item 5.
5. **AI audit layer (Stage 3, D62)** — overnight Haiku batch, ~₹200–350/mo, doctor-only flags.
6. **Historical taxonomy insights** — analysis only; BLOCKED on a de-identified export.

**Still owed from S94 (Claude to prepare):** a one-page DECISION SHEET for items 2 and 3 (the
exact choices needed), and the de-identified export spec for item 6, so those sessions are pure
execution.

### Track 1 backlog (unchanged, when owner returns to it)
- Hindi SPELLING corrections in `vitals_page.html` LIB strings.
- Step 7 — new-patient reconciliation (dovetails with agenda item 2).
- Living Clinic Data Map (§66.6).

### Track 2 live backlog (unchanged)
🔴 WABA authorizer/Lokesh + re-fire TEST · make `wa_approve` a systemd service · rotate
`WA_APPROVE_KEY` · 🔴 service-account key rotation (Lokesh) · AKEY_14 · arm timer-freshness
checker + maintenance jobs · clinic_health_report UTC→IST fix · courtesy-rotate
`CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145, low-risk hygiene) · consider a
`CALLHOOK_SECRET_MISMATCH_403` detector (panel Failed OR no daily raw-log by mid-morning).

### Documentation backlog (NEW — housekeeping, low priority)
- **Commit the current canonical set to GitHub** — the repo lacks KB v1.38/v1.40/v1.42,
  Umbrella v1.29/v1.30/v1.31, the refreshed Runbook, Call_Console v1.5, and the API card.
  GitHub `docs/` is otherwise a good historical archive. (Owner does the actual push.)
- Optional: drop KB v1.37 + Umbrella v1.27 from GitHub into the cold-kit archive so the
  offline backup is complete too.

---

## §3 — KEY PATHS / FACTS

- **Manual follow-up push:** CMD → `cd "C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"`
  → `python push_followups_today.py --push`. No flag = preview.
- **Call-hook:** `call_hook_capture.py` as `call-hook.service`, gunicorn 127.0.0.1:8098; OLS
  `/mo-callhook` → 8098; raw logs `/root/wa/call-hook/call_hook_logs/YYYY-MM-DD.jsonl`; secret
  gate = `CALLHOOK_SECRET` in `/root/wa/.env` (plain-alphanumeric, D144); panel Call
  webhook `?key=` must match it. Join key `client_ref_id`; connect = customer leg answered +
  talk >=15s -> `Call_Durations`.
- **Dashboard Apps Script files:** `WebApp`, `Callconsole`, `OutcomeLog`, `Dashboard.html`,
  plus config/MyOperator/Netting/Sheets/Main/Monitor/CallField/Probe/Diagnostics. Deploy rule:
  **edit existing deployment → New version** (never New deployment — that changes the URL).
- **Sheet:** Clinic Callback Tracker `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`;
  tabs commonly used: `Followups_Today`, `Followups_Settled`, `Followup_Outcomes`,
  `Call_Durations`.
- **Canonical docs (single-file masters):** KB v1.42 · Umbrella v1.31 · Runbook v53. Recovered
  from cold kit: Umbrella v1.28 (consolidated base) + v1.19 delta. Recoverable from GitHub `docs/`:
  KB v1.37 delta, Umbrella v1.27 delta, and older history.

---

## §4 — SESSION-START CHECKS (unchanged)
1. `System_Health` tab — any open incidents?
2. `Diagnostics.gs` live yet? If yes, was the 7 AM check clean today?
3. Any fault codes / banners from staff since last session?
If any incident open → address before new build. Else read KB + runbook, confirm, ask which
backlog item to start. **Default next execution item: agenda Item 1 (duplicate patient entries).**
