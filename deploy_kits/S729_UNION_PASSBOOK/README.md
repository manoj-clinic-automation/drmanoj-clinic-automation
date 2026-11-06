# S729_UNION_PASSBOOK — the Union Bank passbooks in the accountants' pack

Session S390 (the parent), 06-Nov-2026. Owner's word, 16:37–16:38 IST: Union Bank of India savings accounts, his and Dr Bhawna's. "They fill the passbook, it is printed by the printer, and then we can scan and upload it whenever required." The board note gives the cadence: semi-annual.

**What changes.** `/root/finance/packs.py` goes from 7507d991 (S728) to fb987b27. `make_s729.py` applies 9 counted edits to the live bytes.
- **Two half-yearly cells:** April – September and October – March.
- **A hand-added bank, like SBI.** An empty cell says: scan the printed passbook pages to a PDF, then use the Add statements box. The "no statement has come by mail" check leaves these cells out.
- **A scanned passbook has no text,** so the owner's one tap ("This is …") files it, the same as any unplaced paper.
- **Which half-year a passbook belongs to.** It is dated the day it was added. Printed July – December, it belongs to April – September; printed January – June, to October – March. A Union Bank statement with text is known by "Union Bank of India" in its first lines (never from a row) and is placed by the holder's name.
- **No account number** is in any file. The cells go by the holder's name.

**Proof.**
- `walk_s729.py`: 18/18. It covers the real Add statements box, the owner's tap, the cells, the pack row and the mail-road check. The control (the live file) is RED at 11.
- The S728 walk is still green on the new file (27/27).
- All 228 non-Union cells for 2026 were checked on the live database copy, in both files: the same.
- None of the 97 readable papers on the shelf is taken for a Union Bank paper.

**Install.**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s729kit && cp -rp /root/deploy/repo/deploy_kits/S729_UNION_PASSBOOK /tmp/s729kit && bash /tmp/s729kit/install_S729_UNION_PASSBOOK.sh
```
- `DRY=1` runs every gate and writes nothing.
- `--undo` puts the S728 file back.
