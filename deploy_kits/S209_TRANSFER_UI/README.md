# S209_TRANSFER_UI — the owner Transfer control, which had no screen

## The finding (candidate F-245)

`S208_LEDGER3` shipped **two working owner-only API routes**:

- `GET  /finance/darpan/api/ledger-check?date=YYYY-MM-DD`
- `POST /finance/darpan/api/transfer`

and a message written for the owner to read:

> *"NO cash_movement row for 2026-08-27 -- the transfer-out was never saved into
> the day. Record it as an owner transfer below, with the date, so the record
> exists with an audit trail."*

**The words "below" refer to a control that was never built.** There is exactly ONE
`darpan_corrections.html` in the repository (S208_DARPAN, 3,157 bytes) and it
contains **no reference to `ledger-check` and none to `api/transfer`.** The
corrections page renders only the cash-to-UPI table.

So the owner was told for three days to enter the 27-Aug repair "through the
owner-only Transfer control on the corrections page", and **no such control existed
on any page.** The capability was real; the wire was missing.

**This is F-161 exactly** — *"a capability without its wire is a claim; when auditing,
grep for the CONSUMER, not the definition."* Recorded then, repeated here, and it is
the second instance of the class found today.

## What this kit does

Replaces `/root/finance/darpan_corrections.html` with the same page **plus** a second
section: the date-driven ledger check, and the owner transfer form.

**The existing cash-to-UPI section is untouched** — its markup, its script and its
behaviour are carried through byte-for-byte; the new work is appended.

Built to the API contract as read from `darpan_app.py`, not from memory:
parties `counter · drawer · dr_bhawna · dr_manoj · bank`; amount > 0; date
`YYYY-MM-DD`; **note required** (the server refuses without one); `403 owner_only`
handled with a sentence rather than a silent dead button.

## Proof

- **`js_gate.py` PASS** — both script blocks parse. (The S209 gate, applied to its own
  first new page.)
- **not one apostrophe inside any JS string on this page** — the S209 fault, by
  construction rather than by luck.
- every failure path writes a visible message; **no path leaves a section spinning.**

## Install — after publishing, on the VPS

```bash
cd /root/deploy
git -C repo fetch --depth 1 origin main && git -C repo reset --hard origin/main
cp -f /root/finance/darpan_corrections.html /root/finance/darpan_corrections.html.bak_S209
cp -f repo/deploy_kits/S209_TRANSFER_UI/darpan_corrections.html /root/finance/
md5sum /root/finance/darpan_corrections.html
echo "expected:  f2f6f60ed57681c9fde7ddbbc4dc90d7"
```

**No service restart** — the page is read from disk on every request.
Then open `/finance/darpan/corrections`, put **2026-08-27** in the date box, and the
27-Aug transfer can finally be recorded: drawer to dr_bhawna, 23130.

*S209 · 30-Aug-2026 · nothing installed by this kit; it is one file and a copy command.*

---

## S209.2 — CANDIDATE F-246: the warning its own remedy cannot clear

After the owner recorded the 27-Aug transfer exactly as instructed, the page still said
**"NO cash_movement row for 2026-08-27 -- ... Record it as an owner transfer below"**.

The entry had saved. The check reads a **different table**:

- `api_ledger_check` problem 2 counts rows in `cash_movement` (joined to `day_entry`).
- `api_transfer` writes to `cash_custody_event` — deliberately, because an owner transfer
  records **custody**, not a day-ledger movement. Its own docstring says so.

So the message prescribes a remedy that **cannot** satisfy the condition that produced it.
Follow the instruction perfectly and the complaint remains — which reads, to the person
who just did the work, as "it did not save".

**Fixed here page-side, without touching live money code:** the check now displays the
custody events for the date, and when the cash_movement warning is present alongside one,
it says plainly that the two are different records and that the transfer IS saved.

**The server-side wording still needs correcting** — the message should not tell the owner
that recording a transfer will clear it. That is a `darpan_app.py` change and is left for
a kit of its own, deliberately: it is live financial code and the page fix removes the
confusion today.
