

# ---- S973 (27-Nov-2026, Sanjeevni session 540, kit S973_VOUCHER_SCANS; kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4) --------------------
#  THE CUT-NAME ROUTE AHEAD OF THE REGISTER: a cut name that fits several items asks the voucher's PRINT first (voucher_scan.cut_asks -- a
#  print card on Amir's page, for vouchers dated on or after stock.scan_ask_from); Marg's one-item Stock Register is asked only when no
#  print ask is open for that voucher (it closed unclear, or with no scan in the question days) -- plan 2.4. A name the scan settled is
#  told 'the voucher's scan' (marg_lines above). Everything else in the judge is unchanged.
import sys as _s973_sys
KIT_S973 = "S973_VOUCHER_SCANS"
VERSION = "1.4"
_ask_registers_before_s973 = ask_registers


def ask_registers(con, who="voucher check"):                 # noqa: F811 -- S973: the print first; the register only when no print ask is open
    try:
        import voucher_scan as VS                             # noqa: PLC0415 -- beside this file
    except Exception:                                         # noqa: BLE001
        return _ask_registers_before_s973(con, who)
    try:
        if VS.on(con) and not con.in_transaction:
            VS.cut_asks(con)
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_judge S973: cut asks stopped: %s" % str(ex)[:200], file=_s973_sys.stderr)
    n = 0
    try:
        L = [x for x in marg_lines(con) if x.get("ambiguous") and not VS.scan_open(con, x["kind"], x["no"], x["day"])]
        if not L:
            return 0
        import marg_billwatch as BW                           # noqa: PLC0415 -- beside this file: the register asks' own writer
        con.execute(ASK_DDL)
        for x in L:
            for c in x["ambiguous"]:
                if con.execute("SELECT 1 FROM mi_voucher_regask WHERE kind=? AND no=? AND n=? AND item=?", (x["kind"], x["no"], int(x.get("n") or 0), c)).fetchone():
                    continue                                  # asked once already: never again, whatever became of it (review S8)
                ok, _msg, _code = BW.reg_ask_item(con, who, c, x["day"], x["day"])
                if not ok and _code == 503:
                    continue                                  # the database busy: asked again at the next read (second look N3)
                con.execute("INSERT OR IGNORE INTO mi_voucher_regask (kind, no, n, item, at) VALUES (?,?,?,?,?)",
                            (x["kind"], x["no"], int(x.get("n") or 0), c, dt.datetime.now().isoformat(timespec="seconds")))
                n += 1 if ok else 0
        con.commit()
    except Exception as ex:                                   # noqa: BLE001
        try:
            con.rollback()                                    # never leave the reader's transaction open (the next read must not be blocked)
        except Exception:                                     # noqa: BLE001
            pass
        print("voucher_judge S973: register asks stopped: %s" % str(ex)[:200], file=_s973_sys.stderr)
        return n
    return n
# ---- S973 end ---------------------------------------------------------------------------------------------------------------------------
