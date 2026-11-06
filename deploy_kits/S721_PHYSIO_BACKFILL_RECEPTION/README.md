# S721_PHYSIO_BACKFILL_RECEPTION — Bhati's October home visits in one go; reception writes the clinic slips · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** On a home patient's page Bhati ticks every day he visited (from 1 October) and saves once; and Alisha, Shivani and the reception login can write the physiotherapy clinic slips, while the home visits stay Bhati's.

## The owner's words (board, 08:11 IST 06-Nov)
"bhati home visit backfill option required for october mth, reception shd be able to do physiotherapy clinic slips entries also"

## What it changes
- `/root/finance/physio_book.py` a085fee7 → **9c3442d6**
  - **Purane visit ek saath (backfill)** — a fold on each home patient's page: every day from the floor (`physio_book.from`, 01-Oct) to today as a tick box, grouped by month; days already written for that patient (on any of his home courses) show ✓ and cannot be ticked; one amount; *Tick kiye din likho ✓* writes one visit per ticked day (`POST /finance/physio/book/home/visits`, at most 62 days a press). A ticked day before the patient's start moves the start back to it (audited), so his payments of those days can be written too. Read on the 04-Nov copy: one home patient, started 19-Oct, no home visit written yet.
  - **Reception** — a maker NOT named in the setting `physio_book.home_makers` (default `bhati`) writes CLINIC slips exactly as Bhati does; the *Ghar (Home visit)* tab is not shown to it, and every home page and write, voiding a home row and setting a home-only patient's clinic ID are refused. So a receptionist given the role later is clinic-only by default. The doctors are never limited.
  - The day's match card reads *Register (slips)* instead of *Bhati (slips)*, since reception now writes slips too. Two presses at the same moment cannot both write: the backfill takes the database's write lock before it reads what is already written.
- `/root/portal/tile_grants.json` v42 → **v43** (64305c5f → f2dad157): the *Physiotherapy* tile to alisha, shivani and reception by name — their door; on that page the *Patient-wise register ›* button shows for anyone with a register role. Display only; the portal reads the file on every request (no restart).
- `finance.db` `unit_role` (seed_s721.py): physio register maker for alisha, shivani and reception; a *physio* viewer row for the shared reception login (the front gate asks every physio page for one; alisha and shivani already hold physio maker). Only where absent; undo removes exactly these.

## Cold review (independent agent, S390)
**SAFE TO INSTALL**, no blocker. Its should-fix points built: the write lock against two simultaneous presses; *already written* across all the patient's home courses; an allow-list (`home_makers`) instead of a deny-list; the clinic-ID door; the match card's label; `--undo` refuses when the live file is no longer this kit's. Noted, not changed: reception may void a clinic slip of any day (as Bhati may); the reception login's *physio* viewer row opens the physiotherapy day table, which carries no home-visit money.

## Proven
`walk_s721.py` **43 of 43** on a made-up register: Bhati's clinic and home lists byte-identical to the live page before anything new is written; the backfill (three days, the start moved and audited, a day never written twice, before-floor / future / none ticked / over 62 / bad amount / paused all refused, the doctor too); reception (clinic slips written, a slip Bhati wrote refused, no Ghar tab even with `?tab=home`, all five home writes and a home void refused with nothing written, a clinic void allowed), Alisha and Shivani the same, a maker nobody named is clinic-only, a home-only patient's clinic ID refused to reception, a day written on the patient's closed course never written again, the setting governs it, the doctor never limited, a login with no role refused. Control (the live file): **30 red**. Installer rehearsed (as S720's, with the roles step and its undo).

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s721kit && cp -rp /root/deploy/repo/deploy_kits/S721_PHYSIO_BACKFILL_RECEPTION /tmp/s721kit && bash /tmp/s721kit/install_S721_PHYSIO_BACKFILL_RECEPTION.sh
```
## Undo
```
bash /tmp/s721kit/install_S721_PHYSIO_BACKFILL_RECEPTION.sh --undo
```
