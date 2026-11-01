#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s696.py -- S696_MONTH_CONSOLE: the six counted edits to /root/finance/owner_console.py (FROM e414e7ad9e683b5e7ecabff5e481c721,
= the 31-Oct 21:43 bundle and the S374 pin list). The installer re-runs THIS script on the box's live file and the result must
hash to TO_PINS.md5; a drifted live file (any anchor missing or not unique) stops it with nothing written (F-472).

usage: python3 make_s696.py <owner_console.py in> <owner_console.py out>
The edits:
  1  VERSION "S542 1.3" -> "S696 1.4"
  2  MONTH_PAGE beside PAGE (the month page's file, beside this module)
  3  two routes in init(): GET /finance/console/month (the page) and GET /finance/console/api/month (the reading)
  4  sec_month() before ORDER, and ("month", sec_month) in ORDER after "needs"
  5  "month": "The month" in the failed-section name map
  6  month=cx.get("month") in the snapshot
"""
import hashlib
import sys

FROM = "e414e7ad9e683b5e7ecabff5e481c721"


def once(text, anchor):
    n = text.count(anchor)
    if n != 1:
        raise SystemExit("ANCHOR %s: found %d times, need exactly 1 -- the live file drifted; nothing written" % (anchor[:60].replace("\n", "\\n"), n))


EDITS = [
    # 1
    ('VERSION = "S542 1.3"\n',
     'VERSION = "S696 1.4"\n'
     '# S696 (01-Nov-2026, the parent, S376; the owner\'s "Build now" 18:01 IST on the mock-up): THE MONTH -- one more section of the\n'
     '# reading ("The month": the month just ended and the running one, where each stands, his actions) and its own page\n'
     '# /finance/console/month, filled from /finance/console/api/month. The reading is month_read.py\'s, made inside this builder on\n'
     '# the copy like every other section; the page is month_page.html beside this file. Nothing new is written anywhere.\n'),
    # 2
    ('PAGE = os.path.join(FIN, "owner_console.html")\n',
     'PAGE = os.path.join(FIN, "owner_console.html")\n'
     'MONTH_PAGE = os.path.join(FIN, "month_page.html")   # S696: the owner\'s page "The month"\n'),
    # 3
    ('    app.register_blueprint(bp)\n',
     '    @bp.route("/finance/console/month")\n'
     '    def console_month_page():                                      # S696: the owner\'s page "The month" (his login alone)\n'
     '        _u, err = _gate()\n'
     '        if err:\n'
     '            return Response(DENIED, status=403, mimetype="text/html")\n'
     '        try:\n'
     '            with open(MONTH_PAGE, encoding="utf-8") as fh:\n'
     '                html = fh.read()\n'
     '        except OSError as e:\n'
     '            return Response("The month page\'s file could not be read (%s)." % e, status=500, mimetype="text/plain")\n'
     '        r = Response(html, mimetype="text/html")\n'
     '        r.headers["Cache-Control"] = "no-store"\n'
     '        return r\n'
     '\n'
     '    @bp.route("/finance/console/api/month")\n'
     '    def console_month():                                           # S696: the month reading, from the same snapshot as the console\n'
     '        _u, err = _gate()\n'
     '        if err:\n'
     '            return err\n'
     '        snap, age, stale, building, berr = _state(request.args.get("refresh") == "1")\n'
     '        s = snap or {}\n'
     '        r = jsonify(ok=True, month=s.get("month"), as_of_label=_label(snap), as_of=s.get("as_of"), age_s=age, stale=stale,\n'
     '                    building=building, build_error=berr, failed=s.get("failed"), max_age_s=MAX_AGE, version=VERSION)\n'
     '        r.headers["Cache-Control"] = "no-store"\n'
     '        return r\n'
     '\n'
     '    app.register_blueprint(bp)\n'),
    # 4
    ('ORDER = (("needs", sec_needs), ("money", sec_money), ("work", sec_work), ("att", sec_att), ("sanj", sec_sanj),\n',
     'def sec_month(con, cx):\n'
     '    """S696: THE MONTH -- the month just ended and the running one, as month_read.py reads them on the copy. The whole reading\n'
     '    is kept in the snapshot (snap["month"]) for the page /finance/console/month; this section shows its first lines."""\n'
     '    import month_read as MR                                        # noqa: PLC0415 -- beside this file\n'
     '    r = MR.read(con, dict(register=REGISTER_DB, assets=ASSETS_DB), cx["now"])\n'
     '    cx["month"] = r\n'
     '    ended = r["months"][0]\n'
     '    s = ended["summary"]\n'
     '    yours = s["yours"]\n'
     '    chip = ("%d need you" % yours) if yours else ("pack sent" if s["pack_sent"] else "read")\n'
     '    cls = "b" if s["pack_late"] else ("w" if yours else "g")\n'
     '    word = "%s: %d of %d done" % (ended["label"].split(" ")[0], s["done"], s["n"])\n'
     '    lines = MR.section_lines(r)\n'
     '    lines.append(dict(dot="n", text="The whole month, every head and every line, on one page", href="/finance/console/month", link="the month", sub=True))\n'
     '    return dict(ok=True, name="The month", chip=chip, cls=cls, word=word, lines=lines)\n'
     '\n'
     '\n'
     'ORDER = (("needs", sec_needs), ("month", sec_month), ("money", sec_money), ("work", sec_work), ("att", sec_att), ("sanj", sec_sanj),\n'),
    # 5
    ('"sanj": "Sanjeevni", "papers": "Scans & papers", "system": "System"}[key],\n',
     '"sanj": "Sanjeevni", "papers": "Scans & papers", "system": "System", "month": "The month"}[key],\n'),
    # 6
    ('sanj_day=cx["sanj_day"], lwd=cx["lwd"], order=[k for k, _f in ORDER], sections=sections, tile=T, failed=failed,\n',
     'sanj_day=cx["sanj_day"], lwd=cx["lwd"], order=[k for k, _f in ORDER], sections=sections, tile=T, failed=failed,\n'
     '                    month=cx.get("month"),                                      # S696: the month reading, whole, for its page\n'),
]


def main(src, dst):
    raw = open(src, "rb").read()
    h = hashlib.md5(raw).hexdigest()
    if h != FROM:
        raise SystemExit("FROM: %s is %s, not %s -- nothing written" % (src, h, FROM))
    text = raw.decode("utf-8")
    for a, b in EDITS:
        once(text, a)
        text = text.replace(a, b, 1)
    with open(dst, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("make_s696: %d edits; %s -> %s" % (len(EDITS), h[:8], hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
