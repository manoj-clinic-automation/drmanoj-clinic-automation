# HANDOFF RUNBOOK — v127 (Session 191 close · 19 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
> §4 the EOS automation boundary.
> **The canon is current, folded in AT the close — and once DURING the session** (the F-141…F-146
> ruling fold: Register v5.38 · Fault v2.30, both reverse-application-proven, the twelfth GREEN pin
> run proving that fold end to end). **No live code moved. No live data changed. D332 minted AND
> signed. F-147…F-151 appended the session they were raised — none found by a failure.**

---

## §0 — WHAT HAPPENED (Session 191)

**The confirmation session.** The owner asked one question — *"confirm the work done in the staff
advances system"* — and the confirmation, performed on the live box rather than the record (F-135's
rule at scale), became the session. The system CONFIRMED: SL4 kit payload hash = live pin
`470bb113…`, owner-run selftest **218/218**, every D331/SL3/SL4 clause read in the live bytes and
holding, the live pages agreeing to the rupee. What the reading surfaced was the distance between
**D250's written judgment and the machine that had faithfully implemented only its arithmetic**:

**F-147** — the close records recovery the salary could not pay: the projected first real month-end
(Aug) would have recovered ₹30,000 against the ₹20,000 base, writing ≈₹14,000 of repayment no money
paid. D250's own clause ("if salary can't bear all, the instalment skips") was never built.
**F-148** — the drawer→ledger bridge does not exist and the code says so (`PENDING_LEDGER_WIRING`);
B6 died when D330 superseded D329 whole, and nothing re-homed the dependency.
**F-149** — D250's 3rd-skip perks-recovery flag can never fire; the machine hard-refuses instead.
**F-150** — July was ruled pre-policy at S151 ("PREVIEW ONLY, policy starts August", twice) and the
live July salary applied deductions AND incentive anyway: **₹16,552.38 over-deducted across all
twelve staff.** The owner's "JULY NO DED" was his own standing ruling, unenforced.
**F-151** — the live column header and help text say "fine", the word D250's statutory caution
prohibits.

**All five ruled by the owner the same day** (build · build-and-test · correct · build-as-setting ·
correct) and folded into **D332 — the Waiver, Defer & Repayment-Defined Advance layer**, signed as
contract v3 with the owner's refinements minuted. One sentence: *an advance is an amount plus a
repayment schedule defined at approval; the close collects the schedule; the owner can DEFER any
single collection with one tap and a reason; nothing recovers that the salary cannot bear;
everything owed is always visible with its months remaining.*

**Darpan, ruled concretely:** July closes ₹0 payable (fully composed, one narrated adjustment) ·
the 17-Aug money consolidates to ONE ₹20,000 SPECIAL, schedule **₹8,000 Aug · ₹4,000 × 3 Sept–Nov**
(₹7,000 drawable in Aug beside the ₹5,000 loan; cleared November; ₹15,000 steady from December) ·
ceiling **50% from August** · future pharmacy advances are REQUESTS — drawer untouched until the
owner's tap, which releases cash AND writes the ledger. The July sheet
(`Salary_July_2026_for_finalisation.xlsx`) built from the live table, **deliberately NOT in the
public repo (F-31/D320)**, on the PC outside the git tree — the owner finalises it as the waiver
workflow's first test run.

## §1 — MENTAL MODELS

1. **Carried:** survey the box before writing · the projection is the check · verify in the BOOK,
   never on the form (F-146) · a count beats a derivation · record pins as they move · a gate that
   fires is the system working · transcribe hashes from measured values · the record's path is
   READ, not recalled (the `advance_pct.json` slip — LEDGER_DIR was in the code all along).
2. **⭐ When a manual system becomes a machine, its written judgment clauses are requirements, not
   commentary (F-147/F-149).** D250's arithmetic was implemented workbook-exact twice over; its
   "if salary can't bear it" and "recover from perks" sentences were left behind — and no month had
   ever run short, so nothing noticed.
3. **⭐ A policy lives where the machine can read it, or the machine will contradict it (F-150).**
   F-134's shape one layer up: narrative is not procedure, and it is not configuration either.
4. **⭐ When a decision is superseded WHOLE, its dependencies are re-homed or explicitly re-owed
   (F-148).** B6 fell with D329; the need did not.
