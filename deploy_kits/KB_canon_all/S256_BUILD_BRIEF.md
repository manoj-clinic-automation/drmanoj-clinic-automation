# S256 BUILD BRIEF — the vendor payment chapter, and the import that never matched a bill

**14-Sep-2026 · one chat · nine kits `S259 … S267`, all live · D511 … D520 · F-472 … F-478.**
*Read this instead of the papers. One brief is a handover; ten papers are a record.*

## What the day was about

The owner asked for August's vendor NEFT file. The session ended with the whole month running inside
the system: **prepare the sheet → verify it against Marg's own supplier-wise statement → lock it →
print the advice, print the covering letter, download the .xlsx**. Nothing typed twice.

## The three things a future session must not re-learn

**1 · The bank's name and the bill's name are different strings (F-475).** 22 vendor accounts were
imported at S225 under the name the bank knows. Marg's bills carry the name the vendor prints. For 14
of them those differ, so **only 8 of the 24 imported rows had ever been matched by a bill** — the
rest sat correct and unreachable, and **₹2,22,608 of August went to cheques because of it**.
`purchase_vendor_alias` now maps bill-name → register-name. **One account still lives in exactly one
row**; the bill's name points at it. A future rename is one more row, never a re-import.

**2 · A predicted pin is not a live pin (F-472).** `amir_day.py` read the value S246 was built
*over* — the kit had never been installed, and the canon carried its prediction as fact. **A lost
read-back is BLIND, not SHORT.**

**3 · The bank's own formatting is authoritative (D520, F-478).** No thousands separators anywhere —
the July file says `97930`, the letter says `Rs. 472527/`. One function turns a rupee figure into
text for the advice, the letter and the file.

## The kits

| kit | what it did | checks |
|---|---|---|
| `S259_OFF_SWITCHES` | a marker switch per PC-side job; **capture keeps its own, never covered by "all"** | 30 |
| `S260_MACHINE_CONF` | one `machine.conf` per machine; installer reads today's values out of the live scripts | 37 |
| `S261_VENDOR_PAY` | the payment sheet: prepare → verify → lock | 39 + 18 |
| `S262_PAY_TILE` | one tile, granted by name to shavez; no second page — the unit_role makes him read-only | 23 |
| `S263_VENDOR_LINK` | the 14 links + DAANSHI's account; August's cheque lane → ₹1,469 | 28 |
| `S264_PAY_MONTHS` | the month strip; the audit page and the sheet made to name each other | 37 |
| `S265_BANK_ADVICE` | the advice in the bank's own shape, printing A4 landscape | 50 |
| `S266_COVERING_LETTER` | the letter word for word, portrait, amount refused from the browser | 36 |
| `S267_ADVICE_FILE` | the `.xlsx`, written with the standard library alone | 54 |

## The proof that matters

**July was rebuilt from the server and held against `NEFT ADVICE JULY 2026.xlsx`, the file that went
to the bank:** 21 lines against 21, every name identical, **every account number and IFSC identical**,
and **20 of 21 amounts identical to the rupee**. The exception is KEDAR PHARMA — server ₹98,240,
bank ₹97,930, a **₹310** difference that is the owner's to settle.

## Shapes to reuse

- **Wrap, don't edit.** `_vendor_bank` and `_book_nav` are both wrapped, never changed, so the
  original lines stay exactly as they are and the rollback is byte-identical.
- **Walk both files.** Every kit from S263 on loads *the file being replaced* and *the patched file*,
  each against its own copy of the real database, and the only permitted difference is the one
  claimed. `/hub`, `/scans`, `/orders`, `/book` must come back byte-identical.
- **Numbers travel on the install line.** Bank accounts and phone numbers never enter the repository;
  a seeding helper writes them straight to the database, prints them back masked, and **never
  overwrites a value already there**.
- **A .xlsx needs no library.** It is a zip of XML; `zipfile` and string formatting are enough, and
  nothing can be missing on the box at month end.

## Open into S257

RAMA MEDICOSE and AGARWAL SURGICALS need bank details · KEDAR's ₹310 needs a ruling · the medical
PC's own two C.3 settings ride with the next medical change · the cheque register's own screen ·
Club C.4 tokens · Amir's name-check sheet is with the owner.
