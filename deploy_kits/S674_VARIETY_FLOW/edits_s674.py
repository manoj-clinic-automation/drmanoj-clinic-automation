#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""edits_s674.py -- the build record of S674_VARIETY_FLOW: the exact, counted edits that turn stationery.py b6ce217a (S585's,
confirmed by every bundle since 23-Oct) into the kit's whole stationery.py. The large additive block (the flow's functions, pages
and routes) is s674_block.py, inserted whole before the mount. Each old text must occur exactly once.
    python3 -B edits_s674.py <stationery.py FROM> <stationery.py TO>
    python3 -B edits_s674.py --desk <sorting_desk.py FROM> <sorting_desk.py TO>     (its one edit)
"""
import hashlib
import os
import sys

FROM_PIN = "b6ce217a4201d89306f90b24d25f0e72"
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = open(os.path.join(HERE, "s674_block.py"), encoding="utf-8").read()

E = []
# E1 -- the version and the flask imports the pages need
E.append(('VERSION = "S568"\n', 'VERSION = "S674"               # S674_VARIETY_FLOW (D797): the Variety flow on this page -- S568/S585 whole, plus the block below\n'))
E.append(("from flask import abort, flash, g, redirect, request, send_file, url_for\n" if False else "from flask import abort, flash, g, redirect, request, url_for\n",
          "from flask import abort, flash, g, redirect, render_template_string, request, url_for\nfrom markupsafe import Markup\n"))
# E2 -- ensure(): the S674 tables and columns, after S568's
E.append(("""    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    db.commit()
""", """    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    ensure_s674(db)                                                  # S674: the statement table; side and stmt_id on stationery_line
    db.commit()
"""))
# E3 -- the stock counts clinic lines only (an NK line never feeds the clinic's stock)
E.append(('''    return "l.voided_at='' AND l.item_id IS NOT NULL AND l.not_stock=0 AND l.qty IS NOT NULL AND " + _paper_sql(db, "b")
''', '''    return "l.voided_at='' AND l.item_id IS NOT NULL AND l.not_stock=0 AND l.qty IS NOT NULL AND COALESCE(l.side,'clinic')='clinic' AND " + _paper_sql(db, "b")      # S674
'''))
# E4 -- save_lines: a line's side (the desk never sends one: clinic); a paper on a statement is never re-saved
E.append(("""        if sel == "ns":
            new.append((no, name, q, unit, rate, None, 1))
            continue
""", """        side = "nk" if str(x.get("side") or "").strip() == "nk" else "clinic"            # S674: the desk sends none -> clinic
        if sel == "ns":
            new.append((no, name, q, unit, rate, None, 1, side))
            continue
"""))
E.append(("""        new.append((no, name, q, unit, rate, iid, 0))
    old = saved_lines(db, b)
    oldk = sorted(_key_of((l["line_no"], l["name"], l["qty"], l["unit"], l["rate"], l["item_id"], l["not_stock"])) for l in old)
    newk = sorted(_key_of(t) for t in new)
""", """        new.append((no, name, q, unit, rate, iid, 0, side))
    old = saved_lines(db, b)
    if any((l["stmt_id"] if "stmt_id" in l.keys() else None) for l in old):                 # S674: on a statement -- never counted twice
        raise ValueError("%s is on a statement — its lines are changed from the statement, not here." % ((b["stamp_no"] or "").strip() or ("#%d" % b["id"])))
    oldk = sorted(_key_of((l["line_no"], l["name"], l["qty"], l["unit"], l["rate"], l["item_id"], l["not_stock"], (l["side"] if "side" in l.keys() else "clinic"))) for l in old)
    newk = sorted(_key_of(t) for t in new)
"""))
E.append(("""def _key_of(t):
    no, name, q, unit, rate, iid, ns = t
    return (no, name, "" if q is None else "%.4f" % q, unit, "" if rate is None else "%.4f" % rate, iid or 0, ns)
""", """def _key_of(t):
    no, name, q, unit, rate, iid, ns = t[:7]
    side = t[7] if len(t) > 7 else "clinic"                          # S674
    return (no, name, "" if q is None else "%.4f" % q, unit, "" if rate is None else "%.4f" % rate, iid or 0, ns, side)
"""))
E.append(("""    for no, name, q, unit, rate, iid, ns in sorted(new):
        db.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at) "
                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (b["id"], b["created_at"] or "", no, name, q, unit, rate, iid, ns, day, ts, who, now))
""", """    for no, name, q, unit, rate, iid, ns, side in sorted(new):
        db.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at, side) "
                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (b["id"], b["created_at"] or "", no, name, q, unit, rate, iid, ns, day, ts, who, now, side))
