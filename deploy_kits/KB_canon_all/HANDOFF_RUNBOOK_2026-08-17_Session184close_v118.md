# HANDOFF RUNBOOK — v118 (2026-08-17 · Session 184 close — the Sanjeevni cash books corrected LIVE, exceptions regenerated, the D322 holiday classifier shipped, and the reserve/daily-flow model designed end-to-end)

*Tier 0. §0 what happened · §1 mental models · §2 live backlog (⭐ top task at head) · §3 install discipline. Companion to KB Register (state) + Archive (history). **⚠ This session left canonical housekeeping OWED — see §2 item 0.***

## §0 — WHAT HAPPENED LAST (S184 — FULL; a long, multi-thread session)

**Thread 1 — the Sanjeevni (medical) cash books were CORRECTED LIVE.** The −₹30,056 was diagnosed to the cell: the 13-Aug deposit was subtracted in the typed opening AND again by the sheet formula (double-counted; one late-filed row). Then, survey-first (`S184_S1a`, a read-only DB survey — it caught that `finance.db` already held the sheet's 31 deposit movements ₹16,59,114 + 36 carry-forward adjustments −₹84,533, so a blind "add 16 deposits" would have double-counted ₹16 lakh):
- **`S184_C1a`** (gated migration, INSTALLED): 31 sheet deposits → **16 Yes Bank verified credits** (₹16,45,600); 36 legacy adjustments removed (backed up in `s184_removed_*`); **₹40,000 Darpan advances** as drawer expenses (no staff_id → NOT posted to Staff Ledger, owner's choice); ₹337 procedure-medicine as noncash. **Closing 13 Aug −30,056 → +27,654.** `day_line` (sale money) byte-identical. Marker `migration.S184_cash_correction`. Backup `finance.db.bak_S184C1_20260817_065446`.
- **`S184_C2a`** (gated migration, INSTALLED): carry_forward_break + negative_cash are created ONLY by the one-shot importer, so C1a left them stale. C2a resolved all 36 breaks and recomputed negative_cash from `v_cash_ledger` to the **29 real parking-window days** (4 Jun–4 Aug), each labelled "cash parked with Dr Bhawna ahead of a bank trip (verify from her copy)". Marker `migration.S184_C2a_exceptions`. Dashboard now: cash-in-hand **₹42,993**, unexplained adjustments **0**.

**Thread 2 — the D322 missing-day classifier shipped LIVE (`finance_app.py` 86382f62 → `c66bec2b`).** Kit `S184_F1b` (reship of F1a). `refresh_missing_days` revised per **D322**: Sundays + attendance-sourced clinic holidays (`clinic_holiday` table + `festival_day` clinic_closed=1) → optional kind **`clinic_holiday`** (low, not owed); genuine weekday gaps → owed `missing_day`. New `clinic_holidays()` helper reads the attendance DB read-only, **fail-soft** (`FINANCE_ATTENDANCE_DB`, default `/root/staff_register/staff_register.db`). **F1a first went RED (F-106):** its `--selftest` asserted the *pre-S184* store state (cash negative, breaks open, marg unmapped) — our own corrections read as failures; the gate correctly restored. F1b made those four checks **state-adaptive**. **314/314** on the corrected store.

**Thread 3 — Darpan's 14/15 Aug filed as DRAFTS; the app enforced correctness (F-105).** The catch-up was BLOCKED until the deposits were booked — the Submit guard refused because the opening carried the −₹30,056 (negative). This proved the record ("catch-up needs nothing above") wrong and the box right. After C1a, 14 Aug (cash 11,413/UPI 6,530) and 15 Aug (cash 3,926/UPI 4,925) were entered on the maker form and **saved as drafts** (the form requires 3 scans or a reason to Submit; owner chose Darpan attaches scans + submits, Manoj approves). **16 Aug not yet closed** (Sunday — now optional under D322).

**Thread 4 — the reserve / daily-flow model designed end-to-end (NOT built).** Four design docs in project knowledge: `S184_Reserve_Counter_Person_Design` (biometric-as-HINT both ways; standard Darpan-maker/Manoj-checker gate; FOUR cash destinations — Darpan drawer / Dr Bhawna / Dr Manoj / kept-by-reserve; multi-day cumulative stretches reconciled by Marg (sale) + bank (UPI); extensible counter-person registry seeded Vinay Saxena), `S184_Reconciliation_Workbench_Design` (one-screen Marg⋈bank⋈entry, cash→UPI suggestions, correction log — mostly reads existing data), plus the holiday and parking docs.

**Thread 5 — the opening-float question is OPEN and instrumented.** Proven: booking the 29 negatives away is *mathematically impossible at float 0* (short ~₹85k = the first-week float, the sheet's 8-Apr ₹99,017 injection). So "no negatives" and "drawer ≈ ₹43k" are mutually exclusive. Delivered `Sanjeevni_Cash_Reconciliation.xlsx` (4 tabs) — fills to a float verdict from Darpan's drawer count + Dr Bhawna's held cash. **Awaiting those two numbers**; both booking paths are prepped (float≈0 → book nothing; float≈85–99k → gated `S184_C3a` opening-float-with-Bhawna migration).

**D322 minted. F-105, F-106 raised. No incident** (every failure caught by a gate). An expert critical evaluation of the whole design was delivered (accuracy / convenience / single-place recall + prioritised suggestions; the owner accepted #1–4, #6; #5 today; #7 with a blank-but-flagged count field; Hindi to be shown first).

## §1 — MENTAL MODELS WORTH CARRYING
1. **Survey the box before writing to it.** The read-only `S184_S1a` survey is the only reason C1a didn't double-count ₹16 lakh — the record said the deposits were unrecorded; the box said they were already there. D321's lesson, one layer up.
2. **A self-test that asserts a DATA STATE becomes a liability the instant the data is legitimately corrected (F-106).** Same family as F-88 (currency) and F-97 (stale pin). Separate *invariant logic* from *store state*; the latter must be state-adaptive or fixture-based, never frozen.
3. **The bank arbitrates; the human confirms.** UPI/card settle per-day regardless of a lumped report — so a reserve person's cumulative figure is a cross-check, not the source. Cash is the remainder.
4. **A negative drawer is unrecorded movement, not loss — but you cannot book it away without the float.** The 29 negatives need ~₹85k of first-week float parked with Dr Bhawna. Booking them and keeping "drawer ≈ ₹43k" is arithmetically impossible; only a physical count resolves which is real. Don't fabricate a schedule to make a chart look right.
5. **The app enforcing correctness looks like an obstacle and is a feature (F-105).** The Submit guard blocking the catch-up on negative cash was the D313 invariant doing its job.
6. **Keep the common path trivial.** The reserve/workbench/multi-day model is rich; the normal Darpan day must stay a two-field one-tap entry (progressive disclosure), and the labels must be Hindi-first.

## §2 — LIVE BACKLOG

**⭐ 0. OWED CANONICAL HOUSEKEEPING (do FIRST at S185 open — debt compounded from S183).** This session shipped live code + data but did NOT fold the canon. Owed, precisely:
- **KB History Archive** append **§S183 AND §S184** (still at v1.30 → should reach v1.32). S183's append was itself deferred to "S184 opening" and not done.
- **Fault_Action_Register** apply **F-100–F-104 (S183, owed)** + **F-105, F-106 (S184)** → from v2.18 to ~v2.20.
- **KB Register** v5.5 → v5.6: live-file pin **`finance_app.py` 86382f62 → `c66bec2b`**; markers `migration.S184_cash_correction` + `migration.S184_C2a_exceptions`; **D322** into the decisions index; **F-105/F-106** into the findings index; C1a/C2a/F1b live-state.
- **CANONICAL_MANIFEST** rebuild + **MD5SUMS** + `START_HERE_SESSION_185` promotion. Manifest STATUS still reads "current at S183".
- ⚠ **`verify_live_pins.py` will report DRIFT on `finance_app.py`** at S185 open — that is EXPECTED (box = c66bec2b, Register still says 86382f62). Correct the Register FROM the box (D321), do not re-flag.

**⭐ 1. Resolve the opening float, then book.** Get Darpan's drawer count + Dr Bhawna's held cash into `Sanjeevni_Cash_Reconciliation.xlsx` Tab 1 → the verdict says which: float≈0 (book nothing) or float≈85–99k (ship the prepped gated `S184_C3a`). Owner said "book provisionally" — but the honest booking needs this number; the count is 5 minutes.

**Then, in rough order:**
2. **Darpan submits 14 & 15 Aug** with the 3 scans; Manoj approves. **Mark 16 Aug** (Sunday, now optional) — file if a sale, else leave (no longer owed).
3. **Build the reserve / counter-person model** (schema: counter_person registry + held-by-reserve custody; app: biometric-hint + 4-way cash destination + multi-day stretch reconciled by Marg+bank; form: picklist + "cash handed to" + date-range). Sequence AFTER F1b (both touch finance_app.py). **Show Hindi labels for owner approval BEFORE building the UI.**
4. **Build the reconciliation workbench** (Marg⋈bank⋈entry one screen; cash→UPI suggestions graded like D315, never auto-apply; correction log via audit_log) — highest value / lowest risk, mostly reads existing data; delivers the F-91 fix. Add the **drawer-count field (accept blank but flagged)** here (#7).
5. **F-104 WALK-IN reclass** — 118 line_sum_vs_day_total legacy no-ID Marg bills.
6. **Self-test hardening (F-106 follow-up):** split the finance_app `--selftest` into invariant-logic vs seeded-fixture checks so a data correction never blocks a code deploy.
7. Carried: WABA go-live (F-82, vendor) · security rotations · console follow-ons · the S185 canonical fold-in above.

**Cold-kit count: 3 of 3–5** (F-89). One is due soon — but take it AFTER the S185 canonical fold-in so it captures the finalised set.

## §3 — INSTALL DISCIPLINE (unchanged, reinforced)
The D317 kit chain stands; every S184 kit ran it (SUMS → KIT_ID → **currency/state gate** → smoke/selftest BEFORE swap → backup → apply → verify → honest red that restores). This session added the **read-only survey kit** pattern (S184_S1a) and the **state-adaptive self-test** (F1b, F-106). Financial-book changes remain **gated migrations, offline-rehearsed against a copy of the real store, reversible, never ad-hoc SQL**. `verify_live_pins.py` (D321) run at every open/close; Register corrected FROM the box. PHI/finance.db/raw Marg exports never in repo or kit (F-31/F-49/D320).

**END OF HANDOFF RUNBOOK v118 (Session 184).**
