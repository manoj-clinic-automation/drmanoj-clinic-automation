#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""apply_s365.py -- kit S365_DAY_PANEL (Sanjeevni, session 280, 21-Sep-2026).

The approvals page's day panel, as the owner asked on 21-Sep ("simple, human readable, expandable
... which sale returns were there, what were the sales"): Sale -> returns -> UPI -> without cash ->
cash received -> where it went, every line opening to its bills and every bill to its medicines.
  /root/finance/darpan_kal.py  FROM 63c70749 (S363): its init() also mounts sanjeevni_day's blueprint.
  /root/finance/finance_ui/finance_approvals.html (THE PARENT'S -- DECLARED) FROM 5b6ecceb (S363):
      dayDetail() reads /finance/sanjeevni/api/day/<d>; the old panel stays as dayDetailOld().
    python3 apply_s365.py --dir /root/finance               # in place (backups .bak_S365_<from8>)
    python3 apply_s365.py --dir DIR --out OUTDIR            # patched copies (the walk)
"""
import argparse, hashlib, os, shutil

FROM = {"darpan_kal.py": "63c707499efc2a370df65d3f219ce6a5",
        "finance_ui/finance_approvals.html": "5b6ecceb0a78ea0c9b16040f2f4a5496"}
EDITS = {
 "darpan_kal.py": [(
  "    _db, _require, _unit = db_getter, require_fn, unit\n    app.register_blueprint(bp)\n    return bp\n",
  "    _db, _require, _unit = db_getter, require_fn, unit\n    app.register_blueprint(bp)\n"
  "    try:                                           # S365: the owner's day panel (sanjeevni_day.py)\n"
  "        import sanjeevni_day\n"
  "        sanjeevni_day.init(app, db_getter, require_fn, unit)\n"
  "    except Exception as ex:                        # noqa: BLE001 -- the page falls back to the old panel\n"
  "        print(\"sanjeevni_day not mounted: %s\" % ex)\n"
  "    return bp\n")],
 "finance_ui/finance_approvals.html": [(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_old.txt"), encoding="utf-8").read(),
                                        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "a_new.txt"), encoding="utf-8").read())],
}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    new = {}
    for f, edits in EDITS.items():
        p = os.path.join(a.dir, f)
        if not os.path.isfile(p) or md5(p) != FROM[f]:
            raise SystemExit("!! %s is not its FROM pin %s -- nothing touched" % (p, FROM[f][:8]))
        t = open(p, encoding="utf-8").read()
        for old, nw in edits:
            if t.count(old) != 1:
                raise SystemExit("!! %s: anchor occurs %d times -- nothing touched" % (f, t.count(old)))
            t = t.replace(old, nw)
        new[f] = t
    out = a.out or a.dir
    for f, t in new.items():
        dst = os.path.join(out, f); os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not a.out:
            shutil.copy2(os.path.join(a.dir, f), "%s.bak_S365_%s" % (os.path.join(a.dir, f), FROM[f][:8]))
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t)
        print("   %s %s -> %s" % (f, FROM[f][:8], md5(dst)))
    print("APPLIED")


if __name__ == "__main__":
    main()
