#!/usr/bin/env python3
"""probe_s959.py -- S959: what the reply will do with the LIVE settings, said in words, never a value.
  python probe_s959.py <code dir holding calls_staff.py, portal_inbox.py, portal_wa.py, maybe portal_config.py>
Prints one line: PROBE reply on|off . templates offered N (titles) . templates LIVE|TEST MODE . send key named yes|NO"""
import importlib.util
import os
import sys

d = sys.argv[1]
sys.path.insert(0, d)
cfgm = None
p = os.path.join(d, "portal_config.py")
if os.path.exists(p):
    spec = importlib.util.spec_from_file_location("s959_live_cfg", p)
    cfgm = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(cfgm)
    except Exception:
        cfgm = None


def cfg(k, default=None):
    """As the portal's own reader (portal._cfg_get): the config's value if truthy, else the environment, else the default."""
    v = getattr(cfgm, k, None) if cfgm is not None else None
    if not v:
        v = os.environ.get(k)
    return default if v is None or v == "" else v


import calls_staff as CS  # noqa: E402


class _CC:
    _CFG = staticmethod(lambda k, d=None: cfg(k, d))
    _cfg_path = staticmethod(lambda k, d=None: cfg(k, d))


CS.CC = _CC
on = CS.wa_send_on()
ts = CS.wa_templates()
live = str(cfg("PORTAL_WA_DRYRUN", "1")) == "0"
key = "not read"
try:
    import portal_inbox as PI
    key = "yes" if PI._token(lambda k, d="": cfg(k, d)) else "NO (replies would say so; tell Claude)"
except Exception as e:
    key = "not read (%s)" % type(e).__name__
print("PROBE reply %s . templates offered %d (%s) . templates %s . send key named %s" % (
    "on" if on else "OFF", len(ts), ", ".join(t["title"] for t in ts) or "-", "LIVE" if live else "TEST MODE", key))
