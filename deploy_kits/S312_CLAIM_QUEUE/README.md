# S312_CLAIM_QUEUE — Darpan's claim queue (D471), and the door hub step 8 never had (D544)

**Project:** Sanjeevni — Pharmacy & Marg · **Session:** S268 · **18-Sep-2026**

## The one line, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S312_CLAIM_QUEUE/install_S312_CLAIM_QUEUE.sh
```

## What changes on the screens

**Darpan's card** gains one section, *8 · Stock ke sawaal*, and it is invisible on a day when
nothing is being asked. Each line shows what the server already knows about it and five taps:
*Bina bill ke gaya · Supplier ko wapas gaya · Mil gaya · Toota / kharab · **Pata nahin***.
"Pata nahin" is offered first-class on purpose — in a record like this a guessed answer is worse
than an honest blank. A claim older than fourteen days rises to the top of his list with a red
edge and says how old it is (D471).

**The owner's hub, step 8** gains what it never had: Darpan's answer coming back, a one-line count
of where the claims stand, and a settle tap per line. The step can now read **done**.

## The three states, and who may move between them

| from | to | who | where |
|---|---|---|---|
| — | open | nobody taps this — the owner's own word `RECOVER` on the line raises it | the hub, derived |
| open | contacted | **Darpan**, with his answer | his card |
| contacted / open | settled | **the owner only** | the hub |
| open / contacted | settled | **by itself**, when a later count finds the item agreeing | the sweep |

A line whose word is taken back is **withdrawn, not deleted** — the queue is a record of what was
asked, not only of what is outstanding. And a settled claim is **not** resurrected by the next page
load, even though the line is still marked `RECOVER` and always will be: the mark is what the count
recorded, the settlement is what happened afterwards. Only a word given *after* the settlement
reopens it, in the same row.

## The self-close: read `KIT_ID.txt`

The short version: the purchase-return rule is written and asleep because **no purchase return is
stored on this box** (F-527). A later count closes claims today; a credit note is a candidate and
closes nothing.

## Files

| file | what |
|---|---|
| `claim_queue.py` | the queue itself — schema, the three states, the sweep, the reads. No route, no blueprint. |
| `patch_stock_claims_s312.py` | `stock_app.py`: `_pursue_block()`, step 8's state, the owner's settle door |
| `patch_darpan_claims_s312.py` | `darpan_app.py`: his two doors |
| `patch_cards_s312.py` | `darpan_card.html` and `stock_hub.html` |
| `selftest_s312.py` | 47 checks with negative controls, in memory, no Flask |
| `walk_s312.py` | on a scratch copy of the live database: **old = new on every key but step 8** |
| `install_S312_CLAIM_QUEUE.sh` | 8 gates; refuses, walks, places, reads back, restores |
