# S195 — The monthly cycle, as described, and what is still to build

Captured 22-Aug-2026 from Dr Manoj's own account of how the month actually runs. Written
down **before** building anything, so that none of it is lost between sessions. Where a
detail was not stated it is marked **UNKNOWN** rather than guessed — a plausible guess in
a document like this becomes a fact three sessions later.

---

## The people and what each one needs

| Who | Works where | Needs | Produces |
|---|---|---|---|
| **Amir** | the **medical PC** (Marg) | the correction list as **Excel or a Google Sheet**; the **monthly bank statements** | corrected bills in Marg |
| **Shavez** | clinic side | the printed bill-wise purchase + supplier-wise monthly reports | the **bulk NEFT Excel** for vendor payment |
| **Accountants** | outside | **monthly Tally export** files, emailed; **and** the bulk NEFT Excel | — |
| **Darpan** | the counter | his own accuracy feedback (**live**) | the day's entries |

## The monthly vendor-payment chain, as described

1. **Bill-wise purchase** report and **supplier-wise monthly** report are produced as
   **PDFs and printed** — for physical verification.
2. Verification happens against the printed copies. *(Who signs off: **UNKNOWN**.)*
3. **Shavez** builds the **bulk NEFT Excel** for vendor payment from the verified figures.
4. That file **lives in a folder inside Shavez's folder in the CLINIC Google Drive
   account**. *(Exact path: **UNKNOWN**.)*
5. Payment is **physically delivered**: the NEFT file **with a covering letter and a
   cheque**. *(To which bank/branch, and whether the letter is templated: **UNKNOWN**.)*
6. The **accountants are emailed** the monthly **Tally export** and the **bulk NEFT
   Excel**. *(Their addresses: **UNKNOWN**.)*

## The statement flow, separately

- **Monthly bank statements** arrive in Dr Manoj's **personal Gmail** and **Amir needs
  them**. These are *not* the ICICI MPR merchant statements already automated (see
  `S195_UPI_Statement_Gap_Finding.md`) — those are daily, per merchant ID, and feed the
  cash/UPI reconciliation. *(Which bank / which account: **UNKNOWN**.)*

---

## Done in this session

- **Correction checklist as Excel** — `/finance/api/marg-corrections.xlsx`, offered on
  `/finance/marg-worklist` as *Excel for Amir*. One row per day; amounts are **numbers**
  so they add and sort; header frozen; auto-filter on; the re-export warning at the foot.
  Two columns — **Done?** and **Remarks** — belong to Amir and the system never writes in
  them; its own Status column sits beside them, not on top.
- WhatsApp (clipboard) and email (mailto) carry the same list as words, for *telling* him
  the work exists. All routes are asserted by selftest to serve the same list.
- Shipped in `deploy_kits/S195_SHARE.tar.gz`.

## Backlog — in the order that pays off

1. **Get the file to the medical PC without a human carrying it.** Amir cannot use a
   download on Dr Manoj's phone. Candidates: write the workbook into the clinic Drive (the
   medical PC would need Drive), or push it into `D:\SendToClinic` via the existing
   margsync mirror, or simply email it to an address Amir opens on that PC.
   **Needs:** how Amir gets files on the medical PC today.
2. **Monthly bank statement → Amir.** Same shape as the ICICI MPR automation that already
   works: find the mail, take the attachment, put it somewhere Amir can reach.
   **Needs:** bank, sender address, subject pattern, destination.
3. **Tally export → accountants, monthly, by email.** **Needs:** the accountants'
   addresses, where the Tally export is produced (Marg's own Tally export was examined at
   S195 and is pure accounting data — no item names), and what day of the month it is due.
4. **Bill-wise purchase + supplier-wise monthly PDFs.** These are Marg reports, so they
   fall straight into the report router already built — but the router has no **signature**
   for them yet. **Needs:** one sample export of each, and it can identify, date-name and
   file them automatically like the sale report.
5. **Bulk NEFT Excel.** The furthest out and the most care needed — it moves money.
   Nothing should be automated here beyond *assembling* and *filing* it; Shavez builds it
   and a person signs the cheque. **Needs:** the current file's format and the folder path.
6. **Covering letter.** A template, if one exists, is a five-minute job once seen.

## The rule for all of it

Everything above is a **document-handling** problem, not a money problem — except item 5,
which touches a payment instruction. That one gets assembled and filed, never sent. The
maker/checker split (D325) holds: the system may stage; a person applies.
