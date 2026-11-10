# S775_UNSPILL_TAILS — Gunina's two October bills get their lines (purchase_unspill v1.1)

**Session 423 (the Sanjeevni chat), 10-Nov-2026. F-1233. The owner, 13:02 IST: "Why there are still two bills with no lines, even after so much build?"** The same fault as S773 in another shape. For GUNINA's bill numbers `GPPL2678591` and `GPPPL3679039` the spill `L2678591LEFUMED 20MG TAB` matched the old reader's letters+digits shape, so the lines were stored with bill number `L2678591` — the column's last 8 characters, a number no bill carries. S773 looked only at lines with NO number, and walked past these.

| file | from → to | what |
|---|---|---|
| `/root/finance/purchase_unspill.py` | `3c12a4cc` → TO | v1.1: `plan_tails` — a line whose number is EXACTLY the last 8 characters of ONE live bill of the same supplier, no bill of that supplier carrying the short number, the bill in the export's period, neither month FINAL → the full number and the bill's date (the item left as it is). `undo(since=...)` |

`purchase_app.py` is not changed (S773's hook, `51e42707`, calls the module on every push).

**Proofs:** `walk_s775.py` 21/21 green through the real push door (S773's 18 + the wrong split joined, a real short bill never lengthened, two bills ending alike not joined, undo since a time); the CONTROL on the live v1.0 module red. `rehearse_s775.sh` 5/5 (a red after placing puts v1.0 back and undoes ONLY what this install joined — S773's joins kept). On the device's copy of the 10-Nov database: v1.1 joins 104 lines (S773's 65 + Gunina's 39); after it, **no October bill without lines**. The one bill left in any month is Deepam Pharma 502 (18-Aug, a FINAL month): its lines are filed under Mannat Pharma — another fault, not this one.

**Install (the owner's paste):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s775kit && cp -rp /root/deploy/repo/deploy_kits/S775_UNSPILL_TAILS /tmp/s775kit && bash /tmp/s775kit/install_S775_UNSPILL_TAILS.sh
```
**Undo:** the installer prints the one line (v1.0 back, finance restarted, then what this install joined put back).
