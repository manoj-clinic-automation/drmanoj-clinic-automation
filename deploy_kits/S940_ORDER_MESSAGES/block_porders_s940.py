

# ==========================================================================================================================================
# S940_ORDER_MESSAGES (23-Nov-2026, Sanjeevni session 509; D1053) -- order_d1053_msg.py beside this file: his Purchase orders page opens
#  with the day in four steps (sheet in · final · sent · arriving) while the flow is on; the old sheet notice gives way to message A.
#  The messages themselves are made and sent by order_rules' tick (its S940 block). Any fault: the page as before.
# ==========================================================================================================================================
try:
    import order_d1053_msg as _d540                           # noqa: E402
    _d540.install(OS)
    import order_flow as _d540_OF                             # noqa: E402
    _d540_owner_body_before = _d540_OF.owner_body

    def _d540_owner_body(con, now=None, G=None):
        body = _d540_owner_body_before(con, now, G)
        try:
            return _d540.owner_card(con) + body
        except Exception as e:                                # noqa: BLE001 -- the page as before
            print("S940 owner card failed: %r" % (e,), file=sys.stderr)
            return body
    _d540_OF.owner_body = _d540_owner_body
except Exception as _e940:                                    # noqa: BLE001
    print("S940 wraps failed: %r" % (_e940,), file=sys.stderr)
# ---- S940 end ---------------------------------------------------------------------------------------------------------------------------
