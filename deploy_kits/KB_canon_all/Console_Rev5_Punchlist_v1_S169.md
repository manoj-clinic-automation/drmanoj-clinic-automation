# D297 CALL CONSOLE — REV5 PUNCH-LIST & AUTONOMOUS BUILD PLAN — v1 (S169)

**Tier 1 · the ordered, build-ready backlog for the Call Console. Advanced Orthopaedic Surgery Centre, Bareilly.**
**Owner: Dr. Manoj Agarwal · built with Claude · created Session 169, 2026-08-11.**

> **Why this exists (owner mandate, S169).** *"Fold all so next session knows what is to be done, and from where, so I just say START and get the end product with minimum involvement."* This document is that fold. It turns the owner's S169 console review + the full D297 contract into a **top-down execution list**. Each item names its **source** (contract §/dossier §/roadmap #), the **exact file + function** to touch, the **change**, the **gate**, the **install steps**, and the **acceptance test** — so the next session executes it without re-deriving anything. **Decision of record: D302** (this punch-list is the canonical console backlog; execute in order; each item is independently shippable).
>
> **Sources of truth (do not re-derive):** the *what* = `D297_Call_Console_Contract_v4_FINAL.md` (`42991579…`); the *how it was built + every live fact* = `D297_Console_Portal_Build_Dossier_v1_S168.md` (`7429a696…`). If this list and the contract disagree on a target, the contract wins; if this list and live code disagree on a fact, PROBE live (D160/D188).
>
> **Masking/PHI:** last-4 only anywhere numbers appear. `console.db`, `transcript_cache.db`, `rec_cache/`, and any revenue/patient store are **PHI — gitignored, never in a repo or kit (F-31/F-49)**. The MyOperator bearer token lives only in the VPS `.env`.

---

## 0 — GROUND STATE AT S169 CLOSE (what is already true)

- **Builder** `/root/wa/portal_console.py` = **`00b2175f…` INSTALLED** (Stage-2a live; old `81581a6c…` kept as `portal_console.py.bak-S169`).
- **`console.db` REBUILT** this session with `--build --with-myop-reconcile --with-transcripts --days 60`: the additive **`call_agent`** table is live — **1001 distinct answered calls, all exact matches** (Shivani 457 · Alisha 346 · Shavez 104 · Reception 91 · Dr Manoj 2 · Bhati 1). Net-missed-open corrected **155 → 108**. (The build printed 1023 = call-*rows*; the table holds 1001 = distinct join_keys, PK-deduped — harmless, documented.) **D301** = build the agent backfill at `--days 60` (100% vs 75% at 30d; `/search` is time-windowed).
- **Portal `/root/portal/portal.py`** (port 8099, `clinic-portal.service`): live is **rev2 `7a862f74…`**. **rev4 `a7043849d9f77d4bc8c0f68ef3f0b1c3` BUILT + F-63-PASSED (22 assertions / 9 routes) — DELIVERED, staged at `/root/portal/portal.py.new`, NOT installed** (owner paused install to run this review). rev4 = rev3's UX **+** reads `call_agent` (precedence `call_agent.agent > verdict.agent > outbound`) across log display · filter · facet · dropdown · Staff tab. rev3's own changes (unified Call-Detail macro, day-grouped log, inline transcript text) are folded inside rev4.
- **Refresh cron NOT armed** → `console.db` only updates on a manual `--build`. This is the single biggest cause of "everything looks stale/pending." (Item 1.)
- Console page today has **4 views** (Call log · Conversations · Staff · New Leads). The contract calls for **No-shows · Revenue · Referee · Digest · Marketing** on top.

---

## 1 — THE EXECUTION LIST (top-down; each item independently shippable)

> **Standing gates for every item:** build offline → sandbox `py_compile` → (builder) `--selftest` / (Flask) **F-63 test-client route hits (200 + expected content)** → deliver `.new` → owner md5-verify in place → VPS-venv `py_compile` → `cp {,.bak-SNNN}` → `mv` → md5-verify live → restart service → acceptance. VPS python `/root/wa/venv/bin/python3`. New/altered table → run the builder before the page queries it (F-65). One writer per `console.db` table (D235). PHI stores never in repo/kit.

