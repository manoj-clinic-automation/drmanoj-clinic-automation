# START HERE — SESSION 195 (Dr Manoj clinic automation)

Continuing the clinic-automation project. I'm Dr. Manoj Agarwal, orthopaedic surgeon,
Advanced Orthopaedic Surgery Centre / Sanjeevni Medicos, Bareilly. Working protocol unchanged
(plain language; ONE step at a time, wait for my OK; full-file replacements or fail-loud
in-place patches; mask patient numbers to last-4, never print secrets; nothing live rebuilt
without my OK; manual workflow stays as fallback; build/test offline → py_compile → I install;
VPS python `/root/wa/venv/bin/python3` for the ledger).

## Phase 0 — verification before work
1. Open `CANONICAL_MANIFEST.md` and verify by md5. **NOTE (carried from S193 + S194):** the
   manifest / KB Register / Archive md5 fold and the on-box `live_pins.txt` regen are still
   OWED (the monolith is too large to rewrite in-session). Authoritative current state:
   `S194_Triple_Feature_Live_Pins.md`, `HANDOFF_RUNBOOK v129`, `S193_Close_Summary_and_Pins.md`,
   and this file. Doing the canon fold is the top housekeeping item whenever the owner wants it.
2. Read Tier 0 + `S194_Triple_Feature_Live_Pins.md`.

## FINAL LIVE PINS (from S194; confirm on the box)
- `finance_app.py`  `d2863c30ed0d3cc23126c7da13d9fe9b`  (S194E, auto-replay)
- `finance_ingest.py`  `6cb83302b022ca3d46a53b32011a7ddd`  (S194)
- `finance_ui/finance_daily.html`  `7ac94934faf2d4434e4b81974526f0b0`  (S194C)
- `finance_ui/finance_approvals.html`  `402fa7b263b86f75bfccc122f1a0ca37`  (S194)
- `staff_ledger.py`  `acd7b538ec9476f86e243c73eec3d3fd`  (S193, unchanged)
- email agent: `/root/deploy/email_agent.py` (config `/root/deploy/email_agent.json`, app pw on box),
  `email-agent.timer` (3-min). `dr_query.py` at `/root/deploy/`.
Live DB migrated S194: `sale_item.home_med` + table `mode_change_log`.

## What went live in S194 (all GREEN)
Daily Sale v2 page (⭐1) · home-medicine auto-tag + Hub card (⭐2) · cash/UPI reclass log +
Hub card (⭐3) · live doctor hand-overs (⭐4) · email query agent (⭐5) · daily-page switch
(Darpan lands on `/finance/daily`; `/finance/entry` fallback) · **Marg auto-replay** (a day's
Marg loads itself the moment the day is filed). Two July salary models delivered at session
start (`Salary_July_2026_TwoModels.xlsx`).

## WORKFLOW NOTE — read the email agent's replies directly
The connected Gmail IS the agent's account (`drmka.ortho@gmail.com`). So when the owner emails a
`Q:` command, DO NOT ask him to paste the reply — read it straight from Gmail
(`search_threads` → `get_thread`; the reply is the SENT `Re: Q:…` message from drmka.ortho).
Confirmed working S194.

## The backlog (S195)
1. **Re-load 17/18/19 Aug Marg** — their push payloads were pruned pre-F-155, so auto-replay
   can't reach them. Exports connected at `D:\Downloads\MARG REPORTS CLAUDE\SENT\`:
   `REPORT_18-08…` (carries 17 Aug) · `REPORT_19-08…` (18 Aug) · `REPORT_20-08…` (19 Aug).
   Days are filed → re-ingest links all bills, clears the `line_sum_vs_day_total` flags.
2. **08-18 = −₹20,599** (bills exceed the day) — check `Q: day 2026-08-18`; likely a
   double-import from the S193 rescue → de-dup rather than re-load.
3. **Home-medicine history backfill** — tools built + tested in S194 (local `kit_hmbf`:
   `extract_home_medicine.py` parses the period exports for Home-Medisun bills →
   `apply_home_medicine_backfill.py` sets `home_med=1` on the VPS, dry-then-apply, writes only
   that flag). Exports in the same connected folder.
4. **Email-agent hardening (⭐5 follow-up, owner asked S194):** (a) track "already answered" with a
   Gmail **label** instead of the read/unread flag, so a `Q:` is never missed even if the owner
   opens it before the 3-min poll (the current `UNSEEN SUBJECT "Q:"` filter skipped the 18:27
   `Q: sql …` because it had been read first); (b) **always reply, even on error** (run_query
   already returns error text — make sure the send path fires on the failure branch too). Kit files
   live in `deploy_kits/S194_EMAIL/` (email_agent.py current md5 `96cd7b75…`).
   → **DONE (S195 manojz leg):** ⭐5 hardening LIVE on the VPS (label-tracked, always-reply);
   see `S195_Email_Hardening_and_Marg_Guard_BuildState.md`.
5. **Canon fold** (owed S193+S194, now +S195): fold pins into the KB Register, refresh
   manifest/Archive, regenerate `live_pins.txt` on the box. (The EOS routine is now **v6** — step
   **A9** makes the Notion session-log a hard checkpoint; re-point the manifest/custom-instructions
   to v6 here.)
Carried: watch Darpan on the new page; the older May/June `line_sum` flags (small, real);
⭐0 Darpan signed-application scan vs advance `0cc0b26b38c5` (before the August close).

## Next-free numbers
**D334 · F-160 · A-D25 · Session 195.**

---

## ⭐ MEDICAL-PC LEG (21 Aug 2026) — post-update (one-off special session on the medical PC)

A separate leg of S195 ran **directly on the medical PC** (Marg box) via the Claude desktop
file bridge — the only way to finish the Marg auto-export, which needs Marg's own GUI. Full
record: **`S195_Medical_PC_Close_Summary.md`** + **`S195_Medical_PC_Macro_Guard_Runbook.md`**.

**Done on the box (`D:\SendToClinic`), nothing on the VPS:**
- Marg **auto-export macro** `marg_export_macro_v2.ahk` written + **calibrated** (5 positions);
  **export-only test PASSED**. Keys: Ctrl+Alt+C capture · Ctrl+Alt+G run · Esc quit. `RunGuard=false`.
- **Guard runs with zero install:** portable CPython 3.11.9 in `pyportable\`, xlrd 1.2.0 vendored
  in `xlrd\`; launchers auto-find them; `SETUP_CHECK.bat` → GREEN. `.py` md5s == canonical
  (`marg_report.py 28b47d44…`, `guard_and_send.py 6c248d57…`).
- VPS pins UNCHANGED; `verify_live_pins.py` unaffected. `token.txt` / `SEND_TO_CLINIC.bat` untouched.

**Owed for the next medical-PC session (needs Marg's GUI + a person there):**
- Reconcile REPORT_1 vs REPORT_2 / which login, then **flip `RunGuard := true`** and run ONE
  confirmed end-to-end test (generate → guard → SEND stages; Dr Manoj applies).
- Then the **Task Scheduler** morning run; later replicate for the Lab PC.

**Note for whoever picks up next:** the hands-on Marg/guard work can ONLY be driven from a Claude
session running ON the medical PC with `D:\SendToClinic` connected — a manojz/VPS session can read
these docs but cannot drive Marg.

---
*START_HERE_SESSION_195 · regenerated at the S194 close; updated post-close with the email-agent
hardening item + the Gmail-direct workflow note; updated again 21 Aug with the MEDICAL-PC LEG
close (macro calibrated + guard live-with-portable-python on the box).*
