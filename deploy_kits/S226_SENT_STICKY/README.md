# S226_SENT_STICKY — a sent count that forgets it was sent

While Darpan and Amir counted, the end of the flow — **Report** and **Send to
ledger** — had not been driven by anyone today. It was driven offline. The flow
itself is sound: the report names the right differences, the send raises exactly
the right ones with the right numbers, the finding is sealed in the same breath
and the data horizon is frozen with it. **18 of 18** before this change.

One hazard came out of it, and today it was of my own making.

## What happens

On a successful send the page wipes its working copy — correct, the ledger holds
the count now — and sets `SENT` so the button locks and reads *"Sent — count
#N"*. But `SENT` was **a JavaScript variable only**. After a reload:

```
entries = {}      progress = 0 / 373      button = "Send to ledger"  (enabled)
```

An empty list, an enabled Send button, and nothing on screen saying the shelf had
already been counted and recorded. The obvious next move is to count it again and
send it again — and the server records that as a **second, separate count of the
same morning**.

**It is not hypothetical: the owner was told to reload the page mid-count today,
to pick up the search box.** The instruction was mine.

## The fix

The marker is saved with everything else, so it survives a reload, and the page
says plainly what happened:

> **This count has already been sent to the ledger — count #1 at 10:17 AM.**
> 2 difference(s) were raised. The list below is empty because the ledger holds
> the count now — that is normal, and nothing has been lost.
> Do **not** count the shelf again for the same day unless the doctor asks for
> it: a second send is recorded as a second, separate count.
>
> `[ Start a genuinely new count ]`

That button asks first, and says in the question that the count already sent
stays in the ledger untouched while whatever is sent next is a separate count.

**And the clock on it is the wall clock.** The stored stamp is ISO/UTC — right
for a record, wrong for a person. Sliced raw it read **04:46** for a count sent
at **10:16** in Bareilly. The walk checks the banner's time against the machine's
own clock to within five minutes, so this cannot come back.

## Proof

| walk | result |
|---|---|
| `WALK_submit_flow_s226.py` — seeds a real half-count, opens the report, sends it, reads the ledger rows back, then **reloads** and drives *Start a genuinely new count* | **30 / 30** |
| `WALK_count_search_s226.py` re-run unchanged, as the regression | **24 / 24** |

What the submit walk actually checks in the ledger, not on the screen: the count
row and its bill, exactly two differences and the right two, `TYRO BR` at
700 / 690 / −10, the sealed finding, and the frozen readiness payload.

## Installing during a count

Safe, and proven the same way as the last one: the count lives in the browser's
own storage under `sanj-stock-live-v1` and this does not touch it. Amir reloads
once and carries on.

**Best installed BEFORE they press Send**, since that is when the hazard starts.
