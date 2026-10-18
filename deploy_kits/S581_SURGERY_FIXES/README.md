# S581_SURGERY_FIXES — the fixes from the live dummy-case test of S579 (kit S581, session S325, 18-Oct-2026, D735)

**Why.** The owner, 18-Oct 12:17 IST: *"do the entire work in the surgical case app by creating a dummy case so that you can verify
each step and its functionality. Thoroughly and report back."* The test (12:18–12:27 IST, as manoj, two dummy cases, all removed
after) passed all 15 steps and found these, now fixed in `/root/finance/surgery_cases.py` (e56e3f52 → this kit's file):

1. A removed case's papers, and a removed hospital payment's statement, still opened by direct link — now they do not.
2. On a hospital payment, "Still due" showed the amount before this payment — now **Still due after this**.
3. Amounts as 150,000 — now Indian grouping, **1,50,000**.
4. The remove-a-payment/cheque, paper and implant lists start with **— choose —** (nothing picked by itself).
5. The **UTR / reference** is shown on the payment page; the implants table has a **Qty** column.
6. A vendor with no live entries can be **taken off the lists** (kept in the record; writing the same name again brings it back) —
   the test's "TEST VENDOR — dummy" can now be cleared.
7. The vendor page's wording ("Only you can see this page. To share it with the vendor, print it or save it as a PDF."); the scanner
   page no longer prints its own title bar above the scanner's.

Not changed (stated to the owner): the dummies used case numbers S-2026-0001/0002, so real cases start at 0003; the Case Pack's own
remembered draft (pre-existing behaviour of the Case Pack, not this module).

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s581kit && cp -rp /root/deploy/repo/deploy_kits/S581_SURGERY_FIXES /tmp/s581kit && bash /tmp/s581kit/install_S581_SURGERY_FIXES.sh
```
Gates → pin (e56e3f52, the S579 mount present) → compile on both pythons → the walk (67 checks: S579's 53 plus 14 for these fixes)
on a made-up database and on a copy of the live one, and the control (the live S579 module goes red, 55 of 67) → the real finance
app on copies (probe) → backup → place → restart clinic-finance → health → the probe on the placed file. Six broken versions of the
fixes each turn the walk red. A second run says ALREADY INSTALLED.

## Undo
```
cp -p /root/finance/surgery_cases.py.bak_S581_e56e3f52 /root/finance/surgery_cases.py && systemctl restart clinic-finance
```
