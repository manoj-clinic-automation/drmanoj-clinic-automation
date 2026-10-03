#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s466.py -- S466_EXPENSE_WARRANTY (D664 slice 3, session 292, 03-Oct-2026): three exact edits of asset_register.py.

Built from the real file (/root/assetapp/asset_register.py at b0e0915e, as S465 leaves it).
  1+2  the 'Renewals & warranties' page: the Dr MK expense warranties card (clinic_papers.warranty_card) stands above
       'Consumables expiring', and 'Nothing due soon. All clear.' is not said while that card has a row.
  3    the bill page: on a Dr MK expense paper, 'Warranty: ... note it / change' beside S465's 'join pages'.
Each is behind its own 'is defined', so this file with an older clinic_papers.py -- or with none -- renders as before.
/api/due is NOT touched. Every anchor must be found exactly once.   usage: apply_s466.py <asset_register.py>
"""
import hashlib
import sys

FROM = "b0e0915e0b73a6ffb1f4a6e17aec8274"

EDITS = [
    ('''{% if not ordered and not consum %}<p class=muted>Nothing {{'to show.' if show_all else 'due soon. All clear.'}}</p>{% endif %}\n''',
     '''{% set d664w = d664_warranty_card() if d664_warranty_card is defined else '' %}'''
     '''{% if not ordered and not consum and not d664w %}<p class=muted>Nothing {{'to show.' if show_all else 'due soon. All clear.'}}</p>{% endif %}\n'''),
    ('''{% if consum %}<div class=card><h3 style="color:#1f3864">Consumables expiring <span class=muted>({{consum|length}})</span></h3>\n''',
     '''{{ d664w }}\n'''
     '''{% if consum %}<div class=card><h3 style="color:#1f3864">Consumables expiring <span class=muted>({{consum|length}})</span></h3>\n'''),
    ('''{% if d664_can_join is defined %}<a class="btn small" style="margin-left:10px" href="{{url_for('d664_join',bid=b['id'],back=(request.script_root or '')~request.path)}}">join pages</a>{% endif %}<br>{% endif %}\n''',
     '''{% if d664_warranty_label is defined and (b['lane'] or 'clinic')=='owner_expense' %}<b>Warranty:</b> {{d664_warranty_label(b) or 'not noted'}} '''
     '''<a class="btn small" href="{{url_for('d664_paper',bid=b['id'],back=(request.script_root or '')~request.path)}}">{{'change' if d664_warranty_label(b) else 'note it'}}</a> {% endif %}'''
     '''{% if d664_can_join is defined %}<a class="btn small" style="margin-left:10px" href="{{url_for('d664_join',bid=b['id'],back=(request.script_root or '')~request.path)}}">join pages</a>{% endif %}<br>{% endif %}\n'''),
]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s466.py <path to asset_register.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("asset_register.py %s -> %s (%d edits; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
