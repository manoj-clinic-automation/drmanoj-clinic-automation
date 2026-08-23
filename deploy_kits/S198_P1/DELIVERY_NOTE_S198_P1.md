# S198_P1 v2 — portal home revamp (A1 of the Session-198 clubbed plan)

**One file: `portal.py` `ee749cd9f3ac1294aab0d13ce069efc1` → `dc093f1f83598b4e1927c2caee639fc7`.**
No schema change · no new route · no other service touched · no data write.

## What you will see after install

- Your portal home KEEPS the **dark scheme** (your ruling, 23-Aug) with the
  new compact layout, a **46px floating back-to-top**, and the tile order you
  asked for: Console + Tracker together, GMB up, Case Pack after the WhatsApp
  cluster. Login, Console, Gist and the other pages are byte-unchanged.
- A **status strip** on top (your login only): the **Portal Health** card
  (opens `/finance/health`; shows the worst problem's one line, or "All
  clear") + three live chips — Sanjeevni days to approve · Register entries
  to enter · review-queue bills. All fail-soft: if finance is down or the
  viewer isn't the medical checker, static text stands.
- **Half-height tiles, everything on one screen.** New **Staff** group holds
  the connected family (Attendance → Register → Salary → Ledger) with the
  relationship in each subtitle.
- **Clinic-PC tools** render as the **migration-queue chip row** (still only
  on the marked clinic PC; Revenue Reconciler shows everywhere as a held chip
  since it is "migrate first").
- Retired: Ayushman Finder + Surgical Estimate (inside the Case Pack), WABA
  Send (= Send WhatsApp), Nutrition/Physio (folded into Vitals & Plan).
  Renamed: UPI Reconciliation → **UPI Sheet** ("lab + legacy — retires when
  lab moves"). WhatsApp Approvals no longer says "blocked — vendor".
- NEW: **Payment Register** (the Janitor's sheet — MANUAL until you paste its
  URL into `portal_config.py`, one line, instructions in the installer's
  goodbye) and **Forms & Downloads** (held; the A3 build flips it live).

## What is proven, not promised

- Gate **127/127 GREEN** (v2: + dark-scheme, back-to-top and tile-order checks) offline (five identities: manoj/bhawna/darpan/
  alisha/shavez): every mask and grant intact, every surviving tile's URL
  byte-equal to the live baseline, removed tiles absent, no hero for
  non-doctors, PC gating unchanged. The same gate re-runs **on the box,
  against the candidate, before anything moves** (step 3).
- Negative control: the gate refuses the live `ee749cd9…` bytes.
- `py_compile` + `pyflakes` clean.

## Install (VPS)

```
cd /root/deploy/repo && git pull
bash deploy_kits/S198_P1/INSTALL_S198_P1.sh
```

Rollback is automatic on any red; backup kept beside `/root/deploy/`.

*Built S198 (23-Aug-2026) on the hash-verified live bytes (kit `S196_HLT2`
payload = live pin). The KB Register pin moves to `a8cacc3b…` when the
installer prints GREEN, not before.*
