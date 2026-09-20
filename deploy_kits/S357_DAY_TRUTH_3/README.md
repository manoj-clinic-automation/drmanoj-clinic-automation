# S357_DAY_TRUTH_3 — a home / procedure credit note is goods back, not cash short

**Project: Sanjeevni — Pharmacy & Marg · session S275 · 20-Sep-2026, 22:2x IST.** On S356 (live 22:17). The owner, on reading S356's note about 11-Sep: *"The home medicine purchase return is only a bookkeeping entry of what goods or medicines given to home are returned; the amount is not deducted from the day's cash. So the 11 September cash should not be low."*

## What changes

- **`day_resync.py`** (S356 `cfe61ee6` → this kit's pin): pass 2 now turns a credit note on a home / procedure label bill into **one `cash_adjustment` row of +amount** (source `manual`, status `explained`, the ruling as its explanation), once per bill — the ledger's own ± column, which `v_cash_ledger` already adds. The 11-Sep `CN00208` becomes +₹2,300; that day's net cash reads ₹17,223, not ₹14,923.
- **`darpan_kal.py`** (`28e23b15` → `04bb1586`, one anchored edit by `apply_kal_s357.py`) and **`darpan_kal.html`** (`e62746d8` → `31f737f2`): Darpan's expected cash adds the day's adjustment and shows it as one row (Hindi on his card, English on the owner's) only when there is one — so his page and the approval section agree to the rupee. Nothing else on the page changes.
- `clinic-finance` **restarted** (the kal blueprint lives in the app) — **declared to the parent**. Cron unchanged (S356's line runs the same file).

## Proof

- `selftest_s357.py` **30/30**: everything S356 proved plus the credit note as one +2,300 adjustment (explained), none elsewhere, none duplicated on a second run.
- Walk on the PC over a copy of the nightly database: the patched `compute_day` and `v_cash_ledger` agree — 11-Sep expected **17,223** on both; 09-Sep **12,222** on both.
- The installer rehearses the kal patch from the live files into scratch and refuses unless the bytes are the predicted hashes; on red every file is restored byte-identically and the service restarted.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S357_DAY_TRUTH_3/install_S357_DAY_TRUTH_3.sh
```
