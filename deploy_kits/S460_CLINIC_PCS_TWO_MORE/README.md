# S460_CLINIC_PCS_TWO_MORE — session 292, 03-Oct-2026

The *Clinic PCs* page (S450/S451) had one button — the Reception PC. This kit gives the **Medical PC** and **Dr Manoj's PC** theirs.

| where | file | from → to | what |
|---|---|---|---|
| server | `/root/finance/pc_kits.py` | `7889600c` (S451) → `built/pc_kits.py` | a second setup-file template, `SETUP_PYKIT`: the same computer-name guard, code door and md5 checks as the Reception PC's file, then it runs the kit's own `setup_pc.py` with that PC's Python (or one it brings just to run the installer). Two entries in `SETUPS`; for each PC its file name, the plain-letters name the window prints, where it keeps its Python, and its *only a person can do these* list. No enrolment for these two. |
| repository | `deploy_kits/PC_KITS/medical/`, `…/manojz/` | NEW | `kit.zip` + `KIT_INFO.txt` (kits S458, S459) — they arrive with this line's pull. |

**The Reception PC's road is untouched:** its entry, its template and its setup file are byte for byte what they were (the walk holds the two modules' output against each other).

**Both new installers only put back what is not there** — on a working PC they are a read-only check. Nothing is placed on any PC by installing this kit; a button hands out a file only when the owner presses it on that PC.

**The owner's line (one line; it carries its own pull, F-464):**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S460_CLINIC_PCS_TWO_MORE/install_S460_CLINIC_PCS_TWO_MORE.sh
```

**Walk (35 checks, the Flask test client, scratch copies of the kits):** the Reception PC's setup file unchanged; each new setup file is plain letters with Windows line ends, nothing left to fill in, every jump lands on a label, no odd quote; it expects its own computer name and stops on the other two; the press hands out the right file; its code fetches that PC's kit and the Python part and cannot enrol a key; no login, a cross-site press, a planned PC and a tampered kit hand out nothing.

**Owed:** each button pressed once on its own PC (where the installer must report nothing placed) — the Medical PC's after S454 has landed, at a quiet hour.

**Undo:** `\cp -p /root/finance/pc_kits.py.bak_S460_7889600c /root/finance/pc_kits.py && systemctl restart clinic-finance`.
