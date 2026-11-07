# S746_STMT_TWO_BILLS — two bills on Variety's monthly statement: the Clinic's and NK Pathology's (D845 item 4, part A)

*Built in the Scan App chat, session 398, 07-Nov-2026. It follows your answers: "two bills, NK pays its own" (07:40 IST) and an
estimate paid stays out of the accountants' packs (07:47). Your FINAL was given at 07:49 on the mock-up
https://claude.ai/artifact/TnmxQxuSGQ48ggNVrPgBfQ. Kit number from the board (`_numbers` v1031 → v1032). The plan is in
`03_WORKING_PAPERS\S398\S398_NK_SHARE_PLAN.md`.*

## What your Stationery page shows
- **Section 5, Monthly statement:** two boxes, **Clinic's bill** and **NK Pathology's bill**.
  - Each box joins Variety's bill for that side and takes rates for its own lines only. Each is marked paid on its own; NK's says
    *paid by NK*.
  - NK's bill is put on the **NK Pathology lane**: the join moves it there, and the move is audited. It therefore goes into NK's
    accountants' pack (8.1) by itself.
  - A paper on the NK lane cannot be joined as the Clinic's bill, and the same paper is never joined twice.
  - The statement reads **paid** once every bill on it is paid. A statement with lines for one side only shows only that side's box.
- **Section 2, the NK ledger,** and **the account:** each line reads its own side's bill and payment. NK paid while the Clinic is
  not yet paid counts as paid for NK.
- **An estimate** given instead of a bill is joined and paid the same way. It does not go to an accountants' pack (your rule).
- **A statement billed before this kit**, where one bill covered both sides: its NK lines read that same bill and payment. If such a
  statement was billed but not yet paid, mark both boxes paid for the one payment. (None existed on 07-Nov.)

## Files
| file | from | to |
|---|---|---|
| `/root/assetapp/stationery.py` | S743's TO (`PIN_FROM_stationery.txt`) | `PIN_TO_stationery.txt` |

- **The change:** 22 counted edits (`edits_s746.py`), rebuilt on the box by `make_s746.py`.
- **The database:** five additive columns on `stationery_stmt` (`nk_*`). The installer adds them, carries any older statement over
  (after a backup of the database), and does both **before** the new file is placed; the app's own start adds the columns too.
  Only `assetapp` is restarted.
- **Not touched:** the parent's `packs.py` and the NK Pathology chat's files. Pack 8.1 already takes every bill on the NK lane.

## Proof
- **App walk on the real app** (`walk_s746_app.py`, made-up rows): 15 of 15 green. Its control on S743's file: 11 of 11 red, 4 of 4
  guards green.
- **Page walk in Chromium** (`walk_s746_page.py`, 1366 and 390 px): 7 of 7 green. Its control: 4 of 4 red. S743's page walk on the
  new file: 20 of 20.
- **The carry-over step,** on a made-up database: it carried over one old statement, left a Clinic-only one alone, and a second run
  changed nothing.
- **Rehearsal on a made-up root:** 7 of 7.
- **Independent cold review:**
  - R1 NOT SAFE. The blocker: statements billed under the old code would have been misread. Two should-fix points: the account's
    totals and the bill names. All three are built.
  - R2 SAFE TO INSTALL. Its should-fix is built too: the carry-over runs before the file is placed.

## Install (the VPS, as root)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S746_STMT_TWO_BILLS/install_s746.sh
```

## Undo
```
\cp /root/assetapp/stationery.py.bak_S746_d76a808d /root/assetapp/stationery.py && systemctl restart assetapp
```
The five added columns are left in place; the older code ignores them.
