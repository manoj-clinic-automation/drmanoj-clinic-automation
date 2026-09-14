# S265_BANK_ADVICE — the advice, exactly as the bank gets it

## The ask

> "We should be able to see the exact preview of the Excel sheet here as we send
> it to the bank, because it is printed on blank paper A4 and also emailed to the
> bank from the email account linked to the bank account." — 14-Sep-2026

So this card is not a summary of the advice. It **is** the advice: the same four
letterhead lines, the same seven columns in the same order, the same wording
(`NEFT`, `Vendor Payment`), the same alphabetical order by the name on the
account, and the same total in the Amount column as every `NEFT ADVICE` sheet
sent to the bank from April to July 2026.

Printing the page prints **the advice and nothing else**, A4 landscape — the
navigation, the other cards and the buttons are all hidden by print CSS.

## Proved against the bank's own file

The strongest check available was run once, by hand, and is worth recording:
**July 2026 was rebuilt from the server and held against `NEFT ADVICE JULY
2026.xlsx`, the file that actually went to the bank.**

- **21 lines against 21 lines**, and after the account-name rule below, **every
  name identical**;
- **every account number and every IFSC identical** — 21 of 21;
- **20 of the 21 amounts identical to the rupee.**

The one difference is **KEDAR PHARMA: the server says ₹98,240, the bank file paid
₹97,930 — ₹310 less.** That is the same ₹310 that showed up in the August/July
arithmetic earlier in the session. It is a real difference for the owner to
settle, not a fault in this build; the sheet's **Carried in** column is exactly
where it belongs once he decides.

### The account-name rule

The name printed is the account name when the server holds one. Where it does
not, the vendor's own name is used with **Marg's trailing town dropped** — so
`JANTA PHARMACEUTICALS BAREILLY` prints as `JANTA PHARMACEUTICALS`, which is what
the bank's own sheets carry. The town is dropped **only when a whole extra word
follows the normalised name**, which is why `VERMA BROS.AND CO.` keeps its full
stop. Nothing is guessed.

## No number from the letterhead is in this repository

The four printed lines are the firm's own stationery. The **shop's mobile is a
number**, so under F-185 it does not travel here: it is handed in on the install
line and kept in `purchase_pay_config`. Leave it off and the letterhead simply
prints no mobile, and the card says so rather than printing a wrong one.

## What the card refuses to do

- **A cheque vendor never reaches the bank file.** The walk checks every cheque
  vendor by name against the rendered block.
- **A vendor with no confirmed account is left out and named out loud**, with a
  line saying it is on the cheque list instead — never silently dropped.
- **An unlocked month is marked DRAFT**, so a provisional sheet cannot be printed
  and mistaken for one that is signed off.
- Paise, if any ever appear, are rounded to the rupee **and said out loud** — the
  bank file has always been whole rupees.

## The walk — 50 checks

Both files are loaded, the one being replaced and the patched one, each against
its own copy of the real database. For each of the last three months:

- the seven columns are the bank's, **in the bank's order**;
- the letterhead carries the firm, the address, the GSTIN and the DL;
- every NEFT vendor with a payable is on the advice **and no other**;
- **each amount is that vendor's payable, to the rupee**, and the total equals the
  sum of its own lines and is printed under the Amount column;
- the lines are alphabetical by the name on the account;
- every line carries an account number and an IFSC;
- every line says `NEFT` and `Vendor Payment`, as the bank file does;
- no cheque vendor appears anywhere in the block;
- the month is marked DRAFT if and only if it is not locked.

Then: printing hides the rest of the page, is set to A4 landscape, and the Print
button is not itself printed. And `/hub`, `/scans`, `/orders`, `/book` and the
purchase audit page all come back **byte-identical to before**, with the sheet's
own figures unchanged.

Fixture root: clean install, **ALREADY INSTALLED** on re-run, and an install with
no mobile given.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && SHOP_MOBILE=<the shop mobile> bash /root/deploy/repo/deploy_kits/S265_BANK_ADVICE/install_S265_BANK_ADVICE.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `8d7b1eadc70d122ff181002692815bd7` | `f32cdfba36b97d9b402aef122bba1906` |

## Still to come

The **file** for the email, and the **covering letter**, both generated off this
same block so nothing is typed twice.

## Files

| file | what it is |
|---|---|
| `block.py` | the advice, the account-name rule, the letterhead, the print CSS |
| `patch_advice_s265.py` | the one anchored edit and the append |
| `seed_config_s265.py` | writes the printed mobile into the database, masked |
| `walk_s265.py` | the 50 checks |
| `install_S265_BANK_ADVICE.sh` | pins, backup, patch, walk, restart, roll back |
