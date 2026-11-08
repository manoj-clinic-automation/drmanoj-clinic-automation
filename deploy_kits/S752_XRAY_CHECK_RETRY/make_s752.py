#!/usr/bin/env python3
"""make_s752.py -- S752_XRAY_CHECK_RETRY (the parent, S404, 08-Nov-2026): the owner's 'build it' (14:46 IST).
Every filing run re-tries the pictures parked in Drive's "X-ray check" folder that nobody has answered: an ID now on the
day's X-ray list is filed; a name-only picture matching exactly one X-ray patient of the day is filed; an ID one digit off
(or a name match) is a one-tap suggestion on Check karein, never filed by itself.
Counted edits (seven) on the LIVE bytes (/root/finance/records.py 5b325c6f, = the 08-Nov bundle), each anchor found exactly once,
plus the S752 block appended (s752_block.py).
usage: make_s752.py <live records.py> <out_dir>"""
import hashlib
import os
import sys

FROM_MD5 = "5b325c6f4c42893ed11d4ace19020bf8"
HERE = os.path.dirname(os.path.abspath(__file__))


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("STOP: anchor %s found %d times (must be 1)" % (label, n))
    return text.replace(old, new, 1)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        sys.exit(__doc__)
    raw = open(a[0], "rb").read()
    if md5(raw) != FROM_MD5:
        sys.exit("STOP: records.py is %s, not the FROM %s" % (md5(raw)[:8], FROM_MD5[:8]))
    t = raw.decode("utf-8")
    t = edit(t, "Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).\n",
             "S752 (S404, 08-Nov-2026, the owner's 'build it'): the pictures parked in Drive's \"X-ray check\" folder are re-tried on\n"
             "every run -- filed when their ID is now on the day's X-ray list, or (once the day is over) when a name-only picture is\n"
             "word for word the name of one X-ray patient of that day and no other shares a word of it; anything weaker is a\n"
             "suggestion on Check karein, never filed by itself.\n"
             "Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).\n", "E1 doc")
    t = edit(t, '    cfid = setting(con, "xray_check_id")\n    in_check = set()\n',
             '    cfid = setting(con, "xray_check_id")\n    in_check, s752_retry, s752_listed = set(), [], False   # S752: the unanswered pictures, re-tried below\n',
             "E2 retry list")
    t = edit(t, '                    items.append({"id": sid, "action": "file", "name": name, "path": _xray_path(day)})\n'
                '    for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state=\'check\'"):\n',
             '                    items.append({"id": sid, "action": "file", "name": name, "path": _xray_path(day)})\n'
             '                elif not a:                                  # S752: nobody has answered it -- planned again below\n'
             '                    s752_retry.append(f)\n'
             '    items.extend(_s752_retry_safe(con, s752_retry, stamp, notes, s752_listed))\n'
             '    for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state=\'check\'"):\n', "E3 retry call")
    t = edit(t, "            extra = ('<input name=\"new_id\" inputmode=\"numeric\" placeholder=\"Sahi clinic ID\" maxlength=\"8\">'\n"
                "                     '<button name=\"a\" value=\"id_fixed\">Sahi ID lagayein</button>')\n",
             "            extra = ('<input name=\"new_id\" inputmode=\"numeric\" placeholder=\"Sahi clinic ID\" maxlength=\"8\" value=\"%s\">'\n"
             "                     '<button name=\"a\" value=\"id_fixed\">Sahi ID lagayein</button>') % _esc(i.get(\"suggest\") or \"\")   # S752\n",
             "E4 box")
    t = edit(t, "        else:\n            answers = _answers(con)\n            for f in cf:\n",
             "        else:\n            s752_listed = True                           # S752: the check folder was read\n"
             "            answers = _answers(con)\n            for f in cf:\n", "E5 listed")
    t = edit(t, '        if cfid and r["src_id"] not in in_check and r["src_id"] not in ids:\n',
             '        if cfid and s752_listed and r["src_id"] not in in_check and r["src_id"] not in ids:   # S752: never when the folder was not read\n',
             "E6 gone sweep")
    t = edit(t, "                        btn, extra))\n",
             "                        extra, btn))   # S752: the ID box first -- Enter in it is 'Sahi ID lagayein', never 'Yeh X-ray nahi'\n",
             "E7 order")
    block = open(os.path.join(HERE, "s752_block.py"), "rb").read().decode("utf-8")
    if not t.endswith("\n"):
        sys.exit("STOP: records.py does not end with a newline")
    t = t + block
    out = os.path.join(a[1], "records.py")
    open(out, "wb").write(t.encode("utf-8"))
    print("records.py %s -> %s" % (FROM_MD5[:8], md5(t.encode("utf-8"))))


if __name__ == "__main__":
    main()
