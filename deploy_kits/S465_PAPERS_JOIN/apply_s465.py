#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s465.py -- S465_PAPERS_JOIN (D664 slice 2, session 292, 03-Oct-2026): one line of asset_register.py.

Built from the real file (/root/assetapp/asset_register.py at 6dd5f3ab, as S464 left it). S464's line on the bill page
showed a paper's group on the clinic lane only. Joining pages belongs to every lane but the pharmacy's, so the same
line now also carries a 'join pages' button, on a Dr MK expense, lab or other-document paper too. The button is behind
its own 'is defined' (d664_can_join), so this file with an older clinic_papers.py still renders; nothing else moves. The anchor must be found exactly once.   usage: apply_s465.py <asset_register.py>
"""
import hashlib
import sys

FROM = "6dd5f3abb3aa1e9be801028fdd6e40d2"

OLD = ('''{% if d664_group_label is defined and (b['lane'] or 'clinic')=='clinic' and b['status']!='rejected' %}'''
       '''<b>Group:</b> {{d664_group_label(b) or 'not sorted yet'}} <a class="btn small" href="{{url_for('d664_paper',bid=b['id'],back=(request.script_root or '')~request.path)}}">'''
       '''{{'change' if d664_group_label(b) else 'choose'}}</a><br>{% endif %}\n''')
NEW = ('''{% if d664_group_label is defined and (b['lane'] or 'clinic')!='pharmacy' and b['status']!='rejected' %}'''
       '''{% if (b['lane'] or 'clinic')=='clinic' %}<b>Group:</b> {{d664_group_label(b) or 'not sorted yet'}} <a class="btn small" href="{{url_for('d664_paper',bid=b['id'],back=(request.script_root or '')~request.path)}}">'''
       '''{{'change' if d664_group_label(b) else 'choose'}}</a> {% endif %}'''
       '''{% if d664_can_join is defined %}<a class="btn small" style="margin-left:10px" href="{{url_for('d664_join',bid=b['id'],back=(request.script_root or '')~request.path)}}">join pages</a>{% endif %}<br>{% endif %}\n''')


def apply(src):
    got = src.count(OLD)
    if got != 1:
        raise SystemExit("!! the S464 line on the bill page was found %d time(s), expected 1 - nothing written" % got)
    return src.replace(OLD, NEW)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s465.py <path to asset_register.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("asset_register.py %s -> %s (1 edit; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(out) - len(raw)))


if __name__ == "__main__":
    main()
