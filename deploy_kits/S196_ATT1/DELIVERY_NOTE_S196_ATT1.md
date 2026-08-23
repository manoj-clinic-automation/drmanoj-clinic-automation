# S196_ATT1 — Delivery note (attendance self-service + machine late minutes)

**Session 196 · 23 Aug 2026 · built offline on hash-verified live bytes, both
selftests green in the sandbox (necessary, not sufficient — the installer
re-runs everything with the VPS venv, F-53).**

## What this kit does (owner rulings, S196)

1. **Staff logins see "My biometric" — today only.** A portal login mapped to a
   staff member opens `attendance.dr-manoj.in/register/me`: today's date and
   today's punch times. Nothing else — no history, no other staff, no shift or
   salary data. Every other register page routes them back here.
2. **"Mark me present" request.** Only for TODAY, only while the machine has no
   punch for them, one per day, reason required. **The server's receipt time IS
   the punch time** — the phone clock is never trusted, and a delayed request
   costs exactly what a late punch costs (the late bands run off it). Shavez
   verifies (never his own request), and it counts **only after Dr Manoj's
   approval** on the Pending-review board, which shows "#N this month" per
   staffer so a habit stands out. They punch OUT on the machine as usual — the
   approved request is the in-punch, the machine punch the out-punch.
3. **Machine late minutes in the day grid.** Every staff row shows the machine
   first-punch; **60 minutes or more late shows the exact minutes in a loud
   read-only badge** — server-computed, stored in `daily_register.late_minutes`,
   the form cannot supply or override it. Sundays included via the D253 roster
   rule. Sub-60 lates show quietly. Machine facts, maker decisions — separated.
4. **att_month_report v2.6** folds APPROVED requests as synthetic punches
   (presence, late bands, review-file loop, departure pairing — identical to a
   real punch). Request-backed days carry `*` in the grid with a legend line.
   Register DB unreachable → the report runs exactly as v2.5 (fail-soft).

**Frozen core untouched** (attlistener/att_core/att_dashboard/att_doctor,
D251). att_month_report is the sanctioned additive report layer. No portal.py
change needed — the staff-role tiles already point at register URLs, which now
route self users correctly.

## Pins

| file | live (gate) | after install |
|---|---|---|
| `/root/staff_register/staff_register.py` | `cef768594bee5360a388e66028456495` (v0.2, S164) | **`c2059ea1e0157da6cbf820502f4925a3`** (v0.3) |
| `/root/att_month_report.py` | `e64cad19d135618dec1413553e6bdc80` (v2.5, S153) | **`9ab98313bbda7ae5555fb4b5a5a82c4b`** (v2.6) |

Schema: additive only — new table `present_request`, new columns
`staff.username`, `daily_register.late_minutes`. No row is modified or deleted.
Service restarted: `staff-register` only.

## Install (one command on the VPS, after PUBLISH_ALL)

```
cd /root/deploy/repo && git pull && bash deploy_kits/S196_ATT1/INSTALL_S196_ATT1.sh
```

The chain refuses at step 1 if either live file is not at its pin, and restores
backups automatically on any later failure. Step 7 prints the username→staff
mapping it derived — read that line; any "SKIP (ambiguous)" needs a by-hand
`username` (tell Claude).

## After install — the only human steps

1. **Create 7 portal logins** in Manage Users (`/portal/users`), role **staff**
   (this role only opens the self page — no entry, no approvals):
   `awdhesh · pravesh · ranjeet · sukhveer · sandip · vikki · surendra`
   ⚠ each username must match the mapping step 7 printed (first name,
   lowercase, as spelt in the staff master — if the master says "Vicky", the
   username is `vicky`). No login for Arjun (owner ruling). Existing logins
   (alisha, shivani, shavez, darpan) get the self page automatically.
2. **Staff phones:** open `attendance.dr-manoj.in/register` in Chrome → sign in
   → menu → **Add to Home screen**. Sessions last ~6 months; deactivating a
   user in Manage Users still cuts access instantly.
3. At the month-end run, request-backed days appear with `*` — nothing else in
   the routine changes.

## Record-keeping owed at the close

- KB Register: both pins above into the live-file table; `live_pins.txt`
  regenerate (A8) — the installer reminds.
- Candidate decision for minting: the S196 present-request policy
  (request-time-as-punch · same-day-only · no-punch guard · verify-then-doctor)
  — suggest **D334**.
