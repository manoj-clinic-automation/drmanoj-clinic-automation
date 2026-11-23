


# ---- S939_ORDER_FINAL (23-Nov-2026, Sanjeevni session 509; D1053, mock-up "Mockup okay" 18:52 IST) -----------------------------------------
#  On order.source = marg_sheet with setting order.d1053 = 1 the order tab is THE ONE LIST (F-1624): the payload carries `d1053`
#  (order_d1053.darpan_payload -- the Marg sheet's cards as reception orders them, the old-line questions, reception's raises, the
#  final, the sent record) and no engine proposals beside it. POST /finance/darpan/kal/api/order/d1053 {do: decide | final, ...}:
#  staff or owner, as the tab; answers with the tab's payload. Any fault: the tab exactly as before this kit.
_d53_payload_before = _s485_payload


def _s485_payload(con, who):                                 # noqa: F811 -- S939
    out = _d53_payload_before(con, who)
    try:
        import order_d1053                                    # noqa: PLC0415 -- beside this file
        if order_d1053.live(con):
            out = dict(out, d1053=order_d1053.darpan_payload(con), suppliers=[], n_suppliers=0, n_lines=0, order_day_names=[], all_pakka=False,
                       editable=False)
    except Exception as e:                                   # noqa: BLE001 -- the tab as before
        print("S939 darpan payload failed: %r" % (e,), file=sys.stderr)
    return out


@bp.route("/finance/darpan/kal/api/order/d1053", methods=["POST"])
def api_s939_d1053():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    try:
        import order_d1053                                    # noqa: PLC0415
        OR = _s485_or()
        if OR._frozen(con):
            return jsonify(ok=False, error="frozen", message="दवा का ऑर्डर अभी बंद है"), 423
        if not order_d1053.live(con):
            return jsonify(ok=False, error="off", message="यह अभी बंद है"), 409
        b = request.get_json(silent=True) or {}
        do = str(b.get("do") or "")
        if do == "decide":
            body, code = order_d1053.decide(con, u["user"], b)
        elif do == "final":
            body, code = order_d1053.make_final(con, u["user"])
        else:
            return jsonify(ok=False, error="bad_do"), 400
    except Exception as e:                                   # noqa: BLE001
        print("S939 d1053 door failed: %r" % (e,), file=sys.stderr)
        return jsonify(ok=False, error="unavailable", message="अभी नहीं हुआ — थोड़ी देर में फिर"), 503
    if code != 200:
        return jsonify(**body), code
    return jsonify(**dict(_s485_payload(con, who), d1053_done=body))
# ---- S939 end ---------------------------------------------------------------------------------------------------------------------------
