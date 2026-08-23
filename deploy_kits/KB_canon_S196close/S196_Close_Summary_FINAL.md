# S196 — CLOSE SUMMARY (FINAL) · 23-Aug-2026

**The attendance self-service + portal-health completion session. Six kits built, six first-pass GREEN installs, every one landing exactly on its written projection. The weekly Auditor scheduled. Canon fold-in debt now spans S193–S196 and is S197's ⭐0.**

## The live pins at this close (the list to trust)

| file | md5 | version / kit |
|---|---|---|
| `/root/staff_register/staff_register.py` | `9087954c8a4a891e8cdd848d6a9d48b2` | v0.4 (S196_ATT1 → ATT2) |
| `/root/att_month_report.py` | `9ab98313bbda7ae5555fb4b5a5a82c4b` | v2.6 (S196_ATT1) |
| `/root/finance/finance_app.py` | `388c8ac0fdfecdee6029c0033b9b0ef8` | smoke 668 (HLT1→HLT2→HLT3) |
| `/root/portal/portal.py` | `ee749cd9f3ac1294aab0d13ce069efc1` | S196_HLT2 |
| staff_ledger.py · email_agent.py · Marg signatures | unchanged from S195 pins | `acd7b538…` · `e535c4f8…` · `1b21f3bf…` |

finance_app chain this session: `df750243…`(S195) → `cfacce27…`(HLT1, 654→665) → `6fc3becc…`(HLT2, →667) → **`388c8ac0…`**(HLT3, →668). staff_register chain: `cef76859…`(S164!) → `c2059ea1…`(ATT1) → **`9087954c…`**(ATT2). Kit IDs: ATT1 `ba7127b1…` · ATT2 `33f94b40…` · HLT1 `51e9ed7e…` · HLT2 `c50986e8…` · HLT3 `fc99c7d1…`.

## What went live

