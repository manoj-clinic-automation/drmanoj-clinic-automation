# HANDOFF RUNBOOK — v125 (Session 189 close · 18 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
> §4 the EOS automation boundary (NEW).
> **The canon is current, folded in AT the close — and three times DURING the session.** Seven kits
> live, one retired unlived by its own gate, eleven findings (F-130…F-133, F-135…F-140), every one
> raised the session it was found and all but two structural sweeps closed the same day. Smoke
> **478 → 509**. Four proved GREENs. **D329 minted.**

---

## §0 — WHAT HAPPENED (Session 189)

**The session that audited the auditors.** Every layer of the record was put under the code's own
discipline, and three claims written by the record failed it: the F-130 remediation instruction
named two pages that don't carry the design it asked to assert (**F-135**); the manifest carried a
staff-ledger hash no check had looked at since S162 (**F-136**); and the backlog's central diagnosis
— *"cash in hand is overstated by unbooked handovers"* — was **wrong**, and its prescribed fix would
have cut ₹2,05,198 to ≈₹30,000 against a physical count proving the money genuinely held
(**F-137**). The custody facts had been prose in `cash_count.explanation` all along.

**Built and live:** `S189_G1a` (design fingerprints on all four served pages, both directions) ·
`S189_W1a`/`W1b` (the maker's card reads `cash_custody_event`; custody moves the card and not the
ledger, movements the reverse — proven as one selftest sequence) · `S189_C1a` (the 17 Aug counted
position recorded: Dr Manoj ₹18,963 · Dr Bhawna ₹1,56,235 = ₹1,75,198 to the paise; cash in hand
gate-proven byte-identical) · `S189_E1b` (the owner-ruled expense menu; free text demoted behind a
required-details Other; salary-advance identity SERVER-resolved — the old dropdown's hardcoded ids
pointed at a table empty since S179, **F-139**).

**Two kits were refused by their own gates, and both refusals were right.** C1a's first run:
state-asserting checks broke on the store they had just legitimately changed (**F-138** — the delta
discipline applied to one line and not its block). E1a: the rehearsal-day finder walked into a D322
Sunday hole beyond the backfill window — the offline store had the schema, not the SHAPE
(**F-140**). Both reproduced offline to the exact failing set before the fix was written.

**Verified open: the §4a ₹70,000 gate (D326(c)).** Five machine checks + the owner's confirmation:
the Apr–Jun ₹40,000 was recovered from salaries in the workbook era; no double-count in any book;
the D250 engine's first real close matched the workbook replay to the rupee. **The salary bridge
(D3) is unblocked** — and specified: **D329, the Advance Pool** (design signed,
`S189_Advance_Pool_Design_D329.md`).

## §1 — MENTAL MODELS

1. **Carried:** survey the box before writing to it · the projection is the check · a count beats a
   derivation · record live pins as they move · a gate that fires is the system working · "already
   correctly scoped" is a test result or it is nothing · a derived artefact is rebuilt in the same
   routine that changes its source.
2. **⭐ A remediation instruction is a claim about the files it names (F-135).** The diagnosis being
   right does not make the prescription tested. Write the fix against the files, not the finding.
3. **⭐ Duplicate a value and you have created a second thing to keep true (F-136).** A row that
   defers to another document may point, never restate. And a hash in the manifest but not the
   Register is checked by NEITHER standing check.
4. **⭐ A diagnosis in the record is a claim about the schema (F-137).** Read the schema before
   prescribing the fix — the prescribed fix here would have created the exact error it described.
   Custody is LOCATION; movement is QUANTITY; the ledger reads only the latter.
5. **⭐ When a rule is applied to one line, it is applied to the block (F-138).** One delta-converted
   check beside three absolute ones refused the very migration the four existed to protect.
6. **⭐ A dropdown is a claim that its values exist; attribution is the server's to decide (F-139).**
   A structured control pointing at invented ids is worse than free text, because it looks queryable.
7. **⭐ A rehearsal store must carry the live store's SHAPE — its holes, not just its tables — and a
   check that can fail must say why (F-140).** Six bare reds cost a reproduction that one printed
   error would have made free. A rehearsal must stand where the maker is allowed to stand.
