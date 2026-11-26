#!/usr/bin/env python3
"""walk_s963.py -- S963_STOCK_VOUCHERS: the door, end to end, on MADE-UP voucher reports (no real file is ever kept on the box).
    python3 walk_s963.py ROOT KIT_DIR
ROOT holds marg_ingest/ (the rebuilt files, or the live ones for the control); KIT_DIR holds medical/marg_txt.py (the PC's reader S963,
used here only to make the .XLS the medical PC would send). A fresh scratch database and archive; the door's own lock is pointed at a
scratch file, so the five-minute collection is never blocked. Last line: WALK passed/total."""
import importlib.util, os, sqlite3, sys, tempfile

ROOT, KIT = sys.argv[1], sys.argv[2]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]   # never the kit's own copies
sys.path.insert(0, os.path.join(ROOT, "marg_ingest"))
TMP = tempfile.mkdtemp(prefix="walk_s963_")
res = []


def ck(name, cond, got=None):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if got is None else "   [%s]" % (got,)))


sp = importlib.util.spec_from_file_location("marg_txt_s963", os.path.join(KIT, "medical", "marg_txt.py"))
MT = importlib.util.module_from_spec(sp)
sp.loader.exec_module(MT)
import marg_take as T                                          # noqa: E402
import marg_router as R                                        # noqa: E402
T._Lock.__init__.__defaults__ = (os.path.join(TMP, "lock"), 5)
DB, ARCH = os.path.join(TMP, "walk.db"), os.path.join(TMP, "archive")
os.makedirs(ARCH, exist_ok=True)
SIGS = R.load_signatures(os.path.join(ROOT, "marg_ingest", "signatures.json"))


def xls(raw):
    return MT.convert(raw)[0]


def ident(x, name):
    p = os.path.join(TMP, name)
    open(p, "wb").write(x)
    cfg = {"archive": os.path.join(TMP, "arch_id"), "outbox": os.path.join(TMP, "ob"), "dry": True,
           "index": os.path.join(TMP, "arch_id", "index.csv")}
    os.makedirs(cfg["archive"], exist_ok=True)
    return R.process(p, SIGS, cfg, {}, lambda *a: None) or {}


def q(sql, *a):
    con = sqlite3.connect(DB)
    try:
        return con.execute(sql, a).fetchall()
    except sqlite3.OperationalError as ex:
        return "no table (%s)" % ex
    finally:
        con.close()


ISS = MT._vou_sample("ISSUE")
REC = MT._vou_sample("RECEIVE").replace(b" L00000", b" AD0000")
xi, xr = xls(ISS), xls(REC)

MV = None
try:
    _s = importlib.util.spec_from_file_location("mv_under_test", os.path.join(ROOT, "marg_ingest", "marg_vouchers.py"))
    MV = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(MV)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MV.selftest()
    ck("C1 the new reader's own selftest", rc == 0, buf.getvalue().strip().splitlines()[-1])
except Exception as ex:                                          # noqa: BLE001
    ck("C1 the new reader's own selftest", False, "%s: %s" % (type(ex).__name__, str(ex)[:60]))

r1 = ident(xi, "S963_ISSUE.XLS")
ck("C2 the door's router: a stock issue sheet is STOCK_VOUCHERS / ISSUE, VERIFIED, dated by its title 2026-10-01..2026-11-26",
   (r1.get("type"), r1.get("variant"), r1.get("verdict"), r1.get("date_from"), r1.get("date_to"))
   == ("STOCK_VOUCHERS", "ISSUE", "VERIFIED", "2026-10-01", "2026-11-26"), (r1.get("type"), r1.get("verdict"), (r1.get("reason") or "")[:50]))
r2 = ident(xr, "S963_RECEIVE.XLS")
ck("C3 ... and a stock receive sheet STOCK_VOUCHERS / RECEIVE, VERIFIED", (r2.get("type"), r2.get("variant"), r2.get("verdict"))
   == ("STOCK_VOUCHERS", "RECEIVE", "VERIFIED"), (r2.get("type"), r2.get("verdict")))

t1 = T.take(xi, "S963_ISSUE.XLS", source="test", db=DB, archive=ARCH)
ck("C4 marg_take.take(): TAKEN, STOCK_VOUCHERS, VERIFIED, 6 lines read, the file kept (name-free)",
   (t1.get("status"), t1.get("type"), t1.get("verdict"), t1.get("lines"), t1.get("kept")) == ("TAKEN", "STOCK_VOUCHERS", "VERIFIED", 6, 1),
   (t1.get("status"), t1.get("type"), t1.get("lines"), t1.get("kept"), (t1.get("reason") or "")[:40]))
ck("C5 kept: one sound file, 3 vouchers (2 cash, 1 party), 6 lines; MEG QCS 2:14 = 44 units",
   q("SELECT kind, n_vouchers, n_lines, ok FROM mi_voucher_file") == [("ISSUE", 3, 6, 1)]
   and q("SELECT SUM(cash), COUNT(*) FROM mi_voucher_now") == [(2, 3)]
   and q("SELECT units FROM mi_voucher_line_now WHERE item='MEG QCS'") == [(44,)], q("SELECT kind, n_vouchers, n_lines, ok FROM mi_voucher_file"))
