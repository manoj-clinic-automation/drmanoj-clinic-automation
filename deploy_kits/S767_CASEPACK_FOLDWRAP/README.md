# S767_CASEPACK_FOLDWRAP — one CSS selector on the Case Pack page

**Why.** The live read of S764 (09-Nov 18:0x IST, read-only as the owner) found one cosmetic flaw: in the *Build an estimate* card a long fold label
("Anaesthesia · OT meds · ward meds · admission · C-arm · investigations") ran into its ₹ figure. S764's rule `.s764box summary .k{white-space:nowrap}` —
meant for the two box titles (*DTH rates*, *Build an estimate*) — also reached the fold labels inside the Build box. Reproduced in Chromium at a 520 px pane
(the text ran 130 px past the figure); gone on the fixed page.

**What changes.** `/root/wa/casepack/casepack_page.html` 333f7825 → one selector narrowed to `.s764box > summary > .k`. Nothing else; no restart.

**Install** (after the publish): `DRY=1` first, then the line without it.
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s767kit && cp -rp /root/deploy/repo/deploy_kits/S767_CASEPACK_FOLDWRAP /tmp/s767kit && bash /tmp/s767kit/install_S767_CASEPACK_FOLDWRAP.sh
```
