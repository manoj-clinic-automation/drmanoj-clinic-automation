# START HERE — SESSION 168 (regenerated at S167 close)

Paste-to-resume. Evergreen procedure = `START_HERE_PROMPT_v5.md`; this is the S168 state snapshot. **Phase 0 first** — verify `CANONICAL_MANIFEST.md` by md5 (all tiers); read into context only Tier 0.

## Where we are
- Last session **S167** — **D297 Stage A BUILT** (A1·A2a·A2b·A3): the `console.db` spine builder is live. This opens **S168**. Next free: **D299 · F-74**.
- No open incident.
- **Live builder:** `portal_console.py 81581a6cec84b4414827dc71d35548d3` (`/root/wa/`) → `console.db` (+ persistent `transcript_cache.db`, F-31). Reconciles to `Daily_Summary` (14/14 real days) and corrects the net-missed-OPEN list (154→134) via the MyOperator `/search` layer. Selftest 35/35.
- **Live code otherwise UNCHANGED:** `portal.py f0655abd…`, `portal_gist.py 55e111d7…`, `salary_engine.py 5514918…`, `staff_register.py cef76859…`, `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`.
- Build from **`D297_Call_Console_Contract_v4_FINAL.md`** (`42991579…`) — the signed spec; §13-B is Stage B.

## ⭐ Top task — BUILD D297 Stage B (the `/portal/console` page)
`/portal/console` (log · conversation threads · staff summary · cascading filters · CSV · New-Leads · No-shows) reading `console.db`; `/portal/rec/<join_key>` proxy + Track K 60-day/1 GB `rec_cache/`; **F-63 test-client route hits** before install; **cron `*/10 9–21` = `--build --with-myop-reconcile --with-transcripts`** (not plain `--build`). Then gist metric 5. (Full sequence: Runbook §2 / contract §13.)

## Owner input owed
- Red-pen the rubric `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only — last).

## Carried
- **Repo commit owed:** `launcher/portal_console.py` + `.gitignore console.db/.tmp/transcript_cache.db/rec_cache/` (F-31/F-49); plus S162–S166 code + docs mirror.
- Full transcript seed (resumable). Stage-B polish: label empty transcripts, dedupe duplicate transcript rows/Join-Key.
- F-71 rotation · F-69 restart Call_Feed writer · F-70 Core Dossier · August salary reconciliation · key rotations · delete stale `launcher/portal.py 81c2baef` · Notion catch-up.

**Confirm Phase 0 clean, then start D297 Stage B (or the owner's pick).**
