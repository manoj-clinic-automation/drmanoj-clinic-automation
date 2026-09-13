# S247_LEDGER_LATE_COLLECT — collect an advance against a month that is already closed

`staff_ledger.py` **v3.7 → v3.8**, built 13-Sep-2026 on the file that is live now
(`49b13f42…`).

## The owner, 13-Sep-2026

> Alisha advance of twenty fifth August, which was made against the August month, has been marked
> for September in your salary sheet. I want it to be deducted in the August month salary payment
> only. **I cannot find any flow for that.**

He was right: there was none.

## What was actually wrong — read off the live pages, not guessed

| | |
|---|---|
| the advance | Alisha · `2026-08-25` · Rs 5,000 · id `94c417126369` · interest-free |
| its attribution | **against 2026-08 salary — already correct** |
| the ledger's own line | *"recovers in full at the 2026-09 close (quota lane, against 2026-08 salary)"* |
| Sheet 3, August | Alisha · Advance ded. **0** · net 8,650 |
| why | **August's close was pressed on 20 August** (S238's own README records it). The advance arrived on the 25th. `close_month()` refuses a re-close — by design, a month closes once — so everything entered afterwards falls to the next close. |
| what the card offered | **Defer**, which moves a collection *further away*. Nothing pulled one back. |

## What this kit adds — one control, and nothing else

On an open advance card, beside Defer:

> **Collect against a month that is already closed** — a close is never repeated, so this records
> the same collection by hand.
> `[month ▾] [amount] [reason (required)] (Collect in that month)`

It writes **one `ADVANCE_INSTALMENT` row** stamped to that month — byte-for-byte the shape the
close itself writes — carrying the name of the person who decided it, the date, and the reason:

```
collected against 2026-08 salary, recorded by manoj after that month had already
been closed -- <his reason>
```

Narrow on purpose, and each refusal says which rule it hit:

- the month must **already be closed** — an open month's own close will do it;
- **never earlier** than the month the advance counts against;
- **never twice** for the same advance and month;
- **never more** than the balance; a part amount is allowed and leaves the rest open;
- **checkers only**; a maker gets 403.

The month list on the card only ever offers months that will actually be accepted, so a refusal is
something he has to work at rather than something he trips over.

**`close_month()`, the waterfall, the quota lane, the capacity rule, interest and schedules are not
changed by one line.** The ledger stays append-only; nothing is edited or deleted. Because the
collection reduces the balance, the **next close simply finds nothing left to take** — proven.

## Proof — `EVIDENCE_S247.txt`, verbatim

- **The module's own selftest: 323 checks, unchanged and still passing.** This kit adds no check
  to that suite and breaks none of it.
- **`walk_late_collect_s247.py` — 55 checks, 55 ok.** A real ledger directory, real `users.json`
  and `ledger.jsonl`, the real Flask app over WSGI, with the situation rebuilt exactly as it
  happened: **a month is closed first, and the advance arrives afterwards.** It covers the page
  offering the control; seven refusals, each of which leaves the ledger file **byte-identical**; a
  maker refused 403; the collection writing **exactly one** row of the right shape, with the
  person, the reason and a `late_collection` mark; the balance going to nil; the advance leaving
  the open list; a second attempt refused; **the next close collecting nothing more**; a partial
  collection leaving the rest open; the other advance in the ledger untouched; a hand-typed
  instalment still impossible; and `close_month` still refusing a re-close.
- **`probe_live_shape_s247.py` — 22 checks on a COPY of the real ledger**, which renders every page
  the owner uses and then **performs the collection on the copy**, so the thing being installed is
  proven on his own data before it is placed. The copy is deleted; the live store is only read.
- **Negative control:** the walk cannot even start against the live v3.7 file — no `closed_months`.
- `patch(live bytes) == the kit file`, byte for byte — 5 asserted single-match edits.
- F-185 gate clean; all files LF.

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S247_LEDGER_LATE_COLLECT/install_late_collect_s247.sh
```

Refuses unless `/root/staff_ledger.py` is exactly `49b13f42d3a923c5bb2e34230c80e6e8` and
`staff-ledger.service` is the unit running it. Gates in order: kit SUMS + KIT_ID → the live pin →
the module selftest (323) → **the kit's walk on the box** → **the probe against a copy of the real
ledger** → `.bak_S247_LEDGER_LATE_COLLECT_<stamp>` → install → restart → `/ledger/advances` 302 and
the service reporting v3.8. Any red after placing: the old file is restored and the service
restarted. Re-run → `ALREADY INSTALLED`.

**Predicted to-pin:** `staff_ledger.py` → `eacd71544715ff597712aee5e6233135`.

Rollback: the line the installer prints, or

```
\cp -f /root/staff_ledger.py.bak_S247_LEDGER_LATE_COLLECT_<stamp> /root/staff_ledger.py && systemctl restart staff-ledger.service
```

## Then, the correction itself — one card, one tap

```
https://followup.dr-manoj.in/ledger/advances
```

Alisha's card → month **2026-08** → amount **5000** (already filled in) → a reason → **Collect in
that month**. Her August advance deduction becomes 5,000 and the balance goes to nil.

Reload the August money sheet afterwards:

```
https://attendance.dr-manoj.in/register/salary/flow/sheet2?ym=2026-08
```

August is **not locked**, so the salary sheet recomputes. Sheet 2 was approved on 12-Sep — approve
it again after the change so the pack matches what is paid.
