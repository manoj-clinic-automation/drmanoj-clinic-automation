# HANDOFF RUNBOOK — v116 (2026-08-16 · Session 182 close — portal tiles live; a fail-open identity default closed; the live-code pins found unverified)

*Tier 0. §0 what happened · §1 mental models · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to KB Register v5.4 (state) + Archive v1.30 (history).*

## §0 — WHAT HAPPENED LAST (S182 — FULL; two green installs on `portal.py`, one driver placed)

Phase 0 green, and **proved against git bytes for the first time**: 45/45 manifest pins hashed against the cloned repo, independently of the kit's own SUMS file. The transcription hazard is closed by method rather than by care.

- **F-97, the finding that shaped the session.** `portal.py` was pinned `da417709…` (S176); the repo copy matched that byte-for-byte; **the box was running `34f038a765…`** with two live finance tiles present nowhere else. The pin and the repo agreed with each other and both were two sessions stale. Building the obvious way would have deleted the medical unit's **Daily Sale** and **Sanjeevni Medicos** tiles with every gate passing. **Phase 0 verifies documents; nothing verifies the live-code pins.**
- **S182_P1a — clinic portal tiles LIVE** (gate 42/42, run before any swap). **Daily Collection** for shavez/alisha/shivani, **Clinic** for manoj/bhawna **and shavez** — he holds the middle-approver checker seat, which the runbook's one-line spec had omitted and the seeded migration revealed. Labels hydrate from `clinic.tile.*` via `tile-meta`, client-side, so the portal never waits on the finance app. Legacy Google-Sheet tile retired.
- **S182_P2a — F-98 closed** (gate 48/48). A trusted device with **no SSO session** was treated as the doctor, reaching the Gist, the Call Console and the staff coaching report. F-84's pattern in the front door. Fixed keyed to `_sso_ready()` so **D264's inert-on-failure invariant survives** — a config failure degrades to the old behaviour instead of locking the owner out. It also explained the "missing tiles" report: no identity → every grant-only tile vanishes, proven by the *pre-existing* Manage Users tile vanishing too. **Confirmed against real logins afterwards, not just at the gate.**
- **S182_M1a — Marg backfill driver placed**, dry-run by default. Its dry run on the box refused immediately: `(medical, marg_export)` is seeded **active=0 with no column map rows at all**. Read-only survey: **121 medical days filed, 1 Apr → 13 Aug, all legacy_sheet**, and **`sale_item` = 0, `sale_line_item` = 0** — both stores never populated.
- **D320 minted** (repo stays public, owner ruling). **F-96 · F-97 · F-98 (fixed) · F-99** raised. **No incident.** Cold-kit count **2 of 3–5**.
- Live now: `portal.py` **`2784b1cb76abfb9dbe2407c38da5bd83`** · `marg_backfill.py` **`e101c595619dc39a19397abb040d64c9`**.

## §1 — MENTAL MODELS WORTH CARRYING

1. **A hash that matches the record proves agreement with the record, not with reality** (F-97). The stale pin was *reassuring* precisely because git agreed with it. Where a file is replaced whole, the kit must state the md5 it was built on and refuse any other.
2. **When a new thing and an old thing fail together, the new thing is not the cause** (F-98). Two new tiles vanished; so did "Manage Users", untouched since S164. That single observation moved the investigation from the change to the mechanism in one step.
3. **A check that cannot fail is not a check.** Every gate this session was run against the unmodified file to watch it fail, and one was run against a deliberately sabotaged copy. Two of a gate's own assertions turned out wrong and were caught that way.
4. **Rehearse the installer, don't read it.** Rehearsal caught an `importlib` loader bug that would have produced a **false red** on a perfectly good kit, at the console, at night.
5. **A silent success on live data is the worst available outcome** (Marg driver). An empty column map makes the adapter read zero rows while reporting ok — so the driver refuses on a mismatch and aborts if rows read ≠ rows in the file.
6. **A detector whose scope comes from the data it monitors is blind at zero** (F-99). Write that blind spot down when the detector is built, not when a unit goes dark.
7. **Integrity checks say nothing about whether content belongs** (F-96). 48/48 passed while the set carried patient names into a public repo.

