

# ==========================================================================================================================================
# S941_ORDER_ADDINS (23-Nov-2026, Sanjeevni session 509; the owner's "YES FOR ALL" 20:01 IST) -- order_d1053_msg.py v1.1 beside this file.
#  The wrong-bill page GET /finance/porders/d1053/bill/<scan> (the doctor in English, Darpan in his script): each line the order did not
#  carry, or more than ordered, Keep / Send back (two taps). POST /finance/porders/api/d1053/bill {id, act}: keep | back -- the doctor or
#  Darpan (order.d1053_msg_darpan); returned -- any sender, on a 'back' line. Reception's order screen lists the lines to send back with
#  "Wapas kar diya". The messages E-H are made by order_rules' tick. Any fault: the screen as before.
# ==========================================================================================================================================
def _d541():
    import order_d1053_msg                                    # noqa: PLC0415 -- beside this file
    return order_d1053_msg


def d1053_bill_page(scan):
    u, con, kind, login, err = _auth_page()
    if err:
        return err
    en = u["_en"]
    try:
        body = _d541().bill_page_body(con, int(scan), en)
    except Exception as e:                                    # noqa: BLE001
        print("S941 bill page failed: %r" % (e,), file=sys.stderr)
        body = '<div class="err">%s</div>' % esc("This page could not be read just now." if en else "यह पेज अभी नहीं खुला।")
    return shell(con, u, "Wrong bill" if en else "गलत बिल", body, back=(P + "/flow") if en else "/finance/darpan/kal#order", login=login)


bp.add_url_rule(P + "/d1053/bill/<int:scan>", "d1053_bill_page", d1053_bill_page)


@bp.route(P + "/api/d1053/bill", methods=["POST"])
def api_d1053_bill():
    u, con, kind, err = _auth_api()
    if err:
        return err
    b = _body()
    act = str(b.get("act") or "")
    try:
        M = _d541()
        if act in ("keep", "back") and kind != "owner" and str(u.get("login") or u.get("user") or "").lower() not in M.to_darpan(con):
            return jsonify(ok=False, error="darpan_only", message="Iska faisla Darpan karenge."), 403
        body, code = M.bill_answer(con, who(u), int(b.get("id") or 0), act)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    except Exception as e:                                    # noqa: BLE001
        print("S941 bill door failed: %r" % (e,), file=sys.stderr)
        return jsonify(ok=False, error="unavailable"), 503
    return jsonify(**body), code


_d541_order_list_before = order_list


def order_list():                                             # noqa: F811 -- S941: the lines to send back, on reception's screen
    r = _d541_order_list_before()
    try:
        if isinstance(r, tuple) and r[1] == 200 and S778_MARK in r[0]:
            con = _po()._db()
            en = "lang=\"en\"" in r[0][:200]
            add = _d541().returns_html(con, en)
            if add:
                r = (r[0].replace(S778_MARK, S778_MARK + add, 1),) + tuple(r[1:])
    except Exception as e:                                    # noqa: BLE001 -- the page stands as it was
        print("S941 order list failed: %r" % (e,), file=sys.stderr)
    return r
# ---- S941 end ---------------------------------------------------------------------------------------------------------------------------