8. **A count-equal kit is proven by reproducing the failure it cures (W1b, E1b).** When the check
   count cannot see the change, recreate the red on a throwaway copy and show it fixed, before any
   swap.

## §2 — LIVE BACKLOG

**⭐ 0. The ₹30,000 sitting, with Darpan, before 10am — one sitting closes four items.** The 17 Aug
day on the new menu: figures · **₹20,000 → "My salary advance"** · **₹10,000 → "Other" → "Salary
July settled in cash (doctor's instruction)"** · three scans · Save → the check → File (the D2
walk-through, live). Then the owner: approve 17 Aug → **Apply the staged Marg push** → submit and
approve 14 & 15 Aug → enter the ₹20,000 in the Staff Ledger (dated 17 Aug). Proof line projection:
cash in hand prints **₹1,75,198.00** — the counted figure to the rupee.

**⭐ 1. THE D329 BUILD — S190's top task.** `S190_SL1` (Staff Ledger: pool categories, the
`advance_instalment` setting, close-engine integration, the reconciliation card with LINK, the
scoped receive endpoint) → token on-box → `S190_F1` (finance: push-on-approval, LINK, truthful
`ledger_posted`). The signed contract is `S189_Advance_Pool_Design_D329.md`. **Rehearse against a
ledger given the live file's SHAPE (F-140), and read the live engine before integrating (F-137).**

**2. Owed and named:** `dev_seed_smoke_db.py` stalls at the S180 schema — the F-87 tool cannot
build a runnable store unaided (owner's call whether it earns F-141) · the draft-resave hazard: a
re-opened draft saves with its earlier expenses silently dropped (live since S179; mind 14/15 Aug)
· **F-97 part 2** — the repo's `finance/` tree is now eight builds stale; live bytes exist only in
kits · F-136's kin-sweep beyond the manifest · F-106 selftest split · F-107/F-108 checks made
mechanical · CLI `marg_backfill.py` NOT-FILED flag + display bug · 4 May + 27 May · 12 Jun ₹8,487 +
3 May zero-lines · Hindi labels · WABA (F-82, vendor) · F-92 · F-93 · the stray
`followup-tracker/python test_send.py` · the untracked-76 triage (add to Register or IGNORE with
reasons) · Tailscale + RustDesk (+ the VPS on the tailnet) · the scoped deploy-key decision
(D328's boundary — the one thing standing between the owner and zero-click publishing).

**3. The rest of the signed Daily Flow v2 contract** after D329: D-R returns at reception with the
D327 `counter` role → 360 wiring → orthotics purchase side → D5 feeds → D6.

**Cold-kit count: 3 of 3–5** (`KB_S189_close`, taken AT this close). Next due ~S192–S194.

## §3 — INSTALL DISCIPLINE

The D317 chain stands, plus this session's additions: **a count-equal kit proves itself by
reproduction** (apply the change to a throwaway copy; current build must fail exactly, new build
must pass) · **the rehearsal store carries the live store's shape** — its gaps, its Sundays, its
negative tails · **every selftest check that can fail embeds the server's answer in its label** ·
delta assertions across the whole block, never absolutes (F-106/F-138). Financial-book changes stay
gated migrations, offline-rehearsed, reversible, projected before applied. `verify_live_pins.py` at
every open and close; the Register corrected FROM the box (D321(d)). PHI, `finance.db`, raw
exports and tokens never enter the repo, a kit, or chat.

## §4 — THE EOS AUTOMATION BOUNDARY (owner directive, S189 close)

**The assistant executes at every close, without being asked:** the full document set (A0–A8 of
`END_OF_SESSION_PROMPT` v5) · the project-knowledge swap · the Notion update · the repo commit
staged onto the PC via the bridge · the cold kit written to `cold_kits/` when due · the pin list
regenerated LAST (A8). **The owner's residual work is exactly two acts:** one double-click of
`PUBLISH_ALL.bat` (the D328 boundary — repo-write credentials never transit chat; retiring this
click needs the scoped deploy-key ruling, backlog §2) and the on-box pin-list copy + `verify_live_pins.py`
run. Anything beyond those two appearing in a close-out is a fault in the close, not a task for the
owner. The portable definition for other projects: `EOS_DEFINITION_PORTABLE.md`.

**END OF HANDOFF RUNBOOK v125 (Session 189 close).**
