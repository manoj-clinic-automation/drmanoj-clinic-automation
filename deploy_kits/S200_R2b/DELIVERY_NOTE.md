# S200_R2b — register tiles same-origin (phase 1b of the portal-PWA unification)

## What this does
ONE file: `/root/portal/portal.py`
`ab019dda3ac68e566de017c5ae536a6b` → `a48f418961c950f42de744d3729d91bd`

Three links, nothing else (full diff = header note + these three):
- **Staff Register tile** → `/register/review` (was `https://attendance.dr-manoj.in/register/review`)
- **Salary — approve & lock tile** → `/register/salary`
- **"Register to enter" health chip** → `/register/review`

Same-origin links resolve to `followup.dr-manoj.in/register/...` — the doorway
S200_R2a opened — so taps now stay inside the installed portal app instead of
jumping to the attendance domain. The live-counts on the Staff Register tile
are untouched (they already go through the portal's own F-68 proxy).

## Deliberately NOT changed (phase 2/3)
- **Attendance** tile (`attendance.dr-manoj.in` root) and the two **Staff Ledger**
  tiles (`.../ledger`) — those backends aren't proxied under followup yet.
- **Asset Register** (`assets.dr-manoj.in`) and the external Call Tracker.

## Base provenance
Patched from the KB-Register-v5.44 live pin `ab019dda…` (found by hash in
`deploy_kits/S198_G1/`, D188). Guarded replacements, every anchor exactly once;
py_compile clean; diff proven to be only the four intended spots.

## Installer safety
- Refuses if kit bytes fail SUMS, if the R2a `/register` proxy is not answering
  200 (prerequisite), or if the live portal.py is neither the expected base nor
  already the new build.
- Backup → swap → payload-md5 → py_compile → restart → probe `/portal`;
  **auto-rollback + restart on any failure**.

## Install
    bash /root/deploy/repo/deploy_kits/S200_R2b/INSTALL_S200_R2b.sh

Then in the installed portal app: tap Staff Register — it should open WITHOUT
leaving the app. That's the proof of the whole phase-1 pattern.

## Pin move (record at close)
`/root/portal/portal.py` `ab019dda…` → `a48f418961c950f42de744d3729d91bd`
(expect verify_live_pins drift +1 until the S200 close regenerates the list).
