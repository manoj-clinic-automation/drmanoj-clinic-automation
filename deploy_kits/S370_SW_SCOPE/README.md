# S370_SW_SCOPE — the one-character fix

Shivani's phone (via S369) reported: permission **granted**, then `sw-ready-timeout`. My bug: the app's background worker
was registered for `/portal/` while the page lives at `/portal`, so the browser never reported it ready. Now the scope is
`/portal`, the page waits on its own registration (with a timeout and a plain message), and the old registration is retired.
`walk_s370.py` 13/13 with the S369 portal.py as negative control. Restarts `clinic-portal` only.
