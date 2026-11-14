#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s837.py ROOT_UNDER_TEST FINANCE_DB SAMPLE_REGISTER -- kit S837's walk on COPIES (never the live database). ROOT_UNDER_TEST holds
finance/ and marg_ingest/ as they would stand after the install. SAMPLE_REGISTER is a real Stock Register TEXT export (read name-free; nothing
of it is printed but counts). The copies are made in TMPDIR and removed at the end. Last line 'WALK n/m'."""
import datetime as dt, json, os, shutil, sqlite3, sys, tempfile

ROOT, DB, SAMPLE = sys.argv[1:4]
SYN = SAMPLE == "SYNTH"
FIN, ING = os.path.join(ROOT, "finance"), os.path.join(ROOT, "marg_ingest")
sys.path[:0] = [FIN, ING]
tmp = tempfile.mkdtemp(prefix="w837_")
ok = tot = 0


def check(name, cond):
    global ok, tot
    tot += 1
    ok += bool(cond)
    print("%s  %s" % ("PASS" if cond else "FAIL", name))


class Spy:
    """A sheet that records which cells were read (the patient and doctor columns must stay unread)."""
    def __init__(self, sh, mutate=None):
        self.sh, self.nrows, self.ncols, self.seen, self.mutate = sh, sh.nrows, sh.ncols, [], mutate or {}

    def cell_value(self, r, c):
        self.seen.append((r, c))
        return self.mutate.get((r, c), self.sh.cell_value(r, c))


try:
    import marg_register as MR                                     # noqa: E402
    import marg_router as RR                                       # noqa: E402 -- the door's own opener (.xls by xlrd, .xlsx by the stdlib)
    if SAMPLE == "SYNTH":                                          # on the box: a MADE-UP register (no real file is ever kept there)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import mkreg_s837                                          # noqa: E402
        SAMPLE = os.path.join(tmp, "STOCK_REGISTER_WALK.xlsx")
        mkreg_s837.build(SAMPLE)
    sh = RR.open_sheet(SAMPLE)
    # ============================================================ 1 the reader, name-free, with its witness
    sp = Spy(sh)
    rep = MR.read(sp)
    it = (rep.get("items") or [{}])[0]
    check("the real file is read: one item, %d entries, footers agree, no balance step without its entry" % len(it.get("lines", [])),
          rep.get("ok") and len(rep["items"]) == 1 and len(it["lines"]) >= 5 and it["ok"] == 1 and it["n_jumps"] == 0 and not it["note"])
    opening_rows = {r for r in range(sh.nrows) if str(sh.cell_value(r, 0)).strip() == "Opening"}
    bad = [(r, c) for r, c in sp.seen if c == 3 or (c == 2 and r not in opening_rows)]
    check("the Patient and Doctor columns are never read (the Opening row's date cell only)", not bad)
    check("every entry has its number, day and kind", all(l["bill_no"] and l["day"] and l["kind"] for l in it["lines"]))
    check("received - issued = closing - opening", it["received_u"] - it["issued_u"] == it["closing_u"] - it["opening_u"])
    # control: one entry's quantity one loose unit off -> a jump and the footer disagree
    r0 = next(r for r in range(sh.nrows) if str(sh.cell_value(r, 1)).strip() == "Sale")
    q = str(sh.cell_value(r0, 5)).split(":")
    mut = "%s:%d" % (q[0], int(q[1]) + 1) if len(q) == 2 else str(int(float(q[0])) + 1)
    rep2 = MR.read(Spy(sh, {(r0, 5): mut}))
    it2 = rep2["items"][0]
    check("CONTROL: one quantity changed by one unit -> a balance step without its entry, the footer disagrees", it2["n_jumps"] >= 1 and it2["ok"] == 0)
    rep3 = MR.read(Spy(sh, {(r, c): "" for r in range(min(sh.nrows, 30)) for c in (0, 1)}))
    check("CONTROL: no title -> not read, said so", not rep3["ok"] and "title" in rep3["reason"])
    check("the heading splits name and pack: 'FLEMCORT 6 1*10' -> FLEMCORT 6, 10; 'KNEE CAP XL' -> itself, 1",
          MR.split_heading("FLEMCORT 6 1*10") == ("FLEMCORT 6", "1*10", 10) and MR.split_heading("KNEE CAP XL") == ("KNEE CAP XL", "", 1))
    check("quantities: '40:0' at 10 = 400, '-2:10' = -30, '7' = 7", MR.units("40:0", 10) == 400 and MR.units("-2:10", 10) == -30 and MR.units("7", 10) == 7)
    kinds = {l["kind"] for l in it["lines"]}
    check("S2: every entry kind in the register is one the reader signs (%s)%s" % (", ".join(sorted(kinds)), "" if SYN else "; the real one holds Purchase, Sale Return, Sale"),
          kinds and all(MR.sign_of(k) != 0 for k in kinds) and (SYN or kinds <= {"Purchase", "Sale Return", "Sale"})
          and MR.sign_of("Purchase") == 1 and MR.sign_of("Sale Return") == 1 and MR.sign_of("Sale") == -1)

    class Mini:                                                    # a made-up register of three rows, built here (F-1423 S3, S4)
        def __init__(self, rows):
            self.rows, self.nrows, self.ncols = rows, len(rows), 8

        def cell_value(self, r, c):
            return self.rows[r][c] if c < len(self.rows[r]) else ""
    MROWS = [["STOCK REGISTER WHOLE FROM 01-09-2026 - 05-09-2026"], ["DEMO TAB 1*10"], ["Opening", "Balance as on", "01-09-2026", "", "", "", "", "5:0"],
             ["03-09-2026"], ["A000123", "Sale", "", "", "B1", "-1:0", "100.00", "4:0"], ["IR-7", "Issue Return", "", "", "B1", "0:5", "0", "4:5"],
             ["RR-2", "Receive Return", "", "", "B1", "0:5", "0", "4:0"], ["", "", "", "", "Received :", "0:5"], ["", "", "", "", "Issued :", "1:5"]]
    mi = MR.read(Mini(MROWS))["items"][0]
    check("S3: a row holding only a date sets the day of the entries under it (all on 03-Sep, not the opening's 01-Sep)",
          [l["day"] for l in mi["lines"]] == ["2026-09-03"] * 3)
    check("S3: Issue Return comes in, Receive Return goes out; footers agree, no balance step without its entry",
          [l["qty_u"] for l in mi["lines"]] == [-10, 5, -5] and mi["ok"] == 1 and mi["n_jumps"] == 0)
    mdb = sqlite3.connect(":memory:")
    MR.store(mdb, "m1", Mini(MROWS), "t1")

    def boom(_p):
        raise IOError("cannot open")
    MR.store_path(mdb, "m1", "x", "t2", boom)
    check("S4: a failed re-read of the same file leaves none of the earlier read's lines, and says 'not read'",
          mdb.execute("SELECT COUNT(*) FROM mi_register_line WHERE md5='m1'").fetchone()[0] == 0
          and mdb.execute("SELECT ok, note FROM mi_register WHERE md5='m1'").fetchone()[1].startswith("not read"))
    mdb.close()
    # ============================================================ 2 the door, both ways in
    db1 = os.path.join(tmp, "f1.db")
    shutil.copy(DB, db1)
    raw = open(SAMPLE, "rb").read()
    import hashlib                                                 # noqa: E402
    m5 = hashlib.md5(raw).hexdigest()
    c = sqlite3.connect(db1)
    c.execute("DELETE FROM mi_file WHERE md5=?", (m5,))
    c.commit()
    c.close()
    import marg_ingest as MI                                       # noqa: E402
    import marg_take as MT                                         # noqa: E402
    MI.WORK = os.path.join(tmp, "work")
    os.makedirs(MI.WORK, exist_ok=True)
    MT.LOCK_PATH = os.path.join(tmp, "lock")
    arch = os.path.join(tmp, "archive")
    os.makedirs(arch, exist_ok=True)
    res = MT.take(raw, os.path.basename(SAMPLE), source="walk", db=db1, archive=arch)
    c = sqlite3.connect(db1)
    g = c.execute("SELECT item, n_lines, n_jumps, ok, date_from, date_to FROM mi_register WHERE md5=? AND seq=1", (m5,)).fetchone()
    check("take(): TAKEN as STOCK_ITEM_LEDGER, VERIFIED (%s)" % res.get("status"), res.get("status") == "TAKEN" and res.get("type") == "STOCK_ITEM_LEDGER"
          and res.get("verdict") == "VERIFIED")
    check("take(): the register is kept name-free -- one item, its entries (%s)" % (g,), g and g[1] == len(it["lines"]) and g[2] == 0 and g[3] == 1)
    kept = [os.path.join(d, f) for d, _s, fs in os.walk(arch) for f in fs if f.lower().endswith((".xls", ".xlsx"))]
    check("take(): the file itself is NOT kept (S186)", not kept and res.get("kept") == 0)
    check("take(): mi_file says how many entries were read", c.execute("SELECT lines FROM mi_file WHERE md5=?", (m5,)).fetchone()[0] == len(it["lines"]))
    cols = {r[1] for t in ("mi_register", "mi_register_line") for r in c.execute("PRAGMA table_info(%s)" % t)}
    check("no column for a patient or a doctor exists", not [x for x in cols if "patient" in x or "doctor" in x or "name" in x])
    c.close()
    db2 = os.path.join(tmp, "f2.db")
    shutil.copy(DB, db2)
    c = sqlite3.connect(db2)
    c.execute("DELETE FROM mi_file WHERE md5=?", (m5,))
    c.commit()
    c.close()
    src = os.path.join(tmp, "src")
    os.makedirs(src)
    shutil.copy(SAMPLE, os.path.join(src, os.path.basename(SAMPLE)))
    arch2 = os.path.join(tmp, "archive2")
    MI.run(MI.DirSource(src), db2, archive=arch2, out=lambda *a: None)
    c = sqlite3.connect(db2)
    g2 = c.execute("SELECT n_lines FROM mi_register WHERE md5=? AND seq=1", (m5,)).fetchone()
    check("the collector (Drive route) reads it the same way", g2 and g2[0] == len(it["lines"]))
    kept2 = [f for d, _s, fs in os.walk(arch2) for f in fs if f.lower().endswith((".xls", ".xlsx"))]
    check("... and keeps no file either", not kept2)
    c.close()
    # ============================================================ 3 the Marg watch: the ask, the switch, the arrival, the row
    db3 = os.path.join(tmp, "f3.db")
    shutil.copy(DB, db3)
    con = sqlite3.connect(db3)
    con.row_factory = sqlite3.Row                                  # as the service's own connection (finance_app's get_db)
    for t in ("billwatch_act", "marg_watch_ask", "marg_watch_ask_row", "marg_watch_report", "mi_register", "mi_register_line"):
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
            con.execute("DELETE FROM %s" % t + (" WHERE fkey LIKE 'hand:%'" if t == "billwatch_act" else ""))
    con.execute("DELETE FROM setting WHERE key IN ('mwr.reg_shavez')")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('owner_notice.on', 'off')")
    con.commit()
    import marg_billwatch as BW                                    # noqa: E402
    BW.ensure(con)
    con.commit()
    check("ensure: the item column and the switch, Shavez OFF to start", "item" in {r[1] for r in con.execute("PRAGMA table_info(marg_watch_report)")}
          and BW.setting(con, "mwr.reg_shavez", "") == "off" and not BW.reg_shavez(con))
    V = BW.hand_view(con)
    rows = [r for r in V["counted"] if r.get("marg_to") not in (None, 0)]
    check("open moves to work with (%d)" % len(rows), len(rows) >= 3)
    n0 = len(V["counted"])
    rA, rB, rC = rows[0], rows[1], rows[2]
    okk, msg, code = BW.reg_ask_row(con, "manoj", int(rA["id"]))
    check("asked from a row (%s)" % msg, okk and "on your list" in msg and "Shavez" not in msg)
    check("... not twice", BW.reg_ask_row(con, "manoj", int(rA["id"]))[2] == 409)
    a = BW.reg_open(con)
    fr, to = BW._reg_span(rA)
    check("the ask names the item and the day before the move to its closing", len(a) == 1 and a[0]["item"] == BW._reg_norm(rA["item"])
          and a[0]["day_from"] == fr and a[0]["day_to"] == str(rA["day_to"])[:10] and not a[0]["arrived"])
    check("Shavez's sale card does not carry it (rpt_open: sale asks only)", BW.rpt_open(con) == [])
    check("Shavez's page gets nothing while his switch is OFF", BW.reg_for_shavez(con) == [])
    L = BW.reg_needs_lines(con)
    check("the Hub's Needs-you: one line for you, opening your list", len(L) == 1 and L[0]["href"] == BW.REG_TAKE and "for you to take" in L[0]["text"]
          and BW._reg_norm(rA["item"]) in L[0]["text"] and L[0]["cls"] == "warn")
    check("the Hub's Go to count: 1", BW.reg_count(con)[0] == 1)
    h = BW.hand_html(con)
    check("the row says Register asked; the strip names Stock Register and the switch", "Register asked" in h and "Stock Register" in h
          and "Turn Shavez on" in h and "Your list of reports to take" in h)
    check("the other rows carry the ask button", "mwRegAsk(this)" in h and ("Ask Marg's Stock Register — %s" % BW.esc(rB["item"])) in h)
    okk, msg, code = BW.reg_set_shavez(con, "manoj", True)
    check("Shavez ON (%s)" % msg, okk and BW.reg_shavez(con))
    S = BW.reg_for_shavez(con)
    check("... his page now carries the one ask", len(S) == 1 and S[0]["item"] == BW._reg_norm(rA["item"]))
    check("... and your Needs-you line waits a day (Shavez has it)", BW.reg_needs_lines(con) == [])
    con.execute("UPDATE marg_watch_report SET asked_at=? WHERE kind='REGISTER'", ((dt.datetime.now() - dt.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),))
    con.commit()
    L = BW.reg_needs_lines(con)
    check("... after a day not in, it is yours again", len(L) == 1 and "over a day ago" in L[0]["text"])
    BW.reg_set_shavez(con, "manoj", False)
    check("Shavez OFF again: his page empty", BW.reg_for_shavez(con) == [])
    # his own list: ask for any item
    today = dt.date.today()
    bad = [BW.reg_ask_item(con, "manoj", "", "2026-11-01", "2026-11-02"), BW.reg_ask_item(con, "manoj", "X", "2026-11-05", "2026-11-02"),
           BW.reg_ask_item(con, "manoj", "X", "2026-11-01", (today + dt.timedelta(days=1)).isoformat()),
           BW.reg_ask_item(con, "manoj", "X", "2026-01-01", "2026-11-02"), BW.reg_ask_item(con, "manoj", "X", "nope", "2026-11-02")]
    check("his ask box refuses an empty item, a reversed span, a day to come, over 92 days, a bad date", all(b[2] == 400 for b in bad))
    ITEM = it["item"]
    check("his ask box takes a good one (any spacing or case)", BW.reg_ask_item(con, "manoj", ITEM.lower().replace(" ", "  "), "2026-09-02", "2026-09-20")[0])
    # arrival: the real register for TYRO BR closes that ask; a register of another item or other days closes nothing
    MR.store(con, m5, sh, dt.datetime.now().isoformat())
    con.commit()
    n = BW.reg_sync(con)
    left = [x["item"] for x in BW.reg_open(con)]
    check("the register closes the %s ask by itself, and only that one (%d closed)" % (ITEM, n), n == 1 and ITEM not in left and len(left) == 1)
    # a register only Marg holds: a 'Stock Receive' entry equal to row B's move -> the row leaves the count
    def fake(md5, item, per, opening, lines, fr_, to_, ok_=1):
        MR.ensure(con)
        con.execute("INSERT INTO mi_register (md5, seq, item, pack, per, date_from, date_to, opening_u, closing_u, received_u, issued_u, n_lines, n_jumps, ok, note, stored_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (md5, 1, item, "", per, fr_, to_, opening, 0, 0, 0, len(lines),
                                                                 sum(1 for l in lines if l[5]), ok_, "" if ok_ else "Received footer 9, rows 8", dt.datetime.now().isoformat()))
        for i, (day, no, kind, q, bal, jump) in enumerate(lines, 1):
            con.execute("INSERT INTO mi_register_line (md5, seq, n, day, bill_no, kind, batch, qty_u, value_p, bal_u, jump_u) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (md5, 1, i, day, no, kind, "", q, None, bal, jump))
        con.commit()
    sB = int(round(float(rB["shift"])))
    dB = str(rB["day_to"])[:10]
    fake("fakeB", BW._reg_norm(rB["item"]), 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)],
         BW._day(rB["day_from"], -1), dB)
    sC = int(round(float(rC["shift"])))
    dC = str(rC["day_to"])[:10]
    fake("fakeC", BW._reg_norm(rC["item"]), 1, int(rC["marg_from"]), [(dC, "A009999", "Sale", -1, int(rC["marg_from"]) + sC - 1, sC)],
         BW._day(rC["day_from"], -1), dC)
    V2 = BW.hand_view(con)
    ids = {int(r["id"]) for r in V2["counted"]}
    exB = next((r for r in V2["explained"] if int(r["id"]) == int(rB["id"])), None)
    check("a voucher only Marg holds, equal to the move: the row leaves the count", int(rB["id"]) not in ids and exB is not None
          and exB["rec_kind"] == "marg_only" and "SR-0118" in exB["rec_note"] and len(V2["counted"]) == n0 - 1)
    rc = next((r for r in V2["counted"] if int(r["id"]) == int(rC["id"])), None)
    check("a balance that moved with no entry: the row stays counted, with Marg's word", rc is not None and rc["reg"]["kind"] == "jump"
          and "no entry for this" in rc["reg"]["note"])
    h = BW.hand_html(con)
    check("the page: 'An entry only in Marg's Stock Register' under Explained after all; the register table in the row; 'No entry in Marg either'",
          "An entry only in Marg&#39;s Stock Register" in h and "Marg's Stock Register — %s" % BW.esc(BW._reg_norm(rC["item"])) in h
          and "No entry in Marg either" in h and "the balance moved" in h)
    # CONTROL: a register of another item, or not covering the days, explains nothing
    con.execute("DELETE FROM mi_register WHERE md5='fakeB'")
    con.execute("DELETE FROM mi_register_line WHERE md5='fakeB'")
    fake("fakeB2", "SOMETHING ELSE ENTIRELY", 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)],
         BW._day(rB["day_from"], -1), dB)
    fake("fakeB3", BW._reg_norm(rB["item"]), 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)],
         BW._day(rB["day_from"], 5), BW._day(dB, 9))
    V3 = BW.hand_view(con)
    check("CONTROL: another item's register, or one not covering the days -> the row stays counted",
          int(rB["id"]) in {int(r["id"]) for r in V3["counted"]})
    fake("fakeB4", BW._reg_norm(rB["item"]), 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB + 3, int(rB["marg_from"]) + sB + 3, 0)],
         BW._day(rB["day_from"], -1), dB)
    V4 = BW.hand_view(con)
    check("CONTROL: a voucher of other units -> the row stays counted", int(rB["id"]) in {int(r["id"]) for r in V4["counted"]})
    # ---- F-1423: the cold review's three must-fixes, each with its control
    def clear(prefix):
        con.execute("DELETE FROM mi_register_line WHERE md5 LIKE ?", (prefix + "%",))
        con.execute("DELETE FROM mi_register WHERE md5 LIKE ?", (prefix + "%",))
        con.commit()
    clear("fakeB")
    mtB, frB, nmB = int(rB["marg_to"]), BW._day(rB["day_from"], -1), BW._reg_norm(rB["item"])
    fake("fakeM1", nmB, 10, mtB * 10 + 3 - sB, [(dB, "SR-0201", "Stock Receive", sB, mtB * 10 + 3, 0)], frB, dB)
    r5 = next((r for r in BW.hand_view(con)["counted"] if int(r["id"]) == int(rB["id"])), None)
    check("M1 CONTROL: a pack of 10 whose units Marg's balance does not prove -> no guess of 1; the row stays counted, settled by nothing",
          r5 is not None and r5["reg"] and r5["reg"]["kind"] == "unsure" and r5["reg"]["factor"] is None)
    clear("fakeM1")
    fake("fakeM1b", nmB, 10, mtB * 10 - sB * 10, [(dB, "SR-0202", "Stock Receive", sB * 10, mtB * 10, 0)], frB, dB)
    e6 = next((r for r in BW.hand_view(con)["explained"] if int(r["id"]) == int(rB["id"])), None)
    check("M1: a pack of 10 whose balance proves x10, with a voucher of the move's units -> explained", e6 is not None and e6["rec_kind"] == "marg_only"
          and e6["reg"]["factor"] == 10)
    clear("fakeM1b")
    fake("fakeM2", nmB, 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)], frB, dB, ok_=0)
    r7 = next((r for r in BW.hand_view(con)["counted"] if int(r["id"]) == int(rB["id"])), None)
    check("M2 CONTROL: a register whose own footers disagree -> the row stays counted; still shown in the row, saying it settles nothing",
          r7 is not None and r7["reg"]["kind"] == "unsure" and "do not add up" in r7["reg"]["note"]
          and ("Marg's Stock Register — %s" % BW.esc(nmB)) in BW.hand_html(con))
    okk, msg, code = BW.reg_ask_item(con, "manoj", rB["item"], frB, dB)
    check("M2: he can ask again over a faulty one (%s)" % msg, okk)
    check("M2 CONTROL: the faulty register does not close that ask", BW.reg_sync(con) == 0
          and any(a["item"] == nmB and not a["arrived"] for a in BW.reg_open(con)))
    fake("fakeM2b", nmB, 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)], frB, dB)
    check("M2: a sound register of the same days closes it", BW.reg_sync(con) == 1)
    clear("fakeM2")
    fake("fakeM3", nmB + " XR", 1, int(rB["marg_from"]), [(dB, "SR-0118", "Stock Receive", sB, int(rB["marg_from"]) + sB, 0)], frB, dB)
    check("M3 CONTROL: a register of '%s XR' explains nothing for %s" % (nmB, nmB),
          int(rB["id"]) in {int(r["id"]) for r in BW.hand_view(con)["counted"]})
    clear("fakeM3")
    A20, ONE, TWO = "ABCDEFGHIJKLMNOPQRST", "ABCDEFGHIJKLMNOPQRST ONE", "ABCDEFGHIJKLMNOPQRST TWO"
    check("M3 CONTROL: two items agreeing in their first 20 letters are not the same item", not BW._reg_same(ONE, TWO, known=[ONE, TWO]))
    check("M3: Marg's 20-letter cut is its one full name", BW._reg_same(A20, ONE, known=[ONE, "PAN 40"]))
    check("M3 CONTROL: an item whose own full name is exactly 20 letters is not its longer sibling", not BW._reg_same(A20, ONE, known=[A20, ONE]))
    check("M3 CONTROL: ... not when two known items share the cut, nor with no list, nor a shorter name",
          not BW._reg_same(A20, ONE, known=[ONE, TWO]) and not BW._reg_same(A20, ONE, known=[]) and not BW._reg_same("TYRO", "TYRO BR", known=["TYRO BR"]))
    # ---- F-1423 S6: a row whose days cannot be read -> 400
    _span = BW._reg_span
    BW._reg_span = lambda r: ("nope", "2026-11-01")
    try:
        check("S6: a row whose days cannot be read -> 400, not a fault", BW.reg_ask_row(con, "manoj", int(rB["id"]))[2] == 400)
    finally:
        BW._reg_span = _span
    # ============================================================ 4 the pages through Flask (the owner only)
    from flask import Flask                                        # noqa: E402
    app = Flask("w837")
    WHO = {"err": None}

    def req(*roles, **kw):
        return {"user": "manoj"}, WHO["err"]

    def getdb():
        return con
    BW.init(app, getdb, req)
    cl = app.test_client()
    r = cl.get(BW.REG_TAKE)
    t = r.get_data(as_text=True)
    check("his list page opens (200): To take, the switch, the ask box, Arrived with the register that came", r.status_code == 200 and "Marg reports for you to take" in t
          and "Turn Shavez on" in t and 'id="ritem"' in t and ("Marg's Stock Register — %s" % ITEM) in t)
    r = cl.post(BW.PAGE + "/api/register/ask", json={"item": "PAN 40", "from": "2026-11-01", "to": "2026-11-03"})
    check("the ask box through the door (200)", r.status_code == 200 and r.get_json()["ok"])
    r = cl.post(BW.PAGE + "/api/register/shavez", json={"on": "yes"})
    check("the switch door wants on or off (400)", r.status_code == 400)
    r = cl.post(BW.PAGE + "/api/register/shavez", json={"on": True})
    check("the switch door (200), Shavez ON", r.status_code == 200 and BW.reg_shavez(con))
    BW.reg_set_shavez(con, "manoj", False)
    tc = con.total_changes
    j = cl.get(BW.PAGE + "/api/register/count").get_json()
    BW.reg_needs_lines(con)
    check("S5: the Hub's count and Needs-you write nothing on their connection", con.total_changes == tc)
    check("the count for the Hub's Go to (%s)" % j.get("n"), j.get("ok") and j.get("n") >= 1 and "PAN 40" in j.get("title", ""))
    r = cl.get(BW.PAGE)
    t = r.get_data(as_text=True)
    check("the Marg watch page opens (200) with the two buttons' script", r.status_code == 200 and "function mwRegAsk" in t and "function mwRegShavez" in t
          and t.count("</body></html>") == 1)
    WHO["err"] = ("no", 403)
    check("a person who is not the owner gets nothing", cl.get(BW.REG_TAKE).status_code == 403
          and cl.post(BW.PAGE + "/api/register/ask", json={"row": 1}).status_code == 403)
    WHO["err"] = None
    # ============================================================ 5 Shavez's page and the Hub
    import reports_tile as RT                                      # noqa: E402
    con.commit()
    ro = sqlite3.connect("file:%s?mode=ro" % db3, uri=True)
    ro.row_factory = sqlite3.Row
    nro = BW.reg_count(ro)[0]
    check("S5: on a READ-ONLY connection the Hub's count (%d) and Needs-you line still work" % nro, nro >= 1 and nro == BW.reg_count(con)[0]
          and len(BW.reg_needs_lines(ro)) == 1)
    ro.close()
    con.close()
    con = sqlite3.connect(db3)
    con.row_factory = sqlite3.Row                                  # as the service opens it
    card_off = RT._s837_card(BW.reg_for_shavez(con))
    BW.reg_set_shavez(con, "manoj", True)
    s = RT.status(con)
    p = RT.render(s)
    check("Shavez's page: no card while OFF; the Hindi card while ON, above the day's count", card_off == "" and "Stock Register maanga hai" in p
          and "PAN 40" in p and p.count("id=s837reg") == 1)
    BW.reg_set_shavez(con, "manoj", False)
    p2 = RT.render(RT.status(con))
    check("... OFF again: gone", "s837reg" not in p2)
    import sanjeevni_approvals as SA                               # noqa: E402
    SA._unit = "medical"
    ny = SA.needs_you(con)
    hit = [l for l in ny.get("lines", []) if l.get("href") == BW.REG_TAKE]
    grp = [g for g in ny.get("groups", []) if any(l.get("href") == BW.REG_TAKE for l in g["lines"])]
    check("the Hub's Needs-you carries the line, in 'Marg & bank details'", len(hit) == 1 and grp and grp[0]["key"] == "marg" and not ny.get("groups_error"))
    os.environ["NEEDS_YOU_WITHOUT_S837"] = "1"
    check("... and an older kit's frozen walk (NEEDS_YOU_WITHOUT_S837) sees it unchanged", not [l for l in SA.needs_you(con).get("lines", []) if l.get("href") == BW.REG_TAKE])
    del os.environ["NEEDS_YOU_WITHOUT_S837"]
    html = open(os.path.join(FIN, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    check("the Hub's Go to: the line under Marg watch, and its count", 'href="/finance/sanjeevni/marg-watch/take">Marg reports for you to take' in html
          and "/finance/sanjeevni/marg-watch/api/register/count" in html and html.count('id="gotoReg"') == 1)
    BW.rpt_tick(con)
    check("the five-minute tick runs clean with both kinds of ask", True)
    con.close()
except Exception as e:                                             # noqa: BLE001
    import traceback
    traceback.print_exc()
    check("raised: %r" % (e,), False)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("WALK %d/%d" % (ok, tot))
