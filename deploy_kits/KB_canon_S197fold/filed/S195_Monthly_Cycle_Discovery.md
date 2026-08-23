# S195 — The monthly cycle: what unattended discovery established (22-Aug)

Supplements `S195_Monthly_Cycle_Map_and_Backlog.md`. Every UNKNOWN in that document that
could be answered from the connected sources has been; what remains open is listed at the
end. **Method note: all of this is read from primary sources this session — the NEFT file,
the letter, the accountant's own checklist — not inferred.**

---

## The people — communication channels (owner-confirmed)

| Person | Channel | Consequence for design |
|---|---|---|
| **Amir** | **WhatsApp only — NO email.** Works at the medical PC. | Files reach him via the **ToMedical pipe** (files appear on his PC); WhatsApp is the *telling* channel only (owner pastes the "Copy for WhatsApp" text). **No future design may include an email step for Amir.** An automatic WhatsApp *document* push would need a Meta-approved media template via MyOperator — someday item, not a gap. |
| **Hemant Mourya** (accountant) | email `hemantmourya47@gmail.com` | |
| **Shyam Agarwal** (accountant #2) | email `shyamagarwalbly@gmail.com` | There are TWO accountants, not one. |
| **Shavez** | clinic Drive (his folder) | |
| **Darpan** | the portal (his tile + save responses) | |

## The NEFT flow — now fully documented (was Club 5's biggest unknown)

**Where:** clinic Drive → `SHAVEZ / SANJEEVNI MEDICOS FILES /`
`NEFT ADVICE <MONTH> 2026.xlsx` (monthly: APRIL, MAY, JUN, JULY present) +
`NEFT ADVICE LETTER.docx` (the covering letter template).

**Format of the advice file** (sheet "Sheet2"): header block (GSTIN 09AAIHM6109G1Z4,
DL nos., name, address), then columns:

`Sr. No. | Txn. type (NEFT) | Credit Account Number | Credit Account Name | IFSC | Amount | Narration ("Vendor Payment")`

…and a total row. July 2026: **21 vendors, ₹4,72,527**, all pharma suppliers.

**The letter:** addressed to The Manager, **YES Bank, Rampur Garden, Bareilly**; authorises
multiple debits to **a/c ···1923** against **one physical cheque** (July's: no. 953475)
for the file total. So the real-world flow is: Shavez builds the xlsx → letter + cheque
signed → physically delivered to the branch → bank executes the batch.

**Live observation:** both files were edited **today** (xlsx 06:52, letter 07:54, letter
dated AUG 22 with the July total) — the July payment run is happening now. Nothing was
touched.

**Automation boundary (D325 extended):** the system may *pre-fill* next month's advice and
letter from the purchase data once the purchase reports are ingested (Club 3), and *file*
them; it never sends anything. A cheque and a signature stay in the loop by design.

## The accountants — decoded from their own checklist

`SHAVEZ/HEMANT ACOUNTENT NEED DOCE.xlsx` ("AC DOCE") is the accountants' requirements
list, split by who supplies what:

| Head | Documents | Carried by |
|---|---|---|
| Dr. M.K | OPD register · expense file · electricity file | Shavez |
| Dr. Bhawna | lab register accounts + lab receipt book (Sukhveer) · electricity · purchase file | Shavez |
| Sanjeevni | **PAYMENT NEFT DETAILS** | Shavez |
| MKA (by **email**) | **bank statement ICICI · bank statement YES** · CC statements ICICI VISA / ICICI RuPay / HDFC (marked AUTO FORWARD) · **MARG FILE EXPORT — "make from marg"** (= the Tally piece) | Dr Manoj |

**GST calendar** (same file): quarters due 15-Jul / 15-Oct / 15-Jan / 15-Apr, annual 15-Jun.

The MKA-by-email items are now automated by the **bank statement chain** — see
`S195_Bank_Statement_Chain.md` (statements → archive + both accountants + Amir's PC for
Sanjeevni). The CC statements already auto-forward. That leaves only the **MARG FILE
EXPORT** of the MKA list unautomated.

## The delivery pipe to the medical PC — BUILT and self-testing

The two halves already existed; they are now joined:

**Drive `Clinic Data Archive / ToMedical` → (manojz H:) → medical `D:\SendToClinic\FROM_CLINIC`**

- Created the Drive folder (id `1s6EJ_b0NuWphBoJIu8_ehEQl9g1HZvGg`) with a README.
- Added a guarded leg to `margsync/MargPull/PULL_FROM_MEDICAL.bat` on manojz (runs every
  10 min; backup kept beside it as `.before_S195_tomedical`). The leg runs after all pull
  work, tolerates failure, and excludes the README.
- A `DELIVERY_TEST_S195.txt` was placed in the folder. **Verification:** it should appear
  in `margsync/medical_SendToClinic/FROM_CLINIC` (the mirror) within ~2 cycles; check
  next session or ask the medical PC.

This is the answer to *"how does Amir get files"* — consistent with Amir having **no
email**: anything dropped in that Drive folder — the correction workbook, a Sanjeevni bank
statement — is on his machine inside ten minutes.

## Club 3 — parked with the request list

`deploy_kits/S195_STMT/Marg_Sample_Exports_Needed.pdf` — one printable page: the six
sample exports (bill-wise purchase, supplier-wise, stock, purchase register, Labmate,
Docterz), who produces each, how, and where to drop them (margsync or the ToMedical
folder in reverse). Filenames irrelevant — the router reads content.

## Remaining questions (now only one)

1. Whether the **Tally/"MARG FILE EXPORT"** the accountants receive is the plain Marg
   Tally export examined at S195 (pure accounting, no item names) or something Shavez
   post-processes — and which day of the month it goes.

*(Hemant's address, the second accountant, and Amir's channel — all answered by the owner
22-Aug and recorded above.)*
