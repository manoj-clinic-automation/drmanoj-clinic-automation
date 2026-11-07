#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s740.py -- S740_PURCHASE_RETURNS: the appended sections and the owner's routes of the four live files of this project.
    python3 -B make_s740.py <dir holding scan_register.py, amir_day.py, porders_s454.py, purchase_app.py> <out dir> [<dir holding the S740 sections>]
Each FROM file must carry its pinned md5; every anchor must stand EXACTLY ONCE; the TO md5s are printed. The sections are read from
sec_sr740.txt, sec_amir740.txt and sec_p4_740.txt beside this script (or the third argument)."""
import hashlib
import os
import sys

FROM = {"scan_register.py": "f4706186e252d3dc078f039e30ed4e0c",     # S738's TO (live 07-Nov 05:19)
        "amir_day.py": "ff195fc04a57d6b2fb6afaff11ae31cc",          # S738's TO
        "purchase_app.py": "7a0c615efe13d29229d95dcb64b23ecb",      # S738's TO
        "porders_s454.py": "f683b7ed98403b1f6e99a682ad2075a6"}      # S736's TO (the 07-Nov bundle)

ROUTE_OLD = '''# ---- S738 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
'''
ROUTE_NEW = '''# ---- S738 end -----------------------------------------------------------------------------------------------------------------------------


# ---- S740 (07-Nov-2026, Sanjeevni session 399, kit S740_PURCHASE_RETURNS): the owner's own taps on row 8 "Returns" of /page/check -------------
def _s740_owner():
    u, err = _person("checker", "maker", "viewer")
    if err:
        return None, None, err
    if not _is_doctor(u):
        return None, None, _refuse("Only the doctor records or answers a return here.")
    return u, _db(), None


@bp.route("/api/s740/items")
def api_s740_items():
    """For "Record a return": the items bought from one dealer (the last 365 days), each with its last rate and unit. The doctor only. Read only."""
    u, con, err = _s740_owner()
    if err:
        return err
    sup = str(request.args.get("supplier") or "")[:120]
    return jsonify(ok=True, items=_s454_sr().s740_choices(con, sup) if sup else [])


@bp.route("/api/s740/record", methods=["POST"])
def api_s740_record():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ok, msg = _s454_sr().s740_record(con, str(u.get("user") or ""), str(b.get("supplier") or "")[:120], str(b.get("item") or "")[:200], b.get("qty"))
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="refused", message=msg), 400)


@bp.route("/api/s740/flag", methods=["POST"])
def api_s740_flag():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        lid = int(b.get("loss") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_flag_put(con, str(u.get("user") or ""), lid, bool(b.get("yes")))
    return jsonify(ok=True, message=msg) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/cnlook", methods=["POST"])
def api_s740_cnlook():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_cn_look(con, str(u.get("user") or ""), bid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/same", methods=["POST"])
def api_s740_same():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_same_put(con, str(u.get("user") or ""), bid, bool(b.get("same")))
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/withdraw", methods=["POST"])
def api_s740_withdraw():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        oid = int(b.get("id") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_withdraw(con, str(u.get("user") or ""), oid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)


@bp.route("/api/s740/undo", methods=["POST"])
def api_s740_undo():
    u, con, err = _s740_owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    ok, msg = _s454_sr().s740_undo_answer(con, str(u.get("user") or ""), bid)
    return jsonify(ok=True) if ok else (jsonify(ok=False, error="gone", message=msg), 409)
# ---- S740 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


FROM_FULL = {}


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    sd, od = sys.argv[1], sys.argv[2]
    secd = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    src = {}
    for n, pin in FROM.items():
        b = open(os.path.join(sd, n), "rb").read()
        full = FROM_FULL.get(n, pin)
        if md5(b) != full:
            sys.exit("REFUSED: %s is %s, not the pinned %s" % (n, md5(b)[:8], full[:8]))
        src[n] = b.decode("utf-8")
    out = {}
    for n, sec in (("scan_register.py", "sec_sr740.txt"), ("amir_day.py", "sec_amir740.txt"), ("porders_s454.py", "sec_p4_740.txt")):
        if not src[n].endswith("\n"):
            sys.exit("REFUSED: %s does not end in a newline" % n)
        out[n] = src[n] + open(os.path.join(secd, sec), encoding="utf-8").read()
    pa = src["purchase_app.py"]
    if pa.count(ROUTE_OLD) != 1:
        sys.exit("REFUSED: purchase_app.py anchor found %d times (must be once)" % pa.count(ROUTE_OLD))
    out["purchase_app.py"] = pa.replace(ROUTE_OLD, ROUTE_NEW)
    os.makedirs(od, exist_ok=True)
    for n in ("scan_register.py", "amir_day.py", "porders_s454.py", "purchase_app.py"):
        b = out[n].encode("utf-8")
        open(os.path.join(od, n), "wb").write(b)
        print("%s  %s -> %s" % (n, FROM_FULL.get(n, FROM[n])[:8], md5(b)))


if __name__ == "__main__":
    main()
