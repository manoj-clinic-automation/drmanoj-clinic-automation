# HANDOFF RUNBOOK — v106 (2026-08-11 · Session 168 close)

*Tier 0. §0 what happened last · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to the KB Register (state) + Archive (history). This session BUILT live code: the D297 console page (portal.py) + the Stage-2a builder change (delivered, not yet installed).*

## §0 — WHAT HAPPENED LAST (S168) — D297 STAGE B1 (the `/portal/console` page) LIVE; STAGE 2a agent-backfill built & proven

- **B1 — the console page.** `portal.py` gained a doctor-gated **`/portal/console`** + **`/portal/console.csv`** reading `console.db` only (fail-loud/stale-aware, D236), with a **🎧 Call Console** tile. Four views (Call log · Conversations · Staff · New Leads), cascading filters (Direction→Answered/Missed/Net-missed→Agent→Flag→Date + free-text), CSV export, unified expandable **Call Detail** (number·name·diagnosis·last-visit·clinic-ID·staff·outcome·AI-verdict·your-review·flags·recording·transcript), day-grouped log. Built rev1→rev2→rev3; F-63 gate met (test-client 19/19).
  - **Live now = rev2 `7a862f74…`** (installed; a WinSCP overwrite briefly rolled to `f0655abd…`, caught by the md5 gate and re-installed — F-66 held).
  - **rev3 `54c239a3c645860cfd2914e5262e9e08` DELIVERED, NOT installed** (owner mid-review at close): the unified Call-Detail macro + day-grouped log + clearer New-Leads.
- **F-74 (fixed):** first render inflated counts (In 2276 > all 1651) — `LEFT JOIN verdicts`/`patients` fan-out; fixed by dedup subqueries `_DV` (verdict `MAX(id)`/join_key = newest) + `_DP` (patient/phone10). Caught in-browser, no consumer harmed.
- **Live-data punch-list (folded rev2/rev3):** `+05:30` timestamp split; phone10 recovered on 505 outbound rows; AI-verdict column fail-loud ("pending" only when no verdict; error vs no-outcome split); recording fallback; inline transcripts; last-visit/clinic-id/your-review shown.
- **Stage 2a — the staff-attribution prize (BUILT + PROVEN, delivered not installed).** The console's staff looked "Alisha-only" = a **verdict-attribution artefact**. Read-only `/search` probes proved the real handler: `_source._us` entry with `vl=='received'` → its `ky` = MyOperator UserId → **maps 100% to `Agents.UserId` (483/483)**. True 14-day spread: **Shivani 217 · Alisha 182 · Reception Mobile 54 · Shavez 28 · Manoj Bhati 1 · Dr Manoj 1**. Builder change (`portal_console.py`, from live `81581a6c…`) adds an additive **`call_agent`** table (`_us[received].ky→name`, exact-join then ≤90 s proximity), hooked into the existing `/search` pass (no extra API) and reported in `--dry-run`. Selftest **35/35** + `build_call_agent` unit **6/6**. Delivered `portal_console.py` **`00b2175fa11e7d046befa4531a5834b6`**.
- **D299** (agent attribution + backfill) + **D300** (console dedup/display rule + broadened staged build order) minted. **F-74** minted.

**Live now:** `portal.py` **`7a862f74…`** (rev3 `54c239a3…` delivered-not-installed) · `portal_console.py` **`81581a6c…`** (Stage-2a `00b2175f…` delivered-not-installed) · `portal_gist.py 55e111d7…` · `salary_engine.py 5514918…` · `staff_register.py cef76859…` · `staff_ledger.py 92665b64` · `att_month_report.py v2.5 e64cad19…`. `console.db` + `transcript_cache.db` (PHI — F-31/F-49).

## §2 — LIVE BACKLOG

