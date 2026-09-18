# S316_SHEETS_SEEDED

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S316_SHEETS_SEEDED/install_S316_SHEETS_SEEDED.sh
```

The S315 page asked the owner to name amounts. He corrected it: extract the X-rays from the register, drop the word *X-ray*, fix the spellings, list them — and let him **approve, rename, reject or add**. Same for the procedures, from the list he had already given. No backfill.

**Where the two lists come from — found, not invented.**

- **X-rays:** `deploy_kits/S223_XRAY_LIST/xray_list.json`, the S223 extraction of the clinic's own *X-RAY DETAIL RAGISTER* — 6,177 entries, 1,197 distinct typed forms, reduced to **19 studies in frequency order** (Knee 684, Lumbosacral spine 600, Knee studies 423 …), spellings corrected (SHUOLDER/SHOLDER/SHOUKDER → Shoulder, CARVICAL → Cervical, SPAINE → spine, ELWOB → Elbow, CLAVICAL → Clavicle, FORAM → Forearm), and PROSISER removed because he ruled it a procedure.
- **Procedures:** his own rulings of 04-Sep-2026 — the eleven cast/slab sites (U slab may be a cast; the clavicle bandage is neither), the five ILI sites, dressing — **17 lines**, each carrying the consumables exactly as he set them: fibrecast 2″–5″, roller 4″/6″, padding 4″/6″ as size × quantity; stockinette used/not-used; Loftypred **or** Viracort; the D600 drape selectable.

**What he does:** one tap per line. A rejected line is kept, greyed, and can be brought back. A price is optional; what his own days actually carry is shown as a hint, never loaded as data. The read-back door (`/api/services`) now carries **approved lines only**.

**Migration:** the S315 tables are altered in place — six columns added, nothing rewritten, nothing deleted; `test_migration_s316.py` proves an S315 row of his survives with its name and price.

**Proof:** walk **33 checks** through the real module over a scratch copy of the live `finance.db` (both lists arrive written; the taps; a rejected line survives; two lines cannot share a name; the door carries only approvals; a re-run of the seed adds nothing; `clinic_day_line`, `stock_snapshot` and `day_line` row counts unchanged) · migration test 6 checks · negative controls red at 1 (duplicate seeding, caught by the unique index), 26 (door without the approval filter) and 22 (any status accepted).
