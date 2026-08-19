# HANDOFF RUNBOOK — v126 (Session 190 close · 19 Aug 2026)

> **Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
> §4 the EOS automation boundary.
> **The canon is current, folded in AT the close — and SIX times DURING the session.** Eight kits
> live, two kit v1s refused by their own gates (both toolchain faults, both refusals right),
> **D330 + D331 minted AND executed same-session**, the ₹30,000 sitting closed end to end, cash in
> hand landing on the counted rupee. Finance smoke **509 → 550** · ledger selftest **190 → 218** —
> **sixteen consecutive exact projections.** Eleven GREEN pin runs. F-141 ruling deferred to S191.

---

## §0 — WHAT HAPPENED (Session 190)

**The session that put the owner's money rules into the machines the same day he ruled them.**
Walking toward the ₹30,000 sitting, the owner redesigned the expense system twice — and both
designs were signed, built, installed and verified before the session ended.

**D330 (executed, kit `S190_E2`):** Sanjeevni expenses are THREE categories (salary advance ·
home · other); the advance capped by a DERIVED ceiling (per-staff % of base floored to ₹100 —
Darpan 75% of ₹20,000 = ₹15,000/month, others 50%; nothing stores the figure, F-136) shown
inline BEFORE he types and refused server-side past it; home/other = free text + **compulsory
per-row evidence at File, no escape hatch** (photograph at payment, upload at filing — the bill
input is INLINE in the expense row, owner ruling); home = the proprietor's drawings, split in
reporting; petty spends stay manual (digital petty book PARKED); clinic unit gets the two
expense categories + evidence, NEVER an advance path. The draft-resave wipe is CLOSED
(`expense_uid` + full refill). Supersedes D329 whole — nothing of it was built.

