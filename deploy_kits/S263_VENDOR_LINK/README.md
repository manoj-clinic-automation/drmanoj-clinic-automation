# S263_VENDOR_LINK — one firm, two names

## The finding

The bank details of 22 vendors were imported at S225 from the April–July 2026
NEFT advice sheets, under **the name the bank knows**. Marg's bills carry
**the name the vendor prints**. For 14 of them those are not the same string.

Only **8 of the 24 imported rows have ever been matched by a single bill.** The
other 16 have sat on the server since 4-Sep, correct and unreachable — and every
one of those vendors has been falling to the cheque lane while its own account
was already on file. **August routed ₹2,22,608 to cheques for this reason alone.**

Checked across all four sheets: not one vendor changed bank in April–July, and the
server's copy matches July's sheet exactly. Nothing was stale — only unmatched.

## The fix is a link, not a copy

One account still lives in exactly one row. The bill's name simply points at it:

```sql
CREATE TABLE IF NOT EXISTS purchase_vendor_alias (
  bill_norm TEXT PRIMARY KEY, register_norm TEXT NOT NULL, who TEXT, at TEXT)
```

`_vendor_bank` is **wrapped, never edited** — the way S261 wrapped `_book_nav`. A
bill name linked to a confirmed account row inherits that row's NEFT lane and
**says whose row it is** ("account confirmed — on the register as KEDAR PHARMA").
A link to a row with no confirmed account changes nothing: a link cannot invent a
lane. No account number is duplicated, so there is no second copy to go stale, and
when Marg renames a supplier again the answer is one more row — not a re-import.

## The fourteen pairs

Each confirmed by the owner on 14-Sep-2026 after the finding was put to him.

| the name on Marg's bill | the name on the account row |
|---|---|
| KEDAR PHARMACEUTICAL | KEDAR PHARMA |
| GUNINA PHARMACEUTICALS PVT LTD | GUNINA PHARMACEUTICALS |
| L.K. DRUG HOUSE | LK DRUG HOUSE |
| SHRADDHA MEDICOSE | SHRADDHA MEDICOS |
| YOGENDRA AGENCIES | YOGENDRA |
| JUBILEE AGENCIES | JUBLI AGENCY |
| YUVIKA SURGICALS | YUVIKA SURGICAL |
| ESS KAY AGENCIES EXTN | ESS KAY AGENCIES |
| RADHA MEDICAL & SCIENTIFIC | RADHA MEDICAL AND SCIENTIFIC |
| DRUG DEAL | DRUG DEALS |
| RAVI MEDICAL AGENCY | RAVI MEDICAL AGENCIES |
| SAISUN PHARMA PVT. LTD | SAISUN PHARMA PRIVATE LIMITED |
| VERMA BROS. AND CO | VERMA BROS.AND CO |
| SCIENTIFIC&MEDICAL AID CENTRE | SCIENTIFIC & MEDICAL AID CENTRE |

**ESS KAY AGENCIES EXTN** is here because the owner checked it against the bank
himself. It was the one pair the evidence forced back to him: the advice file paid
"Ess Kay agencies" ₹6,861 / ₹13,491 / ₹10,280 / ₹11,235 in April–July, and EXTN's
Marg bills for those months are the same four figures to the rupee, while "Ess Kay
agencies" has no Marg bill at all. His ruling: *"verified, correct bank, name on
bill is ESS KAY AGENCIES EXTN."*

**Not linked, deliberately:** RAMA MEDICOSE and AGARWAL SURGICALS AND MEDICALS
have no details anywhere and stay on the cheque lane by his ruling until they come.

## No account number is in this repository

None. Not in the block, not in the walk, not in this file. A new vendor's account
travels **on the install line** and is written straight into the database by
`seed_account_s263.py`, which prints it back masked to the last four digits.

That script **never overwrites an account that is already there**: a vendor with a
different number on file is left untouched and named, because replacing a live
account is a decision, not an install step.

Leave the three variables off and the install still runs — that vendor simply
stays on the cheque lane, and the walk says so out loud rather than quietly.

## The walk — 28 checks, on the clinic's own data

Both files are loaded — **the one being replaced and the patched one** — each
against its own copy of the real database, and the only difference allowed is the
lane of the vendors the owner confirmed:

- **exactly** those 14 moved onto NEFT — no more, no fewer;
- **not one vendor lost** its NEFT lane;
- the vendors with no account of their own are **still on cheques**;
- each moved vendor **says whose account row** it is using;
- **not one account row was touched** — the link copies nothing, and no linked
  vendor holds a copy of somebody else's number;
- the link table holds 14 rows, and **running it again adds nothing** — it is safe
  on every request;
- **a link to a row with no confirmed account gives no NEFT lane** (proved by
  planting one and watching it refuse);
- the seeded vendor is on NEFT **by its own account, not by a link**;
- month by month: the page answers 200, the vendor lines still add up to Marg's
  own total to the paisa, and the cheque lane is exactly who it should be;
- `/hub`, `/month/…`, `/scans`, `/orders` all still render.

**Result on the live data: August's cheque lane falls from ₹2,22,608 to RAMA
MEDICOSE alone (₹1,469); September's to AGARWAL SURGICALS (₹400).**

Proven against a fixture root: clean install, **ALREADY INSTALLED** on re-run,
an install with no account given, a second seed of the same account (no double
write), a seed of a *different* account (refused), and a deliberately wrong link
— AGARWAL SURGICALS pointed at KEDAR's account — which the walk caught: 24 ok /
4 failed, **purchase_app.py restored byte-identically and the live database never
touched**, because the account is written only after the walk has passed.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && NEW_VENDOR="DAANSHI PHARMA" NEW_ACCT=<account number> NEW_IFSC=<ifsc> bash /root/deploy/repo/deploy_kits/S263_VENDOR_LINK/install_S263_VENDOR_LINK.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `a7df849bb3d22b626eed1a958adc8107` | `c4a64353e3b8d6ed0e0d46fe0ec32954` |

## Files

| file | what it is |
|---|---|
| `block.py` | the link table, the seeding, and the `_vendor_bank` wrapper |
| `patch_vendor_alias_s263.py` | the one anchored append |
| `seed_account_s263.py` | writes one vendor's account, masked, never overwriting |
| `walk_s263.py` | the 28 checks, before and after, on a copy of the real database |
| `install_S263_VENDOR_LINK.sh` | pins, backup, patch, seed the copy, walk, seed live, restart, roll back |
