# START HERE — SESSION 167 (regenerated at S166 close)

Paste-to-resume. Evergreen procedure = `START_HERE_PROMPT_v5.md`; this is the S167 state snapshot. **Phase 0 first** — verify `CANONICAL_MANIFEST.md` by md5 (all tiers); read into context only Tier 0.

## Where we are
- Last session **S166** (design/vetting; **NO live code touched**). This opens **S167**. Next free: **D298 · F-72**.
- No open incident.
- **D297 — the Call-Intelligence Console — is SIGNED and build-ready.** The complete spec + all verified ground truth (schemas, Sheet IDs, Join Key, credential, GAS/tracker port map, recording sizes) is in **`D297_Call_Console_Contract_v4_FINAL.md`** (`42991579f3c20cbd4f512131e58c22f9`) — open it; build from it without re-probing.
- **Live code UNCHANGED:** `portal.py f0655abd…`, `portal_gist.py 55e111d7…`, `salary_engine.py 5514918…`, `staff_register.py cef76859…`, `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`.

## ⭐ Top task — BUILD D297 Stage A
Builder `portal_console.py` → SQLite `console.db`: join Call_Durations × Call_Verdicts (Join Key) × Patient_Master × Outbound_Log/Agents; conversation threads; two-way net-missed; reason-not-judged; latency; transcript back-pull; missed-call reconcile. `--selftest` + **dry-run counts reconciled to the live sheets** before ship. Re-verify pipeline md5s live==repo first. Then Stage B (`/portal/console` page + recording cache), then gist metric 5. (Full 14-track sequence in v4 contract §13.)

## Owner input owed
- Red-pen the rubric `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only — last).

## Carried
- F-71 rotation check (`.secret_key`/`.env` from the uploaded zip). F-69 (restart Call_Feed writer). F-70 (Core Dossier update). August salary reconciliation at month-end. Key rotations overdue. Notion current through S166.

**Confirm Phase 0 clean, then start D297 Stage A (or the owner's pick).**
