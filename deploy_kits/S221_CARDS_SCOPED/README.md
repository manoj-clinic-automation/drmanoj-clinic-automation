# S221_CARDS_SCOPED — the directory becomes his jobs (B6 rev 2)

**One live file:** `/root/finance/darpan_card.html` (`aeb4fd7d` → **`4a31f14e`**), plus
`cards_registry.json`, which is data and is replaced rather than patched. **No server code
changes.** The live bytes were reproduced offline first — `fa6f0a86` → `fb129eee` → `a0bc0c4c` →
`aeb4fd7d`, **every intermediate matching its recorded pin** — before a line of this was written.

## Why

`S218_CARDS_FINAL_CONTRACT` B6 — the owner's own amendment, one day old — put a **directory of
every staff-facing card** on Darpan's page: seven rows, each with *who* and *purpose*,
self-growing. Read back on the real screen the next morning:

> *"i saw many cards links in darpans card, plan was to keep these separate and scoped in the pwa"*
> … and on the choice offered: **"b ok"**

A man working the counter does not need a map of everyone's surfaces. He needs his own work.

## What changes, and what deliberately does not

**The registry mechanism stays exactly as it was** — a card still ships with its own row and still
joins by itself, no hand-edited list. That was the good half of B6 and it is untouched.

What changes is the **audience** and the **shape**: rows are filtered to the person whose page it
is, the page he is standing on is dropped from his own list, and what remains renders as
**buttons** rather than a directory with two lines of metadata under each link. The full directory
of everyone's cards belongs on the owner's hub.

**This is a display scope, not an access control**, and that sentence is in the patcher so nobody
later mistakes it for one. Every page behind these links keeps its own `require()` and its own
`unit_role` rows. **Reception's access to the Vaapsi desk is untouched by this file.**

## Who owns what — the owner's ruling of 03-Sep

| card | who sees its button | changed? |
|---|---|---|
| Din ka card — Daily Sale | Darpan | |
| Drawer card | Darpan | *(never shown on itself)* |
| Vaapsi desk — Sale returns | **Darpan, Shavez, Alisha, Shivani** | was "Reception" |
| Stock count | **Darpan, Alisha, Shivani, Shavez, Amir** | was "Stock staff" — *"might need 2 persons"* (owner, 03-Sep) |
| Stock differences | **Alisha, Shivani, Shavez, Amir + Dr Manoj** | was "Owner + stock staff" |
| Corrections desk | Amir | **the only card that leaves Darpan's page** |
| Staff register | everyone | |

**Darpan's page therefore shows four buttons:** Din ka card · Vaapsi desk · Stock count · Staff register.

The stock-check conflict is **resolved**: the owner's first list of owners left Darpan off stock
check while his ruling that morning had put him on it. Asked, he ruled *"Stock count might needs
2 persons, so keep darpan and other in it"* — so **Darpan is on the count, and not on the
differences screen**, which stays with the other four plus the owner.

## The fail-safe, biased toward showing too much

If **no** row in the registry carries a `who` key — an old data file against this new page — the
page shows **every** card, exactly as it does today. A man's navigation must never go blank
because a data file lagged a code file. A single row without `who` shows on nobody's staff page
but stays in the registry, so it is visible to fix rather than lost.

## Proof

**RENDER 19/19** — headless chromium at 390 px, on the real page: the heading is his work and the
old directory language is gone; his four cards are offered as real links to the real routes;
Amir's desk, the stock-differences screen and the page he is standing on are absent; the fail-safe shows
everything against a `who`-less registry; an empty registry renders no section at all.

**Judged as a differential.** The harness cannot stub every field the card's other sections read,
and chasing them one at a time would only prove the stub complete. So the **unpatched live card is
run through the same harness first**, and only errors it did not already produce count against
this change. There were none. (The F-87 pattern; the first version of this test reported the
stub's own gaps as page faults, which is F-142's family and is exactly the trap being avoided.)

## Also in this kit: the corrected S221_JAANKARI walk

`walk_jaankari_s221_v2.py`. This morning's walk went RED on the box on one check of thirty-one —
*"with nothing to ask, every list is empty"*. **The code was never in question**; both pins came
back exactly as predicted. The **check** was wrong: to test "nothing to ask" it copied the live
database and only pushed `returns.act_from` forward, which empties one list and leaves the other
two full, because a live database legitimately holds open disputes and due spot counts — yours
held **2 and 9**. It asserted a property of my workspace copy rather than of the code, the F-195
family.

**v1 is left exactly as installed** — the C-S216-1 precedent: correct going forward, sealed kits
untouched. Run v2 from now on; it is green on a clean copy and on one deliberately seeded to look
live.

## Files

| file | what |
|---|---|
| `patch_card_myjobs_s221.py` | darpan_card.html — the directory becomes his jobs (1 anchor + a script-tag balance check) |
| `cards_registry.json` | the ownership above — data, copied into place, not patched |
| `RENDER_TEST_myjobs_s221.py` | the browser gate, 19 checks, offline |
| `walk_jaankari_s221_v2.py` | the corrected walk for the earlier kit |
| `EVIDENCE_render_myjobs.txt` | what the browser printed against these bytes |
