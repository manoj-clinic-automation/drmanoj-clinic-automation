#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_vouchers.py -- S963_STOCK_VOUCHERS (26-Nov-2026, Sanjeevni session 530; the owner's "proceed" of 16:16 IST on mock-up v4; D1083, D1084).

Marg's STOCK ISSUE and STOCK RECEIVE reports (Transactions > Stock Issue / Stock Receive > Modify > Alt+P > Report, Detail+Items, a period),
saved as text and converted on the medical PC by marg_txt S963 into the thirteen-column STOCK_VOUCHERS sheet, read at the server's door.

NAME-FREE: the sheet's PARTY cell is "cash" or "party" -- the medical PC never writes the name. Anything else in that cell means a name
may have come through: the sheet is then stored as 'not read' and none of its rows is kept.

THE WITNESS, again here (the PC's checks are not trusted): every line's units are one of the readings its quantity allows (a:b = a packs
of the packing's number after '*' plus b loose; a plain number packs or loose; '+' a free part); every voucher's lines come to its gross
amount; the vouchers come to the TOTAL row (gross and bill value); every day lies inside the title's period. One fails -> 'not read'.

KEPT (finance.db):  mi_voucher_file  one row per sheet (kind ISSUE/RECEIVE, period, counts, ok, note)
                    mi_voucher       one row per voucher (number, day, cash 1/0, gross and bill value in paise, lines)
                    mi_voucher_line  one row per item line (item as Marg cuts it, packing, per, batch, qty as printed, units, unit,
                                     expiry, rate and value in paise)
A LATER REPORT OF THE SAME DAYS REPLACES THEM, NEVER DOUBLES: the views mi_voucher_now / mi_voucher_line_now show, for each kind and day,
only the rows of the newest sound sheet whose period covers that day -- so a voucher deleted or edited in Marg is gone or changed there.
"Newest" is the latest EXPORT (the file's own stamp, YYYYmmdd-HHMMSS: a stale copy that arrives late -- a hand upload, a rescued
quarantine file, a retry -- never replaces a newer one; cold review S3), then the order of first storing (seq: the door's clock reads
only to the second). Re-reading the same bytes keeps its place.
A sheet that is NOT READ leaves a note starting "not read:" -- the door then keeps no file of it either (cold review S1). A store that
FAILED (the database busy) leaves no row and a note starting "failed:"; the five-minute collection reads it again (heal; S7).

S965 (F-1701): a text the medical PC held and retried carries two stamps in its name -- the retry's, then the export's own; the
EXPORT's wins (export_stamp), at the door and once more at every five-minute collection (restamp) for sheets already kept.

Stdlib only.  Called by marg_take.take() and marg_ingest.run() for a VERIFIED STOCK_VOUCHERS.   python3 marg_vouchers.py --selftest
"""
import re
import sys

KIT = "S963_STOCK_VOUCHERS + S964_VOUCHER_NAME_SHAPE"
HEAD = ["DATE", "VOUCHER", "PARTY", "ITEM NAME", "PACKING", "BATCH", "QTY", "UNIT", "EXPIRY", "RATE", "VALUE", "UNITS", "BILL VALUE"]
DDL = (
    "CREATE TABLE IF NOT EXISTS mi_voucher_file (md5 TEXT PRIMARY KEY, kind TEXT NOT NULL DEFAULT '', date_from TEXT NOT NULL DEFAULT '', "
    "date_to TEXT NOT NULL DEFAULT '', n_vouchers INTEGER NOT NULL DEFAULT 0, n_lines INTEGER NOT NULL DEFAULT 0, gross_p INTEGER, "
    "bill_p INTEGER, ok INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL DEFAULT '', stored_at TEXT NOT NULL, seq INTEGER NOT NULL DEFAULT 0, "
    "exported TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS mi_voucher (md5 TEXT NOT NULL, kind TEXT NOT NULL, no TEXT NOT NULL, day TEXT NOT NULL, cash INTEGER NOT NULL, "
    "gross_p INTEGER NOT NULL, bill_p INTEGER NOT NULL, n_lines INTEGER NOT NULL, PRIMARY KEY (md5, no))",
    "CREATE TABLE IF NOT EXISTS mi_voucher_line (md5 TEXT NOT NULL, kind TEXT NOT NULL, no TEXT NOT NULL, n INTEGER NOT NULL, "
    "day TEXT NOT NULL, item TEXT NOT NULL, packing TEXT NOT NULL DEFAULT '', per INTEGER NOT NULL DEFAULT 1, batch TEXT NOT NULL DEFAULT '', "
    "qty TEXT NOT NULL, units INTEGER NOT NULL, unit TEXT NOT NULL DEFAULT '', expiry TEXT NOT NULL DEFAULT '', rate_p INTEGER, "
    "value_p INTEGER, PRIMARY KEY (md5, no, n))",
    "CREATE INDEX IF NOT EXISTS ix_mi_voucher_line_item ON mi_voucher_line(item)",
    "CREATE INDEX IF NOT EXISTS ix_mi_voucher_day ON mi_voucher(kind, day)",
    "CREATE VIEW IF NOT EXISTS mi_voucher_now AS SELECT v.* FROM mi_voucher v WHERE v.md5 = (SELECT f.md5 FROM mi_voucher_file f "
    "WHERE f.ok = 1 AND f.kind = v.kind AND f.date_from <= v.day AND f.date_to >= v.day ORDER BY f.exported DESC, f.seq DESC LIMIT 1)",
    "CREATE VIEW IF NOT EXISTS mi_voucher_line_now AS SELECT l.* FROM mi_voucher_line l WHERE l.md5 = (SELECT f.md5 FROM mi_voucher_file f "
    "WHERE f.ok = 1 AND f.kind = l.kind AND f.date_from <= l.day AND f.date_to >= l.day ORDER BY f.exported DESC, f.seq DESC LIMIT 1)",
)
TITLE_RE = re.compile(r"^\s*STOCK\s+(ISSUE|RECEIVE)\s+FROM\s+(\d{2}-\d{2}-\d{4})\s+TO\s+(\d{2}-\d{2}-\d{4})\s*$", re.I)
DATE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
NO_RE = re.compile(r"^[A-Z]{1,2}\d{5,6}$")
QTY_RE = re.compile(r"^\d+(?::\d+)?(?:\+\d+(?::\d+)?)*$")
ITEM_RE = re.compile(r"^(?=.{1,24}$)[A-Z0-9(][\x21-\x7e]*(?: [\x21-\x7e]+)*$")   # Marg cuts a name at 24 letters; any printed mark
#   inside it (PRIME PAD 4" -- S964: an inch mark refused the 26-Nov receive report), single spaces, never a control or a double space
PACK_RE = re.compile(r"^(?:\d+\*\d+\.?|\d+(?:\.\d+)?(?:ML|GM|G|MG|L|KG|LTR)\.?|VAIL|VIAL|\d+)$")   # the PC's RE_VOU_PACK
BATCH_RE = re.compile(r"^[A-Z0-9-][A-Z0-9./-]*(?: [A-Z0-9./-]+)*$")   # one run of words, or empty
UNIT_RE = re.compile(r"^(?:[A-Z]{2,4}\.?)?$")
EXP_RE = re.compile(r"^(?:[A-Z][a-z]{2}-\d\d)?$")
PARTY_OK = ("cash", "party")
NOT_READ, FAILED = "not read: ", "failed: "


class NotRead(Exception):
    pass


def iso(d):
    m = DATE_RE.match(str(d or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def _txt(v):
    if isinstance(v, float) and v == int(v):
        return "%d" % int(v)
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def _paise(v):
    try:
        return int(round(float(str(v).replace(",", "")) * 100))
    except (TypeError, ValueError):
        return None


def readings(q, packing):
    """Every units reading a quantity as Marg prints it allows: 'a:b' = a packs of the number after '*' + b loose; a plain number packs
    or loose; '+' a free part. -> (sorted readings, per)."""
    m = re.search(r"\*(\d+)", packing or "")
    per = int(m.group(1)) if m and int(m.group(1)) > 0 else 1
    parts = [p.partition(":") for p in q.split("+")]
    scales = (per, 1) if any(b == "" for _a, _s, b in parts) and per != 1 else (1,)
    return sorted(set(sum(int(a) * per + int(b) if b != "" else int(a) * sc for a, _s, b in parts) for sc in scales)), per


def read(sh):
    """sh: an xlrd-like sheet. -> dict(kind, date_from, date_to, vouchers=[...], gross_p, bill_p). Raises NotRead with the reason."""
    def c(r, k):
        return sh.cell_value(r, k) if k < sh.ncols else ""
    if sh.nrows < 4:
        raise NotRead("too few rows")
    mt = TITLE_RE.match(_txt(c(0, 0)))
    if not mt:
        raise NotRead("the title is not a STOCK ISSUE / RECEIVE FROM .. TO .. title")
    kind, d_from, d_to = mt.group(1).upper(), iso(mt.group(2)), iso(mt.group(3))
    if not (d_from and d_to and d_from <= d_to):
        raise NotRead("the title's period cannot be read")
    if [_txt(c(1, k)) for k in range(len(HEAD))] != HEAD:
        raise NotRead("the column heads are not the voucher sheet's")
    vouchers, cur, total = [], None, None
    nos = set()
    for r in range(2, sh.nrows):
        row = [c(r, k) for k in range(len(HEAD))]
        t = [_txt(x) for x in row]
        if not any(t):
            continue
        if total is not None:
            raise NotRead("row %d: a row after the TOTAL" % (r + 1))
        if t[0] == "TOTAL":
            total = (_paise(row[10]), _paise(row[12]))
            if None in total:
                raise NotRead("row %d: the TOTAL cannot be read" % (r + 1))
            continue
        day = iso(t[0])
        if not day or not (d_from <= day <= d_to):
            raise NotRead("row %d: a day outside the title's period, or none" % (r + 1))
        if not NO_RE.match(t[1]):
            raise NotRead("row %d: no voucher number" % (r + 1))
        if t[3] == "":                                                   # a voucher's own row
            if t[2] not in PARTY_OK:
                raise NotRead("row %d: the party cell is not 'cash' or 'party' -- a name may have come through; nothing kept" % (r + 1))
            if t[1] in nos:
                raise NotRead("row %d: voucher %s twice" % (r + 1, t[1]))
            nos.add(t[1])
            if any(t[k] for k in (3, 4, 5, 6, 7, 8, 9, 11)):
                raise NotRead("row %d: a voucher row with a filled item cell" % (r + 1))
            g_, b_ = _paise(row[10]), _paise(row[12])
            if g_ is None or b_ is None:
                raise NotRead("row %d: the voucher's amounts cannot be read" % (r + 1))
            cur = dict(no=t[1], day=day, cash=1 if t[2] == "cash" else 0, gross_p=g_, bill_p=b_, lines=[])
            vouchers.append(cur)
            continue
        if cur is None or t[1] != cur["no"] or day != cur["day"]:
            raise NotRead("row %d: an item line not under its voucher" % (r + 1))
        if t[2] != "" or t[12] != "":
            raise NotRead("row %d: an item line carrying a party or bill-value cell" % (r + 1))
        if not ITEM_RE.match(t[3]) or not PACK_RE.match(t[4]) or (t[5] and not BATCH_RE.match(t[5])) or not UNIT_RE.match(t[7]) \
                or not EXP_RE.match(t[8]):
            raise NotRead("row %d: a cell not of its column's shape (item, packing, batch, unit or expiry)" % (r + 1))
        q = t[6].replace(" ", "")
        if not QTY_RE.match(q):
            raise NotRead("row %d: a quantity that cannot be read" % (r + 1))
        opts, per = readings(q, t[4])
        try:
            uf = float(row[11])
        except (TypeError, ValueError):
            raise NotRead("row %d: no units" % (r + 1))
        if uf != int(uf):
            raise NotRead("row %d: units not a whole number" % (r + 1))
        u = int(uf)
        if u not in opts:
            raise NotRead("row %d: %s -- %d units is not a reading of %s %s" % (r + 1, t[3], u, q, t[4]))
        rp, vp = _paise(row[9]), _paise(row[10])
        if rp is None or vp is None:
            raise NotRead("row %d: the rate or value cannot be read" % (r + 1))
        cur["lines"].append(dict(item=t[3].upper(), packing=t[4], per=per, batch=t[5], qty=q, units=u, unit=t[7], expiry=t[8],
                                 rate_p=rp, value_p=vp))
    if total is None:
        raise NotRead("no TOTAL row")
    if not vouchers:
        raise NotRead("no vouchers")
    for v in vouchers:
        if not v["lines"]:
            raise NotRead("voucher %s has no line" % v["no"])
        if abs(sum(x["value_p"] for x in v["lines"]) - v["gross_p"]) > len(v["lines"]):
            raise NotRead("voucher %s: its lines do not come to its gross amount" % v["no"])
    nv = len(vouchers)
    if abs(sum(v["gross_p"] for v in vouchers) - total[0]) > nv or abs(sum(v["bill_p"] for v in vouchers) - total[1]) > nv:
        raise NotRead("the vouchers do not come to the TOTAL row")
    return dict(kind=kind, date_from=d_from, date_to=d_to, vouchers=vouchers, gross_p=total[0], bill_p=total[1])


def ensure(con):
    for s in DDL:
        con.execute(s)


def _clear(con, md5):
    con.execute("DELETE FROM mi_voucher_line WHERE md5=?", (md5,))
    con.execute("DELETE FROM mi_voucher WHERE md5=?", (md5,))


def _first_stored(con, md5, when):  # noqa: D401
    """(stored_at, seq) of this sheet's first store; a new sheet takes the next seq."""
    row = con.execute("SELECT stored_at, seq FROM mi_voucher_file WHERE md5=?", (md5,)).fetchone()
    if row and row[0] and row[1]:
        return row[0], row[1]
    return when, (con.execute("SELECT COALESCE(MAX(seq), 0) FROM mi_voucher_file").fetchone()[0] or 0) + 1


def _migrate(con):
    cols = [r[1] for r in con.execute("PRAGMA table_info(mi_voucher_file)")]
    if "exported" not in cols:
        con.execute("ALTER TABLE mi_voucher_file ADD COLUMN exported TEXT NOT NULL DEFAULT ''")


def store(con, md5, sh, when, stamp=""):
    """Read the sheet and keep its vouchers under md5 (replacing an earlier read of the same bytes). -> (n lines, note).
    stamp: the export's own time (YYYYmmdd-HHMMSS) -- the newest export wins the days it covers."""
    ensure(con)
    _migrate(con)
    stamp = export_stamp(con, md5, stamp)                    # S965 (F-1701): the export's own stamp, not a retry's
    first, seq = _first_stored(con, md5, when)
    _clear(con, md5)
    try:
        rep = read(sh)
    except NotRead as ex:
        con.execute("INSERT OR REPLACE INTO mi_voucher_file (md5, ok, note, stored_at, seq, exported) VALUES (?,?,?,?,?,?)",
                    (md5, 0, NOT_READ + str(ex)[:200], first, seq, stamp or ""))
        return 0, NOT_READ + str(ex)[:200]
    n_all = 0
    for v in rep["vouchers"]:
        con.execute("INSERT INTO mi_voucher (md5, kind, no, day, cash, gross_p, bill_p, n_lines) VALUES (?,?,?,?,?,?,?,?)",
                    (md5, rep["kind"], v["no"], v["day"], v["cash"], v["gross_p"], v["bill_p"], len(v["lines"])))
        con.executemany("INSERT INTO mi_voucher_line (md5, kind, no, n, day, item, packing, per, batch, qty, units, unit, expiry, rate_p, "
                        "value_p) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [(md5, rep["kind"], v["no"], n, v["day"], x["item"], x["packing"], x["per"], x["batch"], x["qty"], x["units"],
                          x["unit"], x["expiry"], x["rate_p"], x["value_p"]) for n, x in enumerate(v["lines"], 1)])
        n_all += len(v["lines"])
    con.execute("INSERT OR REPLACE INTO mi_voucher_file (md5, kind, date_from, date_to, n_vouchers, n_lines, gross_p, bill_p, ok, note, "
                "stored_at, seq, exported) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (md5, rep["kind"], rep["date_from"], rep["date_to"], len(rep["vouchers"]), n_all, rep["gross_p"], rep["bill_p"], 1, "",
                 first, seq, stamp or ""))
    return n_all, ""