"""))
E.append(("""    nm = len([t for t in new if t[5]])
""", """    nm = len([t for t in new if t[5] and t[7] == "clinic"])           # S674: the stock's lines are the clinic's
    nk = len([t for t in new if t[5] and t[7] == "nk"])
"""))
E.append(("""    msg = ("Stationery: %d line%s matched" % (nm, "" if nm == 1 else "s")) + (" (%d new on the list)" % made if made else "")
    if nm:
        msg += " — into the stock." if ok else " — not added to the stock: %s." % why
    else:
        msg += "."
""", """    msg = ("Stationery: %d line%s matched" % (nm, "" if nm == 1 else "s")) + (" (%d new on the list)" % made if made else "")
    if nm:
        msg += " — into the stock." if ok else " — not added to the stock: %s." % why
    else:
        msg += "."
    if nk:
        msg += " %d line%s to NK Pathology's ledger (not the clinic's stock)." % (nk, "" if nk == 1 else "s")       # S674
"""))
# E4b -- void_lines: a line on a statement is never voided (the desk's re-save to another group would bill it again)
E.append(("""    \"\"\"The paper's live lines voided (kept) -- a re-save that takes it out of Stationery & packaging. No commit.\"\"\"
    n = db.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",""", """    \"\"\"The paper's live lines voided (kept) -- a re-save that takes it out of Stationery & packaging. No commit.
    S674: a line on a statement is never voided from here (it would be billed again) -- refused with the words.\"\"\"
    try:
        if db.execute("SELECT 1 FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' AND stmt_id IS NOT NULL LIMIT 1",
                      (b["id"], b["created_at"] or "")).fetchone():
            raise ValueError("%s is on a supplier statement — its lines stay; withdraw the statement first (Stationery, section 5)." % ((b["stamp_no"] or "").strip() or ("#%d" % b["id"])))
    except sqlite3.OperationalError:
        pass                                                         # no stmt_id column yet (before the first mount): nothing is on a statement
    n = db.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''","""))
# E5 -- the owner's page: the flow's sections above the stock table and below the papers that fed it
E.append(("""<div class=card id=s568mixed>""", """{{flow_top}}
<div class="card s674" id=s674stockhead><b>3 · Clinic stock — the stock book</b> <span class=muted>— received · issued · in stock · counts · the item list, as before.</span></div>
<div class=card id=s568mixed>"""))
E.append(("""<div class=card id=s568items>""", """{{flow_bottom}}
<div class=card id=s568items>"""))
E.append(("""    inv = inventory(db, ym)
    return AR.page(STOCK_TPL, inv=inv, label=AR._month_label(ym), places=PLACES, units=UNITS, q=lambda x: _plain(x) if x is not None else "—",
                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]), many=many_on(db),
""", """    inv = inventory(db, ym)
    ctx = flow_ctx(db, ym)                                           # S674
    return AR.page(STOCK_TPL, inv=inv, label=AR._month_label(ym), places=PLACES, units=UNITS, q=lambda x: _plain(x) if x is not None else "—",
                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]), many=many_on(db),
                   flow_top=flow_top(db, ym, ctx), flow_bottom=flow_bottom(db, ym, ctx),
"""))
# E6 -- the menu: Shavez's sort screen while his desk is on
E.append(("""        if role == "manager" and issue_on(AR.get_db()):
            return [("s568_issue", "Stationery diya", url_for("s568_issue"))]
""", """        if role == "manager":
            out = menu_items_s674(role, AR.get_db())                     # S674
            if issue_on(AR.get_db()):
                out.append(("s568_issue", "Stationery diya", url_for("s568_issue")))
            return out
"""))
# E7 -- the block, before the mount; the routes, in init()
E.append(("""# ---------------------------------------------------------------------------------------------- the mount
def init(ar):""", BLOCK.rstrip("\n") + """


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):"""))
E.append(("""    app.add_url_rule("/stationery/void", "s585_void", ar.owner_required(void_post), methods=["POST"])                # S585
    MOUNTED = True
""", """    app.add_url_rule("/stationery/void", "s585_void", ar.owner_required(void_post), methods=["POST"])                # S585
    app.add_url_rule("/stationery/sort", "s674_sort", ar.checker_required(staff_sort_page))                            # S674
    app.add_url_rule("/stationery/sort/save", "s674_sort_save", ar.checker_required(sort_save_post), methods=["POST"])
    app.add_url_rule("/stationery/supplier", "s674_supplier", ar.owner_required(supplier_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/make", "s674_stmt_make", ar.owner_required(stmt_make_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/sent", "s674_stmt_sent", ar.owner_required(stmt_sent_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/void", "s674_stmt_void", ar.owner_required(stmt_void_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/join", "s674_stmt_join", ar.owner_required(stmt_join_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/paid", "s674_stmt_paid", ar.owner_required(stmt_paid_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/<int:sid>", "s674_stmt_view", ar.owner_required(stmt_view))
    app.add_url_rule("/stationery/leave", "s674_leave", ar.owner_required(leave_post), methods=["POST"])
    MOUNTED = True
"""))


