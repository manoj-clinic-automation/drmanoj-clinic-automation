# HANDOFF RUNBOOK — v130 (Session 196 close · 23 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 196)

**Six kits, six first-pass GREEN installs, each landing exactly on its written projection. Two subsystems finished: staff attendance self-service, and the S193–S195 portal-health plan closed end to end. The weekly Auditor went on the clock.**

1. **S196_ATT1** — staff self-service: `self` role · today-only "My biometric" page · mark-me-present (server time = punch time; Shavez verifies, doctor approves; one/day; punch-blocks-request) · ≥60-min machine late minutes read-only in the day grid, Sundays included · `att_month_report` v2.6 folds approved requests as synthetic punches. Seven staff logins live; Arjun excluded (ruling).
2. **S196_ATT2** — the self page is an installable PWA: manifest + the real clinic-logo icons (extracted from the live Hub bytes), no service worker, nothing cached, ~180-day self sessions.
3. **S196_HLT1** — the renewals line: personal-GAS daily push (own one-path token, fail-closed; wired by the owner, token never in chat) → health card with recomputed-at-render days. LIVE, first push 11:01.
4. **S196_HLT2** — the crisis lesson's last inch: `health_line` in tile-summary + the Sanjeevni tile shows the worst problem FIRST. (S195 had built `_health_headline()` "for the portal tile" and nothing consumed it — F-161 candidate.)
5. **S196_HLT3** — the A4 month-vs-Marg block was DEAD since S195 (`today()` shadowed by a local date; both cards swallowed the error every render) — found by the OWNER's first real read of the page. One-line fix + a smoke check refusing the whole swallowed-exception class. F-162 candidate.
6. **Auditor scheduled** — weekly unattended, Mondays ~07:05 IST, trigger `trig_01XBRt7dcsXcjtmgdmemnR3x`, seed `AUDITOR_SEED_v1.md`, AF-# numbering, push+email summary. First run 24-Aug = slice 1 calibration.

Also: F-160 candidate — a kit delivered OUTSIDE the git tree because the publish path was assumed, not read from `PUBLISH_ALL.bat`; remedied same hour, re-hashed byte-identical.

**Final pins:** `staff_register.py 9087954c…` (v0.4) · `att_month_report.py 9ab98313…` (v2.6) · `finance_app.py 388c8ac0…` (smoke 668) · `portal.py ee749cd9…`. Full chains in `S196_Close_Summary_FINAL.md`.

---

## §1 — MENTAL MODELS (added this session)

- **The publish destination is read from the publisher's config, never assumed from a folder root.** The connected folder was `D:\dr-manoj-git\`; the repo was one level deeper. PUBLISH_ALL's own first line named it. (F-160)
- **A capability without its wire is a claim.** `_health_headline()` existed "for the portal tile" for a whole session while the tile stayed innocent. Grep for the CONSUMER, not the definition. (F-161)
- **A check that displays its own exception has died, not degraded.** "could not be read (…)" rendered politely for a session and read as a minor hiccup; both A4 cards were dead the entire time. A smoke check now refuses the class. (F-162)
- **The seeded-store differential is now a working tool for the finance smoke.** S193_F6's `seed_live_shape.py` + `migrations_concat.sql` + S194 store bits run the whole suite offline; identical-store baseline-vs-new with a fail-set diff catches faults BEFORE the box (it caught one in this session's own test code). Use it for every finance kit.
- **The request time IS the punch time.** Self-policing beats policing: delaying a mark-me-present request costs exactly what punching late costs, so there is nothing to gain by gaming it. Server clock only.
- **A reminder system's own death must be loud.** The renewals push runs daily even when quiet, precisely so "feed stale" can fire when the pusher dies.

---

## §2 — THE LIVE BACKLOG

**⭐0 — THE FOLD-IN (next session, EOS-light, S185 precedent — canon is FOUR sessions behind):**
reconcile the **F-series fork FIRST** (canonical next-free F-155 vs S193's F-155–F-159 vs S196's F-160–F-162 candidates — renumber S196's if needed) → Archive §S193…§S196 pure appends → Register bump (all ~10 moved pins, D333, D334, findings) → Fault Register extend → manifest rebuild → `live_pins.txt` regen (**verify_live_pins has been unprotecting since S193**) → **cold kit TAKE (due, 4 of 3–5)** → knowledge re-compaction (62%).

**⭐1 — owner actions (the copy-block in the S196 close chat):** token rotation (F-MARG + F-CRON, aging since 21-Aug, **still the highest-severity item**) · Darpan's application scan → approve `0cc0b26b38c5` before the Aug close · 17-Aug ₹20,000 ledger entry · file 21-Aug + apply the pending Marg push · 18-Aug 8-bill attribution · correction checklist day · July salary sheet · staff-phone PWA installs · Drive-for-Desktop on the medical PC · Labmate sample.

**⭐2 — watch the Auditor's first report (Mon 24-Aug morning)** — calibration run; triage its ≤3 recommendations.

**⭐3 — August month-end** — first full run on: SL5–SL7 + F6 ledger machinery, the present-request fold (v2.6), the D331/D332 advance rules. Watch, don't assume.

**Carried:** Club 3 router signatures (needs sample exports) · Club 4 (Amir/accountant answers) · expense-scan viewer · entry-page disabled-File explanation · NEFT assembly · repo mirrors of live finance/portal trees (with the auditor).

---

## §3 — INSTALL DISCIPLINE (reinforced this session)

- Baseline-smoke → swap → **grown**-smoke, with the projection written in the installer, remains the chain that catches everything; six for six today.
- Currency gates on EVERY live file a kit touches, including the second file of a two-file kit (HLT2 gated both and would refuse out-of-order installs).
- Kit payloads recovered **by hash from kit tarballs** when the repo tree is stale — never from the working tree by filename.
- Offline differential (identical seeded store, fail-set diff) before any finance kit ships.
- `bash -n` every installer; rehearse the refusal path, not just the happy one.

---

## §4 — THE EOS AUTOMATION BOUNDARY (held, same caveat as v129)

The assistant executed the close: close summary, this Runbook, START_HERE_197, build-state docs — written to project knowledge AND committed into the repo working tree (`deploy_kits/KB_canon_S196close/`). The monolithic Register/Archive/manifest fold stays owed as S197's ⭐0 (flagged, not skipped — now four sessions). **Owner residual: one PUBLISH_ALL double-click.** No pin-list copy this close (the list itself is what's stale; regenerating it is inside ⭐0).

---

*HANDOFF_RUNBOOK v130 · Session 196 close · supersedes v129. If §0, §2 or this end-marker is absent, this file is truncated and must not be used as canonical.*
