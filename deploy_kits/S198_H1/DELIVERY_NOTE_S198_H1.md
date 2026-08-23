# S198_H1 — Portal Health page becomes clickable (A2 of the Session-198 plan)

**One file: `finance_app.py` `388c8ac0fdfecdee6029c0033b9b0ef8` → `4ae49536309dad169441f7dc8fed7012`.**
No schema change · no new route · no data write · `_health_state` + `/finance/api/health`
byte-untouched (the S196 tile wire and the S198_P1 hero see no change).

## What changes on the page

Every health check row with a fix place is now a **link** landing exactly there:
Marg report / Marg-days-never-filed → the Hub's Marg card · Days filed / Flags →
your approval queue · Cash position → the Cash position card · Cash-UPI split /
Correction checklist → `/finance/marg-worklist` · UPI evidence → Today's strip ·
Month-vs-Marg → the month grid. Non-ok mapped rows carry a standing plain-English
**→ what-to-do line** beside the specific hint. Backup and Renewals rows are
deliberately NOT links — neither has an in-app fix (backup is server-side;
renewals ride the Inbox Janitor).

## Proof

Offline differential on the seeded live-shape store (the S193_F6 harness,
modules hash-recovered to their live pins): **557/667 → 563/673, +6 exactly,
fail set byte-identical (110 rows)**. Two of my own first-draft checks were
state-dependent and were fixed to the honest conditional form before they ever
reached this kit (F-106 discipline). `py_compile` clean · pyflakes findings
identical to the live bytes (2 pre-existing) · `check_late_locals` 0 ·
`check_row_keys` 0. Installer projection: live smoke **668 → 674, +6 exactly**.

## Install (VPS)

```
cd /root/deploy/repo && git pull
bash deploy_kits/S198_H1/INSTALL_S198_H1.sh
```
