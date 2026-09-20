#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""apply_kal_s357.py -- S357_DAY_TRUTH_3: Darpan's page reads the day's cash adjustment.

The owner's ruling (20-Sep-2026): a credit note on a home / procedure medicine
bill is bookkeeping -- goods came back, no cash moved.  day_resync.py puts the
amount back to the drawer as one cash_adjustment row; the ledger's own +/-
column already counts it.  Darpan's page computed its expected cash from its
own sources and never read that column, so the two would disagree by exactly
that amount.  Two anchored edits:

  darpan_kal.py  (FROM 28e23b15daae7f92d4ea668fb5a06b77, S243)
      compute_day: out["adjust_p"] = the day's cash_adjustment sum (fail-soft),
      and expected_p += adjust_p.
  darpan_kal.html (FROM e62746d86e349a143179b320f9d6a87f, S243)
      one row in the Hindi card and one in the owner's English card, shown only
      when adjust_p != 0.

    python3 apply_kal_s357.py --dir /root/finance            # apply (backups .bak_S357_<from8>)
    python3 apply_kal_s357.py --dir DIR --out OUTDIR          # write patched copies elsewhere (the walk)
Prints FROM -> TO for each file; exits 1 on any anchor or pin mismatch, touching nothing.
"""
import argparse
import hashlib
import os
import shutil
import sys

PY_FROM = "28e23b15daae7f92d4ea668fb5a06b77"
HTML_FROM = "e62746d86e349a143179b320f9d6a87f"

PY_EDITS = [
    ("""    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"]
    return out
""",
     """    # S357 -- the ledger's own +/- column: a credit note on a home / procedure bill is put
    # back to the drawer there by day_resync (goods returned, no cash; the owner, 20-Sep).
    out["adjust_p"] = 0
    if _has(con, "cash_adjustment"):
        try:
            r = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM cash_adjustment WHERE day_entry_id=?",
                            (e["id"],)).fetchone()
            out["adjust_p"] = int(r[0] or 0)
        except sqlite3.OperationalError:
            out["adjust_p"] = 0
    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"] + out["adjust_p"]
    return out
"""),
    ("""               home_p=0, proc_p=0, online_p=0, online_provisional=1, statement_in=False,
""",
     """               home_p=0, proc_p=0, online_p=0, online_provisional=1, statement_in=False, adjust_p=0,
"""),
]

HTML_EDITS = [
    ("""   '<div class="row tot"><span class="k">= इतना cash होना चाहिए</span><span class="v">'+R(c.expected_p)+'</span></div>');
""",
     """   (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' सुधार (घर / प्रोसीजर की दवा वापस — cash नहीं)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+
   '<div class="row tot"><span class="k">= इतना cash होना चाहिए</span><span class="v">'+R(c.expected_p)+'</span></div>');
"""),
    ("""  '<div class="row tot"><span class="k">= expected cash</span><span class="v">'+R(c.expected_p)+'</span></div>'+
""",
     """  (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' adjustment (home / procedure medicine returned, no cash)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+
  '<div class="row tot"><span class="k">= expected cash</span><span class="v">'+R(c.expected_p)+'</span></div>'+
"""),
]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def patch(text, edits, name):
    for old, new in edits:
        if text.count(old) != 1:
            raise SystemExit("!! %s: anchor found %d times, expected 1 -- nothing written" % (name, text.count(old)))
        text = text.replace(old, new, 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default=None, help="write patched copies here instead of in place")
    a = ap.parse_args()
    py, html = os.path.join(a.dir, "darpan_kal.py"), os.path.join(a.dir, "darpan_kal.html")
    for p, want in ((py, PY_FROM), (html, HTML_FROM)):
        if not os.path.exists(p):
            raise SystemExit("!! missing %s" % p)
        got = md5(p)
        if got != want:
            if a.out is None and os.path.exists(p + ".bak_S357_" + want[:8]):
                print("-- %s already patched (backup present); left alone" % os.path.basename(p))
                continue
            raise SystemExit("!! %s is %s, not the pin %s -- nothing written" % (os.path.basename(p), got, want))
    outs = {}
    for p, edits, want in ((py, PY_EDITS, PY_FROM), (html, HTML_EDITS, HTML_FROM)):
        if md5(p) != want:
            continue
        text = open(p, encoding="utf-8").read()
        new = patch(text, edits, os.path.basename(p))
        dest = os.path.join(a.out, os.path.basename(p)) if a.out else p
        if a.out:
            os.makedirs(a.out, exist_ok=True)
        else:
            shutil.copy2(p, p + ".bak_S357_" + want[:8])
        with open(dest, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        outs[os.path.basename(p)] = md5(dest)
        print("%s  %s -> %s" % (os.path.basename(p), want[:8], outs[os.path.basename(p)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
