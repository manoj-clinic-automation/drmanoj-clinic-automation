    # ---- S489 (D681/D682): the views, the private split, the loan ledger -- made-up people and rows ----
    assert inr(234000) == "2,34,000" and inr(1500) == "1,500" and inr(0) == "0" and inr(-710) == "-710"
    assert inr(12345678.5) == "1,23,45,678.50" and inr(1337.7) == "1,337.70" and inr(999) == "999" and inr(100000) == "1,00,000"

    def _iss(i, staff, d, amt, inst=None, am="", interest=False, narr="", sched=None):
        return {"id": i, "category": "ADVANCE_ISSUE", "status": "APPROVED", "staff": staff, "date_from": d,
                "amount": amt, "instalment": inst, "against_month": am, "interest": interest,
                "narration": narr, "schedule": sched or [], "contra_of": "", "closed_month": "", "ts_entry": d}

    def _sys(i, staff, cat, m, amt, co):
        return {"id": i, "category": cat, "status": "APPROVED", "staff": staff, "date_from": m,
                "amount": amt, "contra_of": co, "closed_month": m, "narration": ""}
    _R = [
        # Asha: ONE loan of 6,000 handed over in three parts (1,500 a month) + two same-month advances
        _iss("a1", "Asha", "2031-08-04", 1500, 1500, "2031-08"),
        _iss("a2", "Asha", "2031-08-06", 2250, 1500, "2031-09"),
        _iss("a3", "Asha", "2031-08-09", 2250, 1500, "2031-10"),
        _sys("a1r", "Asha", "ADVANCE_INSTALMENT", "2031-08", -1500, "a1"),
        _iss("a4", "Asha", "2031-09-05", 700, 700, "2031-09"),
        _iss("a5", "Asha", "2031-09-21", 2600, 2600, "2031-09"),
        _sys("a2r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -1500, "a2"),
        _sys("a4r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -700, "a4"),
        _sys("a5r", "Asha", "ADVANCE_INSTALMENT", "2031-09", -2600, "a5"),
        # Dev: a private long-term loan (with interest), its interest-free part, one ordinary advance,
        # and a schedule advance that is an ordinary instalment loan on the common sheet
        _iss("d1", "Dev", "2031-08-03", 97000, 6000, "", True, "opening balance migrated from workbook (interest-bearing tranche)"),
        _iss("d2", "Dev", "2031-08-03", 64000, 6000, "", False, "opening balance migrated from workbook (interest-free tranche)"),
        _sys("d1c", "Dev", "LOAN_CAPITALISE", "2031-04", -1000, "d1"),
        _sys("d1r8", "Dev", "ADVANCE_INSTALMENT", "2031-08", -5000, "d1"), _sys("d1i8", "Dev", "LOAN_INTEREST", "2031-08", -1000, "d1"),
        _sys("d1r9", "Dev", "ADVANCE_INSTALMENT", "2031-09", -5000, "d1"), _sys("d1i9", "Dev", "LOAN_INTEREST", "2031-09", -1000, "d1"),
        _iss("d3", "Dev", "2031-09-11", 2400, 2400, "2031-09"),
        _sys("d3r", "Dev", "ADVANCE_INSTALMENT", "2031-09", -2400, "d3"),
        _iss("d4", "Dev", "2031-08-12", 15000, 15000, "", False, "",
             [{"month": "2031-08", "amount": 6000}, {"month": "2031-09", "amount": 3000},
              {"month": "2031-10", "amount": 3000}, {"month": "2031-11", "amount": 3000}]),
        _sys("d4r8", "Dev", "ADVANCE_INSTALMENT", "2031-08", -6000, "d4"),
        _sys("d4r9", "Dev", "ADVANCE_INSTALMENT", "2031-09", -3000, "d4"),
    ]
    _G = [{"staff": "Asha", "ids": ["a1", "a2", "a3"], "given": "4-9 Aug 2031"}]
    _lm = ledger_money(_R, "Asha", "2031-09")
    _v = advance_views(_lm, "Asha", "2031-09", True, _G)
    assert [a["id"] for a in _v["month_adv"]] == ["a4", "a5"], _v["month_adv"]
    assert len(_v["loans"]) == 1, "three parts are ONE loan"
    _L = _v["loans"][0]
    assert (_L["amount"], _L["paid"], _L["n_paid"], _L["n_all"], _L["cut"], _L["balance"], _L["ends"]) \
        == (6000, 3000, 2, 4, 1500, 3000, "2031-11"), _L
    assert _L["strip"] == [("2031-08", 1500, "paid"), ("2031-09", 1500, "paid"),
                           ("2031-10", 1500, "due"), ("2031-11", 1500, "due")], _L["strip"]
    assert _L["inst"] == "1,500 a month" and _L["next"] == 1500
    assert round(sum(a["cut"] for a in _v["month_adv"]) + sum(L["cut"] for L in _v["loans"]), 2) == _lm["deducted"] == 4800
    _v0 = advance_views(_lm, "Asha", "2031-09", True, [])        # no group record: each advance its own loan
    assert len(_v0["loans"]) == 2 and sum(L["cut"] for L in _v0["loans"]) == 1500
    _va = advance_views(ledger_money(_R, "Asha", "2031-08"), "Asha", "2031-08", True, _G)
    assert not _va["month_adv"] and (_va["loans"][0]["paid"], _va["loans"][0]["n_paid"], _va["loans"][0]["n_all"]) == (1500, 1, 4)
    # the private split
    _lmd = ledger_money(_R, "Dev", "2031-09")
    _vd = advance_views(_lmd, "Dev", "2031-09", True, [], private=True)
    assert [t["id"] for t in _vd["priv_lines"]] == ["d1", "d2"] and [a["id"] for a in _vd["month_adv"]] == ["d3"]
    assert len(_vd["loans"]) == 1 and _vd["loans"][0]["ids"] == ["d4"] and _vd["loans"][0]["inst"] == "6,000, then 3,000 a month"
    _p = private_split(_vd["priv_lines"], "2031-09", True)
    assert (_p["kept"], _p["cut"], _p["cut_shown"], _p["paid"], _p["reserve"], _p["status"]) == (6000, 6000, 6000, 0, 0, "paid"), _p
    _common = round(sum(a["cut"] for a in _vd["month_adv"]) + sum(L["cut"] for L in _vd["loans"]), 2)
    assert _common + _p["cut_shown"] == _lmd["deducted"] == 11400, "common advances + private instalment = the ledger's figure"
    assert private_split([], "2031-09", True) is None
    _vn = advance_views(_lmd, "Dev", "2031-09", True, [], private=False)      # not private: nothing is held back
    assert not _vn["priv_lines"] and len(_vn["loans"]) == 3
    # a month it is skipped: the whole instalment is paid to him on the private page
    _R2 = _R + [_sys("d1s", "Dev", "LOAN_SKIP", "2031-10", 0, "d1"), _sys("d4r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -3000, "d4")]
    _lmo = ledger_money(_R2, "Dev", "2031-10")
    _po = private_split(advance_views(_lmo, "Dev", "2031-10", True, [], private=True)["priv_lines"], "2031-10", True)
    assert (_po["kept"], _po["cut"], _po["paid"], _po["reserve"], _po["status"]) == (6000, 0, 6000, 6000, "skip"), _po
    # before the ledger close: kept aside, not yet decided
    _lmp = ledger_money(_R, "Dev", "2031-10")
    _pp = private_split(advance_views(_lmp, "Dev", "2031-10", False, [], private=True)["priv_lines"], "2031-10", False)
    assert (_pp["kept"], _pp["paid"], _pp["reserve"], _pp["status"]) == (6000, None, 6000, "pending"), _pp
    # the loan ledger: months before the ledger from the history record, the rest the ledger's own
    _H = {"loan_id": "d1", "opening_date": "2031-03-31", "opening": 111000,
          "pre": [{"ym": "2031-04", "kind": "skip", "added": 0},
                  {"ym": "2031-05", "kind": "paid", "instalment": 6000, "interest": 1000},
                  {"ym": "2031-06", "kind": "paid", "instalment": 6000, "interest": 1000},
                  {"ym": "2031-07", "kind": "paid", "instalment": 6000, "interest": 1000}]}
    _d1 = _vd["priv_lines"][0]
    _rows, _op, _note = loan_ledger(_d1, _H, "2031-09", True)
    assert _op == 111000 and _note == "", _note
    assert [r["status"] for r in _rows] == ["skip", "paid", "paid", "paid", "paid", "paid", "next"], [r["status"] for r in _rows]
    assert [r["end"] for r in _rows] == [111000, 106000, 101000, 96000, 91000, 86000, 81000], [r["end"] for r in _rows]
    assert _rows[-2]["end"] == _d1["end"] == 86000 and skips_in_fy(_rows, "2031-09") == ["2031-04"]
    _rb, _ob, _nb = loan_ledger(_d1, dict(_H, opening=111500), "2031-09", True)
    assert _nb and "difference" in _nb, "a history that does not meet the ledger is SAID"
    _d1o = advance_views(_lmo, "Dev", "2031-10", True, [], private=True)["priv_lines"][0]
    _ro, _oo, _no = loan_ledger(_d1o, _H, "2031-10", True)
    assert _ro[-2]["status"] == "skip" and _ro[-2]["end"] == 86000 and skips_in_fy(_ro, "2031-10") == ["2031-04", "2031-10"]
    _rn, _on, _nn = loan_ledger(_d1, {}, "2031-09", True)          # no history record: the table starts where the
    assert _on == 96000 and _rn[0]["ym"] == "2031-08" and _rn[-2]["end"] == 86000 and _nn == "", (_on, _rn[0], _nn)   # LEDGER starts
    # a record that states no figure: 'paid' is the loan's standing terms, the opening is worked back
    _Hd = {"loan_id": "d1", "opening_date": "2031-03-31", "ledger_adjust": -1000,
           "pre": [{"ym": "2031-04", "kind": "skip"}, {"ym": "2031-05", "kind": "paid"},
                   {"ym": "2031-06", "kind": "paid"}, {"ym": "2031-07", "kind": "paid"}]}
    _rd, _od, _nd = loan_ledger(_d1, _Hd, "2031-09", True)
    assert _od == 111000 and _nd == "" and [r["end"] for r in _rd] == [r["end"] for r in _rows], (_od, _nd)
    assert [(r["inst"], r["interest"], r["principal"]) for r in _rd[:2]] == [(0, 0, 0), (6000, 1000, 5000)]
    _rx, _ox, _nx = loan_ledger(_d1, dict(_Hd, ledger_adjust=0), "2031-09", True)
    assert _nx and "adjustment" in _nx, "the ledger's adjustment is not the one the record was written for -- SAID"
    _d1bare = dict(_d1, caps=[])                                    # the same loan WITHOUT its adjustment row
    assert "adjustment" in loan_ledger(_d1bare, _Hd, "2031-09", True)[2]
    _re, _oe, _ne = loan_ledger(_d1, _Hd, "2031-05", True)          # a month inside the history: no ledger row, no note
    assert [r["ym"] for r in _re if r["status"] != "next"] == ["2031-04", "2031-05"] and _ne == ""
    # a DEFER on the loan with interest ALONE: the ledger takes the instalment for the interest-free part
    _R3 = _R + [_sys("d1f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1"),
                _sys("d2r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -6000, "d2"),
                _sys("d4r10", "Dev", "ADVANCE_INSTALMENT", "2031-10", -3000, "d4")]
    _v3 = advance_views(ledger_money(_R3, "Dev", "2031-10"), "Dev", "2031-10", True, [], private=True)
    _p3 = private_split(_v3["priv_lines"], "2031-10", True)
    assert (_p3["kept"], _p3["cut_shown"], _p3["paid"], _p3["reserve"], _p3["status"]) == (6000, 6000, 0, 0, "paid"), _p3
    _r3 = loan_ledger(_v3["priv_lines"][0], _H, "2031-10", True)[0]
    assert _r3[-2]["status"] == "defer" and _r3[-2]["end"] == 86000
    _lm3p = ledger_money(_R + [dict(_sys("d1f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d1"), closed_month="")], "Dev", "2031-10")
    _d2p = [t for t in _lm3p["lines"] if t["id"] == "d2"][0]
    assert [(m, p) for m, p, _i in _d2p["proj"]][:1] == [("2031-10", 6000)], "before the close the plan already says where the instalment goes"
    # a recorded defer moves the plan as the close will: nothing that month, the schedule one month longer
    _R4 = _R + [_sys("d4f", "Dev", "ADVANCE_DEFER", "2031-10", 0, "d4")]
    _t4 = [t for t in ledger_money(_R4, "Dev", "2031-09")["lines"] if t["id"] == "d4"][0]
    assert [(m, p) for m, p, _i in _t4["proj"]] == [("2031-11", 3000), ("2031-12", 3000)], _t4["proj"]
    _t4o = [t for t in ledger_money(_R, "Dev", "2031-09")["lines"] if t["id"] == "d4"][0]
    assert [(m, p) for m, p, _i in _t4o["proj"]] == [("2031-10", 3000), ("2031-11", 3000)], _t4o["proj"]
    _R5 = _R + [_sys("d1k", "Dev", "LOAN_SKIP", "2031-10", 0, "d1")]          # a recorded skip: the waterfall waits
    _t5 = [t for t in ledger_money(_R5, "Dev", "2031-09")["lines"] if t["id"] == "d1"][0]
    assert _t5["proj"][0][0] == "2031-11" and _t5["proj"][0][1:] == (5000, 1000), _t5["proj"][:2]
    # money that comes back in ONE salary is not an instalment loan: no slip for it
    _R6 = [_iss("z1", "Zed", "2031-09-26", 1900, 1900, "2031-10")]
    _v6 = advance_views(ledger_money(_R6, "Zed", "2031-09"), "Zed", "2031-09", True, [])
    assert len(_v6["loans"]) == 1 and _v6["loans"][0]["n_all"] == 1 and _v6["loans"][0]["late_month"]
    assert not has_slip({"name": "Zed", "views": _v6}, {"ym": "2031-09"})
    assert has_slip({"name": "Asha", "views": _v}, {"ym": "2031-09"})
    # the loan record is cleaned on the way in, and a broken one never raises
    import tempfile as _tf, shutil as _sh
    _td = _tf.mkdtemp(prefix="sp_selftest_")
    _lpp = os.path.join(_td, "loan_pages.json")
    try:
        with open(_lpp, "w", encoding="utf-8") as _f:
            json.dump({"groups": [{"staff": "Asha", "ids": ["a1", "a2", "a2", 7, ["x"]], "given": 5},
                                  {"staff": "Asha", "ids": ["a2", "a3"]}, {"staff": "Asha", "ids": 9}, "junk",
                                  {"staff": 3, "ids": ["q"]}],
                       "history": {"DEV ": {"loan_id": "d1", "opening": "lots", "ledger_adjust": -1000,
                                            "pre": [{"ym": "2031-05", "kind": "paid"}, {"ym": "April 2031", "kind": "paid"},
                                                    "text", {"ym": "2031-04", "kind": "skip", "added": [1]},
                                                    {"ym": "2031-05", "kind": "paid", "instalment": 1}]},
                                   "Bad": "text"}}, _f)
        _c = loan_pages(_lpp)
        assert _c["groups"] == [{"staff": "Asha", "ids": ["a1", "a2"], "given": ""}, {"staff": "Asha", "ids": ["a3"], "given": ""}], _c["groups"]
        assert list(_c["history"]) == ["dev"] and _c["history"]["dev"]["pre"] == [{"ym": "2031-04", "kind": "skip"}, {"ym": "2031-05", "kind": "paid"}]
        assert "opening" not in _c["history"]["dev"] and loan_history("Dev", _c)["loan_id"] == "d1" and loan_history("Nobody", _c) == {}
        for _bad in ("[1, 2]", "{\"groups\": 5, \"history\": []}", "not json", ""):
            with open(_lpp, "w", encoding="utf-8") as _f:
                _f.write(_bad)
            assert loan_pages(_lpp) == {"groups": [], "history": {}}, _bad
    finally:
        _sh.rmtree(_td, ignore_errors=True)
    assert fy_of_ym("2031-03") == 2030 and fy_of_ym("2031-04") == 2031
    assert private_loan_names({}) == {"darpan"} and own_sheet_names({}) == set()
    assert loan_pages("/nonexistent/loan_pages.json") == {"groups": [], "history": {}}
