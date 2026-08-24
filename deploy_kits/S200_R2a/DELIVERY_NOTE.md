# S200_R2a — Staff Register under the portal PWA (phase 1a of the unification)

## What this does
Adds ONE reverse-proxy path — `/register` → `127.0.0.1:8044` — to the LIVE
`followup.dr-manoj.in` vhost, so the Staff Register / Salary flow is reachable
at `https://followup.dr-manoj.in/register/...` — the SAME origin your portal PWA
is installed from. Login carries automatically (the SSO cookie is domain-wide,
`.dr-manoj.in`) and every link in the app is relative, so NO app code changes.

## What it does NOT do (yet)
- It does NOT change the portal tiles. They still point at
  `attendance.dr-manoj.in/register/...`, so *tapping a tile* still leaves the PWA
  until phase 1b retargets them same-origin. After 1a you can reach the register
  in-app by URL; 1b makes the taps stay in-app.
- It removes NOTHING. `attendance.dr-manoj.in/register` keeps working exactly as
  now — this is purely additive, so the old path stays as a fallback.
- Ledger, bare Attendance, and Assets are phase 2/3 — untouched here.

## Safety
- Patches the LIVE file (drifted from the repo: your live vhost carries
  `/wa-approve` + `/finance` that the repo copy lacked — appending avoids
  clobbering them).
- Backs up `vhost.conf` (timestamped) before touching it.
- Refuses if: the vhost is missing, the block bytes are unexpected, `lswsctrl`
  isn't found, the 8044 backend isn't healthy, or an existing path is already
  failing.
- After a graceful restart it probes `/register/health` AND `/portal` AND
  `/finance` via the local socket. If the new path isn't served, or either
  existing path stops answering, it RESTORES the backup and restarts again.
- The `.new`/`.conf0` siblings in the vhost dir are left alone.

## Install
    bash /root/deploy/repo/deploy_kits/S200_R2a/INSTALL_S200_R2a.sh

Expected tail:
    == DONE. https://followup.dr-manoj.in/register is live; /portal and /finance still answer. ==

## After it's green
Open `https://followup.dr-manoj.in/register/salary/flow/sheet1?ym=2026-07`
in the portal app — it should load in-app. Tell me green and I'll build 1b
(retarget the portal tiles) from your live portal.py.

## Files
- register_proxy.block  — the exact proxy block appended (md5 24738a34c86b8ef054ec01997e47a32c)
- INSTALL_S200_R2a.sh    — installer (backup + append + restart + probe + rollback)
