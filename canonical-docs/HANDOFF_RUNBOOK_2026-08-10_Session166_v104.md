# HANDOFF RUNBOOK — v104 (2026-08-10 · Session 166 close)

*Tier 0. §0 what happened last · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to the KB Register (state) + Archive (history). This session was design/vetting — NO live code touched.*

## §0 — WHAT HAPPENED LAST (S166) — design/vetting, NO live code touched

**D297 — the Call-Intelligence Console — designed, vetted end-to-end, and SIGNED.** Everything was grounded by live probing, not memory (D160/D188):
- **Verdict store = two Sheets:** Tracker `1USjArkq…` (Call_Durations spine, Recordings, Transcripts, Followup_Outcomes, Patient_Master, Followups_Today/Settled) + **Call Audit (Doctor Only)** `1rq9VvB5…` (Call_Verdicts 2195 rows current, Verdict_Review, Doctor_Verdicts 19 rows/last-29-Jun — referee loop cold). One SA (`GOOGLE_SA_KEY`/`WA_SA_KEY`) reads both. Join Key `{phone10}_{call_start_unix}`.
- **The follow-up tracker (clinic PC) already pushes** `Followups_Today` (calling list) + `Patient_Master` (nightly, incl. Diagnosis) → conversion (L) + no-show (N) read pushed data, no migration needed. Revenue lives in the tracker (`revenue.py`, `/finance`) → brought in scope via a small daily push (Track V).
- **Most of the ask is a PORT** of the retiring GAS dashboard (`dashboard/*.gs`: Netting, MyOperator, OutcomeLog/WebApp send-back, compliance).
- **Recording sizing:** ~217 KB each; 60 days ≈ 0.30 GB → a 60-day/1 GB VPS cache is trivial (disk 88 GB free).

The full build-ready spec + verified ground truth is **`D297_Call_Console_Contract_v4_FINAL.md`** (`42991579…`). A call-quality rubric is out as an editable Word doc for the owner's red-pen (gates only Track J).

**F-71:** an uploaded follow-up-tracker zip carried PHI + `.secret_key`/`.env` (kin F-56); handled code-only, nothing committed; rotation check owed.

**Live now (UNCHANGED from S165):** `portal.py f0655abd…`, `portal_gist.py 55e111d7…`, `salary_engine.py 5514918…`, `staff_register.py cef76859…`, `staff_ledger.py 92665b64`, `att_month_report.py v2.5 e64cad19…`.

## §2 — LIVE BACKLOG

⭐ **NEXT-SESSION TOP TASK — BUILD D297 (off the v4 contract, `42991579…`)**
1. **Stage A — builder `portal_console.py`** → SQLite `console.db`: join Call_Durations × Call_Verdicts (via Join Key) × Patient_Master (diagnosis) × Outbound_Log/Agents (staff); conversation threads; two-way net-missed; reason-not-judged; latency stamps; transcript back-pull; missed-call reconcile (port MyOperator.gs/Netting.gs). `--selftest` + **dry-run counts reconciled to the live sheets** before anything ships. Re-verify pipeline md5s live==repo first.
2. **Stage B — page** `/portal/console` (log · conversation groups · staff summary · cascading filters · CSV · New-Leads · No-shows) + `/portal/rec/<join_key>` proxy + the **60-day/1 GB recording cache** (Track K). F-63 test-client route hits before install; cron `*/10 9–21`.
3. **Gist metric 5** from `console.db` (verdicts pending referee) — the deferred card goes live.
Then (own gates): G (digest→portal + repoint daily_digest) · M (marketing marks) · send-back (port) → **R** (referee-in-console + Drive export; retire AppScript referee + `verdict_review.py`) → **L/N** (conversion/no-show, read tracker pushes) · **V** (revenue push→portal) → T (transcript hook) · **J** (judge rubric, after red-pen).

**Owner input owed:** red-pen the rubric `D297_Call_Quality_Rubric_for_review.docx` (gates Track J only).

**Carried:**
- **F-71 rotation check** (`.secret_key`/`.env` from the uploaded zip). Overdue key rotations (`CLINIC_SSO_SECRET`, GCP SA key).
- **F-69** restart the dead `Call_Feed` writer (`dashboard/CallField.gs`; reconciliation degraded since Apr). **F-70** update the Callback Tracker Core Dossier from the live Sheet.
- Optional VPS snapshot weekly→daily (~₹600/mo) — whole-stack insurance (not a D297 dependency; dispositions export to Drive nightly).
- August salary reconciliation at/after month-end (approve+lock the register run; Darpan outstation not double-counted, D295); then retire the ledger salary page.
- WABA blocked on Lokesh; `wa_approve` nohup→systemd; delete stale `launcher/portal.py 81c2baef` dup; Notion current through S166.

## §3 — INSTALL DISCIPLINE (F-66)
`.new` upload → `md5sum` in place → `mv`. `cp file{,.bak-SNNN}` before install. A filename is not provenance — trust the hash. New/altered table → `--init` before `systemctl restart` (F-65). Live Flask change → test-client route hit (200 + expected) before install (F-63). VPS python `/root/wa/venv/bin/python3`. **Uploaded PC zips: code-only — never the `data/` folder (F-71/F-56).**

**END OF HANDOFF RUNBOOK v104 (Session 166).**
