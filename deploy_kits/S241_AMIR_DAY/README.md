# S241_AMIR_DAY — Amir's day, seven steps

The owner's design is `claude/S240_AMIR_DAY_FLOW.md`; this kit builds it.

**The seven steps.** Punch (a nudge, never a block) → all purchase and
purchase-return bills into Marg exactly as printed → take the two exports,
1st of the month to date → **the server says whether they arrived and verified**
→ one forced answer on every bill on today's list → the salt, new-item and name
list → DAY CLOSED, with the day shown back to him.

**What the screens will not do.** They never ask him whether a report arrived —
the server reads `purchase_export` and tells him, and when a file is wrong it
names the reason and says *pehle desktop par khuli Excel band kijiye*. He never
types a bill number: the list fills itself from the bill-wise export. The answer
on a bill is forced, not optional — a bill with no answer is simply not written
and comes straight back on the list.

**A day he leaves half-done stays open, never failed.** Everything done is kept.
What is left comes back the next time, and an unanswered bill from an earlier day
appears above today's work under **pichhla baaki**.

**A deficiency becomes a claim.** Anything but *theek hai* writes one row in
`amir_claim` — supplier, bill, date, amount, reason, who raised it, when — in
state `open`. Amir raises and never chases. Darpan's queue is the next kit; the
owner's line is already on `/finance/amir/day`.

**Language.** Amir's screens are Hinglish in Latin script. The owner's view of
the same day is English. Neither page renders a phone number.

**Install** — one line on the VPS:

```
bash /root/deploy/vps_deploy.sh S241_AMIR_DAY
```

The installer walks both proofs on the box before it copies anything, backs the
books up before the first schema touch, anchors the mount rather than naming a
kit, and puts `finance_app.py` back byte-identical if anything after the restart
is not right.

**Still to come, and deliberately not in this kit:** the reception override for a
missing punch (attendance lives in another app and another database), and
Darpan's claim queue.
