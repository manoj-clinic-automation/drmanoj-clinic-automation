# S304_COUNT_PROOF — step 7 of the stock check becomes a real proof

**Session 266 (Sanjeevni project) · 17-Sep-2026 evening**, on the owner's "proceed" on the work list: *after Amir
keys the vouchers, the next Marg export is checked against the shelf, and count #1 closes when they agree.*

## What was wrong (mine)

**Step 7 was showing "done" when nothing had been proved.** Since S297, step 7 of the Stock Check hub, *"The proof —
Marg agrees with the shelf"*, took its state from the **counting close** of 06-Sep. That was the moment the count
sheets were finished. So today it reads **done**, though no voucher has been entered and nothing has been proved. This
is recorded as a fault at the close.

## The change

**How the proof is judged.** Movement since the count is not something we can guess, so the server makes the one test
it can make exactly. For every item with voucher lines **entered in Marg** (S301):

- **Drift** is Marg's figure minus our own computed figure, on the same basis.
- It is taken on the **last export day before the first voucher was entered**, and on the **first export day after the
  last voucher**.
- Only days whose computed figure already carries **that day's purchases** are used. Otherwise a purchase received that
  day moves Marg and not us, and would look like a voucher that went wrong.
- Sales, purchases and returns move both figures alike, so **the drift moves only when Marg is changed without a
  document — by a voucher**.
- An item **agrees** when its drift moved by exactly what its vouchers moved.

**What step 7 shows now:**

| state | when |
|---|---|
| **wait** | no voucher entered yet |
| **now** | vouchers entered and waiting for the next export; or some items differ (each named, e.g. *Marg moved +193, the vouchers say −7*, for Amir to look at in Marg); or voucher lines still to make or enter |
| **done — PROVEN** | every entered item agrees and nothing is left to make or enter |

Items that moved in Marg **without** a voucher are counted and shown, but they do not block the proof.

This kit only reads; it writes nothing, and the sealed count is never touched.

## The proof

**`selftest_s304.py`: 20 checks, 0 failed.** It covers:

- **The file:** pin, anchors, refusal, idempotence, backup, compile; the hub script parses and reads the proof, not the
  counting close.
- **Nothing entered:** *wait*, even with the counting closed.
- **Entered, no later export:** *now*.
- **The export after the vouchers:**
  - every item moved by its voucher gives PROVEN;
  - an item moved without a voucher is counted, not blocking;
  - an export whose computed figure lacks that day's purchases is never used;
  - one item not moved gives *now*, with the item named;
  - a line not yet entered keeps it from done;
  - a re-based computed feed gives *now*, never a false proof.

**Rehearsed on the office PC** against the 17-Sep nightly database, through the live S288 → S301 chain
(`rehearsal_s304.txt`):

- **Units:** the count's Marg figure equals the 06-Sep Marg feed on **207 of 207** differing items, both in units.
- **Today:** step 7 reads **wait**.
- **A simulated round** of 29 lines, all entered 11-Sep, against Marg's real 11-Sep export (which never had them): 0
  of 29 agree, with each named.
- **The same export re-sent as if every voucher had been keyed:** **28 of 29 agree**. The one that differs, JAKMAC 5,
  moved +200 in Marg between 05-Sep and 11-Sep with no document on the server — exactly what a person should look at.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S304_COUNT_PROOF/install_S304_COUNT_PROOF.sh
```

It restarts clinic-finance.

**Rollback:**

1. Put back the two `.bak_S304_*` files beside the originals.
2. Run `systemctl restart clinic-finance`.
