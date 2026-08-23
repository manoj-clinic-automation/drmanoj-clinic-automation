# S193 — live pin record (pins recorded AS THEY MOVED, F-97)

Session 193 shipped **two** kits, both installed GREEN on the box.

## Kit `S193_F6` (2026-08-20 00:46 IST) — F-148 bridge + F-153 contra fix
## Kit `S193_UX` (2026-08-20 06:42 IST) — Darpan-page fixes + Hub readability

## Pins that moved (record in the KB Register live-file table + pin-list regen at close, D321(d))

| Live file | Was | Now |
|---|---|---|
| `/root/staff_ledger.py` | `44e39d6abf34db5e11acc2223ac908d3` (SL7) | **`acd7b538ec9476f86e243c73eec3d3fd`** (S193_F6, F-153) |
| `/root/finance/finance_app.py` | `17e6b84ce90ca7d7a0a9ba0c668ab15f` (F5) | **`9b1afe4f13bec91bc9bb83e8f818a76b`** (S193_F6, F6/F-148) |
| `/root/finance/finance_ui/finance_entry.html` | `bae2dd8983c8c3b886705a4f6b6d8dba` (F3) | **`92477b068c67e28661b049b7f3385708`** (S193_UX) |
| `/root/finance/finance_ui/finance_approvals.html` | `028255054662924713e03362c3976b05` (H1c) | **`881d1db547ec86d8519b0992484688b2`** (S193_UX) |

**Consequence:** `verify_live_pins.py` shows **drift 4** on these files until the pin list is regenerated
from an updated Register at the S193 close — expected, not a fault.

## S193_F6 — what changed
**F6 / F-148 — `finance_app.py`:** approving a medical day with a `salary_advance` expense posts an
`ADVANCE_ISSUE` to the Staff Ledger through the ledger's own writer, attributed to the day's month;
ledger-written-first, idempotent (`ledger_posted` guard), fail-loud (`409 ledger_post_failed`, day stays
submitted). F6b needs no code (owner ruling: drawer reflects cash at entry). **F-153 — `staff_ledger.py`
`make_contra`** carries the original's `against_month`.
- F-87 remedy done offline (seeded store to live SHAPE, differential 458/544→463/549, 0 regressions).
- On-box gate: ledger 287→289, finance 550→555; mapping preflight `manoj → ledger checker: YES`. GREEN.
- Reusable live-shape seed filed at `deploy_kits/S193_F6/dev/`.

## S193_UX — what changed (both served pages patched IN PLACE, fail-loud, smoke-gated 555→555)
Kit `deploy_kits/S193_UX/` (`patch_pages.py` + installer). 7 anchor-verified edits.
- **finance_entry.html:** blank money boxes on load (no stuck "0"); select-on-focus for numeric inputs;
  scroll-position restore after a scan (sessionStorage) so repeated scanning keeps its place.
- **finance_approvals.html (Hub):** every `.card` collapsible (noisy ones start collapsed; Today +
  Approvals open); cash-custody reads **"Held now · total"** + holders, conduits shown as "passed on";
  review tab renamed **"Review & month close"**.
- Verified offline against the live page source: node `--check` OK on both; smoke differential (live
  pages wired into the seeded store) **0 failures added**.

## Open / next (Session 193)
- **Real-world confirmation owed:** approve a Sanjeevni salary-advance day and confirm the `ADVANCE_ISSUE`
  lands on that staff member's ledger statement (closes F-148 in practice).
- **Deferred, raised by the owner's Hub review — NOT yet built:**
  - **17 Aug Marg contradiction** — report shows "applied" but the day shows no Marg + a stale
    "no export" flag. A *data*/link bug: check whether `sale_item` for 2026-08-17 exists and points at the
    day; re-link + clear the stale flag; make "apply" always clear the missing-Marg flag it covers.
  - **Discount column** — the Marg bill drill doesn't show per-bill/item discount; needs the feed/API to
    carry it, then a column.
- At the S193 close: record all four pins in the Register, regenerate the pin list (A8), fold F6/F-153 +
  any new UX findings into the Fault Register. Still owed (S192 carryover): repo-filing of
  `S192_SL5_Live_Pin_Record`, `S192_Gated_Data_Corrections_Executed`, `S192_F6_Design_and_Survey`.
