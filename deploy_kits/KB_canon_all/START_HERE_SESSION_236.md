# START HERE — SESSION 236

*Written at the S235 close, 09-Sep-2026. S235 was long and did a great deal of groundwork on the
Sanjeevni orthotic lane. **The owner's instruction for this session: finalise the spine.***

---

## 0 · THE ONE LINE

**S235 settled the facts. S236 turns them into the spine.** Every ruling is written down, every
figure is measured against the real database, and nothing is waiting on the owner to remember
anything. Do Phase 0, then start at ⭐1 below.

## 1 · PHASE 0, AS ALWAYS

Connections → `CANONICAL_MANIFEST.md` → md5 every row (**a kit gate is verified from INSIDE its own
folder**) → Tier 0 only → `D:\Downloads\ClaudeCowork\00_INDEX.md` and the S235 build brief.

⚠ **Two rows of the S235 close are OWED, not done** — see §5. They are small and they are listed
exactly, so clear them first if the manifest disagrees with anything.

## 2 · WHAT S235 PRODUCED — read these five, in this order

| document | what it settles |
|---|---|
| `claude/S235_TAKEAWAYS_FOUR_OWNERS.md` | **START HERE.** Everything S235 found, filed under who owns it: spine · orthotic section · Amir/voucher · Amir/naming |
| `claude/S235_ORTHOTIC_DISCOUNT_REGISTER_SETTLED.md` | the owner's own discounts for all 93 products — closed, nothing open |
| `claude/S235_ORTHOTIC_STOCK_CYCLE_PLAN.md` | the four-screen cycle he wants built, in nine tasks, with what already exists in the database |
| `claude/S235_ITEM_NAME_FIX.md` | the naming rule, the 22 urgent renames, and where Amir does them |
| `claude/S235_DERIVATION_PASS_BUILT.md` | the pass built at S235 and still awaiting his publish |

## 3 · ⭐1 — FINALISE THE SPINE. This is the session's work.

**Build order is already decided (T1 first — every screen values its lines from it):**

1. **T1 · `marg_item_discount` becomes a real table.** One row per product: `discount_pct`,
   `no_discount`, `internal_use`, `retired`, ruling text, ruling date. **Seed it from the 93 settled
   products** — the data is in `D:\Downloads\margsync\_analysis\Sanjeevni_Item_Naming_Rule_and_Amir_Sheet_09Sep2026.xlsx`
   and in the register document. This is the **`mrp_less_discount` rung** and it replaces
   `MARGIN_ORTHO_DEFAULT = 0.30` in `deploy_kits\S235_DERIVE\marg_derive.py`.
2. **`internal_use` as a third product state** beside active and retired — BLADE, ZIG ZAG COTTON
   500GM, GLOVES SURGICAL 7. No selling price; never unpriced revenue; never a below-MRP flag; still
   correctable in Marg.
3. **`discount_pct = 0` is a decision, not an absence.** A missing row is *undecided*. Never collapse.
4. **Freeze the rate onto the line at the moment of a stock round.**
5. **Hold M.R.P. with the date it was in force.** (241 lines "below MRP" are older M.R.P.s.)
6. **The naming rule becomes a validator** — `WHAT IT IS · BRAND · SIZE`, 20 characters or fewer,
   hand as `LT`/`RT` in the size slot. Refuse a name that would clip.
7. **A purchase name arriving without its size is FLAGGED, never silently assigned one** — new spine
   task type. This is the fault that put bill 585's shoulder unit against M.
8. **The supplier's own description is a name the product wears** — `marg_item_name` with
   `source = vendor`. Also where the future PDF-extractor output lands.
9. **A rename is a spine event, not a break** — old and new name resolve to the same product for ever.
10. **Never prune a stock report.** Two consecutive reports (04-09 and 06-09) proved a question that
    was otherwise unanswerable.

## 4 · THE OTHER TWO THINGS S236 SHOULD CARRY

**A · Amir's naming section.** He already has one page and keeps it — ONE WORKFLOW:

```
https://followup.dr-manoj.in/finance/purchase/page/salts
```

The naming work becomes a **sixth section on that same page**. The change is small and contained:
one new entry in the `SALT_SECTIONS` tuple in `purchase_app.py` (repo copy
`D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S225_SALTS\purchase_app.py`, lines 2874–3260),
then the 22 renames pushed as rows — `a` = name in Marg now, `b` = change it to this, `c` = why.
Amir only ticks DONE; typed answers stay reserved for the `waiting` section. **Trap:** the
housekeeping delete (line ~2908) and the push guard (line ~2975) name `rename`/`create`/`change`
literally — add the new key there too.

**B · The stock voucher is NOT put in front of Amir yet.** Owner's word, 09-Sep: *"WHEN THE NEED IS
THERE WE WILL SHARE THE STOCK VOUCHER WORK."* Do not hand it to him unasked.

## 5 · WHAT THE S235 CLOSE OWES — clear these early

- **Fault Register:** three findings minted in prose but **not yet written into the register** —
  see `claude/S235_CLOSE_REPORT.md` §Findings for the exact text.
- **KB Register + `CANONICAL_MANIFEST.md`:** the six new S235 documents and two new workbooks are in
  project knowledge and on both drives, but **their rows are not yet in the Register or the
  manifest.** Add them, then re-run the gate.

Both were left because the owner ended the session exhausted and neither is load-bearing for the
spine work. Neither needs him.

## 6 · STILL WAITING ON HIM — do not re-ask, just carry

1. **The S235 publish** — `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` — then two
   lines on the VPS (in `OWNER_TODO_LIVE` ⭐0).
2. Ms. Khushi Jain / MyOperator token overlap · the ICICI ·9012 expiry · four values into Bitwarden ·
   the call-recordings decision · the SSD mirror-retention ruling.

---
*START_HERE_SESSION_236 · written at the S235 close, 09-Sep-2026. The groundwork is done; the spine
is the work.*
