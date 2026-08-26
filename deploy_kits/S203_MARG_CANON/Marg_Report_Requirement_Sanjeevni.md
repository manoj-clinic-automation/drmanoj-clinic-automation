# Requirement — Automated Daily Sale Report Export

**Customer:** Sanjeevni Medicos, 35G/15B Rampur Bagh, Bareilly
**Software:** Marg ERP 9+ · Licence `LIC-14116710` · E-Business ID `39548`
**Raised:** 15 August 2026
**Support route:** AnyDesk (remote session)

**Purpose.** The daily sale figures must leave this PC automatically each day and be read by our
accounting system. No staff member should have to click anything, and no figure should be re-typed
by hand.

**This document is objective on purpose.** Every requirement below has a test that either passes or
fails. Section 8 is the acceptance list.

---

## 1. Where the report is

```
Marg ERP 9+  →  Daily Reports  →  Sale Reports  →  BILL WISE STATEMENT
```

Output currently written to: `D:\MARGERP\users\<user id>\report\REPORT_1.XLS`

---

## 2. Settings that produce the report we need

We need **two** saved reports. They differ in three fields only.

| Field on the BILL WISE STATEMENT screen | **Report A — "Daily Sale (Accounts)"** | **Report B — "Daily Sale (Detail)"** |
|---|---|---|
| Operator Name | *(blank — all operators)* | *(blank)* |
| Stock Less | `No` | `No` |
| **Report From** | **1st of the current month** | **today** |
| To | today | today |
| Cash/Cr/Disc. | `Both` | `Both` |
| Club Cash Sale | `No` | `No` |
| Less Cr/Dr Adj. | `Yes` | `Yes` |
| Add Challans | `No` | `No` |
| Patient Mobile | *(blank — all)* | *(blank)* |
| Pres.By Mobile | *(blank — all)* | *(blank)* |
| Report For | `2 Sale-S/R-Brk` | `2 Sale-S/R-Brk` |
| **Report Type** | **`Detail`** | **`Detail`** |
| *(column width, beside Report Type)* | `80 Col` | `80 Col` |
| **Disc.Bill Sign** | **`4-Bill`** | **`1-Bill+Item+Volume`** |
| Day Total | `Yes` | `Yes` |
| **With Item Deta.** | **`No`** | **`Yes`** |
| Single Party | `N` | `N` |
| Selected Group | `N` | `N` |
| Selected COMPNA | `N` | `N` |

**`Report Type` must be `Detail`.** With `Summary-1` the report prints only three columns
(`BILL NO. | DESCRIPTION | BILL VALUE`) and the payment columns are absent, which makes it unusable
for accounting.

### Excel export screen (`SELECT DELIMETER LINE/HEADER`)

| Field | Value |
|---|---|
| Select suitable seperator | `Header` |
| Selected line as heading ? | `No` / `1` |
| Data start from line no. | `5` |
| Data ends at line `<0 for all>` | `0` |
| Report in which Excel Format | `Formated` |

These settings must be **saved with the buttons**, so the operator is not asked for them each time.

---

## 3. Required output — exact column headers

The exported file must carry this header row, these names, in this order:

```
BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH
```

- **`CASH` is mandatory.** It is the only column that shows how much of a bill was actually paid in
  cash. Without it, cash and UPI cannot be separated.
- Report A title line must read `BILL WISE SALES STATEMENT FROM 01-08-2026 TO 15-08-2026`
  (a range).
- Report B title line may read `BILL WISE SALES STATEMENT AS ON 15-08-2026` (single day).
- Each day's block must end with a `DAY TOTAL :` row.
- The file must end with a `GRAND TOTAL :` row and a `Total No. of Bills:` count.

---

## 4. Sample of the current output

Taken from a real export of 01-08-2026. **Patient names and mobile numbers have been replaced with
placeholders in this document for privacy; the structure, spacing and figures are unchanged.**

```
BILL NO.   DESCRIPTION                    D.R.         GROSS AMT.  DISCOUNT   TAX     DR/CR    NET AMT.    CASH
01-08-2026
A002660    9000000001 PATIENT ONE 1001    .UPI       # 1632.78     2.78       0.0     0.0      1630.0      0.0
           1   0 GEN D3 NANO          1*8       0:2     193.51  3/28  18261789A
           2  15 FLACORT 6            1*10      0:8     168.00  9/27  E02AAA
           3   3 PATOPAN DSR          1*10      1:6     100.00 10/27  UC25973A
A002661    9000000002 PATIENT TWO 1002    .CASH      # 852.07      2.07       0.0     0.0      850.0       850.0
           1   0 BIO D3 MAX           1*10      0:7     442.40  2/28  18260991A
           2   3 PATOPAN DSR          1*10      0:7     100.00 10/27  UC25973A
A002662    9000000003 PATIENT THREE       .CASH      # 345.94      0.94       0.0     0.0      345.0       345.0
...
                                        DAY TOTAL :   28937.00    818.00     0.0    -0.0      28119.0     16411.0
Total No. of Bills: 37                GRAND TOTAL :   28937.00    818.00     0.0    -0.0      28119.0     16411.0
```

