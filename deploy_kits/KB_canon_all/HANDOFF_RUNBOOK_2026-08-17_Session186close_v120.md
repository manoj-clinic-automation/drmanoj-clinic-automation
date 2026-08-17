# HANDOFF RUNBOOK — v120 (Session 186 close · 17 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline.
> **The canon is current and NOTHING is owed at this close** — the Archive, the Fault Register, the
> Register and the manifest all moved this session. That is the second clean handover in a row, and
> the Fault Register has no owed append for the first time since S181.

---

## §0 — WHAT HAPPENED (Session 186)

The longest build session in the project: **six kits, five live installs, six findings, two decisions.**
Two kits went red; both were caught by their own gates and restored with nothing half-applied. **No incident.**

**Thread 1 — Phase 0 and the pin chain.** Documents green (63/63 against git bytes; the F-88
cross-check matched 69 of 85 manifest tokens to real bytes, the other 16 all legitimately
non-document; the **F-107 inverse check ran for the first time**). ⭐ Task 0 was answerable from git:
`finance_app.py` = **`c66bec2b9ea8c11af9c4a4244541e96f`**, confirmed on the box — and the record's
`c66bec2b76…` was **wrong in two characters** (**F-109**). The live-pin run then produced **three DRIFT
reds of which two were false** (**F-110**): the pin list had been generated from a Register *draft*
(`ff509b01…`) that never became canonical. Regenerating exposed **F-111** — the generator could not read
the Register S185 wrote. Kit **`S186_V1a`** fixed both: the generator refuses a Register the manifest
does not pin as CURRENT; the checker refuses to *run* on an unattested list.

**Thread 2 — the cash chain, closed by count (D323, F-112).** The owner's custody sheet showed cash
parked with Dr Bhawna 1–7 April totalling **exactly ₹99,017** — the unexplained 8-April injection,
matched to the rupee by an independent record. The custody model was established and written down for
the first time: monthly copy reset with **no taken/carried marker**, **Dr Bhawna never banks**, the
**counter person hands direct**. The Yes Bank statement then proved the **13 Aug ₹75,000 deposit never
happened** (**F-112**) — booked at S184 on a row S183 had itself marked unevidenced. Darpan's drawer
was cleared for the first time and **proved the arithmetic to the rupee**: ₹48,963 = ₹10,000 + ₹20,000
+ ₹18,963. Kit **`S186_C1a`** removed the phantom deposit and parked **₹87,205** as one approved,
reasoned adjustment. ⭐ **`negative_cash` exceptions 29 → 0** — S184's derived requirement of ≈₹85,000
and the counted ₹87,205 **agreed to about ₹2,200**.

**Thread 3 — six upgrades.** `S186_R1a` (data layer: bank statement tables, `counter_person`,
`cash_custody_event` with the taken/carried marker, `finance_yesbank.py` 23/23) · `S186_R2a` (the
workbench, Yes Bank reconciliation, custody, drawer count — **341/341** live) · `S186_I1a` (**F-114**
fixed and **Marg uploads through the portal** — **351/351** live) · `S186_W1a` (**F-104** cleared,
review **2,072 → 0**, flagged days **120 → 4**).

**F-103 is closed and was proved against the fault that motivated it:** given the real statement and
the *uncorrected* store, the reconciler flagged exactly the 13 Aug ₹75,000 and nothing else.

**F-113** was found deciding the item-wise go-live, and **diagnosed wrongly twice** before the real
export and the real adapter settled it. **F-114** was found by the first genuine daily ingest.

**D324** adopted mid-session: kits written straight into the local repo, one-paste publish.

---

## §1 — MENTAL MODELS

1. **Carried and undiminished:** survey the box before writing to it · a self-test that asserts a data
   state is a liability (F-106) · the bank arbitrates, the human confirms · the app enforcing
   correctness looks like an obstacle and is a feature (F-105) · keep the common path trivial and
   Hindi-first · verification catches the wrong row and is blind to the missing one (F-107/F-108) ·
   the fold-in belongs at the HEAD of a session, never the tail.
2. **⭐ A record that asserts something about another component is a claim, not a fact.** F-109 (a hash
   lengthened beyond its evidence), F-112 (a deposit booked on a row marked unevidenced), F-114 (two
   docstrings promising WALK-IN attribution the code never performed), and the still-unchecked S184
   narration *"tracked in salary system"*. **Every one was believed because it was written down.**
   The remedy is never more careful reading; it is a check that compares the claim to the thing.
3. **⭐ A true statement can expire (F-113).** "Not filed, refused harmlessly" was correct when printed
   and false hours later. This is a different failure from silence, and it needs a different fix: not
   *say more*, but **leave something that outlives the run**. Console output is not a record.
