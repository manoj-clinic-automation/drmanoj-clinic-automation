#!/usr/bin/env python3
# walk_s950.py -- kit S950_WRONG_BILL_FIXES: walks the kit's code on a COPY of finance.db (never the live one).
#   python walk_s950.py <code_dir> <copy.db> [control]      Last line: RESULT: ALL PASS | RESULT: n FAIL
#   The scans' readings are faked in memory (no assets database is opened); every row it writes is in the copy and made-up.
import os, re, sqlite3, subprocess, sys, tempfile

code, dbp = sys.argv[1], sys.argv[2]
sys.path.insert(0, code)
os.chdir(code)
FAILS, N = [], [0]


def chk(name, ok, info=""):
    N[0] += 1
    if ok:
        print("PASS %s" % name)
    else:
        FAILS.append(name)
        print("FAIL %s %s" % (name, str(info)[:140]))


con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
try:
    import order_d1053_msg as M
    import order_d1053 as D
except Exception as e:                                         # noqa: BLE001
    print("FAIL import %r" % (e,))
    print("RESULT: 1 FAIL")
    sys.exit(0)

def walk():
    chk("version 1.2", getattr(M, "VERSION", "") == "1.2", getattr(M, "VERSION", ""))
    chk("flow switch on in the copy", D.live(con))
    T = getattr(M, "token_on_order", None)
    chk("word rule exists", T is not None)
    if T:
        chk("UPRISE D3 carries UPRISE 6L INJ (F-1657)", T(con, "UPRISE D3 6L INJ INJ", ["DOLO 650", "UPRISE 6L INJ"]) == "UPRISE 6L INJ")
        chk("punctuation ignored", T(con, "UPRISE-D3 6L INJ.", ["UPRISE 6L INJ"]) == "UPRISE 6L INJ")
        chk("two-word name never by words", T(con, "PAN 40 D TAB", ["PAN 40"]) is None)
        chk("first word must agree", T(con, "NEO UPRISE 6L INJ", ["UPRISE 6L INJ"]) is None)
        chk("a missing word -> no match", T(con, "UPRISE D3 INJ", ["UPRISE 6L INJ"]) is None)
        chk("unrelated -> no match", T(con, "DOLO 650 TAB", ["UPRISE 6L INJ"]) is None)
        chk("a form word does not make three (PAN 40 TAB vs PAN D 40 TAB)", T(con, "PAN D 40 TAB", ["PAN 40 TAB"]) is None)
        chk("a variant word added by the bill refuses (FORTE)", T(con, "MECOVIXR FORTE 1500 INJ", ["MECOVIXR 1500 INJ"]) is None)
        chk("two words plus a form word, nothing added -> match", T(con, "FLORA BC CAP.", ["FLORA BC CAP"]) == "FLORA BC CAP")
        chk("an added letters-word refuses (ZERODOL SP TH TAB)", T(con, "ZERODOL SP TH TAB", ["ZERODOL SP TAB"]) is None)
        chk("an added digit-variant refuses (ZERODOL SP TH4 TAB)", T(con, "ZERODOL SP TH4 TAB", ["ZERODOL SP TAB"]) is None)
        chk("an added strength refuses (UPRISE 60K 6L INJ)", T(con, "UPRISE 60K 6L INJ", ["UPRISE 6L INJ"]) is None)
        chk("an added pack size refuses (UPRISE 6L INJ 10ML)", T(con, "UPRISE 6L INJ 10ML", ["UPRISE 6L INJ"]) is None)

    # order 130 is RADHA's UPRISE 6L INJ order in the bundle's copy; a made-up order is used when the copy lacks it
    o = con.execute("SELECT id, vendor, supplier_norm FROM purchase_order WHERE id=130").fetchone()
    OID = 130 if o and con.execute("SELECT 1 FROM purchase_order_line WHERE order_id=130 AND item='UPRISE 6L INJ'").fetchone() else None
    chk("the copy holds order 130 with UPRISE 6L INJ", OID is not None)
    M.ensure(con)
    # the walk's own made-up rows from an earlier run on this copy go first (so the control on the same copy is honest)
    con.execute("DELETE FROM order_d1053_billq WHERE scan BETWEEN 990001 AND 990009")
    con.execute("DELETE FROM order_d1053_msg WHERE ref LIKE 'walk%'")
    con.commit()
    con.execute("DELETE FROM purchase_order_line WHERE item='WALKTEST ZZQ 99 CAP'")
    con.execute("DELETE FROM purchase_order WHERE vendor='WALKTEST LATER ORDER'")
    con.commit()
    READS = {990001: [("UPRISE D3 6L INJ INJ", 12)], 990002: [("WALKTEST ZZQ 99 CAP", 2)], 990006: [("UPRISE D3 6L INJ INJ", 20)], 990007: []}
    M._reading = lambda scan: READS.get(int(scan))
    if OID:
        t = M._os().now_iso()
        for scan, item in ((990001, "UPRISE D3 6L INJ INJ"), (990002, "WALKTEST ZZQ 99 CAP"), (990006, "UPRISE D3 6L INJ INJ"),
                       (990007, "UPRISE D3 6L INJ INJ")):
            con.execute("INSERT OR IGNORE INTO order_d1053_billq (scan, order_id, stamp, vendor, item, kind, status, made_at) VALUES (?,?,?,?,?,?,?,?)",
                        (scan, OID, "B-%d" % scan, o["vendor"], item, "extra", "open", t))
        con.commit()
        html0 = M.wrong_bills_html(con) if hasattr(M, "wrong_bills_html") else ""
        chk("his page lists both open lines before the re-judge", "990001" in html0 and "990002" in html0, html0[:80])
        # a LATER order of the same dealer carrying the unknown item never excuses this bill (made-up order, dated far ahead)
        lo = con.execute("INSERT INTO purchase_order (vendor, supplier_norm, created_at, created_by, status, order_src) VALUES (?,?,?,?,?,?)",
                         ("WALKTEST LATER ORDER", o["supplier_norm"], "2099-01-01T10:00:00", "walk", "sent", "s454")).lastrowid
        con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size) VALUES (?,?,?,?)", (lo, "WALKTEST ZZQ 99 CAP", 1, 1))
        con.commit()
        n = M.rejudge_open(con) if hasattr(M, "rejudge_open") else -1
        st = {r[0]: r[1] for r in con.execute("SELECT scan, status FROM order_d1053_billq WHERE scan BETWEEN 990001 AND 990009")}
        chk("re-judge keeps a word-matched line that came MORE than ordered", st.get(990006) == "open", st)
        chk("re-judge keeps a line whose bill now reads empty", st.get(990007) == "open", st)
        chk("re-judge clears the UPRISE line", st.get(990001) == "cleared", st)
        chk("re-judge leaves the unrelated line open (a later order never excuses it)", st.get(990002) == "open", st)
        chk("re-judge cleared at least one", n >= 1, n)
        con.execute("DELETE FROM purchase_order_line WHERE order_id=?", (lo,))
        con.execute("DELETE FROM purchase_order WHERE id=?", (lo,))
        con.commit()
        html1 = M.wrong_bills_html(con)
        chk("his page: the cleared line gone, the open one there with its bill link",
            "990001" not in html1 and "/finance/porders/d1053/bill/990002" in html1 and "Wrong bills waiting (" in html1, html1[:120])
        dw = M.darpan_wrong(con)
        us = [x["url"] for x in dw if "99000" in x["url"]]
        chk("Darpan's list: the open lines only (not the cleared one)", "/finance/porders/d1053/bill/990001" not in us and "/finance/porders/d1053/bill/990002" in us, us)
        bp = M.bill_page_body(con, 990001, True) if hasattr(M, "rejudge_open") else ""
        chk("the bill page names a cleared line and offers no buttons", "matched by name" in bp and "d941(this" not in bp, bp[-160:])
        # judge_bill with faked readings: the UPRISE D3 name is on the order; an unknown name is 'extra'
        READS[990003] = [("UPRISE D3 6L INJ INJ", 12), ("WALKTEST ZZQ 99 CAP", 2)]
        got = M.judge_bill(con, OID, 990003, "B-990003")
        chk("judge: UPRISE D3 not 'extra'; the unknown is", [g[0] for g in got] == ["WALKTEST ZZQ 99 CAP"], got)
        READS[990004] = [("UPRISE D3 6L INJ INJ", 20)]
        got = M.judge_bill(con, OID, 990004, "B-990004")
        chk("judge: a word-matched line of this order still gets the quantity check (20 came, 12 ordered)",
            [(g[0], g[1]) for g in got] == [("UPRISE 6L INJ", "more")], got)
        READS[990005] = [("UPRISE 6L INJ", 12), ("UPRISE ZQ 6L INJ", 5)]
        got = M.judge_bill(con, OID, 990005, "B-990005")
        chk("judge: an ordered line already taken by another bill line is not taken twice", [g[0] for g in got] == ["UPRISE ZQ 6L INJ"], got)

    # messages today: one sent, one not delivered, one waiting (made-up rows, today)
    t = M._os().now_iso()
    for i, (sent, res) in enumerate(((t, '{"sent": 1, "failed": 0}'), (t, '{"sent": 0, "failed": 1}'), (None, None))):
        con.execute("INSERT OR IGNORE INTO order_d1053_msg (kind, ref, to_user, title, body, url, made_at, sent_at, result) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("H", "walk%d" % i, "manoj", "t", "b", "/", t, sent, res))
    con.commit()
    mh = M.messages_today_html(con) if hasattr(M, "messages_today_html") else ""
    nt = con.execute("SELECT COUNT(*) FROM order_d1053_msg WHERE substr(made_at,1,10)=?", (M._os().today().isoformat(),)).fetchone()[0]
    chk("messages today: the count of today's rows", ("Messages today (%d)" % nt) in mh, mh[:120])
    chk("messages today: not delivered and waiting shown", "not delivered" in mh and "waiting" in mh, mh[:200])
    chk("messages today: folded (details)", mh.startswith('<details id="d950msgs"'))

    oc = M.owner_card(con)
    chk("his card carries both new parts", 'id="d950msgs"' in oc and 'id="d950wrong"' in oc and 'id="d1053steps"' in oc, oc[:80])
    try:
        p = D.darpan_payload(con)
        chk("Darpan's payload carries 'wrong'", isinstance(p.get("wrong"), list) and any("990002" in x["url"] for x in p["wrong"]), list(p.keys()))
    except Exception as e:                                         # noqa: BLE001
        chk("Darpan's payload carries 'wrong'", False, repr(e))

    # darpan_kal.html: the line is drawn and every script still parses
    h = open(os.path.join(code, "darpan_kal.html"), encoding="utf-8").read()
    chk("Darpan's tab draws d950wrong", 'id="d950wrong"' in h and "d.wrong" in h)
    bad = 0
    import shutil                                              # noqa: PLC0415
    if shutil.which("node") is None:
        print("INFO node is not on this machine -- the scripts were parsed by node in the offline walk")
        return
    for i, s in enumerate(re.findall(r"<script>(.*?)</script>", h, re.S)):
        f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
        f.write(s)
        f.close()
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
        os.unlink(f.name)
        bad += r.returncode != 0
    chk("darpan_kal.html scripts parse (node --check)", bad == 0, bad)



try:
    walk()
except Exception as e:                                         # noqa: BLE001 -- a crash is a FAIL, never a pass
    chk("the walk ran to its end", False, repr(e))
con.close()
print("RESULT: ALL PASS" if not FAILS else "RESULT: %d FAIL" % len(FAILS))
