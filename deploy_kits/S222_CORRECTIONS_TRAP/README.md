# S222_CORRECTIONS_TRAP — a control that refuses is a trap

**Session 222 · ⭐1-2 part A · 03-Sep-2026**

> *"Hide the ledger-check and transfer controls the corrections page still draws for a viewer —
> they refuse him safely; a control that refuses is a trap."* — the owner, at the S221 close

He is describing the softer half of F-296. S221 gave Amir `viewer` so he could work the
corrections desk. The **bottom half** of that page is the owner's: a ledger check for one date,
and the control that records an owner transfer. Both are checker-only on the server, and S221's
own patcher re-verified that they still are — so nothing was ever exposed.

What was wrong is smaller and still worth fixing: a purchase man was being shown two controls,
in his own workplace, that exist to tell him no. **Nothing is more corrosive to a new man's trust
in a system than a button that is there to refuse him.**

## How the page decides

It **asks the server** instead of guessing at a role.

```
fetch("/finance/darpan/api/ledger-check")   →   403  →  the block stays hidden
                                                else →  the block is shown
```

That route is checker-only and verified so at S221. The block is hidden **in the markup** and
revealed afterwards, so a viewer never sees a flash of controls he must not use.

**An error shows the block.** That is a ruling, not an oversight. The server is the real gate and
this kit does not touch it, so failing open cannot expose anything — while failing *closed* would
silently rob the owner of his own control on a bad connection. A page-level hide is about not
drawing a trap; it is never about permission.

**Cost, stated plainly:** one extra GET per page load, for the owner only. For a viewer the route
refuses at its guard before doing any work.

## Why no role is read client-side

Because this page has no honest way to learn one. It carries no `data-user`, and giving it one
would have meant editing `darpan_app.py` — whose live bytes **no store holds**. Three divergent
copies sit in the repository and fourteen patchers have run over them since; nothing reproduces
the live pin. Guessing at a file nobody can reproduce is how this session already produced one
false RED. Not twice in one day.

*(That is also why this kit exists at all rather than a server-side hide: see
`S222_DARPAN_CORRECTIONS_PIN_CONFLICT.md`. The Register's pin table names `b3cfd86f…` for this
page; the box reads `f2f6f60e…`. The table is stale — the S209 close never bumped it, and the
S210 narrative paid the debt in prose only. Confirmed by reading the box at this session's open,
and corrected at this close.)*

## What it is proven by

`RENDER GREEN 17/17` — headless chromium, on the **exact live bytes**, loading the patched page
three times:

1. **as Amir**, the server answering 403 — the block is not on his screen, the words *"Record an
   owner transfer"* and *"Ledger check"* appear nowhere, and his corrections list renders normally
2. **as the owner**, the server answering 200 — the block is there, both buttons are there, the
   list is there
3. **against a route that is not there at all** — the block is shown, proving the fail-open

Plus: no server file changed, and the block genuinely starts hidden in the markup.

## What it does not do

No server file. No route. No permission. **No restart** — the page is read from disk per request;
a hard reload is enough.
