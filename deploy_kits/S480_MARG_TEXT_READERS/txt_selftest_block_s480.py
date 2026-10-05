# ------------------------------------------------------------------------ S480: made-up texts, one per spec (F-185: no real sample)
def _t(*parts):
    """A printed line: (column, text) -- the text starts at the column; a negative column means the text ENDS at that column."""
    s = ""
    for col, txt in parts:
        a = col if col >= 0 else (-col - len(txt) + 1)
        s = s.ljust(a) + txt
    return s


def _txt(lines, tail=0):
    return ("\r\n".join(lines) + "\r\n" + "\r\n" * tail).encode("latin-1")


_R80, _R132 = "-" * 80, "-" * 132
_LETTER = ["", _t((31, "TEST MEDICOS")), _t((24, "TEST STREET , TESTTOWN")), _t((16, "GSTIN : TESTGST  TIN No. : TESTTIN")), ""]
_PI_HEAD = _t((0, "BILL"), (8, "ITEM DESCRIPTION"), (36, "PACKING BATCH"), (53, "EXP."), (60, "TAX"), (66, "QTY."), (72, "FREE"),
              (80, "RATE"), (86, "DIS."), (93, "AMOUNT NET RATE"), (111, "LOOS PURC. ?"), (126, "AMOUNT"))
_LIST_HEAD = _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (56, "P.RATE"), (65, "S.RATE"), (74, "M.R.P."))


def _pi_item(bill, name, batch, amt, net):
    return _t((0, bill), (8, name), (36, "1*10"), (44, batch), (-56, "1/31"), (-62, "5.00"), (-69, "10"), (-83, "100.00"), (-89, "0.00"),
              (-98, amt), (-107, "10.00"), (-114, "100"), (-122, "100.00"), (-131, net))


def _pi_total(word_at, word, amt, net):
    return _t((word_at, word), (-98, amt), (-131, net))


def _list_item(sno, name, pack, mrp):
    return _t((0, str(sno)), (6, name), (36, pack), (-61, "10.00"), (-70, "0.00"), (-79, mrp))


def _list_page2(title):
    return [_R80, _t((66, "Continued..2")), "", "", "", "", "TEST MEDICOS", title, _t((68, "Page No..2")), _R80, _LIST_HEAD, _R80]


