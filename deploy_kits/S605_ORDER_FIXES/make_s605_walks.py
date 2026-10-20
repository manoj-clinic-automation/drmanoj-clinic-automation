# -*- coding: utf-8 -*-
"""make_s605_walks.py -- kit S605_ORDER_FIXES, F-957: the anchored edits of the two kit-held walks (read by make_s605.py, never imported).
walk_s603.py: section 1 lays its OWN visit day (a day far ahead, its taps and receipts by key) in place of the live 18-Oct replay -- the same
controls, the same expectations. walk_s598.py: the walk lays its own rows -- the seven rows S593 marked, put back on ITS COPY from the S598
install's JSON (--rows-json) before anything is read, by id; the KIT line may name a later kit; on a spine built by S605 (F-951) the renamed
sizes own their keys. The live days no longer decide either walk."""

WALKS = {}

# ======================================================================================================================= walk_s603.py
W603 = []
W603.append(("W1 the header", '''--expect-red is the negative control: the same walk on the OLD files, every 'C:' check must be red. Prints 'WALK OK S603 ...'."""
''', '''--expect-red is the negative control: the same walk on the OLD files, every 'C:' check must be red. Prints 'WALK OK S603 ...'.
S605 (F-957): section 1 lays its OWN visit day (45 days ahead: step-2 taps, a receipt, the step-3 tap, by key) -- the live 18-Oct replay
read Amir's real day, which his next export cleared on the server; the controls and their expectations are the same."""
'''))
W603.append(("W2 section 1: the walk's own visit day", '''    def s1():
        c = conn()
        S = AD.state(c, "2026-10-18", "amir")
        ticks = S.ticks
        due0 = AD._reexport_due(c, "2026-10-18", ticks)
        say("   18-Oct on the copy: taps %s; _reexport_due -> %s" % ({k: v["done_at"] for k, v in sorted(ticks.items())}, due0))
        check("C: (1) the 18-Oct replay: _reexport_due is (True, '2026-10-18 09:35:24') -- his step-3 tap of 09:37:53 clears nothing, no file came after 09:35:24",
              tuple(due0) == (True, "2026-10-18 09:35:24"), due0)
        receipt_mi(c, "mi-20oct", "2026-10-20 09:00:00")
        due1 = AD._reexport_due(c, "2026-10-18", ticks)
        c.execute("DELETE FROM mi_file WHERE md5=?", (w603("mi-20oct"),))
        receipt_pe(c, "pe-20oct", "2026-10-20 09:00:00")
        due2 = AD._reexport_due(c, "2026-10-18", ticks)
        c.execute("DELETE FROM purchase_export WHERE md5=?", (w603("pe-20oct"),))
        c.commit()
        say("   with a synthetic mi_file PURCHASE_BILLWISE receipt of 20-Oct 09:00 -> %s; with a synthetic purchase_export BILLWISE receipt instead -> %s" % (due1, due2))
        check("C: (1) a VERIFIED mi_file receipt of ANOTHER day (20-Oct) after T2 clears the band (True -> False): the same-day cut is gone", due0[0] is True and due1[0] is False, (due0, due1))
        check("C: (1) a purchase_export receipt after T2 clears it too (the pusher's receipt is a receipt)", due0[0] is True and due2[0] is False, (due0, due2))
''', '''    def s1():
        c = conn()
        # S605 (F-957): the walk's OWN visit day in place of the live 18-Oct -- 18-Oct's shape: bills keyed, the pair received, a bill keyed
        # after it (09:35:24), 'Dono report nikaal di' tapped (09:37:53) and no file after it
        R = (today + dt.timedelta(days=43)).isoformat()
        tap(c, R, 2, R + " 09:10:00")
        receipt_mi(c, "mi-R-first", R + " 09:20:00")
        receipt_pe(c, "pe-R-first", R + " 09:20:30")
        tap(c, R, 2, R + " 09:35:24")
        tap(c, R, 3, R + " 09:37:53", "export")
        c.commit()
        S = AD.state(c, R, "amir")
        ticks = S.ticks
        due0 = AD._reexport_due(c, R, ticks)
        say("   the walk's own visit day %s on the copy: taps %s; _reexport_due -> %s" % (R, {k: v["done_at"] for k, v in sorted(ticks.items())}, due0))
        check("C: (1) the 18-Oct replay: _reexport_due is (True, '%s 09:35:24') -- his step-3 tap of 09:37:53 clears nothing, no file came after 09:35:24" % R,
              tuple(due0) == (True, R + " 09:35:24"), due0)
        R2 = (today + dt.timedelta(days=44)).isoformat()
        receipt_mi(c, "mi-R-next", R2 + " 09:00:00")
        due1 = AD._reexport_due(c, R, ticks)
        c.execute("DELETE FROM mi_file WHERE md5=?", (w603("mi-R-next"),))
        receipt_pe(c, "pe-R-next", R2 + " 09:00:00")
        due2 = AD._reexport_due(c, R, ticks)
        c.execute("DELETE FROM purchase_export WHERE md5=?", (w603("pe-R-next"),))
        c.commit()
        say("   with a synthetic mi_file PURCHASE_BILLWISE receipt of %s 09:00 -> %s; with a synthetic purchase_export BILLWISE receipt instead -> %s" % (R2, due1, due2))
        check("C: (1) a VERIFIED mi_file receipt of ANOTHER day (%s) after T2 clears the band (True -> False): the same-day cut is gone" % R2, due0[0] is True and due1[0] is False, (due0, due1))
        check("C: (1) a purchase_export receipt after T2 clears it too (the pusher's receipt is a receipt)", due0[0] is True and due2[0] is False, (due0, due2))
        cleanup(c)
'''))
WALKS["walk_s603.py"] = ("deploy_kits/S603_AMIR_CALENDAR_SAFE/walk_s603.py", "8be61d69ffc6dc3e5a0abecf342d3ad2", W603)

