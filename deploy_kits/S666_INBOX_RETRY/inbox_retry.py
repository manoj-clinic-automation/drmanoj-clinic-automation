#!/usr/bin/env python3
"""inbox_retry.py -- kit S666_INBOX_RETRY (the parent, S358, 27-Oct-2026). Run by cron every 2 minutes under flock:
tries again the WhatsApp Inbox sends MyOperator's gateway refused at its authorizer (portal_inbox.run_retries).
Prints one line only when something was due. Never prints a key."""
import os, sys
HERE = os.environ.get("INBOX_PORTAL_DIR", os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    import portal_config as _cfg                # the portal's own settings (VPS-only, chmod 600)
except Exception:                                                       # noqa: BLE001
    _cfg = None


def cfg_get(name, default=""):
    v = getattr(_cfg, name, None) if _cfg is not None else None
    return v if v else os.environ.get(name, default)


import portal_inbox                             # noqa: E402

if __name__ == "__main__":
    line = portal_inbox.run_retries(cfg_get)
    if line:
        print(line, flush=True)
