# S371_PURCHASE_WRONG_RESOLVE — kit README

**Project:** Sanjeevni (session 281, 22-Sep-2026) · **Touches a parent file:** no · restarts `clinic-finance` (declared) · `finance.db`: the resolver clears the WRONG bills Marg has answered, after a backup, one audit row each.

## The fault — F-614
On the purchase month page a bill is marked **Wrong** with the amount believed right. When Marg is re-exported with that amount, bill-wise and supplier-wise agree again — and with the disagreement the **Correct button leaves the row**, so the WRONG verdict can never be cleared and the month reads *"marked Wrong and not yet resolved"* for ever. Found 22-Sep on August: bills 148 (Kedar, ₹4,608) and 67025 (L.K. Drug House, ₹1,862); the owner's 17:51 supplier-wise export reached the server at 18:01 with exactly those amounts.

## What it does
- `/root/finance/purchase_app.py` `d1476f80` → `8788962a` by `apply_s371.py` (rev 13):
  - `_resolve_wrong()` — after every bill-wise / supplier-wise push, a WRONG bill whose live Marg amount is the amount marked right (within ₹1) becomes **Correct** by itself; the reason names the export; audit row `verdict_resolved`. A FINAL month is never touched.
  - a WRONG bill **keeps its Correct button** until the month is final, so a person can always clear one by hand.
  - a resolved bill shows *"resolved: Marg's re-export … carries ₹…"* beside its Correct chip.
- `resolve_now.py` — run once at install over every WRONG bill in the live database (idempotent; prints supplier, bill number, rupees). If an amount he typed differs from what Marg now carries, the bill stays WRONG and the page offers Correct.

## Proof
`walk_s371.py` — real app, scratch copy: the two bills marked WRONG at 4,608 and 1,862 exactly as the page does it, plus a third at an amount Marg does not carry · August cannot finalise and names them · all three keep their button · Marg's 22-Sep supplier-wise export pushed through the door (at build) / the resolver run as the installer runs it (on the box, where the export already landed) · 148 and 67025 resolve themselves, two audit rows · the third stays WRONG, is cleared by the button · August can finalise · the page offers FINALISE and shows the resolution — **11/11** in both modes.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S371_PURCHASE_WRONG_RESOLVE/install_S371_PURCHASE_WRONG_RESOLVE.sh
```
