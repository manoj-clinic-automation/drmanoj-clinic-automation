# S261_VENDOR_PAY — the NEFT sheet, inside the system

*Session 256 · 14-Sep-2026 · one anchored insert into `purchase_app.py`, not one existing line edited*

## What it is

Until now the month's payment was worked out in a workbook on the owner's PC,
prefilled by a script from an export. That is how a draft carrying **last
month's** figures could sit in the payment folder for two weeks looking
finished. The sheet now lives where the figures live.

```
https://followup.dr-manoj.in/finance/purchase/page/pay
```

That address always opens the newest month, so it is what a tile points at.
A month has its own address too: `/finance/purchase/page/pay/2026-08`.

## The order is the owner's, 14-Sep-2026

**1 · PREPARE.** The sheet, filled by the system from its own figures: every
vendor, the bills split into the two fortnights the sheet has always used
(1st–15th, 16th–end), the month, what is payable, and which lane the vendor is
paid through. Open a vendor for its bills; open a bill for the bill itself —
every item line with batch, expiry, quantity, rate, discount and amount, loaded
only when asked for. Below it, the same thing as a table: **the sheet as it
prints**, with a TOTAL row.

**Carried in** is the one figure typed here, and the page says so: July was
settled outside this system, so this server does not know what an earlier month
left outstanding and does not pretend to. It is typed on the line, kept per
vendor per month, audited, and added into that vendor's payable at once.

**2 · VERIFY.** The supplier-wise purchase statement is the **cross-check, not a
tick-box**. The check reads Marg's own supplier-wise export of the same month and
holds the prepared sheet against it three ways: every bill it carries, the
per-bill amounts where both reports exist, and **the statement's own printed
grand total**. It either says it agrees to the rupee or names exactly what does
not. Every run is kept — who ran it, when, and what it found — and the page shows
the last one rather than claiming a check that never happened.

**3 · LOCK.** Finalise the month once the check agrees, and the figures stop
moving. The advice file and its covering letter are built from this sheet and
from nothing else.

## The two standing rules, in the page

**A vendor whose account is not confirmed on this server is never in the NEFT
total.** The server already holds each vendor's account name, number, IFSC,
branch and a bank status that can be marked VERIFIED with who verified it and
when — the phone book page has done that all along. This page reads it:
confirmed → NEFT; anything else → a CHEQUE chip on the line, and a section
naming them with the reason in plain words and a link to the one screen that
fixes it. **The moment an account is added and confirmed, the vendor moves to the
NEFT lane by itself.**

**A small difference is flagged, never swallowed.** KEDAR's bill 148 reads: *the
lines add up to ₹4,608, ₹6 more than the bill — Marg reports a purchase return
against it. Worth opening: it may be an entry that needs correcting.* A bill
merely waiting for its item lines is a quiet grey note; a CHECK chip means
something is actually wrong.

## What is touched

`/root/finance/purchase_app.py` — **from `52550e63e7fdffc186de4fcd4f93717b`
to `a7df849bb3d22b626eed1a958adc8107`**, patched on the box from its own live
bytes. The kit does not carry that file.

Two small tables are created on first request, never at import (F-303):
`purchase_pay_line` (what a person types — carried in, paid, a note) and
`purchase_pay_check` (every run of the verification, appended, never
overwritten).

The insert adds `_vendor_bank`, `_pay_rows`, `_verify_statement`,
`/api/bill-lines`, `/api/pay-line`, `/api/pay-verify`, `/page/pay/<month>`,
`/page/pay`, the page's CSS, and a **wrapper** around the nav helper so every
purchase screen gains the way in. The nav's format string, the hub, the month
page and every existing behaviour are left exactly as they were — the wrapper is
why there is one anchor and not three.

A final month refuses both writes, by the doctor's own rule.

## Proof

**`walk_vendor_pay_s261.py` — 39 checks, all green, offline.** The page is
rendered over HTTP from a real database built on the server's own schema, and
every check reads the bytes that came back. Among them: the sheet comes first and
the verification second; the sheet carries both fortnights, carried-in and
payable; a vendor with no confirmed account is routed to a cheque and named, and
one *with* a confirmed account carries no chip; the ₹6 return is flagged in those
words; a typed carry-forward of ₹310 moves that vendor's payable by exactly
₹310; the bill's own item lines really load; the verification agrees on a good
month, **fails and says what to go and take when no supplier-wise statement has
arrived**, and **catches a statement whose printed grand total differs**; and the
page never claims a check it has not run.

**`walk_live_s261.py` — 18 checks, run by the installer ON THE BOX against a
COPY of the real database**, before the service is restarted. It proves the page
on the clinic's own months: the vendor lines add up to the month's own Marg total
to the rupee, every supplier has one line, every bill sits under its vendor, the
verification runs and reports, and a real bill's lines load.

The installer refuses on a from-pin mismatch, backs up, checks the patched file
against its predicted md5, runs the walk, and **restores byte-identically if any
of it fails** — proven end to end against a fixture root, including the rollback
path and a second run reporting ALREADY INSTALLED.

## Installing

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S261_VENDOR_PAY/install_S261_VENDOR_PAY.sh
```

## What it does not do yet

The tiles. `S262_PAY_TILE` puts it on the owner's PWA and grants the same page to
Shavez, who needs the NEFT list to carry into the advice file.
