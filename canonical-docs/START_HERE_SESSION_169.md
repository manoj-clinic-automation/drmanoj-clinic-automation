# START HERE — SESSION 169 (regenerated at S168 close)

Paste-to-resume. Evergreen procedure = `START_HERE_PROMPT_v5.md`; this is the S169 state snapshot. **Phase 0 first** — verify `CANONICAL_MANIFEST.md` by md5 (all tiers); read into context only Tier 0.

## Where we are
- Last session **S168** — **D297 Stage B1 (`/portal/console` page) LIVE** + **Stage 2a agent-backfill BUILT & PROVEN** (delivered, not installed). This opens **S169**. Next free: **D301 · F-75**.
- No open incident.
- **Live now:** `portal.py` **`7a862f74…`** (console page rev2 installed; **rev3 `54c239a3…` delivered-not-installed**) · `portal_console.py` **`81581a6c…`** (builder; **Stage-2a change `00b2175f…` delivered-not-installed**) · `portal_gist.py 55e111d7…` · `salary_engine.py 5514918…` · `staff_register.py cef76859…` · `staff_ledger.py 92665b64` · `att_month_report.py v2.5 e64cad19…`. `console.db` + `transcript_cache.db` are PHI (F-31/F-49).
- Build from **`D297_Call_Console_Contract_v4_FINAL.md`** (`42991579…`) — the signed spec.

## ⭐ Top task — MEASURE Stage-2a agent coverage, then wire it through
The delivered builder was NOT on the VPS at close (`md5sum /root/wa/portal_console.new.py` → "No such file" — WinSCP had not placed it). Exact sequence:
1. Upload delivered `portal_console.py` (md5 **`00b2175f…`**) as **`/root/wa/portal_console.new.py`** (staging — don't overwrite live). `md5sum` → `00b2175f…`.
2. Dry-run (writes nothing): `/root/wa/venv/bin/python3 /root/wa/portal_console.new.py --dry-run --with-myop-reconcile --days 30` → read the **`-- Stage-2a agent backfill … --`** coverage block. (Consider a one-time `--days 60/90` for the back-catalogue.)
3. If good: install the builder (`.new`→md5→`mv`→`--build --with-myop-reconcile --with-transcripts`) + install portal **rev3** (`54c239a3…`), then build **portal rev4** = read `call_agent` (prefer `call_agent.agent > verdict.agent > outbound`); F-63 test-client gate.

**Proven this session:** the handling agent = `/search` `_us[vl=received].ky` → `Agents.UserId` (100%, 483/483); real 14-day spread Shivani 217 · Alisha 182 · Reception 54 · Shavez 28 · others 1 — the "Alisha-only" look was a verdict-attribution artefact.

## Then (broadened D297 brief, staged — D300 · Runbook §2)
Capture AI reason/evidence · Follow-ups tab (Settled due−seen + booked-not-visited no-show) · Track R your-verdict dropdowns→`dispositions` (one writer + training) · push-back to the staff tracker's OWN calling-list tab (auto "booked-not-visited" + manual "Dr Manoj list"; never clobber `push_followups_today.py`, D235) · B2 rec proxy + Track K cache · B3 arm cron `*/10 9–21` = `--build --with-myop-reconcile --with-transcripts` · gist metric 5. No-shows → Track N.

## Owner input owed
- Red-pen the rubric `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only — last).

## Carried
- **Repo commit owed (grown):** `launcher/portal_console.py` (+ gitignore the PHI stores) + `launcher/portal.py` (console page) + S162–S167 code + docs mirror. One commit before the next code drop.
- Full transcript seed (resumable). Stage-B polish: label empty transcripts, dedupe duplicate transcript rows/Join-Key.
- F-69 restart `Call_Feed` writer · F-70 Core Dossier · F-71 secret rotation · August salary reconciliation · key rotations · delete stale `launcher/portal.py 81c2baef` · `wa_approve` nohup→systemd · Notion catch-up.

**Confirm Phase 0 clean, then start the Stage-2a coverage measurement (or the owner's pick).**