_TWO = re.compile(r"^(?:[A-Za-z]+__)?(\d{8}-\d{6})__(\d{8}-\d{6})__")      # MEDICAL__RETRY__EXPORT__... (cold review M2)
_ONE = re.compile(r"^(?:[A-Za-z]+__)?(\d{8}-\d{6})__")


def export_stamp(con, md5, stamp=""):
    """S965 (F-1701): the export's own time for this sheet, from the medical PC's file name (mi_file.drive_name, after its source folder
    word, e.g. MEDICAL__): two stamps = a
    held text retried (the retry's, then the export's -- the second wins); one = the export's. Else the stamp passed. Never raises."""
    try:
        for (nm,) in con.execute("SELECT drive_name FROM mi_file WHERE md5=?", (md5,)):
            m = _TWO.match(str(nm or "")) or _ONE.match(str(nm or ""))
            if m:
                return m.group(m.lastindex)
    except Exception:                                 # noqa: BLE001
        pass
    return stamp or ""


def restamp(con):
    """S965 (F-1701): every kept sheet's 'exported' set to its export's own stamp where the name tells it. -> rows changed. Never raises."""
    n = 0
    try:
        for md5, ex in con.execute("SELECT md5, exported FROM mi_voucher_file").fetchall():
            new = export_stamp(con, md5, ex)
            if new and new != ex:
                con.execute("UPDATE mi_voucher_file SET exported=? WHERE md5=?", (new, md5))
                n += 1
    except Exception:                                 # noqa: BLE001
        return n
    return n


