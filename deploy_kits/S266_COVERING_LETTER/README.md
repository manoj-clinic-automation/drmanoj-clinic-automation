# S266_COVERING_LETTER — the letter that goes with the advice

> "Covering letter is not there." — 14-Sep-2026

The advice never goes to the bank on its own: it goes with a signed letter
authorising the debit. This is that letter, **word for word as Sanjeevni has
always sent it**, with three things filled in instead of typed:

| | where it comes from |
|---|---|
| the date | today in IST, in the letter's own form (`SEPTEMBER 14, 2026`), editable |
| the cheque number | the one thing only he knows — typed once, kept per month, audited |
| the amount | **taken from the advice, never retyped and never accepted from the browser** |

It has **its own page**, prints **A4 portrait** with nothing else on the paper,
and the payment sheet still prints the advice **A4 landscape**.

## Two typos in the original are fixed

Said out loud so nobody thinks the letter drifted:

- the September file read **"SEPTEMBAR"**;
- the subject line ended **"transactions.S"** with a stray capital.

Everything else is left exactly as it has always read — the wording, the bold on
*account*, the order of the signature block. The bank has accepted this letter
every month; this kit reproduces it, it does not rewrite it.

## And one drift of mine, caught and fixed

The advice card I shipped at S265 printed amounts as `353,410`. **The bank's own
sheets carry no separators at all** — the July file says `97930`, and the letter
says `Rs. 472527/`. So this kit also takes the separators back out of the advice's
Amount column and its total. `_rupees_s266` is now the one place a rupee figure is
turned into text, for both the letter and the advice.

## No account number is in this repository

The firm's own debit account is a number, so under F-185 it does not travel here:
it is handed in on the install line and kept in `purchase_pay_config`, exactly as
the shop's mobile is. Leave it off and the letter prints a blank there to fill by
hand, and the card says so rather than printing a wrong one. The same is true of
the cheque number before it is typed.

## The walk — 36 checks

Both files are loaded, the one being replaced and the patched one, each against
its own copy of the real database:

- **the before-state is proved**: there was no letter on the sheet and no letter
  page at all (404);
- every line of the letter is checked **word for word** — the Manager, the bank,
  the branch, the subject, the NEFT/RTGS sentence, the annexure line, both
  signature lines;
- both original typos are gone;
- **the amount is the advice's own total, to the rupee**, on the letter page and
  on the sheet's preview, written **the bank's way — plain digits, no separators**,
  and the advice's own column is plain too;
- the date defaults to today in IST in the letter's form;
- with no cheque number a blank line is printed to fill by hand;
- a cheque number can be saved, appears on the letter, **is kept**, and **is in the
  audit trail**;
- **the amount cannot be set from the browser** — posting one changes nothing;
- the letter's page prints portrait, the payment sheet still prints landscape, and
  the buttons and boxes are not printed;
- a FINAL month refuses a new cheque number;
- `/hub`, `/scans`, `/orders`, `/book` and the purchase audit come back
  **byte-identical**, and the advice block is unchanged apart from the separators
  coming out — proved by showing the before-block really did have them.

Fixture root: clean install, **ALREADY INSTALLED** on re-run, and an install with
no debit account given.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && DEBIT_ACCOUNT=<the account the bank debits> bash /root/deploy/repo/deploy_kits/S266_COVERING_LETTER/install_S266_COVERING_LETTER.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `f32cdfba36b97d9b402aef122bba1906` | `30f6c28697eabab5beae609fa7965389` |

## Still to come

The **.xlsx file for the email** — the same rows, written as the bank's own
workbook, so the attachment is generated rather than maintained by hand.

## Files

| file | what it is |
|---|---|
| `block.py` | the letter, its page, its API, and the one rupee-to-text rule |
| `patch_letter_s266.py` | three anchored edits and the append |
| `seed_config_s266.py` | writes the debit account into the database, masked |
| `walk_s266.py` | the 36 checks |
| `install_S266_COVERING_LETTER.sh` | pins, backup, patch, walk, restart, roll back |
