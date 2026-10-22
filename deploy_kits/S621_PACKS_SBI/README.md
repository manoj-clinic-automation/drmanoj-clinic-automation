# S621_PACKS_SBI — the SBI papers on the packs page (S336, 22-Oct-2026, D754)

**The owner, 22-Oct-2026 08:09 IST:** three SBI savings accounts (his, Dr Bhawna's, the HUF), two SBI loans (his, Dr
Bhawna's), two SBI PPF (his, Dr Bhawna's). He downloads them by hand, password-locked, with useless names. *"I need the
system to check these, incorporate these, and make a provision for these in future packs."* Board note: SBI quarterly,
PPF half-yearly.

**What it does** (`/root/finance/packs.py` e46264b8 → new, 17 edits; `/root/finance/packs.html` 49906969 → new, 3 edits,
all in `edits_s621.py`):

* Seven SBI cells on the statement shelf. Savings and loans are asked for every quarter of the financial year (Jun, Sep,
  Dec, Mar packs: one statement covering the quarter); the PPF every half-year (Sep, Mar: April–September,
  October–March). In other months they are not pack rows at all.
* SBI is read by its own head — the bank, the holder's *Account Name* line (Bhavna = Bhawna), savings / loan / PPF, the
  period in the date forms SBI prints. Never by file name.
* **Add statements** near the top of the page: pick one or several PDFs (PC or phone), any name. Each is kept, opened with
  its stored password, filed by content; the answer says which account and period, or why not. Same bytes twice = one
  file. One file per request, 12 MB each.
* A password box per SBI account on the Statement passwords card (the shelf opens the PDF itself, as for Yes Bank).
* The statement road (the Gmail relay's watch) leaves SBI and the uploads out of its count.

No password and no full account number anywhere in either file; the made-up statements in the walk carry made-up names.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S621_PACKS_SBI/install_S621_PACKS_SBI.sh

**Proven by:** `walk_s621.py` — five SBI heads in different layouts; an ICICI statement naming SBI in a narration stays
ICICI; five made-up PDFs added at once (a .txt refused), each on its own account; a locked one waits, then opens when its
password is typed; one added after the password opens at once; the cadence for Sep / Oct / Dec / Mar; the PPF's
half-year; the road; the page's script parses. On the box, a scratch copy of the live database: every other account's
cells identical for Aug, Sep and Oct, the road's verdict identical, September's pack carries seven SBI rows, October's
none. The S568 file goes RED. Screen review at 375 px by a separate reader.

**Undo:** `--undo` puts both old files back (`/root/s621_backup/`), takes the seven SBI cells off the shelf (their files kept, not placed) and restarts clinic-finance.