def store_path(con, md5, path, when, open_sheet, stamp=""):
    """The door's call: never raises. -> (n lines, note). Inside a savepoint: a failure leaves nothing half-written. The database
    busy or locked -> no row at all, note 'failed: ...' (the collection's heal reads it again); any other fault -> 'not read: ...'."""
    import sqlite3
    try:
        con.execute("SAVEPOINT s963")
    except Exception as e:                            # noqa: BLE001
        return 0, FAILED + str(e)[:200]
    try:
        n, note = store(con, md5, open_sheet(path), when, stamp)
        con.execute("RELEASE s963")
        return n, note
    except sqlite3.OperationalError as e:
        try:
            con.execute("ROLLBACK TO s963")
            con.execute("RELEASE s963")
        except Exception:                             # noqa: BLE001
            pass
        return 0, FAILED + str(e)[:200]
    except Exception as e:                            # noqa: BLE001
        try:
            con.execute("ROLLBACK TO s963")
            ensure(con)
            _migrate(con)
            first, seq = _first_stored(con, md5, when)
            _clear(con, md5)
            con.execute("INSERT OR REPLACE INTO mi_voucher_file (md5, ok, note, stored_at, seq, exported) VALUES (?,?,?,?,?,?)",
                        (md5, 0, NOT_READ + str(e)[:200], first, seq, stamp or ""))
            con.execute("RELEASE s963")
        except Exception:                             # noqa: BLE001
            pass
        return 0, NOT_READ + str(e)[:200]