# ---- sorting_desk.py (bb206e5d): ONE edit -- the desk's waiting list leaves a listed supplier's paper to the Stationery page
FROM_PIN_DESK = "bb206e5dfcc6bb0dff71524b68e33f5f"
E_DESK = [("""        if sg == PATIENT:                             # FIX1 C2: a patient's paper is in Kept apart only (Open B-____ still opens it)
            continue
""", """        if sg == PATIENT:                             # FIX1 C2: a patient's paper is in Kept apart only (Open B-____ still opens it)
            continue
        if _s674_listed(db, b):                       # S674: a listed supplier's paper is sorted on the Stationery page, never here
            continue
"""),
          ("""    st = _s568_st()
    if st is None:
        return msgs
    b = _row(db, bid)
    if dest == "stationery" and (b["subgroup"] or "") == "stationery":""", """    st = _s568_st()
    if st is None:
        return msgs
    b = _row(db, bid)
    if hasattr(st, "is_goods") and _s674_listed(db, b) and st.is_goods(b):        # S674: a listed supplier's challan is sorted on the Stationery page
        if "st_lines" in p:
            raise DeskError("%s is %s's — its lines are sorted on the Stationery page, not here. Nothing was saved." % (_stamp(b), b["vendor"]))
    if dest == "stationery" and (b["subgroup"] or "") == "stationery":"""),
          ("""    elif st.has_lines(db, b):
        st.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        msgs.append("Its stationery lines are taken off the stock (it is no longer in Stationery & packaging).")""", """    elif st.has_lines(db, b):
        try:
            st.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        except ValueError as e:                                      # S674: lines on a supplier statement stay
            raise DeskError(str(e) + " Nothing was saved.")
        msgs.append("Its stationery lines are taken off the stock (it is no longer in Stationery & packaging).")"""),
          ("""def _s568_st():
    \"\"\"stationery.py, when it is mounted; else None (the panel and its lines then give nothing).\"\"\"
""", """def _s674_listed(db, b):
    \"\"\"S674: is this paper a listed stationery supplier's (the Stationery page sorts it)? False when stationery.py is not mounted.\"\"\"
    st = _s568_st()
    try:
        return st is not None and bool(st.is_listed(db, b["vendor"]))
    except Exception:                                                # noqa: BLE001
        return False


def _s568_st():
    \"\"\"stationery.py, when it is mounted; else None (the panel and its lines then give nothing).\"\"\"
""")]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build_desk(src, dst, out=print):
    raw = open(src, "rb").read()
    if md5(raw) != FROM_PIN_DESK:
        out("sorting_desk.py: FROM is %s, not the pin %s -- STOP" % (md5(raw)[:8], FROM_PIN_DESK[:8]))
        return 1
    t = raw.decode("utf-8")
    for n, (a, b) in enumerate(E_DESK, 1):
        k = t.count(a)
        if k != 1:
            out("sorting_desk.py D%d: its old text occurs %d times, not once -- STOP" % (n, k))
            return 1
        t = t.replace(a, b)
    open(dst, "wb").write(t.encode("utf-8"))
    out("sorting_desk.py: %d counted edits, FROM %s -> TO %s" % (len(E_DESK), FROM_PIN_DESK[:8], md5(t.encode("utf-8"))))
    return 0


def build(src, dst, out=print):
    raw = open(src, "rb").read()
    if md5(raw) != FROM_PIN:
        out("FROM is %s, not the pin %s -- STOP" % (md5(raw)[:8], FROM_PIN[:8]))
        return 1
    t = raw.decode("utf-8")
    for n, (a, b) in enumerate(E, 1):
        k = t.count(a)
        if k != 1:
            out("E%d: its old text occurs %d times, not once -- STOP" % (n, k))
            return 1
        t = t.replace(a, b)
    open(dst, "wb").write(t.encode("utf-8"))
    out("stationery.py: %d counted edits, FROM %s -> TO %s" % (len(E), FROM_PIN[:8], md5(t.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--desk":
        sys.exit(build_desk(sys.argv[2], sys.argv[3]))
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