### ITEM 1 — Arm the refresh cron (B3) · *config only · do this FIRST*
- **Goal:** `console.db` refreshes automatically so the page is never a stale snapshot (kills most "pending" complaints).
- **Source:** contract §13 (B3); dossier roadmap #7; runbook §2.
- **Change:** cron `*/10 9–21 IST` running **`/root/wa/venv/bin/python3 /root/wa/portal_console.py --build --with-myop-reconcile --with-transcripts`** (NOT plain `--build`, or the net-missed correction + transcripts + `call_agent` are lost each rebuild). Use a small `--days` (e.g. 2–3) for the incremental daily window; the 60-day back-catalogue is already seeded (Item 0).
- **Gate:** dry-run the exact cron command once by hand; confirm `console.db` `built_at` advances and `call_agent` count holds. Watch the FIRST scheduled fire (F-41 lesson: prove by artefact/`built_at`, never the "installed" message; cron runs IST only if the box clock/TZ is IST — verify).
- **Acceptance:** `meta.built_at` moves every 10 min in clinic hours; page banner shows "fresh".

### ITEM 2 — Install portal rev4 · *already built + F-63-passed; just promote*
- **Goal:** the true staff handler shows on every answered call (log · filter · facet · Staff tab); inline transcript; unified per-row detail go live.
- **Source:** D299/D301; dossier §4.5; this session's build (rev4 `a7043849…`).
- **Steps (rev4 is staged at `/root/portal/portal.py.new`):**
  1. `md5sum /root/portal/portal.py.new` → expect **`a7043849d9f77d4bc8c0f68ef3f0b1c3`**.
  2. `/root/wa/venv/bin/python3 -m py_compile /root/portal/portal.py.new && echo OK`.
  3. `cp /root/portal/portal.py /root/portal/portal.py.bak-S169` → `mv /root/portal/portal.py.new /root/portal/portal.py` → `md5sum` (expect `a7043849…`).
  4. `systemctl restart clinic-portal.service`.
- **Acceptance:** `/portal/console` Staff tab shows the real split (Shivani top), agent filter lists real handlers, a call whose verdict said "Alisha" now shows its true handler. (F-63 already passed in build: filter-by-Alisha excludes the Shivani-handled call; CSV row carries Shivani.)
- **Note:** rev4 is the base for Items 3–4 (build from the installed rev4, D160).

### ITEM 3 — AI reason/evidence + pipeline lag, per row · *answers owner points #4 + #8*
- **Goal:** show *why* the AI ruled and the transcription/verdict **times** so lag is visible; stop the mysterious "pending".
- **Source:** contract §5 (latency) + §6; dossier §2 (builder drops AI Reason/Evidence), roadmap #2; owner review #4/#8.
- **Builder change (`portal_console.py`):** stop dropping **AI Reason** + **Evidence** (they exist in `Call_Verdicts`) — carry into the `verdicts` table; ensure `transcripts.transcribed_at` and `verdicts.judged_at` land in `console.db`; surface the `latency` table (t_call `captured_at_ist` → t_transcript `Transcribed At` → t_judge `Judged At`, and the three lags). Builder gates: header-by-name discovery, `--selftest`, dry-run.
- **Page change (`portal.py`):** in `_LOG_COLS`/`_log_row` add `ai_reason`, `evidence`, `transcribed_at`, `judged_at`; render them in the `detail()` macro beside the AI verdict (reason text + "transcribed HH:MM · judged HH:MM · lag Xm"). Add a **Pipeline/latency mini-view** (median/p90/max + backlog aging + "no recording / no transcript / judge pending / judge error" reason counts) — the early-warning instrument (F-69 lesson). Distinguish, per row, *why* a call has no verdict: no recording (missed) vs recorded-not-judged (real backlog).
- **Gate:** F-63 (routes 200 + reason/time strings present); builder selftest.
- **Acceptance:** every answered-call row shows the AI reason + transcribe/judge times; "pending" appears only for recorded-but-unjudged calls, with the reason named.