def heal(con, archive, open_sheet, when, limit=5):
    """S963 (cold review S7): a voucher sheet the door VERIFIED and KEPT but whose read failed (no mi_voucher_file row) is read
    again from the archive -- at most `limit` a run. Called by the five-minute collection. Never raises. -> sheets read."""
    import hashlib
    import os
    done = 0
    try:
        ensure(con)
        _migrate(con)
        restamp(con)                                        # S965 (F-1701)
        rows = con.execute("SELECT md5, server_name, date_from, stamp FROM mi_file WHERE type='STOCK_VOUCHERS' AND verdict='VERIFIED' "
                           "AND kept=1 AND md5 NOT IN (SELECT md5 FROM mi_voucher_file) ORDER BY received_at LIMIT ?", (limit,)).fetchall()
        for md5, name, d_from, stamp in rows:
            p = os.path.join(archive, "STOCK_VOUCHERS", (d_from or "unknown")[:7], name or "")
            ok_file = bool(name) and os.path.isfile(p)
            if ok_file:
                with open(p, "rb") as fh:
                    ok_file = hashlib.md5(fh.read()).hexdigest() == md5
            if not ok_file:                                 # marked, so it never blocks the sheets behind it (second look 3)
                first, seq = _first_stored(con, md5, when)
                con.execute("INSERT OR REPLACE INTO mi_voucher_file (md5, ok, note, stored_at, seq, exported) VALUES (?,?,?,?,?,?)",
                            (md5, 0, NOT_READ + "the archived file is missing or changed", first, seq, stamp or ""))
                done += 1
                continue
            n, note = store_path(con, md5, p, when, open_sheet, stamp or "")
            if note.startswith(NOT_READ):                   # not read: no file of it kept, as at the door (second look 1)
                try:
                    os.remove(p)
                except OSError:
                    pass
                con.execute("UPDATE mi_file SET kept=0 WHERE md5=?", (md5,))
            if not note.startswith(FAILED):
                done += 1
        con.commit()
    except Exception:                                 # noqa: BLE001
        pass
    return done


