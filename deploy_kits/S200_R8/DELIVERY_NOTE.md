# S200_R8 — the ledger joins the PWA origin (phase 2) · sheets bolder · real back buttons

## The 404s, explained honestly
Every `/ledger/...` door on Sheet 2 404'd because the ledger was never proxied under
`followup.dr-manoj.in` — that was the deliberately deferred phase 2 of the unification (R2a/R2b
did the register only). Your July run-through surfaced it the first time a Sheet-2 door was
actually pressed. This kit completes phase 2 for the ledger:

1. **Vhost**: `/ledger → 127.0.0.1:8043` appended to the LIVE followup vhost (same additive
   pattern as R2a; `attendance.dr-manoj.in/ledger` keeps working; `/wa-approve`, `/finance`,
   `/register` untouched; existing-path pre-probes; full rollback).
2. **Portal tiles**: both Staff-Ledger tiles (doctor + manager) go same-origin `/ledger`, so
   taps stay inside the installed app. (The bare Attendance tile and Assets remain the last
   cross-domain holdouts — phase 2b/3.)
3. **salary_policy v1.6**: back links become real buttons ("← Back to the flow", slate style);
   sheet cells 16px semi-bold (grid cells 14px); the sheet nav gains **Lock desk** and
   **⏮ prev / next ⏭ month** arrows that keep you on the same sheet.

| target | was | now |
|---|---|---|
| followup `vhost.conf` | no `/ledger` | `+ ledger_app` context (block `cb0a5ded…`) |
| `/root/portal/portal.py` | `a48f4189…` (R2b) | `24ea2c0b44bad08fbce71908a5019ecc` |
| `/root/staff_register/salary_policy.py` | `c9dd846e…` (R7) | `73aca693e28c4670af74c0c016643af9` (v1.6) |

Proof offline: hash-gated bases, anchors exactly once, py_compile clean, policy selftest PASS.
Installer refuses unless the ledger backend answers on 8043 and every existing path is healthy
first; probes `/ledger/login` + `/portal` + `/register/health` after; one rollback restores all
three targets together.

## Install
    PUBLISH_ALL.bat →  cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R8/INSTALL_S200_R8.sh

Then reload Sheet 2 — the ledger doors open in-app, the Back button is unmissable, and the
tables read at a glance. Continue the run-through: approve Sheet 1 → approve Sheet 2 → LOCK.