**D331 (executed, kits `S190_SL2` + `S190_F2`):** every staff member sees month-to-date beside
the derived ceiling on the Staff Ledger; above it = SPECIAL — maker drafts, maker uploads the
written application signed by Dr Manoj / Dr Bhawna (the ledger's first attachment), checker
approves, approval REFUSES without it; `against_month` attribution (an advance consumes ITS
month's quota, recovered from its month's close); the Sanjeevni gate counts forward-attributed
salary-side advances (fail-soft, forward-only — no double-count by construction).

**Owner live-looks fixed four faults the same hour each was found:** SL3 (the S155 migration
rows, dated Aug 2026, ate the quota — ruling: the quota counts from the install; loans never
consume it) · F4 (the medical locked-day gate read the SSO broker role, refusing THE DOCTOR) ·
F5 (an edited legacy day vanished from the approvals queue while its money counted) · **SL4,
the quota lane (owner ruling "A")**: a quota advance (explicit `against_month` · not a loan ·
recover-fully instalment) recovers IN FULL at the first close ≥ its month, in its own lane
beside the D250 waterfall — never behind the ₹3.59 lakh loan book. Partial instalments opt back
into the waterfall; a loan Skip pauses only the waterfall. F3 shipped the inline-bill flow.

**The ₹30,000 sitting closed to the rupee:** ₹10,000 · 31 July (filed AND approved) · ₹15,000 ·
Aug from medical (exactly the ceiling) · ₹5,000 transfer-out to Dr Manoj, ledger-attributed
**against September** (September's drawer limit becomes ₹10,000 automatically). Cash in hand
**₹1,75,198.00 — the counted figure** — verified on the live tile with Claude driving the
owner's Chrome. All three ledger advances present in the book (an earlier "done" had been a
missed refusal — proven absent, re-entered walked). 14 & 15 Aug approved. The August ledger
close will recover ₹25,000 and September's the ₹5,000 — nothing manual remains.

## §1 — MENTAL MODELS

1. **Carried:** survey the box before writing to it · the projection is the check · a count
   beats a derivation · record live pins as they move · a gate that fires is the system working
   · a rehearsal store carries the live store's SHAPE · a check that can fail says why · a
   count-equal kit proves itself by reproduction · a derived artefact is rebuilt in the same
   routine that changes its source.
2. **⭐ The gates catch the toolchain too.** Both kit-v1 refusals this session (the fabricated
   hash tail · the tail-1 harness) were faults in the INSTALLER, not the payload — and the D317
   chain refused both with the box untouched. Write gate constants by transcription from a
   measured value, never from a narrative prefix; a harness that reads "the last line" must
   first prove the last line is the summary.
3. **⭐ A refusal that looks like a save costs real entries.** The owner entered two advances
   pre-SL3, the gate refused them, the red was missed, and "done" entered the session's belief
   state until `/ledger/book` proved absence. Verify entries in the book, not on the form.
4. **⭐ Attribution decides which month; the close collects it (SL4).** Quota money recovers in
   its own lane at its own month's close; the waterfall is for legacy tranches and loans. A
   deliberately partial instalment is a choice to wait in the waterfall.
5. **⭐ Identity comes from the unit layer, not the broker (F4; the F-84 family again).** Audit
   every `u["role"]` use when a broker sits in front of a unit.
6. **⭐ A queue that hides a class of rows must un-hide a row the moment it stops being that
   class (F5).** The edit made the legacy day an app day; the marker had to follow.
7. **Chrome automation:** never click a native `<select>` — the OS dropdown wedges the
   extension. form_input, or let the owner touch selects.

## §2 — LIVE BACKLOG

**⭐ 0. With Darpan (owner deferred to S191):** complete the 17 Aug and 18 Aug drafts — real
figures + the three scans each (17 Aug's Marg push already applied) → File → owner approves.
The days exist as deliberate zero-figure drafts; the refill (E2) makes reopening safe.

**⭐ 1. Surendra's ₹8,000 advance — PENDING decision** (maker shavez, "given by dr bhawna").
Over his ₹5,200 ceiling and grandfathered (pre-gate entry): approve as-is or reject and
re-enter as SPECIAL with the application. Owner's call, two taps on /ledger/pending.

**⭐ 2. The F-141 ruling — six candidates + one UX note:** (1) the fabricated hash tail (E2 v1)
· (2) the wrong install path in the delivery note · (3) the tail-1 harness (F3 v1) · (4) the
migration-dated quota (SL2→SL3) · (5) the broker-role locked-day gate (F4) · (6) the
hidden-legacy queue (F5). UX note: a refusal that looks like a save (§1.3). The owner says
which earn numbers; the Fault Register then gains its append (it stays v2.29 until then —
nothing owed, the candidates are recorded here and in Archive §S190).

**3. First real month-end on the new machinery (end Aug):** the ledger close should recover
₹25,000 from Darpan (quota lane) + the loan's ₹5,000+₹1,000 (waterfall) — watch the first live
run of SL4 against its selftest's promise. September: Darpan's drawer limit reads ₹10,000.

**4. Owed and named:** `dev_seed_smoke_db.py` stalls at the S180 schema · F-97 part 2 — the
repo's `finance/` tree is now TEN builds stale; live bytes exist only in kits · the
untracked-76 triage (add to Register or IGNORE with reasons) · interest-loan application
requirement stays procedural (wiring breaks the migration path — recorded in the D331 contract)
· F-106 selftest split · F-107/F-108 checks made mechanical · CLI `marg_backfill.py` NOT-FILED
flag + display bug · 4 May + 27 May owed days · 12 Jun ₹8,487 + 3 May zero-lines · Hindi labels
· WABA (F-82, vendor) · F-92 · F-93 · the stray `followup-tracker/python test_send.py` ·
Tailscale + RustDesk · the scoped deploy-key decision (D328's boundary).

**5. The rest of the signed Daily Flow v2 contract:** D-R returns at reception with the D327
`counter` role → 360 wiring → orthotics purchase side → D5 feeds → D6. (D329 is superseded;
the D3 salary bridge's advance problem is SOLVED by D330/D331/SL4.)

**Cold-kit count: 3 of 3–5** (`KB_S189_close`). Next due ~S192–S194.

## §3 — INSTALL DISCIPLINE

The D317 chain stands, plus this session's additions: **gate constants are transcribed from a
measured value, never composed from narrative** (E2 v1) · **an installer's summary-reader must
prove it read the summary** — grep the whole output, require the expected fail-set by name
(F3 v2) · single chained VPS commands on the owner's ruling (`cd && git pull && bash kit.sh`) ·
count-equal kits prove themselves by reproduction · rehearsal stores carry the live shape ·
delta assertions across whole blocks · financial-book changes stay gated migrations. `verify_live_pins.py`
at every open and close; the Register corrected FROM the box (D321(d)). PHI, `finance.db`, raw
exports and tokens never enter the repo, a kit, or chat. Ledger runs on
`/root/wa/venv/bin/python3`; finance + asset apps on system python3.

## §4 — THE EOS AUTOMATION BOUNDARY (owner directive, S189 close — held at this close)

**The assistant executes at every close, without being asked:** the full document set (A0–A8 of
`END_OF_SESSION_PROMPT` v5) · the project-knowledge swap · the Notion update · the repo commit
staged onto the PC via the bridge · the cold kit when due · the pin list regenerated LAST (A8).
**The owner's residual work is exactly two acts:** one `PUBLISH_ALL.bat` double-click (D328 —
repo-write credentials never transit chat) and the on-box pin-list copy +
`verify_live_pins.py` run. Anything beyond those two appearing in a close-out is a fault in the
close. Portable definition: `EOS_DEFINITION_PORTABLE.md`.

**END OF HANDOFF RUNBOOK v126 (Session 190 close).**
