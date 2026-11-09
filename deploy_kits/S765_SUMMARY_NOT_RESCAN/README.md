# S765_SUMMARY_NOT_RESCAN — dealer summaries are not bills

**Session 417 (the Sanjeevni chat), 09-Nov-2026. The owner, 17:34 IST:** Alisha's list showed the dealers' month summaries she scanned on 08-Nov as *"Yeh bill nahi hai — asli bill dhoondh kar scan kijiye"*, and *Aaj ka bill kaam* said *"Dobara scan karo 22"*.

**Found:** the 22 open rescan asks were all raised by the server's own asking (S736) on 08-Nov: not a bill 8, no total 9, cut 4, blurred 1. None of them is tied to a Marg bill. A summary paper (S750: the *summary* tick → `bills.kind 'Summary'`) lands on the pharmacy lane. `scan_quality` judged it as a bill, and S736 asked for it again.

| file | from → to | what |
|---|---|---|
| `/root/shared/scan_quality.py` | `16fb2402` → `505a114f` | `is_summary()` (the filed kind `Summary` alone — a reader's guess never hides a bill); `detail()` never judges a summary paper, so it never shows *bill nahi hai* |
| `/root/finance/porders_s454.py` | `c463b87c` → `903df714` | `s736_plan`: a summary paper is *gone* for the server's asking — never asked, and the server's own open ask on it is withdrawn when reception's home next opens. An ask a person sent stays. |

**Proofs:** `walk_s765.py` 14/14 green on made-up rows; the CONTROL on the live files has 6 S765 checks red and 8 old checks green, including a bill whose reading guessed "summary" still being asked for. A cold review: SAFE; its one should-fix (decide on the filed kind alone) is applied. An unreadable summary is no longer asked for by the server; it shows as unreadable in the month-end step view (row 7), and a person sends it back. The rules for real bills are unchanged: blurred, cut, no total and not a bill are still asked for. `rehearse_s765.sh` 5/5. `proof_s765.py` (on the box) shows the server's open asks on summary papers and that the kit's files would withdraw every one.

**Install (the owner's paste; DRY first):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s765kit && cp -rp /root/deploy/repo/deploy_kits/S765_SUMMARY_NOT_RESCAN /tmp/s765kit && DRY=1 bash /tmp/s765kit/install_S765_SUMMARY_NOT_RESCAN.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s765kit && cp -rp /root/deploy/repo/deploy_kits/S765_SUMMARY_NOT_RESCAN /tmp/s765kit && bash /tmp/s765kit/install_S765_SUMMARY_NOT_RESCAN.sh
```
**Undo:** the installer prints the one line: the two `*.bak_S765_*` files put back, and finance restarted. Withdrawn asks stay withdrawn; they are audit rows, and they were never real work.
