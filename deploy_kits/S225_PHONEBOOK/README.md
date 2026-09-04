# S225_PHONEBOOK — the stockist phone book (rev 7), and the rounding rule where it belongs

**Two things the owner said today, both in this kit.**

**1 · "No corrections done here??"** — on his Orders page. Rev 6 had put the rounding rule ("round to 10 strips, then
multiples of 10") only on the staff page. Wrong: the rule is the *order quantity*, so it now lives **once, in the engine**
(`reorder_plan`) — the doctor's Orders page (column now *Order qty*, with the unit word), the *Copy this order* text
(`Item — qty strips`), the staff page and the WhatsApp message all carry the same number. A line the rule changed says so
in its *Why* column. Bottles, tubes and units keep the engine's box quantity.

**2 · The stockist phone book** — spec §3 with his S225 rulings:
- **`/finance/purchase/page/book`** for **Dr Manoj, Darpan and Shavez** — an allow-list in `finance.db` (`setting
  purchase.phonebook_users`, seeded by the install; the doctor always). **Fail-closed**: no setting, nobody but the doctor.
  Nobody else sees the page, the link, or a number.
- **Two numbers per stockist**; edit either; add a new stockist (name as Marg prints it, phones, bank fields).
- **Bank details — server-side only** (F-185/F-31: never in a kit, never in the repo): account name, account number, IFSC,
  bank/branch, UPI id. Saved by Darpan or Shavez → **UNVERIFIED** until the doctor taps **Verify**; saved by the doctor →
  **VERIFIED** by that act; any later change by anyone but him drops it back to UNVERIFIED. The table shows the account's
  last four digits; the full number sits only in the editors' pre-fill. **Existing bank details stand as accepted** (his
  ruling) — they live in `NEFT_Vendor_Master` on the PC and are not imported here today. The future NEFT leg reads
  `bank_status` and refuses UNVERIFIED.
- **The nightly manojz push never overwrites a number edited here** (`source='server'` wins; the push fills only what it owns).
- **Every change is audited by field name and last-4**, never by value.
- The staff page rings either number (**Call 1 / Call 2**); WhatsApp goes to the first.

**Proof:** `selftest_phonebook.py` **290/290** — the whole S224 selftest and the rev-6 staff checks as regression, then the
engine rounding on the doctor's page, the allow-list (doctor only until seeded; Darpan once named; Amir refused page, API
and link), phones normalised and validated, the push-does-not-clobber rule, both Call buttons, the UNVERIFIED → Verify →
VERIFIED → modified → UNVERIFIED cycle, IFSC validation, duplicate names, signed-out 401s, and that no audit row carries a
number. `walk_phonebook_gate_s225.py` runs on the box inside the install line through the real gate.

**Owed, next (§8):** the arrival flow (acknowledge / supplied qty / short) with the scan button in context · Sarvam-vs-Marg
cross-check **live on the event** (his ruling) · new-items log · salt list · stock snapshot on capture.
