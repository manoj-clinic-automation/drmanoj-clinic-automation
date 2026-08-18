# HANDOFF RUNBOOK — v105 (2026-08-11 · Session 167 close)

*Tier 0. §0 what happened last · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to the KB Register (state) + Archive (history). This session BUILT live code: the D297 console builder.*

## §0 — WHAT HAPPENED LAST (S167) — D297 STAGE A BUILT (A1·A2a·A2b·A3), proven live

**One new live VPS builder: `portal_console.py` `81581a6cec84b4414827dc71d35548d3`** (`/root/wa/`) — the D297 Call-Intelligence Console spine builder. Built off the signed v4 contract, grounded in live source code, not memory (D160/D188). Selftest **35/35** offline; every stage proven against live data by `--dry-run` before `--build`.

- **A1 core** — joins `Call_Durations`(spine, probe excluded; 1651+1=1652) × `Call_Recordings`(bridge; 99.9% of *recorded* calls matched — the scary "61%" is just missed-calls-have-no-recording) × `Call_Verdicts`(2195; NOT-FILED=blank Claimed Outcome) × `Patient_Master`(diagnosis) × `Outbound_Log`/`Agents`; conversation threads; reasons-not-judged; latency. Full-rebuild-idempotent (atomic tmp→replace); every column found by **header name** (fail-loud on a missing required col).
- **A2a** — net-missed rule ported from live `Netting.gs`/`Config.gs` (incoming-miss candidate + either-direction connect; `RESOLUTION_MUST_BE_AFTER=false`). Faithful, but a **no-op on the real data** (outbound-miss-only barely exists) — not the cause of the reconcile deltas.
- **A2b `--with-myop-reconcile`** — the deltas were a *source* gap: `Daily_Summary` is built from the MyOperator **`/search`** log, not our webhook `Call_Durations`. Pulling the same source (client ported verbatim from `flag_investigator.py`) **reproduces `Daily_Summary` 14/14 real days (delta 0)** and corrects the over-counted open list **154 → 134**. `myop_daily` + `resolved_by='myop'` persisted.
- **A3 `--with-transcripts`** — Drive read-only (`get_media`, `text/plain`) → **persistent** `transcript_cache.db` (survives rebuilds, incremental by Join Key) → merged into `console.db`. First seed 1303/1447; batch-of-20 proven; **full seed resumable** (may still be completing).

**Faults (both caught in dry-run before any consumer existed — no incident):** **F-72** mixed tz-aware/naive datetime subtraction crashed `build_latency` → `parse_ts` strips tzinfo (one IST wall clock). **F-73** two live files disagreed on the `/search` `status` vocabulary (Netting numeric vs flag_investigator string) → resolved by a read-only `--myop-probe`: numeric wins. **D298** minted (console.db build architecture).

**Live now:** `portal_console.py 81581a6c…` (NEW) · `portal.py f0655abd…` · `portal_gist.py 55e111d7…` · `salary_engine.py 5514918…` · `staff_register.py cef76859…` · `staff_ledger.py 92665b64` · `att_month_report.py v2.5 e64cad19…`. `console.db` + `transcript_cache.db` built (PHI — F-31/F-49).

## §2 — LIVE BACKLOG

⭐ **NEXT-SESSION TOP TASK — BUILD D297 STAGE B (the `/portal/console` page), off the v4 contract §13-B**
1. **`/portal/console`** (doctor-gated): call log · conversation groups (expandable threads) · staff-performance summary · cascading filters (Direction→Agent→Answered/Missed/Net-missed→Flag/Quality→Date, live counts) · CSV export · **New-Leads** (unknown incoming) · **No-shows**. Reads `console.db` only (fail-loud/stale-aware, D236).
2. **`/portal/rec/<join_key>`** recording proxy (local-first) + **Track K** cache `/root/wa/rec_cache/` (60-day / 1 GB, oldest-pruned; ~0.30 GB measured). Drive never deleted.
3. **F-63 gate:** Flask **test-client route hits** (200 + expected content) on every new route before install.
4. **Arm the refresh cron** `*/10 9–21 IST` running **`--build --with-myop-reconcile --with-transcripts`** — NOT plain `--build`, or the 154→134 correction + new transcripts are lost each rebuild. (MyOperator `/search` is an API pull — a slightly longer window/cadence is fine; decide at build.)
5. **Gist metric 5** from `console.db` (verdicts pending referee) — the deferred card goes live.
Then per contract §13: G (digest→portal) · M (marketing marks) · send-back(reason) → **R** (referee-in-console + Drive export; retire AppScript referee + `verdict_review.py`) → **L/N/V** (conversion / no-show / revenue) → **T** (transcript hook) · **J** (judge rubric, after red-pen).

**Owner input owed:** red-pen `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only).

**Carried from S167:**
- **Repo commit owed:** `launcher/portal_console.py 81581a6c…` (confirm path alongside `portal.py`/`portal_gist.py`) **AND** `.gitignore console.db console.db.tmp transcript_cache.db rec_cache/` (F-31/F-49) BEFORE the commit. Also the S162–S166 code + canonical-docs mirror still owed.
- **Full transcript seed** completion (data, resumable): `--build --with-myop-reconcile --days 16 --with-transcripts`.
- **Stage-B polish (from live observations):** label empty/near-empty transcripts (a 5-char sample = silent call); dedupe duplicate transcript rows per Join Key (the 20→22 merge).

**Older carried:** F-71 rotation check (`.secret_key`/`.env`). F-69 restart dead `Call_Feed` writer. F-70 Core Dossier update. August salary reconciliation at month-end. Overdue key rotations. Delete stale `launcher/portal.py 81c2baef` dup. `wa_approve` nohup→systemd. Notion catch-up.

## §3 — INSTALL DISCIPLINE (F-66)
`.new` upload → `md5sum` in place → `mv`. `cp file{,.bak-SNNN}` before install. A filename is not provenance — trust the hash. New/altered table → `--init` before `systemctl restart` (F-65). Live Flask change → test-client route hit (200 + expected) before install (F-63). VPS python `/root/wa/venv/bin/python3`. **Salary/PHI stores never in repo/kit (F-31/F-49): `console.db`, `transcript_cache.db`, `rec_cache/` gitignored.** Uploaded PC zips: code-only (F-71/F-56).

**END OF HANDOFF RUNBOOK v105 (Session 167).**