# ------------------------------------------------------------------------------------------------------------------ selftest
class _Sheet:
    def __init__(self, rows):
        self.rows = rows
        self.nrows = len(rows)
        self.ncols = max(len(r) for r in rows)

    def cell_value(self, r, c):
        row = self.rows[r]
        return row[c] if c < len(row) else ""


def _rows(kind="ISSUE", frm="01-10-2026", to="26-11-2026", party="cash"):
    return [["STOCK %s FROM %s TO %s" % (kind, frm, to)] + [""] * 12, list(HEAD),
            ["04-10-2026", "L000001", party, "", "", "", "", "", "", "", 899.0, "", 899.0],
            ["04-10-2026", "L000001", "", "ANKLE BINDER M BAMBOO", "1", "", "2", "ITE", "", 344.0, 688.0, 2.0, ""],
            ["04-10-2026", "L000001", "", "KNEE CAP UNISON M LYCRA", "1*1", "", "1", "ITE", "", 211.0, 211.0, 1.0, ""],
            ["15-10-2026", "L000002", "cash", "", "", "", "", "", "", "", 1980.95, "", 1981.0],
            ["15-10-2026", "L000002", "", "MEG QCS", "1*15", "TSF E1222", "2:14", "TAB", "May-28", 101.0, 296.27, 44.0, ""],
            ["15-10-2026", "L000002", "", "CCM", "1*40", "A954", "3", "TAB", "Nov-27", 561.56, 1684.68, 120.0, ""],
            ["TOTAL", "", "", "", "", "", "", "", "", "", 2879.95, "", 2880.0]]