5. **⭐ Attach rules to instruments, never to people (D332).** The defer penalty binds to
   interest-bearing loans; today that is Darpan by construction, tomorrow it is whoever holds one —
   and no rule ever names him.
6. **⭐ One approval, both books.** A control that requires remembering to write twice will
   eventually be a control that was written once. The request-not-draw flow makes the cash and the
   ledger row the same act.

## §2 — LIVE BACKLOG

**⭐ 0. GO on the gated data corrections — BEFORE the August close** (owner's separate explicit GO;
each row shown before writing): (1) close out the ₹10,000 `fbd756fe1473` as settled-inside-July —
**the tripwire: un-closed, the August close collects it a second time** · (2) contra ₹15,000
`540acd6b8e7c` + ₹5,000 `d6162b009451` → ONE ₹20,000 SPECIAL, schedule 8/4/4/4, the signed
application scanned at booking (the D331 gate refuses without it — owner obtaining it) · (3) the
July composition adjustment entry · (4) `advance_pct.json` Darpan 75 → 50.

**⭐ 1. The D332 builds (S192): `S192_SL5` (waiver + settings-dates + F-151 wording) → `S192_SL6`
(defer + schedule lane + capacity + loud surfaces) → `S192_SL7` (perks view) → `S192_F6` (request
flow).** SL6's first collection is the September close — the August close waits only on ⭐0.

**⭐ 2. Owner-side, running now:** Darpan's signed application for the ₹20,000 SPECIAL · introduce
Darpan to the Sanjeevni daily entry portal for his daily submissions (17/18 Aug drafts → File →
approve) · finalise the July sheet (per-rules column + waivers + actual-paid) — the waiver
workflow's first test run, closed with actual amounts.

**⭐ 3. Surendra's ₹8,000 — still PENDING** (owner ruling, S191 fold). The recorded fact stands:
approved as-is it recovers IN FULL at the August close (no `against_month` → waterfall, instalment
= whole amount) against his ₹5,200 ceiling. Under D332 the gentler route is reject → re-enter with
a schedule.

**4. Watch (end Aug):** the first real month-end — now expected to collect Darpan ₹8,000 quota +
₹5,000 loan (after ⭐0), not the un-corrected ₹30,000. **5. F-146's UI fix** (refusal ≠ save) —
owed, unbuilt. **6. Owed and named, carried:** `dev_seed_smoke_db.py` schema stall · F-97 part 2
(the repo `finance/` tree TEN builds stale) · the untracked-76 triage · F-106 selftest split ·
F-107/F-108 mechanical checks · `marg_backfill.py` NOT-FILED flag · 4 May + 27 May · 12 Jun ₹8,487
· Hindi labels · WABA (F-82) · F-92 · F-93 · Tailscale + RustDesk · the scoped deploy-key decision.

**Cold-kit count: 3 of 3–5** (`KB_S189_close`). **Due within 1–3 sessions — take it at the S192 or
S193 close.**

## §3 — INSTALL DISCIPLINE

Unchanged from v126 (the D317 chain; gate constants transcribed; grep the whole output; single
chained VPS commands; count-equal kits prove by reproduction; rehearsal stores carry the live
SHAPE; financial-book changes stay gated migrations; PHI/`finance.db`/tokens never in repo, kit or
chat; ledger on `/root/wa/venv/bin/python3`, finance + asset on system python3) — plus S191's
addition: **all-staff salary artefacts never enter the public repo** (F-31/D320 applied to the July
sheet); they travel owner-side only, placed outside any git working tree.

## §4 — THE EOS AUTOMATION BOUNDARY (held at this close)

The assistant executed the close end to end: A0–A8, the project-knowledge swap, the repo files
staged onto the PC via the bridge, this Runbook, the manifest, the pin list LAST (A8). **The
owner's residual work is exactly two acts: one `PUBLISH_ALL.bat` double-click + the on-box
pin-list copy & `verify_live_pins.py` run** (expect the thirteenth GREEN, match 43). Portable
definition: `EOS_DEFINITION_PORTABLE.md`.

**END OF HANDOFF RUNBOOK v127 (Session 191 close).**
