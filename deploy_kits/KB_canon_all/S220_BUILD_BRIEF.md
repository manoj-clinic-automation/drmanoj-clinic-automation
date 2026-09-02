# S220 BUILD BRIEF — the one document Session 221 reads instead of ten papers

**02-Sep-2026, 19:05 → 23:15 IST. The intent session.** Nine installs on the live box, twenty pins
predicted offline and matched, one read back as declared; the first live day through all of it
reconciled to the rupee. Canon: Register **v5.68** · Archive **v1.66** · Fault **v2.50** (F-277
closed; F-280 … F-285) · Runbook **v152** · `START_HERE_SESSION_221`.

## What is live now (pins at the S220 close)

| file | pin | carries |
|---|---|---|
| `finance_ingest.py` | `d5ff50ad` | attach by ID only; a disagreeing name → `identity_dispute` (self-closing on a later agreeing export) |
| `finance_returns_audit.py` | `d693c0b4` | verdict **"identity disputed"** (amber, a question; never escalated) |
| `darpan_app.py` | `43abdd58` | the ₹1,000 gate in `needs` · `/api/spot-check` · `metrics` · English coverage text · `/api/intent` (owner only) · the card counts and lists parked bills with the full mobile |
| `finance_returns_escalate.py` | `c4864500` | `spot_list_day()` → `stock_spot_check` after Apply and hourly |
| `finance_ui/finance_approvals.html` | `e1652297` | gist line · gate line · row badges · Spot-count list · Intent signals block — all inside the returns card |
| `finance_app.py` | `f7dd9e57` | "Marg — total" reads `v_day_attribution` (returns subtracted, parked bills counted) |
| `darpan_card.html` | `aeb4fd7d` | *Din ki sale* counts parked bills; *bina pehchaan ke bill (N)* expands — bill · naam · ID · full mobile · ₹ |
| `marg_report.py` | `f9370dde` | the lines CSV carries `mobile` (ten digits or nothing) |
| `finance_intent.py` | `6f11548a` NEW | seven signals vs own baselines → `intent_signal`; cron `30 1 * * *` |
| `finance.db` | data | 17 returns re-keyed to their CNs; tables `identity_dispute` · `stock_spot_check` · `intent_signal` |

## The owner's rulings (verbatim intent) — all in `S220_RETURNS_INTENT_DESIGN` §8

Marg's user-wise register exists; every user is entry-only, modify only on his login · extend the
returns card's drill-down · clinic ID + mobile on bills from 18-Jun only; every return must have item
lines from then · bill gaps tracked from today · Darpan keys > 90 % of days · **cash-only refunds
(D362)** · the owner's portal all English (D366) · the metric: flagged share of return ₹ · the export
reaches the VPS next morning, manual · the doubling needs attention · **spot counts of flagged items
are the deterrent (D365)** · **"phone full 10 for me and Darpan" (D363)**.

## The measurements that matter

- The doubling is bigger returns, not more: ₹1,000+ returns 0 → 6 in August (45 % of the month).
- July 71 % examinable / 50 % flagged; August 75 % / 29 % — now two lines on the card.
- The first scorer run (as of 02-Sep): 7 returns in 4 weeks whose sale was UPI-paid (₹3,887); rate
  3.0 % vs 2.0 % median; items at 3–7× — DISPERZYME CD, NURVION LC, RUNVACE TP, DFO MR, ONKET DT,
  TAPAL ER. Inherited from August; the second week is the first real measurement.
- 02-Sep: 27 bills, 20 accepted, 7 parked (a name, no clinic ID), one CN; declared 17,644 = Marg net.

## Three rules this session paid for

1. **Reproduce the live bytes offline (previous bases + previous patchers → current pins, md5-proven),
   anchor on them, predict every pin.** A pin not held offline is *declared pending*, never guessed.
2. **Nothing that writes runs inside a kit folder on the owner's disk** — no compile, no `git
   status`; the device shell cannot delete its residue (F-233, F-285). Test numbers are assembled at
   runtime; the F-185 gate is right to refuse literals.
3. **Read the view that already knows** (D349). `v_day_attribution` had the day's truth since S180;
   two screens re-derived it and both were wrong.

## Owed / next

Darpan's Hindi list on the Vaapsi Desk (⭐1-1) · the D355 ladder at ingest (F-283) · the user-wise
register on the router · one word on the whole-history re-join · re-export 02-Sep so the seven
parked bills gain their mobiles · the S214/S215/S216 candidate sets and F-244.

*Lives in three places: project knowledge · `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S220\` ·
`F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`.*
