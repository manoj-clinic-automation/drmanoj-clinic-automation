#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prove_s800.py -- kit S800_WA_SEND_KNOCK (S437, 12-Nov-2026, the parent). SENDS NOTHING.

Calls the Inbox's sender WITH the S800 change -- the real key, an EMPTY number and EMPTY text, so nothing can be delivered --
and reports what each try got. The key is read on the box the way inbox_retry.py reads it and is never printed.

  prove_s800.py <portal dir>              up to 3 cycles: PROVEN when a first try is refused at the gateway ("500A") and a later try
                                          of the same call is not; a cycle that is not refused at all (the gateway was warm) waits
                                          150 s and tries once more; FAILED when every try of a cycle is refused
  prove_s800.py <portal dir> --installed  one call through the installed sender: refused at the end, or not

Last line:  PROVE: PROVEN ...  |  PROVE: WARM ...  |  PROVE: FAILED ...  |  PROVE: ERROR ...
"""
import os
import sys
import time

PORTAL_DIR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/root/portal"
CYCLES = int(os.environ.get("S800_CYCLES", "3"))
IDLE = float(os.environ.get("S800_IDLE", "150"))


def load():
    if PORTAL_DIR not in sys.path:
        sys.path.insert(0, PORTAL_DIR)
    cfgdir = os.environ.get("S800_CONFIG_DIR", "/root/portal")         # the portal's own settings stay where they are (never copied)
    if cfgdir not in sys.path:
        sys.path.append(cfgdir)
    try:
        import portal_config as _cfg
    except Exception:                                                  # noqa: BLE001
        _cfg = None

    def cfg_get(name, default=""):
        v = getattr(_cfg, name, None) if _cfg is not None else None
        return v if v else os.environ.get(name, default)
    import portal_inbox as pi
    if os.path.dirname(os.path.abspath(pi.__file__)) != PORTAL_DIR:
        raise RuntimeError("portal_inbox came from another folder")
    if not hasattr(pi, "_myop_send_once"):
        raise RuntimeError("this portal_inbox does not carry the S800 change")
    tok = os.environ.get("S800_TOKEN") or pi._token(cfg_get)
    if os.environ.get("S800_API_URL"):
        pi.API_URL = os.environ["S800_API_URL"]
    if os.environ.get("S800_WAITS"):
        pi.S800_WAITS = tuple(float(x) for x in os.environ["S800_WAITS"].split(","))
    return pi, tok


def one_call(pi, tok):
    tr = {}
    pi.myop_send(tok, "", {"type": "text", "context": {"body": ""}}, trace=tr)   # an empty number, empty text: nothing can go
    return list(tr.get("attempts") or []), bool(pi.gateway_refusal(tr))


def main():
    try:
        pi, tok = load()
    except Exception as e:                                             # noqa: BLE001
        print("PROVE: ERROR the Inbox sender could not be loaded (%s: %s)" % (type(e).__name__, str(e)[:80]))
        return 2
    if not tok:
        print("PROVE: ERROR no key on the box")
        return 2
    if "--installed" in sys.argv:
        att, ref = one_call(pi, tok)
        good = bool(att) and att[-1] == "400" and not ref              # 400 = the gateway let it through and the service refused the empty number
        print("INSTALLED: the Inbox sender, nothing sent, tries: %s -- %s" % (" then ".join(att), "not refused" if good else "REFUSED OR NO PROPER ANSWER"))
        return 0 if good else 1
    seen = []
    for c in range(CYCLES):
        att, ref = one_call(pi, tok)
        seen.append(" -> ".join(att))
        print("  cycle %d, nothing sent: %s" % (c + 1, seen[-1]), flush=True)
        if ref:
            print("PROVE: FAILED every try of a call was refused (%s)" % seen[-1])
            return 1
        if att and att[-1] != "400":
            print("PROVE: FAILED a try got no proper answer (%s) -- 400 is the proper answer to an empty number" % seen[-1])
            return 1
        if att[0] == "500A":
            print("PROVE: PROVEN the first try was refused and try %d of the same call was let through (%s)" % (len(att), seen[-1]))
            return 0
        if c + 1 < CYCLES:
            print("  the gateway did not refuse (it was warm); waiting %d s for it to go idle" % IDLE, flush=True)
            time.sleep(IDLE)
    print("PROVE: WARM never refused in %d calls (%s)" % (CYCLES, " | ".join(seen)))
    return 3


if __name__ == "__main__":
    sys.exit(main())
