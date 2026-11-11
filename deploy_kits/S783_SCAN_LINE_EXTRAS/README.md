# S783_SCAN_LINE_EXTRAS — the scanner reads free goods, MRP, discount and GST; the page shows them and the newest scan

**Session 426 (the Sanjeevni chat), 11-Nov-2026. The owner's word 05:51 IST: "Add the scanner lines", and "some purchases have been delivered but not yet entered in Marg — they should come on this page".**

| file | from → to | what |
|---|---|---|
| `/root/assetapp/claude_reader.py` | `ce3868ed` → TO | the S783 block appended — **the Scan App's file**, planned on the board (D646) at v1211; the Scan App chat is told at the close |
| `/root/finance/provisional_s781.py` | `15daff39` → TO | replaced whole (S781's module + the two additions) |

Read, unchanged, pinned by the installer: `purchase_app.py 54d27cd3` (S781's TO) · `scan_register.py 9262c5dc` · `section_count.py a67da5a2`.

**(1) The reader.** Only the pharmacy reading (`read_pharmacy` → `PHARMACY_PROMPT`, `clean_pharmacy`) asks each item line of a single bill for `free`, `mrp`, `discount` (%), `gst` (%) and keeps them as numbers or null in `claude_reading.data`. `read()`, `PROMPT`, `clean()`, `to_bill()`, `bill_items`, dealer statements, challans and `claude_reread` are unchanged. The pharmacy answer may run to 16000 tokens; a bill still too long is asked once more with the prompt as it was before S783, so no bill that read before fails because of it (that second ask is one more call, rare). Papers already read are not read again. Cost: four short numbers more per line on each new pharmacy bill.

**(2) The page.** The four figures are laid onto the bill's lines from the reading (line for line where the names agree, else by name; two batches of one item stay two); each column shows only when present; "Not read on this scan: …" names the rest. On a phone the wide table drops Packing, Batch, Expiry and Rate to fit.

**(3) The newest scan.** A line at the top: *Newest bill scanned* (IST; dealer statements and challans not counted) · *Marg's bills on the server reach*. When no bill has been scanned for two working days or more (Sundays not counted), it says so plainly: the bills that came since are not on the page until reception scans them. On 11-Nov: newest bill scan 08-Nov; Marg's bills reach 07-Nov.

**Proofs:** `walk_s783.py` GREEN — the reader (A1–A7: the prompt, the cleaning, '5%' read as 5, to_bill and the statements untouched, the other lanes untouched, the longer answer and the fallback) and the page (S781's 49 checks + three S783 checks), also with the server's clock 17½ hours off; the CONTROL on the live files red. Cold code review: 3 must-fix + 7 should-fix, fixed (one left as said: challans and re-reads never carry the four figures). Screen review (PC 1366, phone 390): the wide table fixed to fit the phone (measured: 324 px in a 324 px box). `rehearse_s783.sh` 6/6 (dry, a changed file, install, again, a red at [6/6], a Traceback in the journal).

**Install (the owner's paste, after the publish):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s783kit && cp -rp /root/deploy/repo/deploy_kits/S783_SCAN_LINE_EXTRAS /tmp/s783kit && bash /tmp/s783kit/install_S783_SCAN_LINE_EXTRAS.sh
```
**Undo:** the installer prints the one line — both backups back, both services restarted.