### ITEM 4 — Row-level patient context on every tab · *owner points #1 + #9*
- **Goal:** name · clinic-ID · diagnosis · last-visit visible at **row level** on every tab (not only inside the expand); Staff tab drill-through carries context.
- **Source:** contract §3; owner review #1/#9.
- **Page change (`portal.py`):** move diagnosis/clinic-ID/last-visit into `rowsummary()` (currently only in `detail()`); keep the expand for the rest. For the Staff tab, ensure the click-through to the filtered log carries the full per-row context.
- **Gate:** F-63 (row markup contains diagnosis/clinic-id at summary level).
- **Acceptance:** owner sees the four fields on each row without expanding, on log/threads/leads.

### ITEM 5 — "Your review" write-back + AI-training collection (Track R) · *owner point #10 · the big one*
- **Goal:** doctor enters a verdict via **curated dropdowns + free text**, saved once, collected in **one place** for AI training/refinement.
- **Source:** contract §10 (Track R); dossier roadmap #4; owner review #10.
- **Design (one writer, D235):** a new **`console.db.dispositions`** table (`join_key · final_outcome · note · refereed_by='manoj' · refereed_at`), written **only** by a new doctor-gated route (e.g. `POST /portal/console/review`), **idempotent** (write twice → one row, upsert on join_key). Dropdowns = the curated outcome vocabulary (from the AI Verdict Layer Master + Followup_Outcomes codes) + free text. The `dispositions` table **is** the AI-training feed (join_key ↔ transcript ↔ AI verdict ↔ doctor's final = the labelled set). Add a **self-review ⚠ flag** when the handler == ext-10 (Dr Manoj). Worst-first ordering optional (port `verdict_review.py` `sort_key`/bands) — can follow.
- **Gate:** F-63 including a POST round-trip (write → re-read shows the disposition; write-twice → one row). PHI: `dispositions` lives in `console.db` (VPS only).
- **Acceptance:** doctor sets a review on a call; it persists, shows on the row, and appears in a single export for training. **This also enables the eventual retirement of the AppScript referee + `verdict_review.py`** (cutover order in contract §10 — do that only after this is live + idempotent + the digest is repointed).

### ITEM 6 — Send-back-to-staff (free-text reason) · *owner point #5*
- **Goal:** doctor sends a call back to staff to call again, with a free-text reason, under a clear heading.
- **Source:** contract §0 / §12a-ish (C-write) + Appendix B (GAS `sendBackToStaff`/`SENT_BACK`); dossier roadmap #5; owner review #5.
- **Design (one writer):** a doctor-gated route writes to its **own** `console.db` table (e.g. `send_backs`: `join_key · reason · sent_by · sent_at · status`) AND pushes to the staff callback tracker's **OWN** calling-list tab — a section headed **"Call list from Dr Manoj"** — via a small push (mirror `push_followups_today.py`'s pattern). **NEVER clobber `push_followups_today.py` (D235).**
- **Gate:** F-63 + push dry-run (writes to its own tab only).
- **Acceptance:** doctor sends a call back with a reason; it lands in the staff calling list under the manual heading and shows as "sent back" on the console row.

### ITEM 7 — No-show next-day callback list (Track N) · *owner point #6*
- **Goal:** appointment booked but patient didn't show → auto-surface for next-day calling under a heading.
- **Source:** contract §12c (Track N); dossier roadmap #3/#5; owner review #6.
- **Design:** builder join **booked-but-not-seen** = `Followups_Today` (due) − `Followups_Settled`/visit (seen) for the date; surface as a console **No-shows view** with a section **"Appointment booked, not visited"** + close-the-loop columns (called back? · when · which staff · outcome · did they then show). Reads the tracker's pushed tabs — loosely coupled. Confirm the exact no-show tag against the live tabs at build (Stage-A verify).
- **Gate:** builder dry-run reconciles the no-show count against the tabs; F-63 on the view.
- **Acceptance:** the No-shows view lists yesterday's booked-not-visited with a next-day call action.

### ITEM 8 — Recording: local proxy + in-page player (Track K / B2) · *owner point #2*
- **Goal:** recordings open **in-page** (not a Google-Drive tab), served **local-first**.
- **Source:** contract §12 (Track K) / §13 (B2); dossier roadmap #6; owner review #2.
- **Design:** builder pulls recent recordings Drive→`/root/wa/rec_cache/` (cap **60 days OR 1 GB**, oldest-pruned; **Drive never deleted**, owner). New route **`GET /portal/rec/<join_key>`** serves local-first, Drive-fetch fallback for older, streamed to an in-page `<audio>` player. Replace the `target="_blank"` Drive link in `detail()` with the in-page player.
- **Gate:** F-63 (route streams audio; player renders); disk-cap prune proven.
- **Acceptance:** clicking ▶ plays the recording inside the page; old recordings still resolve via Drive fallback.

