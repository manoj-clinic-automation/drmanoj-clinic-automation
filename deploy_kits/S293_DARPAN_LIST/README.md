# S293_DARPAN_LIST — Darpan writes the reason against the count-day figures; he does not count again

**Session 264 (Sanjeevni project), after its close · 17-Sep-2026 · step 1 of the stock-check sequence.**

## The ruling

Step 1 is Darpan's printed list. Before list 1 was cut, the assistant noticed the list (S227,
`pad_receipt.render_tranche`) told him to *"go to the shelf and count it again, write the new count in
RECOUNT"* — eleven days after the count, a recount that could never match. The assistant first
proposed holding a new count against Marg's latest closing. **The owner ruled otherwise:**

> *"What is needed is the Marg 6-September stock and the physical counted stock against each other so
> that the actual deficit is visible. Don't take Marg stock of a later date — you have in your record
> the Marg record made available just before the count started."*

He is right, and the list already carries exactly those figures: `stock_count_item.marg_qty` (the Marg
stock loaded before the count, as on 05-09, bills to A003425) and `counted_qty` (the shelf, 06-09),
with the difference. Only the question it asked was wrong.

## The change

`pad_receipt.py`, six anchored edits in the Darpan list only:

- columns **Marg | Shelf | Difference**, then **REASON no.** and a wide **REMARKS** box — the two RECOUNT
  boxes are gone;
- header **LIST n FOR DARPAN — MEDICINES — WRITE THE REASON** (was COUNT AGAIN);
- the instruction names the count day, says what each figure is, asks for the reason number and
  remarks (who, when, which bill), and says **do not count again**;
- footer **Answered by / Date / Returned to**;
- a surplus reads **over 1s**, not a bare 1s.

`stock_amir.html`: the typing board's column *Note / recount* is now *Note*.

No table, no route, no data. The owner's own differences sheet (`render_diffs`, same file) is proven
unchanged. `clinic-finance` is restarted because the running app has imported `pad_receipt`.

## The proof

`selftest_s293.py`, **28 checks, 0 failed**: both files at their live pins; every anchor once; refusal on
a wrong `--from`; idempotence; backups are the live bytes; compile; then the untouched and the patched
`render_tranche()` over one fixture, read back as text (the old says COUNT AGAIN / RECOUNT, the new says
WRITE THE REASON / Do not count again, has no RECOUNT column, names 06-09-2026, and every row keeps its
three figures, the surplus reading *over 1s*); and `render_diffs` identical before and after. The
installer was rehearsed in a scratch root: install, idempotent second run, and refusal on a tampered
file. A rendered page is in `EVIDENCE_list_s293.png`.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S293_DARPAN_LIST/install_S293_DARPAN_LIST.sh
```

Rollback: the two `.bak_S293_*` files beside the originals, then `systemctl restart clinic-finance`.

## Then

Amir's board → **Darpan's lists** → cut list 1 (medicines) → print → hand to Darpan → back → Amir types
the reason numbers and notes → the owner decides on the desk.