t1b = T.take(xi, "S963_ISSUE_again.XLS", source="test", db=DB, archive=ARCH)
ck("C6 the same bytes again: ALREADY, nothing doubled", t1b.get("status") == "ALREADY"
   and q("SELECT COUNT(*) FROM mi_voucher_line") == [(6,)], (t1b.get("status"), q("SELECT COUNT(*) FROM mi_voucher_line")))
t2 = T.take(xr, "S963_RECEIVE.XLS", source="test", db=DB, archive=ARCH)
ck("C7 a stock receive report: TAKEN, kept apart from the issues", t2.get("status") == "TAKEN"
   and q("SELECT kind, COUNT(*) FROM mi_voucher_now GROUP BY kind ORDER BY kind") == [("ISSUE", 3), ("RECEIVE", 3)],
   q("SELECT kind, COUNT(*) FROM mi_voucher_now GROUP BY kind ORDER BY kind"))
rows = MT.voucher_rows(ISS)
named = [r[:2] + ["RAJ TEST"] + r[3:] if r[2] == "party" else r for r in rows]
xn = MT.ole2(MT.workbook_stream(named))
t3 = T.take(xn, "S963_NAMED.XLS", source="test", db=DB, archive=ARCH)
md5n = t3.get("md5", "")
_left = [os.path.join(d, f) for d, _s, fs in os.walk(ARCH) for f in fs if open(os.path.join(d, f), "rb").read().find(b"RAJ") >= 0]
ck("C8 a sheet with a person's name in its party cell keeps NOTHING of it: no voucher, no line, the name in no table, no file kept",
   t3.get("status") == "TAKEN" and t3.get("kept") == 0 and not _left and q("SELECT ok FROM mi_voucher_file WHERE md5=?", md5n) == [(0,)]
   and q("SELECT COUNT(*) FROM mi_voucher WHERE md5=?", md5n) == [(0,)]
   and "RAJ" not in repr(q("SELECT * FROM mi_voucher_file")) + repr(q("SELECT * FROM mi_voucher")) + repr(q("SELECT * FROM mi_voucher_line")),
   (t3.get("status"), q("SELECT ok, substr(note,1,40) FROM mi_voucher_file WHERE md5=?", md5n)))
later = [r for r in rows if r[1] != "L000001" and r[0] != "TOTAL"]
later[0] = ["STOCK ISSUE FROM 10-10-2026 TO 26-11-2026"] + [""] * 12
later = [r if r[3] != "BLADE" else r[:6] + ["90", "", "", 5.0, 450.0, 90.0, ""] for r in later]
later = [r if not (r[1] == "L000002" and r[3] == "") else r[:10] + [746.27, "", 746.0] for r in later]
later.append(["TOTAL", "", "", "", "", "", "", "", "", "", 1254.89, "", 1255.0])
t4 = T.take(MT.ole2(MT.workbook_stream(later)), "S963_LATER.XLS", source="test", db=DB, archive=ARCH)
now = q("SELECT no, item, units FROM mi_voucher_line_now WHERE kind='ISSUE' ORDER BY no, n")
ck("C9 a later report of the same days replaces them, never doubles: BLADE now 90, L000001 (04-10, before it) kept from the first",
   t4.get("status") == "TAKEN" and now == [("L000001", "ANKLE BINDER M BAMBOO", 2), ("L000001", "KNEE CAP UNISON M LYCRA", 1),
                                            ("L000002", "MEG QCS", 44), ("L000002", "BLADE", 90), ("L000003", "OSTOVAXL DM", 25),
                                            ("L000003", "ENZOMAC OINTMEN", 2)], now)
md51 = t1.get("md5", "")
_c = sqlite3.connect(DB)
try:
    _c.execute("DELETE FROM mi_voucher_line WHERE md5=?", (md51,))
    _c.execute("DELETE FROM mi_voucher WHERE md5=?", (md51,))
    _c.execute("DELETE FROM mi_voucher_file WHERE md5=?", (md51,))
    _c.commit()
    _h = MV.heal(_c, ARCH, R.open_sheet, "2026-11-26T18:00:00+05:30")
except Exception as ex:                                          # noqa: BLE001
    _h = "%s: %s" % (type(ex).__name__, str(ex)[:50])
_c.close()
ck("C11 a voucher sheet whose read failed is read again from the archive by the collection (heal): its 6 lines back",
   _h == 1 and q("SELECT COUNT(*) FROM mi_voucher_line WHERE md5=?", md51) == [(6,)], _h)
src = open(os.path.join(ROOT, "marg_ingest", "marg_ingest.py"), encoding="utf-8").read()
ck("C10 the five-minute collection carries the same hook (marg_ingest.run): STOCK_VOUCHERS -> marg_vouchers.store_path",
   'if typ == "STOCK_VOUCHERS" and verdict == "VERIFIED" and not dry:' in src and "marg_vouchers.store_path(con, f[\"md5\"], local" in src
   and "marg_vouchers.heal(con, cfg[\"archive\"]" in src)
print("WALK %d/%d" % (sum(res), len(res)))