## §2 — LIVE BACKLOG

⭐ **S183 top task — the Marg April→August backfill.** (a) **v2 driver** doing both stores per day: `ingest_day` → `sale_item` *and* `finance_returns.load_lines` → `sale_line_item` (the return pipeline needs the drug lines; today's driver writes only bills). (b) **`marg_export` column map + activation** — currently active=0 with zero map rows; map onto the parser's real headers (`bill_date · bill_no · clinic_id · patient_name · phone_last4 · description · amount · mode`), not the selftest's display names. (c) the fortnight chunks, 1 Apr → 15 Aug, ~10 exports with item detail. **Reachable and zero-risk:** filed days start exactly at 1 Apr, and both target tables are empty.

**Then, in rough order:**
1. **Clinic parallel-run checks** — a clinic day vs the Google Form to the rupee; the verify→approve flow exercised for real; the variance alarm observed. Note **F-99**: until the first clinic day is filed, nothing shouts about unfiled days.
2. **Wire `gas/VPS_Push_TrackerDay.gs`** in the clinic Gmail (Script Properties + ~21:30 trigger).
3. **F-97 structural fix** — something that verifies live-code pins as a class, not one kit at a time.
4. **Ask Darpan about 11 and 14 August** — both 100% cash across 48 bills, ₹38,355, against 40–76% cash on every other day. F-91's shape in the pharmacy. No code recovers this; only memory does.
5. Small and known: the clinic month-close prompt still says "Sanjeevni sale register" (the unit-name rewrite missed the string; also the `legacy_medicine_copy` scan labels) · the tile named "Clinic" collides with the section named "Clinic" · watch whether Shavez's "Awaiting your approval" KPI counts verifications or final approvals.
6. **Owner decisions still open:** the Docterz reception mode-selection fix (F-91) · Razorpay + ICICI MIS auto-forwards · lab module (parked).
7. Carried: the rest of the Marg chain (U7·U8·U9·U12) · WABA go-live (F-82, vendor) · security rotations · console follow-ons · cold-kit cadence (**2 of 3–5**).

**Medical unchanged** all session, proven at every gate.

## §3 — INSTALL DISCIPLINE (S182 revision)

The D317 chain stands: kit → `deploy_kits/` via `push_kit.bat` → `vps_deploy.sh <KIT>`. **Two additions this session:**

**The live-file currency gate.** Any kit that replaces a file whole carries the md5 it was built on and **refuses, touching nothing**, if the live file differs. Born from F-97.

**Gate before swap where nothing forces otherwise.** The finance kits swap then gate because a migration must run first. A portal change needs neither, so its gate runs **before** anything is touched — a red then costs nothing at all.

Unchanged and still binding: preflight every binary the script uses · stage from the kit dir · `.bak` backups · smoke as the gate · restart only on green · an **honest red** that states whether live files were touched and restores only what was · a re-issued kit takes a new name · never numbered steps, never pasted heredocs · salary/PHI/`finance.db`/raw Marg exports never in repo or kit (F-31/F-49, and D320 makes this sharper — the repo is public by ruling). **Rehearse the installer offline against a throwaway target before shipping it.** **EOS mechanics per D319:** the assistant writes the canonical set into project knowledge; the owner double-clicks the KB kit push and downloads the cold kit.

**A formatting rule for the assistant, learned twice this session:** deploy commands go in their own fenced block. Written inline followed by a full stop, the trailing dot gets copied and the installer refuses (`S182_P2a.`, `S182_M1a.`). Harmless both times — and the refusals were exemplary.

**END OF HANDOFF RUNBOOK v116 (Session 182).**