# ======================================================================================================================= walk_s598.py
W598 = []
W598.append(("V1 the header", '''the OLD files, every 'C:' check must be red. --state prints the install-day state (the brief's section 5). Prints 'WALK OK S598 ...'."""
''', '''the OLD files, every 'C:' check must be red. --state prints the install-day state (the brief's section 5). Prints 'WALK OK S598 ...'.
S605 (F-957): --rows-json <the S598 install's purchase_order_line JSON>: the walk LAYS ITS OWN ROWS -- the seven rows as S593 marked them,
put back on ITS COPY by id before anything is read (the live re-judge of 19-Oct no longer decides the walk); the KIT line may name a later
kit (S602 placed stock_figure since); on a spine built by S605 (F-951) the renamed sizes own their keys (sp_alias 'rename_family')."""
'''))
W598.append(("V2 the argument", '''    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S598_WALK_ANYWHERE") == "1"
''', '''    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    ap.add_argument("--rows-json", default="")                 # S605 (F-957): the seven rows laid on the walk's copy
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S598_WALK_ANYWHERE") == "1"
'''))
W598.append(("V3 the walk lays its own rows before reading them", '''    c_ = conn()
    PO.ensure_schema(c_)
    OR.ensure(c_)
    c_.commit()
    c_.close()
''', '''    c_ = conn()
    PO.ensure_schema(c_)
    OR.ensure(c_)
    c_.commit()
    if a.rows_json:                                            # S605 (F-957): the seven rows as S593 marked them, on THIS copy, by id
        J = json.load(open(a.rows_json, encoding="utf-8"))
        cols = [x for x in J["columns"] if x != "id"]
        laid = []
        for j in J["rows"]:
            if j["id"] in SEVEN:
                c_.execute("UPDATE purchase_order_line SET %s WHERE id=?" % ", ".join("%s=?" % x for x in cols), [j[x] for x in cols] + [j["id"]])
                laid.append(j["id"])
        c_.commit()
        say("   S605 (F-957): the walk laid its own rows on its copy -- lines %s as S593 marked them (the S598 install's JSON)" % laid)
    c_.close()
'''))
W598.append(("V4 the four spellings on an S605 spine", '''        check("the four spellings resolve to one key (the sp_alias fold; the per-line rule tells M and L apart)", len(set(keys.values())) == 1, keys)
''', '''        fam605 = bool(sw.q("SELECT 1 FROM sp_alias WHERE kind='rename_family' LIMIT 1"))
        if fam605:                                             # S605 (F-951): the old spellings share the old key; each new spelling owns its own
            check("the old spellings resolve to one key and each renamed size owns its own (S605, F-951: sp_alias 'rename_family')",
                  keys["ANKLE BINDER BAMBOO M"] == keys["ANKLE BINDER BAMBOO L"] and len(set(keys.values())) == 3, keys)
        else:
            check("the four spellings resolve to one key (the sp_alias fold; the per-line rule tells M and L apart)", len(set(keys.values())) == 1, keys)
'''))
W598.append(("V5 the KIT line may name a later kit", '''        check("C: KIT = \\"S598 in stock_figure.py", 'KIT = "S598' in sf)
''', '''        check("C: KIT = \\"S598 in stock_figure.py (or a later kit's: S602 placed it since -- F-957)", bool(re.search(r'KIT = "S(59[89]|6[0-9][0-9])', sf)))
'''))
W598.append(("V6 the size names by their words (Marg prints the renamed sizes on the old bills since 19-Oct)", '''def hit_text(h, packs=None):
''', '''def _w(name):
    """S605 (F-957): a size name by its words -- 'KNEE SUPPORT HINGED M' and 'KNEE SUPPORT M HINGED' (the rename Marg now prints on the old
    bills' lines) are the same size."""
    return tuple(sorted(str(name or "").split()))


def hit_text(h, packs=None):
'''))
W598.append(("V7 line 3's family bill: the sizes by their words", '''h3 is None and bool(fb3) and SF._bill(fb3["bill"]) == "672" and fb3["date"] == "2026-09-28" and fb3["sizes"] == ["KNEE SUPPORT HINGED M", "KNEE SUPPORT HINGED L"], (h3, fb3))''',
             '''h3 is None and bool(fb3) and SF._bill(fb3["bill"]) == "672" and fb3["date"] == "2026-09-28" and [_w(x) for x in fb3["sizes"]] == [_w("KNEE SUPPORT HINGED M"), _w("KNEE SUPPORT HINGED L")], (h3, fb3))'''))
