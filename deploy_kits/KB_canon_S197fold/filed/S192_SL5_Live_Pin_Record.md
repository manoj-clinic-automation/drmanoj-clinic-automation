# S192 · LIVE PIN RECORD — recorded AS THEY MOVED
### Session 192 · 19 Aug 2026 · kits `S192_SL5`, `S192_SL6`, `S192_SL7` all installed GREEN

> **Why this file exists.** A live-code pin is recorded **at the moment it moves**, never saved for
> the close — an unrecorded live pin is the **F-97** condition. The full canonical fold (Register
> bump, Archive append, Fault-Register append, Runbook bump, manifest rebuild, A8 pin-list
> regeneration) is **owed at the S192 close** and is named here so the debt cannot go unrecorded
> (**F-107**'s lesson applied forward).

---

## 1 · The pins, in the order they moved

| Kit | `/root/staff_ledger.py` after | Selftest | Backup on the box |
|---|---|---|---|
| (entering state, S190_SL4) | `470bb1133046d9076de5a2edd413f66c` | 218 | — |
| **`S192_SL5`** | `0ed19495e026d9629b75294f39075dc2` | **218 → 240** (+22, exact) | `…bak_S192_SL5_20260819_221025` |
| **`S192_SL6`** | `0279540ed8e6fe8ebd75781544ffc209` | **240 → 274** (+34) | `…bak_S192_SL6_20260819_224421` |
| **`S192_SL7`** | **`44e39d6abf34db5e11acc2223ac908d3`** | **274 → 287** (+13) | `…bak_S192_SL7_20260819_232258` |

KIT_IDs: `S192_SL5 0ed19495…` · `S192_SL6 0279540e…` · `S192_SL7 44e39d6a…`

**No schema change, no migration, no data write in any of the three.** `staff-ledger.service` active
after each swap. All three built on the **live bytes recovered by hash, not filename** (D188) — the
repo's `staff_ledger/staff_ledger.py` (`92665b64…`) is the stale mirror and was deliberately not used
(F-52 / F-97 part 2).

## 2 · SL5 — waiver instrument · policy-date settings · F-151 wording (D332 §2.7 · §2.8 · §2.10)

1. **WAIVE (§2.8).** Forgives a deduction. Scopes **LINE / STAFF_MONTH / ALL_MONTH**; compulsory
   written reason, no escape hatch; the amount is **DERIVED at compute time, never frozen**;
   append-only and **contra-reversed** (activeness derived from contra records, never mutated in
   place); own **`+waived`** column on both salary tables, the per-staff breakdown and
   `salary_final_<month>.csv`. Stored per month in `waivers_<YYYY-MM>.json`. `waiver_authority`
   seeded **manoj: true, bhawna: false** — scoped in but INACTIVE, deliberately not a one-tap web
   toggle. **Owner ruling (S192): a waiver may forgive ANY deduction line** — attendance
   (`att:<type>`) or a ledger debit (`led:<row id>`). WAIVE forgives; DEFER postpones; two verbs.
2. **Policy-date settings (§2.7 / F-150).** `ledger_settings.json` + **`/ledger/settings`**.
   `attendance_enforce_from` is the notice-served month; while unset, **every month is PREVIEW-ONLY**
   — attendance deductions shown struck-through, not applied to NET. Ledger money always applies
   (owed, not a penalty). July and August are preview until the owner sets the date. Also
   `sunday_enforce_from`, `incentive_rungs`, `min_takehome`.
3. **F-151, attendance-only** (owner's scope ruling): rendered "fine" → **"attendance deduction"**.
   Uniform / i-card / ad-hoc ledger charges keep their names; att-report CSV headers untouched.
4. **Token coverage:** the approval token hashes waivers **and** settings — a stale preview refuses.

## 3 · SL6 — schedule lane · DEFER · capacity rule (D332 §2.1 · §4 · F-147)

1. **THE SCHEDULE (§4).** An advance is an amount **plus a repayment schedule**. A schedule that does
   not add to the advance exactly is **refused**. The close collects the current month's step in its
   **own lane beside the waterfall** — never behind the loan book. **SL4's recover-in-full and a
   uniform instalment are both special cases**; one generalisation subsumes all three. Rows with no
   schedule behave **exactly** as before.
2. **DEFER replaces SKIP (§2.1).** The instalment shifts whole and the schedule **EXTENDS** — the
   tail is never swallowed. *(The first implementation capped the elapsed count at the number of
   listed steps, silently eating the final step after a defer; caught by testing the arithmetic
   before writing the test block, and fixed by counting elapsed months from the schedule's first
   step, unbounded.)* **No automatic capitalisation.** The 2/FY discipline survives as a **waivable
   penalty on interest-bearing loans only** — first two free, from the 3rd ₹1,000 capitalises unless
   waived with a reason. Interest-free advances defer penalty-free always. Reason compulsory.
   `LOAN_SKIP` untouched for history.
3. **CAPACITY (F-147).** One budget per staff per month = base − other debits booked − `min_takehome`,
   spent by every lane in order. What cannot be taken becomes a **`CAPACITY_HOLD`** line and **stays
   owed** — never silently dropped. **No base salary on file DISABLES the gate** rather than freezing
   recovery (the D331 fail-open design), and says so.
4. **Loud surfaces:** the Advances card shows amount · schedule · recovered · months left · next
   collection, a red **DEFERRED** band, and the defer tap with its FY counter. Salary table and full
   report gain a **deferred** column beside `+waived`.

## 4 · SL7 — the per-staff Perks view (D332 §2.9, closes F-149)

New checker-only **`/ledger/perks`** in the nav. A perk is a **record of a benefit paid, not money
owed** — no approval chain, excluded from salary by design — and the gap was that it could be
**entered and then never read**. Now: an index of every staff member's net perk total, tap for
detail; a per-staff view with the **lifetime** total and a **year** filter; and append-only honesty —
a contra'd perk nets to zero with **both rows still visible**, greyed, because a contra is simply a
negative PERK row and needs no special case.

## 5 · CONSEQUENCE — the pin list is stale until A8 runs

`verify_live_pins.py` reports **DRIFT on `/root/staff_ledger.py`** until the Register is bumped and
the pin list regenerated. **Correct behaviour, not a fault** — the list came from Register **v5.39**,
which pins the SL4 build. The last run before SL5 was **GREEN, match 43, drift 0, `source:
VERIFIED`** (the thirteenth consecutive GREEN), so the box was proven clean immediately before the
first swap. **Do not re-run expecting green until the close regenerates the list** (F-134 / step A8).

## 6 · CANDIDATE FINDINGS from this session (recorded, unminted — next free F-152)

- **The `.gitattributes` line-ending gap.** `PUBLISH_ALL` warned that `KIT_ID.txt` and `SUMS.md5`
  would become CRLF. A CRLF `SUMS.md5` makes `md5sum -c` read the filename as `staff_ledger_X.py\r`,
  fail to find it, and turn a **perfectly good kit RED at gate [1/6]** — a gate firing wrongly, which
  D316 warns is worse than no gate. **FIXED this session** (owner's OK): `*.md5 eol=lf` and
  `*.txt eol=lf` added, with the reasoning written into the file. Kin of **F-100**, D164.
- **A contra does not carry the original's attribution.** `make_contra` copies category, staff, dates
  and the negated amount but **not `against_month`**, so a reversed advance keeps eating that month's
  quota — Darpan's August would have read ₹35,000 instead of ₹20,000. Worked around in the correction
  script by stamping it on; **the gap in `make_contra` is still open.** One-line fix.

## 7 · Process note (the F-45 family, twice this session)

SL6 projected 270 and measured 274; SL7 projected 286 and measured 287. **Both misses were the
assistant counting his own new checks by eye**, not behavioural surprises — each reconciled exactly
against the test block (`ck(` occurrences minus the `ck(False, …)` guards inside `try` blocks, which
never execute). **Procedural fix adopted mid-session: count the block programmatically BEFORE
running.** Both kits shipped with the **measured** figures, not a retro-fitted projection.

## 8 · OWED AT THE S192 CLOSE

- **KB Register** v5.39 → v5.40: **all three** live pins, D332/SL5+SL6+SL7 progress, a lineage row,
  end marker; zero loss proven by **reverse application** onto the `28a807a0…` pin.
- **CANONICAL_MANIFEST**: new Register row + an §S192 fold block; **A8 last** (F-110).
- **KB History Archive** v1.42 → v1.43 · **HANDOFF_RUNBOOK** v127 → v128 ·
  **Fault_Action_Register** v2.31 → v2.32 (**F-147 CLOSED** by SL6's capacity rule; **F-149 CLOSED**
  by SL7; **F-150 · F-151 CLOSED** by SL5; **F-148 remains OPEN** pending F6; plus the two candidates
  in §6 if minted).
- **The KB cleanup** (47 superseded docs deleted after byte-verification against git; knowledge
  1,919,222 → 1,149,776) and deletion of `claude/S192_OPENING_NOTE_KB_cleanup.md`.
- **Cold kit**: count 3 of 3–5, **due**.

## 9 · D332 state

| Kit | State |
|---|---|
| `S192_SL5` · `S192_SL6` · `S192_SL7` | **LIVE** |
| `S192_F6` (the ledger bridge, F-148) | **designed, not built** — blocked on the seeded-store rehearsal (F-87); see `S192_F6_Design_and_Survey.md` |

**Gated data corrections (§6 items 1–4): DONE** — see `S192_Gated_Data_Corrections_Executed.md`.
Still on the owner: scan Darpan's signed application against row `0cc0b26b38c5` and approve it
**before the August close** if the ₹8,000 is to be collected this month; and the July salary close.

---
*Recorded at the moment each pin moved, per the S186/S189/S190 practice. Session 192.*
