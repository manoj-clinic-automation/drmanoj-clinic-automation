#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""edits_s833.py -- S833_READER_TOLD: the counted edits on two live files of the scan app (and one NEW file, reader_watch.py, shipped whole).
Each edit replaces text that occurs EXACTLY the number of times given; anything else stops the build.

  /root/assetapp/claude_reader.py  1c9e952e -> F-1404: a refused key is named -- 'the key has expired' when the answer says so, else
                                              'the key was refused (expired or revoked)' (three places: read, read_summary, S754's one call).
  /root/assetapp/clinic_papers.py  89a3cd0a -> F-1194: auto_home never moves a dealer's summary (kind Summary / doc_kind summary) -- at
                                              start too (heal_auto runs at mount, before S754's guard is installed at the foot of the app).
"""
import hashlib

FROM = {"claude_reader.py": "1c9e952eefe72bd75da1d4385e8861bc", "clinic_papers.py": "89a3cd0a91076cc6c5e0a5c2a420c4a6"}

EDITS = {
    "claude_reader.py": [
        ("the refused key's words, once per place", 3,
         'set_setting(con, "read.claude", "stopped:the key was refused")',
         'set_setting(con, "read.claude", "stopped:" + _refused_words(low))'),
        ("the helper beside state()", 1,
         'def available(db_path):',
         'def _refused_words(low):\n'
         '    """F-1404 (S833): a refused key, named -- \'the key has expired\' when the answer says so, else that it was refused (an\n'
         '    expired or a revoked key reads the same). reader_watch.py tells the owner the words, at once."""\n'
         '    return "the key has expired" if "expir" in (low or "") else "the key was refused (expired or revoked)"\n'
         '\n\n'
         'def available(db_path):'),
    ],
    "clinic_papers.py": [
        ("a summary is never sent anywhere by history", 1,
         '    if "page_of" in b.keys() and b["page_of"]:\n        return did\n    if (b["kind"] or "") == "Pharmacy expense":',
         '    if "page_of" in b.keys() and b["page_of"]:\n        return did\n'
         '    if (b["kind"] or "") == "Summary" or ((b["doc_kind"] if "doc_kind" in b.keys() else "") or "") == "summary":\n'
         '        return did                                                   # F-1194 (S833): a dealer\'s summary is never moved by history, at start too\n'
         '    if (b["kind"] or "") == "Pharmacy expense":'),
    ],
}


def build(name, src, dst, out=print):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if not m.startswith(FROM[name]):
        out("%s is %s, not the FROM pin %s -- STOP" % (name, m[:8], FROM[name][:8]))
        return 1
    t = raw.decode("utf-8")
    for what, n, old, new in EDITS[name]:
        c = t.count(old)
        if c != n:
            out("%s: %s -- found %d times, not %d -- STOP" % (name, what, c, n))
            return 1
        t = t.replace(old, new)
        out("  %s: %s -- %d replacement%s" % (name, what, n, "" if n == 1 else "s"))
    with open(dst, "wb") as h:
        h.write(t.encode("utf-8"))
    return 0
