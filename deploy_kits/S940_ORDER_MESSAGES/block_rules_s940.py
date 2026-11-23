# ---- S940_ORDER_MESSAGES (23-Nov-2026, Sanjeevni session 509; D1053) ----------------------------------------------------------------------
#  The tick makes and sends the purchase order flow's messages (order_d1053_msg.tick: A sheet in, B final, C sent, D each delivery) after
#  S454's pass, and the old sheet notice gives way to A while the flow is on (order_d1053_msg.install). Any fault: the tick as before.
_s940_s454_pass_before = _s454_pass


def _s454_pass(con):                                         # noqa: F811 -- S940
    try:
        import order_d1053_msg                               # noqa: PLC0415 -- beside this file
        order_d1053_msg.install()
    except Exception as e:                                   # noqa: BLE001
        print("S940 install failed: %r" % (e,), file=sys.stderr)
    out = _s940_s454_pass_before(con)
    try:
        import order_d1053_msg                               # noqa: PLC0415
        r = order_d1053_msg.tick(con)
        if isinstance(out, dict):
            out["d1053"] = r
    except Exception as e:                                   # noqa: BLE001
        if isinstance(out, dict):
            out["d1053"] = "error: %s" % str(e)[:80]
    return out
# ---- S940 end ---------------------------------------------------------------------------------------------------------------------------