W598.append(("V8 line 1's bill line: its name by its words", '''bool(ha) and ha.get("how") == "a" and ha.get("units") == 1.0 and ha.get("seq") is not None and ha.get("name27") == "ANKLE BINDER BAMBOO L", ha)''',
             '''bool(ha) and ha.get("how") == "a" and ha.get("units") == 1.0 and ha.get("seq") is not None and _w(ha.get("name27")) == _w("ANKLE BINDER BAMBOO L"), ha)'''))
W598.append(("V9 the re-judge's audit rows: the walk's own run only (the live re-judge of 19-Oct left its own on the copy)", '''        before = line_rows(c, SEVEN)
        c.close()
        r = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "rejudge_s598.py"), "--fin", fin, "--db", dbp, "--json", JSONP], cwd="/tmp", capture_output=True, text=True, timeout=600)
''', '''        before = line_rows(c, SEVEN)
        aud0 = c.execute("SELECT COALESCE(MAX(id), 0) FROM purchase_audit").fetchone()[0]       # S605 (F-957): the walk's own run's rows only
        c.close()
        r = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "rejudge_s598.py"), "--fin", fin, "--db", dbp, "--json", JSONP], cwd="/tmp", capture_output=True, text=True, timeout=600)
'''))
W598.append(("V10 ... counted after aud0", '''        aud = {i: c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='line_rejudged_s598' AND ref=?", (str(i),)).fetchone()[0] for i in SEVEN}
''', '''        aud = {i: c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='line_rejudged_s598' AND ref=? AND id>?", (str(i), aud0)).fetchone()[0] for i in SEVEN}
'''))
W598.append(("V11 the owner's arrival clauses: the sizes by their words; XXX's family bill on an S605 spine", '''        ok = set(cl_) == set(want) and all(("(its bill %s of %s carried %s, not this size)" % (b, d, s)) in cl_[k] for k, (b, d, s) in want.items())
''', '''        if SW.Spine().q("SELECT 1 FROM sp_alias WHERE kind='rename_family' LIMIT 1"):   # S605 (F-951): after the split day the bills of the sizes are theirs;
            want[XXX] = (ROWS0[2]["billed_bill_no"], "07-10", "L S BELT XXL CONT GRAY UNI")   # the old key's newest family bill is 07-10's (the XXL size)

        def _clause(t):
            m = re.search(r"\\(its bill (\\S+) of (\\d\\d-\\d\\d) carried (.*), not this size\\)", t)
            return (m.group(1), m.group(2), sorted(_w(x) for x in m.group(3).split(", "))) if m else None
        ok = set(cl_) == set(want) and all(_clause(cl_[k]) == (b, d, sorted(_w(x) for x in s.split(", "))) for k, (b, d, s) in want.items())
'''))
W598.append(("V12 the dumps: Darpan's S605 section and today's shortage words", '''                elif path == "/finance/sanjeevni/api/needs-you":   # the arrival lines (the clause, the two added lines) and the shortage card's count
                    ok = all(("counted as arrived" in l) or re.match(r'^"count": \\d+,?$', l) or re.match(r'^"text": "Orthotic shortages: \\d+ items? -- order not sent",?$', l) for l in gone + new)
''', '''                elif path == "/finance/sanjeevni/api/needs-you":   # the arrival lines (the clause, the two added lines) and the shortage card's count
                    ok = all(("counted as arrived" in l) or re.match(r'^"count": \\d+,?$', l) or ("not offered for ordering" in l)
                             or ("waits for a purchase export taken after it" in l)          # S603's stock_watch line: S598's OLD stock_watch predates it
                             or re.search(r"the voucher proof has waited \\d+ hours", l)       # the clock between the two runs
                             or re.match(r'^"text": "Orthotic shortages: \\d+ items? -- (order not sent|an order is out, more still short)",?$', l) for l in gone + new)
'''))
W598.append(("V13 the dumps: Darpan's day API in S605's shape (the lines put to him)", '''                    ok = all((XL in l) or (XXX in l) or re.match(r'^"(n|short|shelf|keep|on_order|family_shelf|topup)": -?\\d+,?$', l) for l in gone + new)
''', '''                    ok = all((XL in l) or (XXX in l) or re.match(r'^"(n|short|shelf|keep|on_order|family_shelf|topup)": -?\\d+,?$', l)
                             or re.match(r'^("items": \\[\\]?,?|"approx": (true|false),?|[\\[\\]{},]+)$', l) for l in gone + new)   # S605 (D749): Darpan's section, its JSON shape
'''))
WALKS["walk_s598.py"] = ("deploy_kits/S598_ARRIVALS_BY_LINE/walk_s598.py", "9bb3fafacbba847c5e6ae7702aad199c", W598)
