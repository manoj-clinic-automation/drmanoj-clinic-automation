# S369_PUSH_DIAG — the notification card speaks up, and reports

Two staff phones (Shivani's OnePlus, the reception mobile) tapped **सूचना चालू करें** and "nothing happened". Nobody can
see those screens from here, so the card now (1) shows a clear line under itself at every step — *waiting for Chrome*,
*blocked — do this*, *done*, or the exact error; (2) never hangs — Chrome's permission ask and the phone registration
each have a timeout with their own message; (3) reports every step (permission state, installed-app or browser, error,
phone/browser make) to the portal, where the doctor's login reads it at
`https://followup.dr-manoj.in/portal/push/diag` — the assistant reads that from his browser. Staff cannot read it.

Pins: `portal.py` `7bddc17c…` (S366) → see `install_S369_PUSH_DIAG.sh` · `portal_push.py` `6fa0a56a…` → same.
`make_s369.py` = the two card blocks swapped whole; `walk_s369.py` 13/13 with the S366 portal.py as negative control.
Restarts `clinic-portal` only. Touches nothing else.