def selftest():
    import sqlite3
    ok = True

    def ck(name, cond, got=None):
        nonlocal ok
        print(("  OK   " if cond else "  FAIL ") + name + ("" if got is None else "   [%s]" % (got,)))
        ok = ok and bool(cond)
    rep = read(_Sheet(_rows()))
    ck("a sound sheet: ISSUE, the period, 2 vouchers, 4 lines; CCM 3 of 1*40 = 120 units",
       rep["kind"] == "ISSUE" and (rep["date_from"], rep["date_to"]) == ("2026-10-01", "2026-11-26") and len(rep["vouchers"]) == 2
       and [x["units"] for v in rep["vouchers"] for x in v["lines"]] == [2, 1, 44, 120])
    for bad, why in ((_rows(party="RAJ TEST"), "a party cell that is a name"),
                     ([r if r[3] != "CCM" else r[:11] + [121.0, ""] for r in _rows()], "units not a reading of the quantity"),
                     ([r if r[3] != "MEG QCS" else r[:10] + [296.37] + r[11:] for r in _rows()], "a line changed (the gross fails)"),
                     ([r if r[0] != "TOTAL" else r[:12] + [2881.0] for r in _rows()], "the TOTAL altered"),
                     (_rows()[:-1], "no TOTAL"),
                     (_rows(frm="05-10-2026"), "a day outside the title's period"),
                     ([r if r[3] != "MEG QCS" else r[:5] + ["Raj  Kumar"] + r[6:] for r in _rows()], "a batch cell not of a batch's shape (cold review S2)"),
                     ([r if r[3] != "MEG QCS" else r[:11] + [44.9, ""] for r in _rows()], "units not a whole number"),
                     ([r if not (r[1] == "L000002" and r[3] == "") else r[:5] + ["X1"] + r[6:] for r in _rows()], "a filled cell on a voucher row")):
        try:
            read(_Sheet(bad))
            ck("not read: " + why, False)
        except NotRead as ex:
            ck("not read: %s -- %s" % (why, str(ex)[:60]), True)
    _inch = read(_Sheet([r if r[3] != "MEG QCS" else r[:3] + ['PRIME PAD 4"'] + r[4:] for r in _rows()]))
    ck("S964: a real name with an inch mark (PRIME PAD 4\") is read", [x["item"] for v in _inch["vouchers"] for x in v["lines"]][2] == 'PRIME PAD 4"')
    for _bad in ("A" * 25, "-PAD"):
        try:
            read(_Sheet([r if r[3] != "MEG QCS" else r[:3] + [_bad] + r[4:] for r in _rows()]))
            ck("S964: an item cell not of a name's shape is not read (%r)" % _bad, False)
        except NotRead:
            ck("S964: an item cell not of a name's shape is not read (%r)" % _bad, True)
    con = sqlite3.connect(":memory:")
    n, note = store(con, "a" * 32, _Sheet(_rows()), "2026-11-26T10:00:00")
    ck("stored: 4 lines, file ok", n == 4 and con.execute("SELECT ok, n_vouchers FROM mi_voucher_file").fetchone() == (1, 2))
    ck("the name-bearing sheet keeps NOTHING", store(con, "b" * 32, _Sheet(_rows(party="RAJ TEST")), "2026-11-26T10:01:00")[0] == 0
       and con.execute("SELECT COUNT(*) FROM mi_voucher WHERE md5=?", ("b" * 32,)).fetchone()[0] == 0
       and "RAJ" not in repr(con.execute("SELECT * FROM mi_voucher_file").fetchall()))
    later = [r for r in _rows(frm="10-10-2026") if r[1] != "L000001"]          # a later report from 10-10: L000002 only, CCM edited to 2
    later = [r if r[3] != "CCM" else r[:6] + ["2", "TAB", "Nov-27", 561.56, 1123.12, 80.0, ""] for r in later]
    later = [r if not (r[1] == "L000002" and r[3] == "") else r[:10] + [1419.39, "", 1419.0] for r in later]
    later = [r if r[0] != "TOTAL" else r[:10] + [1419.39, "", 1419.0] for r in later]
    store(con, "c" * 32, _Sheet(later), "2026-11-26T10:00:00")          # the SAME second as the first: the order decides
    now = con.execute("SELECT no, item, units FROM mi_voucher_line_now ORDER BY no, n").fetchall()
    ck("a later report of the same days replaces them, never doubles: L000001 (04-10, outside it) kept from the first; CCM now 80",
       now == [("L000001", "ANKLE BINDER M BAMBOO", 2), ("L000001", "KNEE CAP UNISON M LYCRA", 1), ("L000002", "MEG QCS", 44),
               ("L000002", "CCM", 80)], now)
    store(con, "a" * 32, _Sheet(_rows()), "2026-11-28T10:00:00")              # the first sheet's bytes read again later
    ck("re-reading the older bytes keeps their first time: the later report still wins",
       con.execute("SELECT units FROM mi_voucher_line_now WHERE item='CCM'").fetchone() == (80,))
    rec = _rows(kind="RECEIVE")
    store(con, "d" * 32, _Sheet([[c.replace("L0000", "AD000") if isinstance(c, str) else c for c in r] for r in rec]), "2026-11-27T11:00:00")
    ck("issue and receive are apart: a receive report replaces no issue",
       con.execute("SELECT COUNT(*) FROM mi_voucher_now WHERE kind='ISSUE'").fetchone()[0] == 2
       and con.execute("SELECT COUNT(*) FROM mi_voucher_now WHERE kind='RECEIVE'").fetchone()[0] == 2)
    con2 = sqlite3.connect(":memory:")
    store(con2, "e" * 32, _Sheet(_rows()), "2026-11-27T10:00:00", "20261126-1700")             # the newer export, stored first
    stale = [r if r[3] != "CCM" else r[:6] + ["2", "TAB", "Nov-27", 561.56, 1123.12, 80.0, ""] for r in _rows()]
    stale = [r if not (r[1] == "L000002" and r[3] == "") else r[:10] + [1419.39, "", 1419.0] for r in stale]
    stale = [r if r[0] != "TOTAL" else r[:10] + [2318.39, "", 2318.0] for r in stale]
    store(con2, "f" * 32, _Sheet(stale), "2026-11-27T11:00:00", "20261120-0900")               # an OLDER export arriving later
    ck("a stale export arriving later never replaces a newer one (cold review S3): CCM stays 120",
       con2.execute("SELECT units FROM mi_voucher_line_now WHERE item='CCM'").fetchone() == (120,))
    n_, note_ = store_path(con2, "g" * 32, "/nonexistent.xls", "2026-11-27T12:00:00", lambda p: _Sheet(_rows(party="RAJ TEST")))
    ck("a sheet not read says 'not read:' (the door then keeps no file of it)", n_ == 0 and note_.startswith(NOT_READ))

    class _Busy:
        def __init__(self, c):
            self.c, self.n = c, 0

        def execute(self, sql, *a):
            if sql.startswith("INSERT INTO mi_voucher_line"):
                raise sqlite3.OperationalError("database is locked")
            return self.c.execute(sql, *a)

        def executemany(self, sql, *a):
            if sql.startswith("INSERT INTO mi_voucher_line"):
                raise sqlite3.OperationalError("database is locked")
            return self.c.executemany(sql, *a)
    n_, note_ = store_path(_Busy(con2), "h" * 32, "x.xls", "2026-11-27T12:00:00", lambda p: _Sheet(_rows()))
    ck("the database busy half-way: 'failed:', nothing half-written, no file row (so it is read again) (cold review S7)",
       n_ == 0 and note_.startswith(FAILED) and con2.execute("SELECT COUNT(*) FROM mi_voucher WHERE md5=?", ("h" * 32,)).fetchone()[0] == 0
       and con2.execute("SELECT COUNT(*) FROM mi_voucher_file WHERE md5=?", ("h" * 32,)).fetchone()[0] == 0, note_[:40])
    print("SELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)
