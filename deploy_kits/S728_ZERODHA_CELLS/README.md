# S728_ZERODHA_CELLS — the Zerodha papers in the accountants' pack (F-1007, D754)

Session S390 (the parent), 06-Nov-2026. Owner's word (D754): "zerodha papers - quarterly flow to be built".

**What changes.** `/root/finance/packs.py` goes from 94923368 to 7507d991. `make_s728.py` applies 10 counted edits to the live bytes.
- **Six quarterly slots.** The Zerodha statement of account, retention statement and statement of transactions, each for Dr Manoj and for Dr Bhawna.
- **How a paper is identified.** By its own head: "Zerodha Broking Limited", with the holder printed left of it. Its kind comes from its own words: Retention Statement, the Cost Center / Voc. No columns, or "transaction". Its narrations never supply a bank tail. A Zerodha paper that is none of the three (for example a contract note) goes into no slot.
- **Which quarter.** A paper belongs to the quarter that holds its end date minus 45 days. Zerodha settles each quarter in the weeks after it ends, so the paper of 04-Jul → 16-Oct is July – September's.
- **How it is filed.** As the broker's statement; no bank lines are read from it. A "Zerodha" password box is added for the locked statement of transactions.

**Proof.**
- `walk_s728.py` runs PDFs laid out like the real ones (`fixtures/`, made-up names and numbers) through `pdftotext -layout`, the shelf's own passes, the real `stmt_shelf.py unlock` and `cells()`: 27/27. The control (the live file) is RED at 18.
- Live shape: the head rules were run against the four real papers on the shelf through the owner's session. Holder, kind and dates came out right for all four, and no value was printed.
- The Zerodha test was run against all 97 readable papers on the shelf: it picks exactly the four Zerodha papers. Three bank statements that name Zerodha in a narration stay with their banks.
- A cold review found that a bank statement with a Zerodha row near its top could be taken over. That is fixed: the Zerodha line must be in the first 8 lines and carry no date or NEFT/UPI. Also fixed: dates written as 03-Oct-2026, the BHAVNA spelling, a P&L paper ("Securities Transaction Tax") no longer taken for a statement of transactions, and no copies list on a Zerodha cell.
- Every non-Zerodha cell is unchanged: all 204 cells for Jan–Nov 2026 and Dec 2025 were checked on the live database copy, in both files.

**Install.**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s728kit && cp -rp /root/deploy/repo/deploy_kits/S728_ZERODHA_CELLS /tmp/s728kit && bash /tmp/s728kit/install_S728_ZERODHA_CELLS.sh
```
- `DRY=1` runs every gate and writes nothing.
- `--undo` puts the old file back.
- After placing the file, the installer restarts clinic-finance and runs the shelf once, so the waiting papers land.
