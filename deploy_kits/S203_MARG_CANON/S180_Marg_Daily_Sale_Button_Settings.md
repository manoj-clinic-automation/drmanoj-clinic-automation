# Marg "Daily Sale" button — exact settings

**Sanjeevni Medicos · Marg ERP 9+ · `BILL WISE STATEMENT`**
Prepared 15-08-2026 · for the Marg engineer to save as a one-click default.

**Verified, not guessed.** These settings are taken from a real export made on this machine on
15-08-2026 whose arithmetic I checked line by line — every money column summed exactly to the
`DAY TOTAL` and `GRAND TOTAL` rows, and `GROSS − DISCOUNT + TAX + DR/CR` reproduced `NET AMT.` on
every bill. Only the three fields marked **CHANGE** differ from that verified file.

---

## A. Report screen — `BILL WISE STATEMENT`

| Field | Set to | Note |
|---|---|---|
| Operator Name | *(leave blank)* | blank = all operators |
| Stock Less | `No` | |
| **Report From** | **`01`** of the current month | **CHANGE** — month-to-date, not a single day |
| To | current date | |
| Cash/Cr/Disc. | `Both` | |
| Club Cash Sale | `No` | |
| Less Cr/Dr Adj. | `Yes` | |
| Add Challans | `No` | |
| Patient Mobile | *(leave blank)* | blank = all |
| Pres.By Mobile | *(leave blank)* | blank = all |
| Report For | `2 Sale-S/R-Brk` | |
| **Report Type** | **`Detail`** | **the critical one** — `Summary-1` collapses the report to 3 columns and loses the CASH column entirely |
| *(width, beside Report Type)* | `80 Col` | **leave as is** — 80 Col already produces all nine columns |
| **Disc.Bill Sign** | **`1-Bill+Item+Volume`** | **CHANGE** — see the caution below |
| Day Total | `Yes` | required — the `DAY TOTAL` rows are used to self-check each day |
| **With Item Deta.** | **`Yes`** | **CHANGE** — wanted for item-level analysis |
| Single Party | `N` | |
| Selected Group | `N` | |
| Selected COMPNA | `N` | |

### The report this produces

Header row, nine columns, in this exact order:

```
BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH
```

Title line must read `BILL WISE SALES STATEMENT **FROM** 01-08-2026` (a range).
If it reads `AS ON <date>`, the date range was not applied.

---

## B. Excel export screen — `SELECT DELIMETER LINE/HEADER`

These settings produced the verified file. **Do not change them.**

| Field | Set to |
|---|---|
| Select suitable seperator | `Header` |
| Selected line as heading ? | `No` / `1` |
| Data start from line no. | `5` |
| Data ends at line `<0 for all>` | `0` |
| Report in which Excel Format | `Formated` |

Output stays at `D:\MARGERP\users\<user id>\report\REPORT_1.XLS`.

---

## C. One caution before saving the button

**`Disc.Bill Sign` is being changed from `2-Bill+Item` to `1-Bill+Item+Volume`.** The verified file
used `2-Bill+Item`. Adding volume discount may add or shift a column, and the Excel export splits
columns off the header line — so a layout change would change the file's shape.

**Please export once with the settings above and send that file for checking before the button is
saved.** If the layout shifted, we fall back to `Disc.Bill Sign = 2-Bill+Item`, which is already
proven. One test export now avoids configuring the button twice.

---

## D. Questions for the Marg engineer

1. **Can the saved button set the date range automatically** — From = 1st of the current month,
   To = today — so no one has to type dates each morning?
2. **Can the operator/biller be included as a column** in the `Detail` layout? Every person who bills
   has their own Marg login, so the attribution is reliable and worth having on each row. Filtering
   by `Operator Name` instead would mean running the report once per operator, which defeats the
   one-click goal — we want one report with the operator shown per bill.
3. **The file name is fixed** (`REPORT_1.XLS`) and is overwritten on each run. Can it be date-stamped?
   *Not a blocker* — the report is month-to-date, so a later file always contains everything an
   earlier one did, and an overwrite cannot lose data. Asked only in case it is a simple option.
4. Separately, the two automation requests already sent — the scheduled auto-report into
   `users\<user id>\report\auto\`, and enabling `up_sale` / `up_saleinfo` in the e-business cloud sync
   (E.BUSID `39548`).

---

## E. Why item detail is included

The item rows cost the accounting feed nothing — they carry an empty `BILL NO.`, so the reader skips
them automatically. They are kept because they answer questions the bill-level report cannot:

- **repeat/self-refill patterns** — same patient, same item, over time;
- **partial pickup** — which prescribed items were actually bought and which were left;
- **discount leakage** — per-item and per-bill discount, alongside the `DR/CR` adjustment.

On the verified file, `DR/CR` carried adjustments of up to **₹19 on a ₹319 bill (6%)**, booked as
round-off. That is the field to watch.

**Who bills, in practice (owner, 15-08-2026):** Darpan on most days; a reserve person on roughly
2–4 days a month; **Amir enters purchases only**, about twice a week. Each has their own Marg login.
So once the operator column exists (question 2 above), two checks come almost free:

- discount and `DR/CR` as a percentage of gross, **reserve-person days vs Darpan days** — Darpan's own
  days are the baseline, and like is compared with like;
- **Amir's login appearing on any sale bill** — it should never happen, so any occurrence is worth a look.

*Forward note, not a task: purchases are entered in Marg under a separate login, so a purchase-side
export exists too. Sale + purchase together would give margin and stock reconciliation. Out of scope
for this build; recorded so it is not forgotten.*
