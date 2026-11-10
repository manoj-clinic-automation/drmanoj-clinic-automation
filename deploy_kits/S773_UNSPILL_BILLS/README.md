# S773_UNSPILL_BILLS — bills whose number Marg fused onto the item name get their lines back

**Session 423 (the Sanjeevni chat), 10-Nov-2026. F-1233. The owner's "GO" 12:43 IST.** Marg's SUPPLIER/ITEM WISE purchase report prints the bill number in a column 8 characters wide. A longer number spills: the bill column is empty and the number's last 8 characters are fused onto the item (`06202627CAST SHOE M TYNOR` for Yuvika YS0706202627; `A000207_TYRO BR` for Kedar A000207_). The reader split only the shape letters + 5-7 digits, so these lines never joined their bill: the Items check showed the bills with no lines, the scan-beside-Marg check could not compare them.

| file | from → to | what |
|---|---|---|
| `/root/finance/purchase_app.py` | `8424e05b` → TO | one guarded call in `api_push`, before the lines are re-dated (a failure never fails a push — unless the push's own writes were lost, then it is not reported stored) |
| `/root/finance/purchase_unspill.py` | NEW | the split by evidence, its log (`purchase_unspill_log`), its undo |

**The rule — evidence, never a guess:** a line with no bill number is joined only when its item begins with a real bill number of the SAME supplier (the whole number or its last 8 characters, at least 6 long), a LIVE bill (purchase_app's EFF_BILL), dated inside the export's own period, ONE bill only, the next character not a digit; never a line or a bill in a month made FINAL. It runs inside every push (a bill-wise push joins item lines that came before their bill) and once at install over the stored lines.

**Proofs:** `walk_s773.py` 18/18 green on made-up rows through the real push door (Yuvika's and Kedar's shapes; two bills ending alike; a digit after the number; a bill outside the period; another supplier's number; lines before their bill; idempotent; undo, and undo leaving alone a line changed since; a failure part-way changes nothing; a failing repair never fails a push; a FINAL month untouched); the CONTROL on the live files red. `rehearse_s773.sh` 5/5 (a red after placing puts the file back, restarts, then undoes the joined lines). `proof_s773.py` on the device's copy of the 10-Nov database: **65 lines join 2 bills** — YS0706202627 (52 lines, 13 exports) and A000207_ (13) — applied, read back (0 left), undone, on the copy. Cold-reviewed: SAFE, its six findings fixed. purchase_app.py read whole first (drift 5).

**Install (the owner's paste):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s773kit && cp -rp /root/deploy/repo/deploy_kits/S773_UNSPILL_BILLS /tmp/s773kit && bash /tmp/s773kit/install_S773_UNSPILL_BILLS.sh
```
**Undo:** the installer prints the one line (the old file back and finance restarted first, then the joined lines put back, then the new file removed).
