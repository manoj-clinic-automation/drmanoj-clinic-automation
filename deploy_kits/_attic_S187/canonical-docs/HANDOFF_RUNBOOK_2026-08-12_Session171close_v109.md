# HANDOFF RUNBOOK — v109 (2026-08-12 · Session 171 close)

*Tier 0. §0 what happened last · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to the KB Register (state) + Archive (history). This session installed live code NINE times across THREE files and FINISHED the Call-Intelligence Console: sweep signed off · enrichment live · digest in-portal · Console v3 FINAL design live · Hindi coaching report live.*

## §0 — WHAT HAPPENED LAST (S171) — the console FINISHED end-to-end

- **Acceptance sweep (task 0): SIGNED OFF.** ▶ playback · review persists across rebuild (D304 proven) · send-back badge/list/Resolve · No-shows 125 · spam→Block list. Sweep caught F-76 (SA write 403 → WITHDRAWN by D306) + F-77 (training CSV → fixed, BOM) + the No-shows quality defects (F-78 date-format correctness bug → fixed).
- **Track G LIVE:** `/portal/digest` renders from `console.db`; `daily_digest.py` repointed off `Verdict_Review` → **`8140f54310bc19c238e9cf11f34b21e7`**.
- **P2 patient enrichment LIVE:** taxonomy master shared to the SA; builder → **`552135b53564491dfe5629b2311b2076`** — `found=True rows=7610 updated=7548 inserted=62` (F-80 gspread-6.x `.client` fixed en route). Dead `Dr_Manoj_Call_List` sheet-push REMOVED (D306).
- **Console v3 FINAL LIVE:** `portal.py` → **`d74aa3f9054430981e719dcc7830cad6`** (chain `b513c67a→e6b80f0a→81e9ec58→11f1aea8→d74aa3f9`, backups on VPS). G1 cured at the root (stale flex rules DELETED — F-79); v3 design system (D307: tokens 15/13/12/11 · 1480px cap · one 7-col grid · SVG sprite · two-line cells); signals l2 shows AI verdict · staff outcome in the staff's own Hindi words (`HI_OUTCOME` ← `GAS_Outcome_Vocabularies_v1_S171.md`, new Tier-1); on-row review/send-back/☎ tel; no-shows due-day efforts timeline + table (agents via `call_agent`); **staff tab = 7-day matrix + per-agent day sections**; **`/portal/console/staffreport`** = Hindi coaching sheet (D308: आपने दर्ज किया ❌ → सही ✅ → क्यों → मरीज़ के शब्द → 🎧) with per-staff Copy-WhatsApp + CSV + Print/A4; **`/portal/rl/<jk>/<sig>`** HMAC recording-only staff links (403 on forged sig, gate-proven). F-63: 11 routes / 16 assertions incl. served-HTML checks.
- **D306–D308 · F-76 withdrawn · F-77/78/79/80 closed · F-81 OPEN** (duplicate log rows — see backlog). No incident. Full narrative: Archive §S171.

**Live now:** `portal.py` **`d74aa3f9054430981e719dcc7830cad6`** (v3 FINAL) · `portal_console.py` **`552135b53564491dfe5629b2311b2076`** · `daily_digest.py` **`8140f54310bc19c238e9cf11f34b21e7`** · cron `*/10 9-21` full 60-day build under flock (D303) · `portal_gist.py 55e111d7…` · `salary_engine.py 5514918…` · `staff_register.py cef76859…` · `staff_ledger.py 92665b64` · `att_month_report.py e64cad19…`. **PHI stores (F-31/F-49): `console.db` · `transcript_cache.db` · `console_reviews.db` · `rec_cache/` — ALL gitignored, never in repo/kit.**

## §2 — LIVE BACKLOG

⭐ **S172 top task — F-81 duplicate-calls investigation (builder-side):** same phone/time/duration rows appearing twice in the log (e.g. 16:51:55 ×2). Suspect the MyOperator reconcile double-insert. Read the builder's insert path, prove the natural key, dedupe or prove two genuine legs. Small, contained, data-integrity.

**Console follow-ons (owner-priority order to confirm):**
1. **Nightly `console_reviews.db` → Drive backup** (D306 tail; small systemd timer or cron; the db is the training corpus — protect it).
2. **MyOperator OBD click-to-call** — replace the ☎ `tel:` with a real OBD trigger (E.164, unique `reference_id`, panel-hex `user_id`; API card).
3. **Outcome-options admin UI** — `console_options` store seeded from `GAS_Outcome_Vocabularies_v1` so vocab edits need no build.
4. **Week PDF + Month PDF** — either a VPS PDF lib or extend the print-CSS path that already gives the daily A4.
5. **WhatsApp inline-reply panel** for selected agents (per-user permission flag; tile-masking pattern).
6. **PWA** (manifest + SW) · **webhooks-v2 call-pop** (needs Lokesh's v2 webhook).
7. **Insight Harvest** analyses (best calling time · retry-value · min talk duration · said-coming vs came) — data now all in `console.db`.

**Repo commit owed (order matters):** FIRST verify `.gitignore` carries `console.db`, `*.tmp`, `transcript_cache.db`, `console_reviews.db`, `rec_cache/`; THEN `launcher/portal.py` (`d74aa3f9…`) + `launcher/portal_console.py` (`552135b5…`) + `recordings-archive/daily_digest.py` (`8140f543…`) + `canonical-docs/` mirror of this EOS set incl. `GAS_Outcome_Vocabularies_v1_S171.md`. Behind it: the S162–S167 mirror backlog. Owner commits via GitHub Desktop.

**Carried (non-console):** Notion Tech & Systems catch-up (owed since S169; S171 page written at this EOS) · staff-master single-source project (owner-named, parked — needs its own plan) · Anthropic auto-reload/billing alert · unaccounted `ANTHROPIC_API_KEY` in `/root/wa/.env` · F-69 dead `Call_Feed` writer · F-70 Callback Tracker Core Dossier update · F-71 `.secret_key`/`.env` rotation check · August salary reconciliation at month-end (ledger salary-page retirement AFTER it) · overdue key rotations (Lokesh) · `wa_approve` nohup→systemd · WABA sends blocked pending Lokesh · D223 gist tile follow-ons · Docterz export migration · bad_due=1 junk feed row · Track V revenue (needs the PC) · Item 10 Track J rubric (blocked on the owner's red-pen).

## §3 — INSTALL DISCIPLINE
`.new` upload → `md5sum` in place → VPS-venv `py_compile` BEFORE promotion → `cp file{,.bak-SNNN}` → `mv` → md5-verify live → restart → acceptance. A filename is not provenance — trust the hash. New/altered table → builder/`--init` before the page queries it (F-65). Live Flask change → F-63 test-client hits on ACTUAL routes; **UI changes also assert on the SERVED HTML incl. absence of known-stale CSS (F-79/D307c), and ship an owner-approved HTML preview first (D307b)**. Prove any schedule by artefact invariants (F-41/F-75). Builder rebuilds `console.db` WHOLE — doctor data ONLY in `console_reviews.db` (D304/D306). One writer per store (D235). Never slice a date string — parse it (F-78). Never let a version-sensitive attribute path fail silently (F-80). VPS python `/root/wa/venv/bin/python3`. Salary/PHI never in repo/kit (F-31/F-49).

**END OF HANDOFF RUNBOOK v109 (Session 171).**
