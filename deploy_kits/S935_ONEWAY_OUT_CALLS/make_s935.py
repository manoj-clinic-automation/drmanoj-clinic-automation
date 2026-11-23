#!/usr/bin/env python3
"""make_s935.py -- kit S935 (the parent, S498, 23-Nov-2026): outgoing calls dialled from a staff member's MyOperator app
('oneway' / direction 'outgoing') are kept like incoming calls. Exact anchors; FROM md5 pinned; writes the TO files.
    python3 make_s935.py <call_hook_capture.py FROM> <portal_console.py FROM> <out dir>"""
import hashlib, os, sys
HOOK_FROM = "2d25fe7b93dd82dd8eab164d8459acbe"
PC_FROM = "a8d050ef8c9e78b57467b58a68789841"

HOOK = [
 ('''    else:
        return None                              # oneway/callback/webcall/otp/etc.
''',
  '''    elif category == "oneway" and str(p.get("direction", "") or "").strip().lower() == "outgoing":
        # S935 (23-Nov-2026): an outgoing call dialled from a staff member's own MyOperator app.
        # Keyed "OUT-<session_id>" (payload.id; the same in call.end and call.summary, so the pair is one row);
        # phone10 = the patient's last-10 (customer_number, else the customer leg's number).
        session_id = str(p.get("id", "") or body.get("session_id", "") or "").strip()
        if not session_id:
            return None                          # cannot key it; raw log keeps it
        client_ref_id = "OUT-" + session_id
        phone10 = last10(p.get("customer_number")
                         or body.get("customer_identifier")
                         or leg.get("phone_number") or "")
    else:
        return None                              # callback/webcall/otp/oneway-incoming/etc.
'''),
 ('''    log("Phase B receiver v3.2 (dual-key + incoming capture; the verified row, S698). raw logs: %s" % RAW_DIR)''',
  '''    log("Phase B receiver v3.3 (dual-key + incoming + app-dialled outgoing capture, S935; the verified row, S698). raw logs: %s" % RAW_DIR)'''),
]
PC = [
 ('''    if c == "obd":
        return "Out"
    return "?"''',
  '''    if c == "obd":
        return "Out"
    if c == "oneway":                     # S935: dialled from a staff member's MyOperator app (OUT-<session> rows)
        return "Out"
    return "?"'''),
]

def md5(b): return hashlib.md5(b).hexdigest()

def patch(path, pin, subs):
    raw = open(path, "rb").read()
    if md5(raw) != pin:
        sys.exit("FROM pin mismatch on %s: %s (expected %s)" % (path, md5(raw), pin))
    s = raw.decode("utf-8")
    for old, new in subs:
        n = s.count(old)
        if n != 1:
            sys.exit("anchor found %d times in %s: %r" % (n, path, old[:60]))
        s = s.replace(old, new)
    return s.encode("utf-8")

if __name__ == "__main__":
    hook, pc, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    for name, src, pin, subs in (("call_hook_capture.py", hook, HOOK_FROM, HOOK), ("portal_console.py", pc, PC_FROM, PC)):
        b = patch(src, pin, subs)
        open(os.path.join(out, name), "wb").write(b)
        print("%s %s -> %s" % (name, pin[:8], md5(b)[:8]))