def _s480_samples():
    """name -> a made-up text export in the layout Marg prints (invented names, invented figures)."""
    S = {}
    S["PURCHASE_BILLWISE"] = _txt([
        _t((11, "BILL WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R80,
        _t((0, "BILL NO."), (13, "PARTY NAME"), (63, "CASH"), (73, "CREDIT")), _R80,
        "01-01-2030",
        _t((0, "101"), (13, "TEST PHARMA ONE"), (-66, "-"), (-78, "1000.00")),
        _t((0, "A00012"), (13, "DEMO AGENCY"), (43, "TESTTOWN"), (-66, "-"), (-78, "500.50")),
        "02-01-2030",
        _t((0, "0077"), (13, "TEST PHARMA ONE"), (-66, "-"), (-78, "250.00")),
        _R80, _t((0, "TOTAL"), (-54, "1750.50"), (-66, "-"), (-78, "1750.50")), _R80, END])
    S["PURCHASE_ITEMWISE"] = _txt([
        _t((7, "SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R132, _PI_HEAD, _R132,
        "TEST PHARMA ONE",
        _pi_item("101", "TESTCILLIN 500", "TB001", "1000.00", "1050.00"),
        _t((80, "-" * 52)), _pi_total(80, "TOTAL", "1000.00", "1050.00"),
        _t((0, "DEMO AGENCY"), (30, "TESTTOWN")),
        _pi_item("0077", "DEMOCIN TAB", "DB07", "200.25", "210.00"),
        _pi_item("0077", "DEMOGEL", "540021", "300.25", "315.50"),
        _t((80, "-" * 52)), _pi_total(80, "TOTAL", "500.50", "525.50"),
        _R132, _pi_total(0, "GRAND TOTAL", "1500.50", "1575.50"), _R132, END])
    S["PURCHASE_SUPPLIERWISE"] = _txt([
        _t((9, "SUPPLIER WISE PURCHASE STATEMENT FROM 01-01-2030 TO 31-01-2030")), _R80,
        _t((0, "SUPPLIER NAME"), (32, "DATE"), (43, "BILL NO."), (63, "CASH"), (73, "CREDIT")), _R80,
        _t((0, "TEST PHARMA ONE"), (32, "02-01-2030"), (43, "101"), (-66, "-"), (-78, "1000.00")),
        _t((32, "09-01-2030"), (43, "0077"), (-66, "-"), (-78, "250.00")),
        _t((36, "-" * 44)), _t((36, "TOTAL :"), (-54, "1250.00"), (-66, "-"), (-78, "1250.00")), "",
        _t((0, "DEMO AGENCY"), (32, "05-01-2030"), (43, "A00012"), (-66, "-"), (-78, "500.50")),
        _t((36, "-" * 44)), _t((36, "TOTAL :"), (-54, "500.50"), (-66, "-"), (-78, "500.50")), "",
        _R80, _t((0, "GRAND TOTAL"), (-54, "1750.50"), (-66, "-"), (-78, "1750.50")), _R80, END])
    S["PURCHASE_BILLITEMWISE"] = _txt([
        _t((9, "BILL/ITEM WISE PURCHASE STATEMENT FROM 01-01-2030 TO 02-01-2030")), _R132, _PI_HEAD, _R132, "",
        "01-01-2030",
        _pi_item("101", "TESTCILLIN 500", "TB001", "1000.00", "1050.00"),
        "02-01-2030",
        _pi_item("0077", "DEMOCIN TAB", "DB07", "200.25", "210.00"),
        _pi_item("0077", "DEMOGEL", "540021", "300.25", "315.50"),
        _R132, _pi_total(0, "TOTAL", "1500.50", "1575.50"), _R132, END])
    for key, title, heading in (("SALT_WISE_ITEM_LIST", "SALT WISE ITEM LIST", "TESTSALT ONE + TWO"),
                                ("CATEGORY_WISE_ITEM_LIST", "CATEGORY WISE ITEM LIST", _t((0, "TESTCAT"), (-46, "0.00"), (57, "D98")))):
        S[key] = _txt([
            _t((32, "TEST MEDICOS")), _t((30, title)), _R80, _LIST_HEAD, _R80, "",
            _t((0, "1"), (-61, "0.00"), (-70, "0.00"), (-79, "0.00")), "",
            heading,
            _list_item(1, "TESTCILLIN 500", "1*10", "15.00"), _list_item(2, "DEMOCIN TAB", "1*10", "25.50"), "",
            "TESTSALT",
            _list_item(1, "DEMOGEL", "30GM", "99.00")]
            + _list_page2(title) + [
            _list_item(2, "DEMOGEL FORTE", "30GM", "120.00"), "",
            " OTHER SALT X",
            _list_item(1, "TEST WRIST SPLINT LF L ELASTI", "1*1", "450.00"), "", _R80, END, ""])
    S["ITEM_MASTER"] = _txt([
        _t((32, "TEST MEDICOS")), "", _t((34, "LIST OF ITEMS")), _R80,
        _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (54, "Compnay")), _t((54, "P.RATE"), (63, "S.RATE"), (72, "M.R.P.")), _R80,
        _t((0, "1"), (54, "OTHER PRODUCTS")),
        _t((0, "2"), (6, "TESTCILLIN 500"), (36, "1*10"), (54, "TESTCO")),
        _t((0, "3"), (6, "DEMOCIN TAB"), (36, "1*10"), (54, "DEMO LABS")),
        _R80, _t((66, "Continued..2")), "", "", "", "", "TEST MEDICOS", "LIST OF ITEMS", _t((68, "Page No..2")), _R80,
        _t((0, "S.No. DESCRIPTION"), (36, "PACKING"), (54, "Compnay")), _R80,
        _t((0, "4"), (6, "DEMOGEL"), (36, "30GM"), (54, "DEMO LABS")),
        _R80, END, ""])
    S["SALE_BILLWISE_SUMMARY1"] = _txt([
        _t((18, "BILL WISE SALES STATEMENT AS ON 01-01-2030")), "-" * 78,
        _t((0, "BILL NO."), (12, "DESCRIPTION"), (68, "BILL VALUE")), "-" * 78,
        "01-01-2030",
        _t((0, "A000001"), (12, "TEST ONE 1001"), (54, ".CASH"), (-77, "80.00")),
        _t((0, "A000002"), (12, "TEST TWO"), (54, ".UPI"), (65, "#"), (-77, "540.00")),
        "-" * 78, _t((0, "Total No. of Bills: 2"), (56, "DAY TOTAL :"), (-78, "620.00")), "-" * 78, "", END])
    S["SALE_RETURN_SUMMARY"] = _txt(_LETTER[:-1] + [
        _t((19, "SALE RETURN FROM 01-01-2030 TO 31-01-2030")), "", "-" * 78,
        _t((0, "BILL NO."), (12, "DATE"), (18, "PARTY"), (72, "AMOUNT")), "-" * 78,
        _t((0, "CN00001"), (12, "02-01"), (18, "TEST ONE 1001"), (-77, "100.00")),
        _t((0, "CN00002"), (12, "09-01"), (18, "TEST TWO"), (-77, "50.50")),
        "-" * 78, _t((0, "T o t a l"), (-77, "150.50")), "-" * 78, "", END])

    def rd(first, *v):
        return _t(first, *[(-e, x) for e, x in zip((52, 63, 74, 85, 96, 107, 118, 129), v)])
    S["SALE_RETURN_DETAIL"] = _txt([
        _t((20, "SALE RETURN FROM 01-01-2030 TO 31-01-2030")), "-" * 130,
        _t((1, "BILL NO."), (13, "PARTY NAME"), (40, "GROSS AMOUNT TRADE DIS. CASH DISCO"), (78, "PACKING CASH DISCO"),
           (98, "SALES TAX"), (111, "OTHER \xb1 BILL VALUE")), "-" * 130,
        "02-01-2030",
        _t((1, "CN00001"), (13, "TEST ONE 1001"), (-52, "100.00"), (-63, "5.00"), (-74, "0.00"), (-85, "0.00"), (-96, "0.00"),
           (-107, "0.00"), (-118, "0.00"), (-129, "95.00")),
        "09-01-2030",
        _t((1, "CN00002"), (13, "TEST TWO"), (-52, "50.50"), (-63, "0.00"), (-74, "0.00"), (-85, "0.00"), (-96, "0.00"),
           (-107, "0.00"), (-118, "-0.50"), (-129, "50.00")),
        "-" * 130,
        rd((0, "TOTAL"), "150.50", "5.00", "0.00", "0.00", "0.00", "0.00", "-0.50", "145.00"), "-" * 130, "", "", END])
    S["STOCK_VALUATION_BATCHWISE"] = _txt(_LETTER + [
        _t((18, "WHOLE STORES STOCK VALUATION AS ON 01-01-2030")), _R132,
        _t((0, "S.No. Description"), (55, "Batch"), (72, "M.R.P."), (81, "Exp.Date"), (97, "Stock"), (112, "Rate"), (123, "Value")), _R132,
        _t((-4, "1"), (6, "TESTCILLIN 500"), (36, "1*10"), (55, "TB001"), (-77, "61.60"), (81, "Aug.,2031"), (-101, "3:2"),
           (-115, "49.288"), (-127, "152.80")), "",
        _t((-4, "2"), (6, "DEMOGEL"), (36, "30GM"), (-77, "402.19"), (-101, "-0:10"), (-115, "305.664"), (-127, "-203.77")),
        _t((-4, "3"), (6, "DEMOGEL"), (36, "30GM"), (55, "540021"), (-77, "99.00"), (81, "Feb.,2032"), (-101, "6"), (-115, "70.5"),
           (-127, "423.00")),
        _t((88, "-" * 44)), _t((73, "Batch TOTAL"), (-101, "-4"), (-127, "219.23")), "",
        _R132, _t((0, "TOTAL"), (-101, "28"), (-127, "372.03")), _R132, END], tail=12)
    S["STOCK_EXPIRY"] = _txt(_LETTER + [
        _t((30, "EXP. BEFORE *BA.,   0")), _R80,
        _t((0, "S.No. Description"), (44, "Batch"), (57, "Expiry"), (70, "Stock Unit")), _R80,
        _t((-4, "1"), (6, "TESTCILLIN 500"), (37, "1*10"), (44, "TB001"), (-62, "11/2030"), (-75, "3:2"), (77, "STR")), "",
        _t((-4, "2"), (6, "DEMOGEL"), (37, "30GM"), (44, "540021"), (-62, "1/2031"), (-75, "-"), (77, "TUB")),
        _t((-4, "3"), (6, "DEMOGEL"), (37, "30GM"), (44, "540022"), (-62, "1/2031"), (-75, "6"), (77, "TUB")),
        _t((47, "-" * 33)), _t((47, "Batch TOTAL"), (-75, "6")), "",
        _t((-4, "4"), (6, "DEMOCIN TAB"), (37, "1*10."), (44, "DB07"), (-62, "12/2030"), (-75, "-1:3"), (77, "STR")), "",
        _R80, _t((0, "TOTAL"), (-75, "25")), _R80, END], tail=6)
    S["STOCK_ITEM_LEDGER_TEXT"] = _txt(_LETTER + [
        _t((16, "STOCK REGISTER WHOLE FROM 01-01-2030 - 31-01-2030")), _R132,
        _t((0, "Bill No. /"), (13, "Type"), (29, "Patient Name"), (55, "Doctor Name"), (81, "Batch"), (94, "Quantity"), (110, "Value"),
           (123, "Balance")),
        _t((2, "Date"), (82, "No."), (122, "Quantity")), _R132,
        "TESTCILLIN 500 1*10",
        _t((0, "Opening Balance as on 01-01-2030 TAB"), (-131, "43:7")),
        _t((0, "02-01-2030"), (13, "PURCHASE"), (29, "TEST PHARMA ONE"), (81, "TB001"), (-104, "10:0"), (-117, "1000.00"), (-131, "53:7")),
        "101",
        _t((0, "A000001"), (13, "SALE"), (29, "TEST ONE 1001"), (55, "TEST DOCTOR"), (81, "TB001"), (-104, "0:4"), (-117, "80.00"),
           (-131, "53:3")),
        _t((76, "-" * 56)),
        _t((76, "Received :"), (-104, "10:0"), (-117, "1000.00")),
        _t((78, "Issued :"), (-104, "0:4"), (-117, "80.00")),
        _t((76, "-" * 56))])
    return S


EMPTY_DAY_SAMPLE = _txt([
    _t((18, "BILL WISE SALES STATEMENT AS ON 02-01-2030")), _R132,
    "BILL NO.    DESCRIPTION                       D.R.          GROSS AMT.    DISCOUNT         TAX       DR/CR    NET AMT.        CASH",
    _R132, _R132,
    "Total No. of Bills: 0                         DAY TOTAL :         0.00        0.00        0.00        0.00        0.00        0.00",
    _R132, "", END])
# what marg_txt S454 (ed17bb76) made of its own three samples: S480 must make the same bytes of them (the brief's 9.1, in small)
_S454_BYTES = {"SALE": "@@MD5_SALE@@", "STOCK": "@@MD5_STOCK@@", "ORDER": "@@MD5_ORDER@@"}


def _selftest_s480(ck):
    import datetime as _dt
    T, S_, O_ = SELFTEST_SAMPLE, STOCK_SAMPLE, ORDER_SAMPLE
    for k_, raw_ in (("SALE", T), ("STOCK", S_), ("ORDER", O_)):
        ck("S480: the %s text converts to the same bytes as before S480" % k_,
           hashlib.md5(convert(raw_)[0]).hexdigest() == _S454_BYTES[k_], hashlib.md5(convert(raw_)[0]).hexdigest()[:8])
    M = _s480_samples()
    want = {"PURCHASE_BILLWISE": "PURCHASE", "PURCHASE_ITEMWISE": "PURCHASE", "PURCHASE_SUPPLIERWISE": "PURCHASE",
            "PURCHASE_BILLITEMWISE": "PURCHASE", "SALT_WISE_ITEM_LIST": "SALT", "CATEGORY_WISE_ITEM_LIST": "CATEGORY",
            "ITEM_MASTER": "ITEMS", "SALE_BILLWISE_SUMMARY1": "SALE_SHORT", "SALE_RETURN_SUMMARY": "RETURN",
            "SALE_RETURN_DETAIL": "RETURN", "STOCK_VALUATION_BATCHWISE": "VALUATION", "STOCK_EXPIRY": "EXPIRY",
            "STOCK_ITEM_LEDGER_TEXT": "LEDGER"}
    ck("S480: one spec per report, each with its made-up text", sorted(M) == sorted(sp["key"] for sp in TEXT_SPECS) == sorted(want))
    bad = {"PURCHASE_BILLWISE": (b"250.00", b"350.00"), "PURCHASE_ITEMWISE": (b"300.25", b"900.25"),
           "PURCHASE_SUPPLIERWISE": (b"      250.00", b"      950.00"), "PURCHASE_BILLITEMWISE": (b"300.25", b"900.25"),
           "SALT_WISE_ITEM_LIST": (b"2     DEMOGEL FORTE", b"3     DEMOGEL FORTE"),
           "CATEGORY_WISE_ITEM_LIST": (b"Page No..2", b"Page No..3"), "ITEM_MASTER": (b"4     DEMOGEL", b"5     DEMOGEL"),
           "SALE_BILLWISE_SUMMARY1": (b"Bills: 2", b"Bills: 3"), "SALE_RETURN_SUMMARY": (b" 50.50", b"950.50"),
           "SALE_RETURN_DETAIL": (b"     50.00", b"    950.00"), "STOCK_VALUATION_BATCHWISE": (b"TOTAL" + b" " * 91, b"TOTEL" + b" " * 91),
           "STOCK_EXPIRY": (b"TOTAL" + b" " * 69 + b"25", b"TOTAL" + b" " * 69 + b"26"),
           "STOCK_ITEM_LEDGER_TEXT": (b"Issued :", b"Issue  :")}
    R = {}
    for key in sorted(M):
        raw_ = M[key]
        sp = spec_of(raw_)
        try:
            R[key] = spec_rows(raw_)
            got = True
        except (Refused, NotThisReport) as ex_:
            got = str(ex_)[:60]
        a_, b_ = bad[key]
        try:
            spec_rows(raw_.replace(a_, b_))
            neg = raw_.count(a_) and "taken"
        except (Refused, NotThisReport) as ex_:
            neg = True
        x1_, i1_ = (convert(raw_) if got is True else (b"", {}))
        ck("S480 %s: recognised as %s, its figures hold, one changed figure refuses, the same bytes every time"
           % (key, want[key]), sp is not None and sp["key"] == key and kind(raw_) == want[key] and got is True and neg is True
           and raw_.count(a_) >= 1 and x1_ == convert(raw_)[0] and i1_.get("kind") == want[key] and i1_.get("version") == VERSION,
           (sp and sp["key"], got, neg))
    ck("S480: a number is a number, a bill number with a leading zero stays as printed, '-' stays '-'",
       R["PURCHASE_BILLWISE"][3] == [101.0, "TEST PHARMA ONE", "-", 1000.0] and R["PURCHASE_BILLWISE"][6][0] == "0077"
       and R["PURCHASE_BILLWISE"][-1] == ["TOTAL", 1750.5, "-", 1750.5], R["PURCHASE_BILLWISE"][3])
    ck("S480 rule B: a supplier heading is one cell; rule A: a supplier and its town are cut at the column heads",
       R["PURCHASE_ITEMWISE"][2] == ["TEST PHARMA ONE"] + [""] * 11 and R["PURCHASE_ITEMWISE"][5][:3] == ["DEMO", "AGENCY", "TESTTOWN"]
       and R["PURCHASE_ITEMWISE"][3][9] == "1000.00    10.00" and R["PURCHASE_ITEMWISE"][3][11] == 1050.0, R["PURCHASE_ITEMWISE"][5][:3])
    sl = R["SALT_WISE_ITEM_LIST"]
    ck("S480: the letterhead and the title are one cell each; Continued and Page No as Marg's sheet has them; a heading is one cell",
       sl[0] == ["TEST MEDICOS", "", "", "", ""] and sl[1] == ["SALT WISE ITEM LIST", "", "", "", ""]
       and ["", "", "", "", "Continued..2"] in sl and ["", "", "", "Page", "No..2"] in sl
       and ["TESTSALT ONE + TWO", "", "", "", ""] in sl and ["OTHER SALT X", "", "", "", ""] in sl
       and ["1     TESTCILLIN 500", "1*10", 10.0, 0.0, 15.0] in sl, sl[:2])
    ck("S480: a category heading with its trailing figure and code is cut by column", ["TESTCAT", 0.0, "D98", "", ""] in R["CATEGORY_WISE_ITEM_LIST"])
    im = R["ITEM_MASTER"]
    ck("S480: the item list's two-line heads stay two rows, the columns the union of both lines'",
       ["S.No. DESCRIPTION", "PACKING", "Compnay", "", ""] in im and ["", "", "P.RATE", "S.RATE", "M.R.P."] in im
       and [1.0, "", "OTHER", "PRODUCTS", ""] in im and ["2     TESTCILLIN 500", "1*10", "TESTCO", "", ""] in im, im[3:5])
    lg = R["STOCK_ITEM_LEDGER_TEXT"]
    ck("S480: the register's first head row is its header; it closes on Received : / Issued : and prints no end mark",
       ["Bill No. /", "Type", "Patient Name", "Doctor Name", "Batch", "Quantity", "Value", "Balance"] in lg
       and ["Date", "", "", "", "No.", "", "", "Quantity"] in lg and lg[-1][4] == "Issued :" and END.encode() not in M["STOCK_ITEM_LEDGER_TEXT"],
       lg[-1])
    ck("S480: the short sale statement is SALE_SHORT, the statement with item detail stays SALE",
       kind(M["SALE_BILLWISE_SUMMARY1"]) == "SALE_SHORT" and kind(T) == "SALE"
       and R["SALE_BILLWISE_SUMMARY1"][-1][0] == "Total No. of" and R["SALE_BILLWISE_SUMMARY1"][-1][2] == 620.0)
    ck("S480: a report cut before its end -- Marg's end mark, or the register's closing pair -- is not recognised",
       kind(M["PURCHASE_BILLWISE"][:-30]) is None and kind(M["STOCK_ITEM_LEDGER_TEXT"][:-300]) is None)
    pe_ = M["PURCHASE_BILLWISE"]
    pe_ = pe_[:pe_.index(b"01-01-2030\r\n")] + pe_[pe_.index(b"-" * 80 + b"\r\nTOTAL"):].replace(b"1750.50", b"   0.00")
    try:
        spec_rows(pe_)
        ck("S480: an empty purchase statement is refused as EMPTY", False)
    except EmptyReport:
        ck("S480: an empty purchase statement is refused as EMPTY", kind(pe_) == "PURCHASE")
    # the no-sale day (D675 a, F-729)
    E_ = EMPTY_DAY_SAMPLE
    xe_, ie_ = convert(E_, exported_at=_dt.datetime(2030, 1, 3, 9, 0, 0))
    re_ = to_rows(E_, exported_at=_dt.date(2030, 1, 3))
    ck("S480: a zero-bill sale report of a past day is a NO-SALE DAY: title, heads, its one total row",
       ie_.get("empty") is True and ie_.get("as_on") == "02-01-2030" and ie_["kind"] == "SALE" and len(re_) == 3
       and re_[2] == ["Total No. of", "Bills: 0", "DAY TOTAL :", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] and re_[1] == HEAD
       and xe_ == convert(E_, exported_at="20300105-101500")[0], re_[2][:3])
    for when_, why_ in ((_dt.datetime(2030, 1, 2, 23, 59, 0), "the same day"), (_dt.date(2030, 1, 1), "a day before")):
        try:
            convert(E_, exported_at=when_)
            ck("S480: the same report exported on %s is refused in the staff's words" % why_, False)
        except TodayNotOver as ex_:
            ck("S480: the same report exported on %s is refused in the staff's words" % why_, str(ex_) == TODAY_WORDS)
    try:
        convert(E_)
        ck("S480: with no export time the zero-bill report is refused, never guessed", False)
    except TodayNotOver:
        ck("S480: with no export time the zero-bill report is refused, never guessed", False)
    except Refused:
        ck("S480: with no export time the zero-bill report is refused, never guessed", True)
    for bad_, why_ in ((E_.replace(b"Bills: 0", b"Bills: 1"), "a footer that says one bill"),
                       (E_.replace(b"DAY TOTAL :         0.00", b"DAY TOTAL :         5.00"), "a total that is not zero"),
                       (E_.replace(b"AS ON 02-01-2030", b"FROM 01-01-2030 TO 02-01-2030"), "a period, not a day")):
        try:
            convert(bad_, exported_at=_dt.date(2030, 1, 9))
            ck("S480: not an empty day -- %s" % why_, False)
        except TodayNotOver:
            ck("S480: not an empty day -- %s" % why_, False)
        except Refused as ex_:
            ck("S480: not an empty day -- %s" % why_, "GRAND TOTAL" in str(ex_))
    ck("S480: a sale with bills is read exactly as before whatever the export time",
       to_rows(T, exported_at=_dt.date(2030, 1, 9)) == to_rows(T) and "empty" not in convert(T)[1])