### ITEM 9 — The remaining D297 tracks (separate stages, any order after 1–8)
- **Track M — Marketing/spam** (contract §12a): a console mark → `console.db` flag + **block-list view** (numbers to lock at the MyOperator panel; the block itself stays a panel action) + optional `Do_Not_Call` row; marked numbers drop from New-Leads + net-missed-open.
- **Track L — New-caller conversion** (contract §12b): unknown incoming today → patient tomorrow (after `push_patient_mirror.py`); new-leads/day → converted → rate, by day and (where attributable) agent.
- **Track V — Daily revenue** (contract §12d): needs a **tracker-side daily push** (`revenue.py` summary → a `Revenue_Daily` Sheet tab or JSON, mirroring `push_followups_today.py`) → a portal Revenue view (day/period totals, consult/procedure/lab, concessions, ▲▼ vs ₹600). **Tracker code is on the clinic PC (PHI — never in repo/kit).**
- **Track G — Digest → portal** (contract §11): `/portal/digest` renders the 11:00 pulse + 21:30 digest live from `console.db`; repoint `daily_digest.py` off `Verdict_Review` onto `console.db` (this frees `verdict_review.py` to retire, with Track R).
- **Gist metric 5** (contract §13 C): "verdicts pending referee" tile from `console.db` — deferred card, no portal rework.

### ITEM 10 — Track J: judge quality rubric · *LAST · blocked on owner*
- **Goal:** the judge grades opening/info-asked/info-given/closing/digression on every row + a conduct-watch filter.
- **Source:** contract §6 (Track J); Appendix C rubric.
- **BLOCKER:** owner must **red-pen `D297_Call_Quality_Rubric_for_review.docx`** first. Only Track J waits on this; nothing else does. Propose-only (doctor confirms, D191).

---

## 2 — CARRIED (non-console) — keep in view, not part of the rev5 order
- **Repo commit owed (grown):** `launcher/portal_console.py` (`00b2175f…`) + `launcher/portal.py` (rev4 `a7043849…`) + `.gitignore` for `console.db` / `*.tmp` / `transcript_cache.db` / `rec_cache/` (F-31/F-49) + the S162–S167 code + canonical-docs mirror. **A git kit for the two console files + `.gitignore` + commit summary was produced at S169 EOS** (see the S169 kit); the S162–S167 files still need pulling from the PC/VPS.
- Full transcript seed completion (resumable); label empty/near-empty transcripts; dedupe duplicate transcript rows per Join Key.
- F-69 restart the dead `Call_Feed` writer (`CallField.gs`). F-70 Callback Tracker Core Dossier update. F-71 `.secret_key`/`.env` rotation check (kin F-56). August salary reconciliation at month-end. Overdue key rotations (Lokesh). Delete stale `launcher/portal.py 81c2baef` dup. `wa_approve` nohup→systemd. Notion catch-up. `wa_approve`/WABA sends blocked pending Lokesh.

---

## 3 — DECISIONS THIS DOSSIER ENCODES
- **D301** — Stage-2a agent backfill built at **`--days 60`**: 100% coverage (1001 distinct answered calls, all exact), net-missed-open 155→108. Rationale: `/search` is time-windowed; 30d gave 75%, 60d gave 100%; the daily cron stays incremental (small `--days`) while the one-time 60-day build seeds the back-catalogue. PK-dedup (1023 rows → 1001 distinct join_keys) documented as harmless.
- **D302** — this **rev5 punch-list is the canonical, ordered console backlog**; next session executes it top-down for minimum owner involvement ("say START → get the end product"). Each item is independently shippable behind the standing gates. Supersedes the scattered roadmap in the build dossier §8 as the *execution* authority (the build dossier remains the frozen build *reference*).

*Full narrative: KB History Archive §S169. Backlog authority: HANDOFF_RUNBOOK §2 (v107). Contract of record: `D297_Call_Console_Contract_v4_FINAL.md`.*

**END OF D297 CALL CONSOLE REV5 PUNCH-LIST v1 (S169).**