This structure is correct and we do not want it changed, other than the addition requested in §5.

---

## 5. Requirements

### R1 — One click
Each of the two reports above must be saved as a single named button, so that pressing it once
produces the file with all settings already applied. The operator must not have to set dates,
report type, or export options.

**Test:** press the button, a file appears, no dialog asks for a setting.

### R2 — Automatic daily generation (auto-save)
Both reports must generate **automatically once every day**, without any person opening Marg or
pressing anything, and must be saved to disk.

We can see an empty `report\auto\` folder under each user, which suggests this facility exists.

**Please confirm in writing:** the exact folder and the exact filename each report will be saved
to, and whether the filename is date-stamped or overwritten daily.

**Test:** with nobody touching the PC, both files are present the next morning, containing the
previous day's sales.

### R3 — Two separate output files
Both reports currently write to the same filename, `REPORT_1.XLS`. One would overwrite the other.

**They must be saved as two distinct files** — different filenames, or different folders.

**Test:** run both; two files exist, neither has overwritten the other.

### R4 — A DATE column on every bill row  ← **new requirement**
At present the date appears **only as a group heading row** above each day's bills. The individual
bill rows carry no date of their own:

```
01-08-2026                                       <-- the date is only here
A002660    ...   1632.78 ... 1630.0   0.0        <-- this row has no date
A002661    ...    852.07 ...  850.0 850.0        <-- nor this one
```

This makes the file fragile to read: a program must infer each bill's date from the last heading it
saw, so any change to page breaks, sorting or heading placement silently mis-dates the bills.

**Please add a date column to each bill row**, so every row is self-describing — for example as a
first column `BILL DATE`, or appended after `BILL NO.`. Format `DD-MM-YYYY` is fine.

The existing group heading and `DAY TOTAL :` rows should remain as they are.

**Test:** every bill row in the export carries its own date, and the file can be read correctly even
if the rows are sorted.

### R5 — Automatic email
Both reports must be **emailed automatically each day** to the address we will provide.

Note for your engineer: the mail facility on this installation appears **never to have been set up**
— `D:\MARGERP\emailserver\` and `D:\MARGERP\emailpend\` are both completely empty, and no mail has
ever been queued or sent. This is a fresh configuration, not a repair. Please tell us what SMTP
details you need from us.

Please also advise on the outgoing sender: outgoing messages currently show the demo sender ID
`MARGDEMO`. We would like our own sender configured.

**Test:** the email arrives the next morning with both files attached, unprompted.

---

## 6. Defect to be fixed or explained — the export truncates silently

**This is the most important item in this document.**

A month-to-date report **with item detail switched on** does not export completely. It stops
part-way through and gives **no error and no warning**.

**Evidence — export made on 15-08-2026:**

| | |
|---|---|
| Requested range | `FROM 01-08-2026 TO 15-08-2026` (15 days) |
| Settings | `Report Type = Detail`, `With Item Deta. = Yes` |
| Rows produced | 1,207 |
| Pages | 44 |
| Days actually present in the file | **only 01-08 to 06-08 (6 days)** |
| Day 06-08 | incomplete — **no `DAY TOTAL :` row** |
| Days 07-08 to 15-08 | **entirely absent** |
| `GRAND TOTAL :` row | **absent** |

The file opened normally in Excel and looked complete. Only the missing `GRAND TOTAL` row revealed
that it was not.

**Questions:**
1. Is there a page limit, a line limit or a memory limit on the Excel export?
2. Can it be raised or removed?
3. If it cannot, can the export be made to **fail with a visible error** rather than write a partial
   file silently?

**Until this is answered we must keep the two reports separate** (§2), because a single combined
report exceeds whatever the limit is.

**Test:** a 15-day range with item detail exports every day requested, ending with a `GRAND TOTAL :`
row.

### R6 — Historical export, month by month
We also need the historical item-wise bill data up to the current date.

**Because of the defect above, please supply it as one file per calendar month**, not as a single
file covering everything. Each monthly file must end with its own `GRAND TOTAL :` row so we can
confirm it is complete.

---

## 7. What must not change

- The nine column headers in §3, their names and their order.
- The `DAY TOTAL :` and `GRAND TOTAL :` rows.
- The `Total No. of Bills:` footer count.
- The credit-note rows (`CN…`), which must continue to carry negative amounts.

Our accounting system reads these exactly. A change to any of them will stop the daily import.

---

## 8. Acceptance list

| # | Requirement | Pass condition |
|---|---|---|
| R1 | One click | Button produces the file; no dialog asks for a setting |
| R2 | Auto daily generation | Both files present next morning with nobody touching the PC |
| R3 | Two separate files | Both exist; neither overwrites the other |
| R4 | Date on every bill row | Every bill row self-describes its date |
| R5 | Auto email | Email arrives next morning with both files attached |
| — | Defect §6 | 15-day range with item detail exports in full, ending in `GRAND TOTAL :` |
| R6 | History | One file per month, each ending in its own `GRAND TOTAL :` |

**Please also confirm in writing, after the session:** exactly what was changed on this
installation, and the folder and filename each scheduled report will use.

Please do not change any other setting on this installation.

---

**Contact:** Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly
