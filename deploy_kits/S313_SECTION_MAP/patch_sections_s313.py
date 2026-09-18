#!/usr/bin/env python
"""S313_SECTION_MAP -- the stock_app.py half.  Anchored, idempotent, refuses on
drift.  Adds a read-only owner page and two doors, and changes NOTHING else:

    GET  /finance/stock/page/sections      the review page (owner only)
    GET  /finance/stock/api/sections       seed-if-absent, then the rows
    POST /finance/stock/api/sections/set   the owner moves one item

Nothing in the estate reads stock_item_section yet.  That is deliberate: the
seed may be wrong for a while and it must cost nothing while it is.
"""
import argparse
import hashlib
import os
import shutil
import sys

MARK = "S313_SECTION_MAP"

IMP_OLD = '''# --- S312_CLAIM_QUEUE end ------------------------------------------------

bp = Blueprint("stock", __name__)
'''
IMP_NEW = '''# --- S312_CLAIM_QUEUE end ------------------------------------------------

# --- S313_SECTION_MAP begin (F-528) --------------------------------------
# One stored answer to "which section is this item in".  Four rules in this
# estate answer that question differently today and none of them is stored;
# nothing sectioned can be trusted until one answer exists.  Read-only, and
# read by nothing but its own page -- see section_map.py for why that matters.
PAGE_SECTIONS = os.path.join(HERE, "stock_sections.html")
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import section_map as _sm                              # noqa: PLC0415
    SECTION_MAP_OK = True
except Exception:                                          # pragma: no cover
    _sm = None
    SECTION_MAP_OK = False
# --- S313_SECTION_MAP end ------------------------------------------------

bp = Blueprint("stock", __name__)
'''

ROUTE_OLD = '''def _xlsx_rows(title, note, heads, rows, widths):
    """A one-sheet workbook through padwriter's stdlib writer."""
'''
ROUTE_NEW = '''@bp.route("/page/sections")
def page_sections():
    """S313 (F-528).  THE SECTION MAP -- the owner's page, and read-only to the
    estate.  It exists to be looked at and corrected long before anything
    depends on it: a monthly orthotics round is a promise that these lines were
    counted and those were not, and today four different rules in this codebase
    would name four different sets of lines."""
    from flask import Response, redirect                    # noqa: PLC0415
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return redirect("/finance/stock/page/count", code=302)
    if not SECTION_MAP_OK or not os.path.exists(PAGE_SECTIONS):
        return jsonify(ok=False, error="unavailable", message="The section map is not loaded."), 503
    html = open(PAGE_SECTIONS, encoding="utf-8").read()
    return Response(html, mimetype="text/html",
                    headers={"Cache-Control": "no-store"})


@bp.route("/api/sections")
def api_sections():
    """Seed anything not yet classified, then hand back every row with what
    each of the four rules says about it.  Seeding is insert-only and never
    overwrites the owner's word, so this is safe to call on every load."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="This page is the owner's."), 403
    if not SECTION_MAP_OK:
        return jsonify(ok=False, error="unavailable", message="The section map is not loaded."), 503
    con = _db()
    ensure_schema(con)
    added = kept = 0
    try:
        added, kept = _sm.seed(con, None, (u or {}).get("user") or "seed")
        con.commit()
    except Exception:                                      # noqa: BLE001
        pass
    only = str(request.args.get("disputed") or "").strip() in ("1", "yes", "true")
    rows = _sm.rows(con, only_disputed=only)
    return jsonify(ok=True, sections=list(_sm.SECTIONS), rows=rows,
                   summary=_sm.summary(con), added=added, kept=kept,
                   disputed=sum(1 for r in _sm.rows(con, only_disputed=True, limit=10000)),
                   list_version=_sm.LIST_VERSION)


@bp.route("/api/sections/set", methods=["POST"])
def api_sections_set():
    """The owner's tap: {item, section}.  His word becomes source='owner' and a
    later re-seed never touches it; what the seed had said is kept beside it, so
    the disagreement stays visible instead of being tidied away."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="Only the doctor sets a section."), 403
    if not SECTION_MAP_OK:
        return jsonify(ok=False, error="unavailable", message="The section map is not loaded."), 503
    b = request.get_json(silent=True) or {}
    con = _db()
    ensure_schema(con)
    ok, msg = _sm.set_section(con, str(b.get("item") or ""), str(b.get("section") or ""),
                              (u or {}).get("user") or "")
    if not ok:
        return jsonify(ok=False, error="bad_request", message=msg), 400
    con.commit()
    return jsonify(ok=True, message=msg)


def _xlsx_rows(title, note, heads, rows, widths):
    """A one-sheet workbook through padwriter's stdlib writer."""
'''

EDITS = [("the section_map import", IMP_OLD, IMP_NEW),
         ("the section map's three doors", ROUTE_OLD, ROUTE_NEW)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="frm", default="")
    ap.add_argument("--expect", default="")
    a = ap.parse_args()
    p = a.file
    if not os.path.exists(p):
        print("MISSING %s" % p); return 2
    src = open(p, encoding="utf-8").read()
    cur = hashlib.md5(src.encode("utf-8")).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED -- %s" % cur); return 0
    if a.frm and cur != a.frm:
        print("REFUSED -- live md5 %s, expected %s" % (cur, a.frm)); return 3
    for name, old, new in EDITS:
        n = src.count(old)
        if n != 1:
            print("REFUSED -- anchor '%s' occurs %d times, expected 1" % (name, n)); return 4
        src = src.replace(old, new)
    shutil.copyfile(p, p + ".bak_S313_" + cur[:8])
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)
    got = hashlib.md5(src.encode("utf-8")).hexdigest()
    if a.expect and got != a.expect:
        print("REFUSED AFTER WRITE -- got %s, expected %s" % (got, a.expect)); return 5
    print("PATCHED %s -> %s" % (cur, got))
    return 0


if __name__ == "__main__":
    sys.exit(main())