4. **⭐ Test the mechanism, do not argue about it.** Three diagnoses this session were plausible,
   fitted the evidence, and were wrong — Dr Bhawna banking directly, a short Marg export, a driver
   abort. Each died in under a minute against the real file, the real adapter, or one sentence from
   the owner. **A mechanism that explains the data is a hypothesis; the box is the arbiter** (D172,
   D188 — applied to diagnoses, not only to hashes).
5. **⭐ The projection is the check.** `S186_W1a` printed *days flagged after: 4* before writing, and
   its verify refused an outcome of 56. That one assertion — *"flags fell to the projected number, not
   to a hoped-for one"* — caught a defect that had silently dropped 116 credit notes. **State the
   expected result before acting, then hold the result to it.**
6. **A count beats a derivation.** Five months of custody could not be reconciled from records, because
   the records had no column for the movements that mattered. Clearing the drawer settled it in one
   evening and proved two handovers nothing had connected.
7. **Record live pins as they move, not at the close.** Five Register bumps this session, deliberately.
   Unrecorded live pins are the F-97 condition, and this session was spent digging out of it.

---

## §2 — LIVE BACKLOG

**⭐ 1. The item-wise go-live decision.** The daily path is now proven end to end (14/15 Aug ingested,
33 bills, 147 drug lines), the queue is empty and the dashboard is quiet. The call is the owner's.

**⭐ 2. 12 June — Marg lines exceed the declared day total by ₹8,487.** Live money, invisible inside
120 identical shouts since June. Pull that day's manual copy against the Marg bills. *(Also: 3 May has
**zero** lines — re-upload the May export through the workbench; 9 May −₹665 and 2 Jun −₹690 are
probably one bill each and the same re-upload may clear them.)*

**3. Darpan's ₹30,000**, blocked on the three scans. **The ₹10,000's category is still an open
question** — free text if it settled July salary, `salary_advance` if it is a new advance; booking it
wrong double-counts in his Staff Ledger. Cash reads ₹2,05,198 until it goes in; ₹1,75,198 after.

**4. Submit and approve 14 & 15 Aug** — both still `draft`.

**5. Hindi labels**, parked by the owner. Unblocks the custody block on Darpan's entry screen — the
last piece of the reserve model. Schema is already built; it is a UI-only change.

**6. The Staff Ledger check.** ₹70,000 of Darpan's advances (₹40,000 S184 + ₹30,000 on 17 Aug) rest on
an unverified claim in a SQL comment — *"tracked in salary system, NOT posted to Ledger"*. Nobody has
looked. He is also skipping an August loan instalment to be recovered in September.

**7. `marg_backfill.py` (CLI)** — still lacks the NOT-FILED `data_flag` the portal path now writes
(**F-113**), and still prints `attributed ? · review ?` because it asks `ingest_day` for two keys it
does not return.

**8. F-106 follow-up** — split `finance_app --selftest` into invariant-logic and seeded-fixture halves.

**9. F-107 / F-108 structural checks** — assert every Tier-0 document about to be read has a manifest
row (run by hand this session, not yet mechanical); assert the Fault Register's next-free number equals
its last index row + 1 at every append.

**10. F-97 part 2** — the loaded-in-memory check, the PC-side half of the pin verifier, and triage of
the untracked live files (**68 → 76** this session).

**11. Two missing days** — 4 May and 27 May, owed since May.

**12. Carried:** WABA go-live (F-82, vendor) · security rotations · console follow-ons · F-92 discount
capture · F-93 concession-parser footer.

**Cold-kit count: 2 of 3–5** (`KB_S185_close`, plus this close's set in the repo).

---

## §3 — INSTALL DISCIPLINE

The D317 kit chain stands: SUMS → KIT_ID → currency/state gate → precheck or smoke **before** any
swap → backup → apply → verify → **an honest red that restores**. Standing additions: `push_kit.bat`
v4 refuses to publish if `.gitignore` drops a kit file (F-100); the read-only survey kit (S184_S1a);
the state-adaptive self-test (F-106); **`verify_live_pins.py` v1.1 refuses to run on a pin list whose
source Register was never proved canonical** (F-110); **`gen_live_pins.py` v1.1 refuses to build one**
(F-110/F-111); and **D324** — kits written straight into the repo with a `PUSH.bat`, checked in both
directions (every file present is listed, every file listed is present).

Financial-book changes remain **gated migrations, offline-rehearsed against a copy of the real store,
reversible, never ad-hoc SQL** — and now **projected before they are applied**, with the verify holding
the outcome to the projection. `verify_live_pins.py` at every open and close; the Register is corrected
**FROM the box**. PHI, `finance.db` and raw Marg exports never enter the repo or a kit (F-31 / F-49 /
D320) — and since S186 an export need not reach the VPS at all: it uploads through the portal and is
deleted inside the request.

**END OF HANDOFF RUNBOOK v120 (Session 186).**