1. **Staff self-service (ATT1)** — role `self` for portal logins mapped to staff rows (`staff.username`, `--map-usernames` printed all 12 clean); today-only "My biometric" page (`/register/me`): today's date + punch times, nothing else (owner leakage ruling); **mark-me-present**: same-day only · refused if a machine punch exists · one/day · reason required · **server receipt time IS the punch time** (phone clock never trusted; late bands run off it) · Shavez verifies (never his own) · counts only on Dr Manoj's approval · "#N this month" on the board. Out-punch stays on the machine. `att_month_report` v2.6 folds APPROVED requests as synthetic punches (`*` in the grid), fail-soft to v2.5.
2. **Machine late minutes in the day grid (ATT1)** — ≥60 min: exact minutes, loud read-only badge, stored in `daily_register.late_minutes`, form-proof; sub-60 quiet; Sundays via the transcribed D253 roster. Seven staff logins created by owner (awdhesh, pravesh, ranjeet, sukhveer, sandip, vikki, surendra); nothing for Arjun.
3. **PWA (ATT2)** — manifest + real clinic-logo icons (extracted from the live S187_H1c Hub bytes; Canva host unreachable from sandbox), linked on the self page only; NO service worker, nothing cached; self sessions ~180 days; "Add to Home screen" = the app.
4. **Renewals line (HLT1)** — personal Inbox-Janitor GAS (`Renewal_Nag_v2.gs`, wrapper keeps trigger + emails identical, pushes every daily run) → one-path token `FINANCE_RENEWALS_TOKEN` (own secret, fail-closed; owner wired it on the box; end-to-end proof = `bad_payload` with the real token) → JSON state file → health card: OVERDUE bad · stale-feed warn · ≤7d warn (reaches the tile) · ≤30d info · no-feed quiet info. Days recomputed from dates at render. **Card LIVE**: first push landed 11:01.
5. **The tile wire (HLT2)** — `tile-summary` carries `health_line`; the Sanjeevni portal tile shows the worst problem FIRST, unchanged when all clear. The Marg-401 crisis lesson finally reaches the glance surface.
6. **A4 revived (HLT3)** — the shadowed-`today()` fix; both A4 cards alive for the first time since S195; new class-refusing smoke check (no health card may be a swallowed exception).
7. **Auditor SCHEDULED** — weekly unattended cloud run, Mondays ~07:05 IST (trigger `trig_01XBRt7dcsXcjtmgdmemnR3x`), from `AUDITOR_SEED_v1.md` + unattended adjustments (slice rotation from AUDIT_RUN docs; AF-# numbering; owner-commands section instead of pause-for-paste; push+email summary). First firing 24-Aug = slice 1 calibration.

## Findings + decision to mint at the S197 fold-in

- **D334 (candidate)** — the present-request policy (request-time-as-punch · same-day-only · no-punch guard · verify-then-doctor · month-count visibility). Owner-ruled S196.
- **F-160 (candidate)** — kit delivered OUTSIDE the git tree (`D:\dr-manoj-git\` vs the real `…\drmanoj-clinic-automation\`): the publish destination was assumed from the connected-folder root instead of read from `PUBLISH_ALL.bat`'s own `REPO_DIR`. PUBLISH pushed without it; VPS pull had no kit. Remedied same hour by `mv` + full re-hash. F-135/F-141 family.
- **F-161 (candidate)** — `_health_headline()` built at S195 "for the portal tile", consumed by NOTHING: page red, tile innocent. Found by reading live bytes on the owner's "is it all taken care of?" question. Closed by HLT2.
- **F-162 (candidate)** — `_health_state`'s local `today = dt.date.today()` shadowed the module `today()`; BOTH A4 cards died into their except on every render since S195 while the S195 close recorded the check as done. Caught by the OWNER's first real read of the page (F-132 pattern). Closed by HLT3 + the class-refusing check.
- **⚠ F-SERIES FORK (fold-in must reconcile FIRST):** canonical Fault Register v2.32 says next-free **F-155**; S193 standalone docs used **F-155–F-159**; S196 candidates assume **F-160–F-162**. The F-108 drift pattern, live. No new bare F-numbers anywhere (the Auditor mints AF-# only) until reconciled.

## Verification discipline this session

Every kit: hash-verified base bytes (repo == pin for ATT1; kit-tarball hash-recovery for HLT1/HLT2 — repo `finance/`/`portal/` trees are S180/S182-stale) · offline pre-flight (py_compile · pyflakes · check_late_locals · check_row_keys) · **the finance smoke's first-ever OFFLINE runs** via the reconstructed S193_F6 seeded-store harness — differentials +11/+2/+1, every one exact, fail-sets byte-identical; the HLT1 differential caught a request-context fault in my own test code before the box could · installers rehearsed (ATT1 full end-to-end incl. refusal path) · six on-box installs, six first-pass GREENs: 654→665→667→668 finance · att+register suites grown and green.

## Debts carried to S197 (⭐0 = the fold-in, EOS-light, S185 precedent)

Archive §S193–§S196 appends · Register bump (all pins/decisions/findings; ~10 moved pins) · Fault Register reconcile the fork + extend · manifest rebuild · `live_pins.txt` regen (**verify_live_pins has been unprotecting since S193** — its list is built from Register v5.40) · **cold kit TAKE (due — 4 of 3–5 since S192)** · knowledge at 62% (re-compaction headroom exists once superseded S19x docs fold in) · `.gitattributes`: pin `*.md`/`*.gs` eol=lf (F-152 family) · refresh repo mirrors of live `finance/`/`portal/` trees (with the auditor). Owner actions list: `S196 pending jobs` block in the close chat (token rotation ⭐ still #1).

*S196 close, 23-Aug-2026. Companions: `S196_Attendance_SelfService_Build_State.md` · `S196_Health_Renewals_Build_State.md` · HANDOFF_RUNBOOK v130 · START_HERE_SESSION_197.*