⭐ **NEXT-SESSION TOP TASK — MEASURE the Stage-2a agent coverage, then wire it through.** The delivered builder was NOT yet on the VPS at close (`md5sum /root/wa/portal_console.new.py` → "No such file"; WinSCP had not placed it). Exact sequence:
1. **Upload** the delivered `portal_console.py` (md5 **`00b2175f…`**) to the VPS as **`/root/wa/portal_console.new.py`** (staging — do NOT overwrite the live builder). `md5sum` in place → expect `00b2175f…`.
2. **Dry-run (writes nothing):** `/root/wa/venv/bin/python3 /root/wa/portal_console.new.py --dry-run --with-myop-reconcile --days 30` → read the **`-- Stage-2a agent backfill … --`** block (tagged / exact / proximity / coverage %). `/search` is time-windowed, so a bigger one-time `--days 60/90` pass may be needed to backfill the back-catalogue — decide from the number.
3. If coverage is good: **install the builder** (`.new`→md5→`mv`→run `--build --with-myop-reconcile --with-transcripts` to populate `call_agent`), **install portal rev3** (`54c239a3…`), then build+deliver **portal rev4** = read `call_agent` (prefer `call_agent.agent > verdict.agent > outbound`) so staff shows on every answered call. F-63 test-client gate on rev4.

**Then (broadened D297 brief, staged — D300):**
- Builder: **capture AI reason/evidence** (Call_Verdicts has AI Reason + Evidence cols the builder currently drops) → show WHY the AI ruled + training.
- **Follow-ups tab:** Settled (due−seen) + **booked-not-visited no-show flag**, from the tracker's `Followups_Settled`.
- **Track R:** enter your-verdict via curated dropdowns + free text → `console.db.dispositions` (ONE writer) + AI-training feed; retire the AppScript referee + `verdict_review.py`.
- **Push-back to the staff callback tracker** in its OWN calling-list tab, two sections: auto "Appointment booked, not visited" + manual "Call list from Dr Manoj". **Never clobber `push_followups_today.py` (D235).** Reception Mobile = ext16 named agent, leave as-is.
- **B2** recording proxy `/portal/rec/<join_key>` + **Track K** `rec_cache/` (60-day/1 GB, oldest-pruned). **B3** arm cron `*/10 9–21 IST` = `--build --with-myop-reconcile --with-transcripts` (not plain `--build`, or the 154→134 correction + transcripts + call_agent are lost each rebuild). No-shows → Track N.
- Gist metric 5 (verdicts pending referee) from `console.db`.

**Owner input owed:** red-pen `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only).

**Carried:**
- **Repo commit owed (grown):** `launcher/portal_console.py` (+ `.gitignore console.db / .tmp / transcript_cache.db / rec_cache/`, F-31/F-49) **AND** `launcher/portal.py` (console page) **AND** the S162–S167 code + canonical-docs mirror. One commit, before the next code drop.
- Full transcript seed completion (resumable). Stage-B polish: label empty/near-empty transcripts; dedupe duplicate transcript rows per Join Key.
- F-69 restart the dead `Call_Feed` writer. F-70 Callback Tracker Core Dossier update. F-71 `.secret_key`/`.env` rotation check. August salary reconciliation at month-end. Overdue key rotations (Lokesh). Delete stale `launcher/portal.py 81c2baef` dup. `wa_approve` nohup→systemd. Notion catch-up. `wa_approve`/WABA sends blocked pending Lokesh.

## §3 — INSTALL DISCIPLINE (F-66)
`.new` upload → `md5sum` in place → `mv`. `cp file{,.bak-SNNN}` before install. A filename is not provenance — trust the hash. New/altered table → run the builder/`--init` before the page queries it (F-65). Live Flask change → test-client route hit (200 + expected) before install (F-63). VPS python `/root/wa/venv/bin/python3`. **Salary/PHI stores never in repo/kit (F-31/F-49): `console.db`, `transcript_cache.db`, `rec_cache/` gitignored.** Uploaded PC zips: code-only (F-71/F-56).

**END OF HANDOFF RUNBOOK v106 (Session 168).**
