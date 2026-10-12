#!/usr/bin/env python3
"""make_s535.py -- kit S535_PUNCH_SOURCE_WATCH: builds /root/attlistener_v2.py from its pinned FROM bytes by exact,
counted edits (every anchor exactly once), in memory first; nothing is written unless every edit applies.
  python3 make_s535.py <dir with attlistener_v2.py> <out dir>"""
import hashlib, os, sys

FROM = "94fc58caff28de0d400f788374106952"

WATCH = '''# --- S535 (session 305, 12-Oct-2026): THE SOURCE WATCH -- step 1 of 2, it only RECORDS -------------------------
# The owner, 12-Oct 05:33 IST: "close it only if it is safe and keeps attendance running glitch free" (D713; his
# word is the waiver of the attendance freeze D247 for this change only).
# Step 1 changes NOTHING the device sees and nothing in punches.csv. For every punch -- and for the first
# SRC_OTHER_PER_DAY other requests from each sender each day -- it appends one line to SOURCE_LOG: who sent it
# (the address), the device's own headers (a header named like a password or key is masked), and the punch's
# user and time. A week of these lines shows which mark is on every genuine punch; step 2 (refuse a stranger,
# keep it aside, never lose a genuine punch) is built only on that evidence. Every failure here is swallowed:
# the ack never depends on it. /root/att_source_summary.py reads the file each night (01:25).
SRC_OTHER_PER_DAY = 30
_src_lock = threading.Lock()
_src_other = {}                # {(day, address): other requests recorded today}
_SRC_MASK = ("pass", "pwd", "key", "auth", "token", "secret", "cookie")


def record_source(handler, method, rc_hdr, ack, raw):
    try:
        ip = handler.client_address[0] if handler.client_address else ""
        day = datetime.now().strftime("%Y-%m-%d")
        punch = (ack == "OK")
        uid = when = None
        if punch:
            try:
                obj = json.loads(extract_json(raw).decode("utf-8", "replace"))
                uid = str(obj.get("user_id"))
                when = parse_io_time(obj.get("io_time", ""))
            except Exception:
                pass
        hdrs = {}
        for k, v in handler.headers.items():
            kl = k.lower()
            if kl == "content-length":
                continue
            v = str(v)
            if any(m in kl for m in _SRC_MASK):
                v = "<masked len=%d>" % len(v)
            hdrs[k] = v[:80]
        line = json.dumps({"t": now_str(), "ip": ip, "method": method, "path": (handler.path or "")[:120],
                           "request_code": rc_hdr, "ack": ack, "punch": punch, "user_id": uid, "datetime": when,
                           "headers": hdrs}, ensure_ascii=True, sort_keys=True)
        with _src_lock:
            if not punch:
                if len(_src_other) > 200:
                    for k in [k for k in _src_other if k[0] != day]:
                        del _src_other[k]
                n = _src_other.get((day, ip), 0)
                if n >= SRC_OTHER_PER_DAY:
                    return
                _src_other[(day, ip)] = n + 1
            with open(SOURCE_LOG, "a", encoding="utf-8") as f:
                f.write(line + "\\n")
    except Exception:
        pass


'''

EDITS = [
    ("E1 the docstring names S535",
     '"""\nattlistener_v2.py — STANDALONE attendance capture + local ack (no upstream).\n',
     '"""\nattlistener_v2.py — STANDALONE attendance capture + local ack (no upstream).\n'
     'S535 (12-Oct-2026): + THE SOURCE WATCH (records who sends each punch; changes nothing the device sees).\n'),
    ("E2 the source log's place",
     'DEBUG     = False\n',
     'DEBUG     = False\n'
     'SOURCE_LOG = os.environ.get("ATT_SOURCE_LOG", "/root/attlistener_sources.jsonl")   # S535\n'),
    ("E3 the watch itself, before the handler",
     'class Handler(BaseHTTPRequestHandler):\n',
     WATCH + 'class Handler(BaseHTTPRequestHandler):\n'),
    ("E4 each request recorded once its ack is decided, before the reply",
     '        if DEBUG:\n',
     '        record_source(self, method, rc_hdr, ack, raw)   # S535: records only; never raises\n\n'
     '        if DEBUG:\n'),
    ("E5 the start-up line says the watch is on",
     'f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call")',
     'f"loaded {len(_seen)} existing punch keys  DEBUG={DEBUG}  — NO upstream call  SOURCE_WATCH=S535")'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, out):
    b = open(os.path.join(src, "attlistener_v2.py"), "rb").read()
    if md5(b) != FROM:
        raise SystemExit("REFUSED: attlistener_v2.py is %s, not the FROM pin %s" % (md5(b), FROM))
    t = b.decode("utf-8")
    for label, old, new in EDITS:
        n = t.count(old)
        if n != 1:
            raise SystemExit("REFUSED: %s: the anchor occurs %d times" % (label, n))
        t = t.replace(old, new)
    nb = t.encode("utf-8")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "attlistener_v2.py"), "wb") as fh:
        fh.write(nb)
    print("attlistener_v2.py  %d edits  %s -> %s" % (len(EDITS), FROM[:8], md5(nb)[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    build(sys.argv[1], sys.argv[2])
